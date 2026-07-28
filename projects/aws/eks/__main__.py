import base64
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s
import lbrlabs_pulumi_eks as eks
import yaml
import ip_calc
import context

PROJECT_NAME = pulumi.get_project()
STACK = pulumi.get_stack()
PULUMI_CONFIG = pulumi.Config("pulumi")
RESOURCE_PREFIX = PULUMI_CONFIG.require("resourcePrefix")

CONFIG = pulumi.Config()
PULUMI_CONFIG = pulumi.Config("pulumi")

TAGS = {
    "environment": STACK,
    "project": PROJECT_NAME,
    "owner": "lbriggs",
    "deployed_by": "pulumi",
    "tailscale_org": "lbrlabs.com",
}

VPC_STACK = CONFIG.get("vpcStack", "lbrlabs/demo-aws-vpc/west")
vpc_stack = pulumi.StackReference(VPC_STACK)
VPC_ID = vpc_stack.require_output("vpc_id")
PUBLIC_SUBNET_IDS = vpc_stack.require_output("public_subnet_ids")
PRIVATE_SUBNET_IDS = vpc_stack.require_output("private_subnet_ids")

AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")

CONFIG = pulumi.Config("")
ADMIN_ROLE_NAME = CONFIG.require("admin_role_name")


NAME = "-".join(REGION.split("-")[:2])

CONFIG = pulumi.Config()
CLUSTER_ENDPOINT_PRIVATE_ACCESS = CONFIG.get_bool(
    "cluster_endpoint_private_access", default=True
)
CLUSTER_ENDPOINT_PUBLIC_ACCESS = CONFIG.get_bool(
    "cluster_endpoint_public_access", default=True
)
KARPENTER_VERSION = CONFIG.get("karpenter_version", "1.13.0")

ADMIN_ACCESS_PRINCIPAL = aws.iam.get_role_output(name=ADMIN_ROLE_NAME)

ENABLE_SPOT_INSTANCE = CONFIG.get_bool("enable_spot_instance", default=False)


def check_kubernetes_api_connection(kubeconfig: str) -> str:
    parsed_kubeconfig = yaml.safe_load(kubeconfig)
    clusters = parsed_kubeconfig.get("clusters", [])
    if not clusters:
        raise pulumi.RunError("Could not find a Kubernetes API server in kubeconfig.")

    cluster_config = clusters[0].get("cluster", {})
    server = cluster_config.get("server")
    if not server:
        raise pulumi.RunError("Could not find a Kubernetes API server in kubeconfig.")

    parsed_server = urlparse(server)
    host = parsed_server.hostname
    if host is None:
        raise pulumi.RunError(f"Could not parse Kubernetes API server host from {server!r}.")

    users = parsed_kubeconfig.get("users", [])
    exec_args = users[0].get("user", {}).get("exec", {}).get("args", []) if users else []
    cluster_name = "unknown"
    if "--cluster-name" in exec_args:
        cluster_name_index = exec_args.index("--cluster-name")
        if len(exec_args) > cluster_name_index + 1:
            cluster_name = exec_args[cluster_name_index + 1]
    healthz_url = f"{server.rstrip('/')}/healthz"
    ca_data = cluster_config.get("certificate-authority-data")
    ssl_context = None
    if ca_data is not None:
        ssl_context = ssl.create_default_context(cadata=base64.b64decode(ca_data).decode())

    try:
        request = Request(healthz_url, headers={"Accept": "text/plain"})
        with urlopen(request, timeout=5, context=ssl_context) as response:
            body = response.read().decode().strip()
            if response.status != 200 or body != "ok":
                raise pulumi.RunError(
                    f"Kubernetes API health check at {healthz_url} returned "
                    f"HTTP {response.status} with body {body!r}."
                )

            pulumi.log.info(
                f"Successfully checked Kubernetes API health at {healthz_url}",
                ephemeral=True,
            )
    except HTTPError as e:
        body = e.read().decode(errors="replace").strip()
        message = (
            f"Kubernetes API health check at {healthz_url} returned HTTP {e.code}. "
            f"Make sure Tailscale is connected and the kubeconfig points at the "
            f"current cluster endpoint for {cluster_name}: {body}"
        )
        pulumi.log.error(message)
        raise pulumi.RunError(message) from e
    except (OSError, TimeoutError, URLError, ssl.SSLError) as e:
        message = (
            f"Could not reach Kubernetes API health endpoint at {healthz_url}. "
            f"Make sure Tailscale is connected and the kubeconfig points at the "
            f"current cluster endpoint for {cluster_name}: {e}"
        )
        pulumi.log.error(message)
        raise pulumi.RunError(message) from e

    return kubeconfig


cluster = eks.Cluster(
    f"{RESOURCE_PREFIX}-{NAME}",
    cluster_version="1.35",
    cluster_subnet_ids=PRIVATE_SUBNET_IDS,
    system_node_subnet_ids=PRIVATE_SUBNET_IDS,
    system_node_instance_types=["t3.medium"],
    system_node_desired_count=2,
    cluster_endpoint_public_access=CLUSTER_ENDPOINT_PUBLIC_ACCESS,
    cluster_endpoint_private_access=CLUSTER_ENDPOINT_PRIVATE_ACCESS,
    enable_external_ingress=False,
    enable_internal_ingress=False,
    karpenter_version=KARPENTER_VERSION,
    admin_access_principal=ADMIN_ACCESS_PRINCIPAL.arn,
    lets_encrypt_email="lets-encrypt@lbrlabs.com",
    tags=TAGS,
)

# retrieve the security group used for node to node communitation
sg = cluster.control_plane.vpc_config.cluster_security_group_id
vpc = aws.ec2.get_vpc_output(id=VPC_ID)

# allow all access from inside the VPC cidr
ingress = aws.ec2.SecurityGroupRule(
    f"lbr-{NAME}-allow-vpc-traffic",
    type="ingress",
    to_port=0,
    from_port=0,
    protocol="all",
    security_group_id=sg,
    cidr_blocks=[vpc.cidr_block],
)

# create a provider
# we need to wait for the ingress sg rule so we can use it
provider = k8s.Provider(
    f"{RESOURCE_PREFIX}-{NAME}",
    kubeconfig=pulumi.Output.all(cluster.kubeconfig, ingress.id).apply(
        lambda args: check_kubernetes_api_connection(args[0])
    ),
    opts=pulumi.ResourceOptions(depends_on=[ingress]),
)

context.resource_name = f"{RESOURCE_PREFIX}-{NAME}"
context.parent = cluster
context.provider = provider
context.stack = STACK
context.tags = TAGS
context.cluster_issuer = cluster.oidc_provider.url.apply(
    lambda issuer: issuer if issuer.startswith("https://") else f"https://{issuer}"
)

import tailscale  # noqa: E402

requirements = [
    eks.RequirementArgs(
        key="kubernetes.io/arch",
        operator="In",
        values=["amd64"],
    ),
    eks.RequirementArgs(
        key="kubernetes.io/os",
        operator="In",
        values=["linux"],
    ),
    eks.RequirementArgs(
        key="karpenter.k8s.aws/instance-family",
        operator="In",
        values=["t3"],
    ),
    eks.RequirementArgs(
        key="karpenter.k8s.aws/instance-size",
        operator="In",
        values=["medium"],
    ),
]

if ENABLE_SPOT_INSTANCE:
    requirements.append(
        eks.RequirementArgs(
            key="lbrlabs.com/spot",
            operator="In",
            values=["true"],
        )
    )


# create a karpenter autoscaling group
workload = eks.AutoscaledNodeGroup(
    f"{RESOURCE_PREFIX}-{NAME}-private",
    node_role=cluster.karpenter_node_role.name,
    security_group_ids=[cluster.control_plane.vpc_config.cluster_security_group_id],
    subnet_ids=PRIVATE_SUBNET_IDS,
    requirements=requirements,
    disruption=eks.DisruptionConfigArgs(),
    opts=pulumi.ResourceOptions(
        provider=provider,
    ),
)

pulumi.export("kubeconfig", cluster.kubeconfig)
pulumi.export("cluster_name", cluster.cluster_name)
pulumi.export("tailscale_operator_federated_identity_audience", tailscale.federated_identity.audience)
pulumi.export("tailscale_operator_federated_identity_client_id", tailscale.federated_identity.id)
pulumi.export("tailscale_operator_federated_identity_subject", tailscale.federated_identity.subject)
