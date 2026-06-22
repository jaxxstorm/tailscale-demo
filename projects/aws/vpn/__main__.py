import sys
from pathlib import Path

import pulumi
import pulumi_aws as aws
import pulumi_cloudinit_tailscale as cloudinit_tailscale

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from components import AutoScalingEC2, AutoScalingEC2Args  # noqa: E402

import context

PROJECT_NAME = pulumi.get_project()
STACK = pulumi.get_stack()

AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")
REGION_SHORT_NAME = "-".join(REGION.split("-")[:2])

CONFIG = pulumi.Config()
PULUMI_CONFIG = pulumi.Config("pulumi")

RESOURCE_PREFIX = PULUMI_CONFIG.require("resourcePrefix")
VPC_STACK = CONFIG.get("vpcStack", "lbrlabs/demo-aws-vpc/west")
INSTANCE_TYPE = CONFIG.get("instanceType") or "t4g.nano"
DESIRED_CAPACITY = CONFIG.get_int("desiredCapacity") or 1
MIN_SIZE = CONFIG.get_int("minSize") or 1
MAX_SIZE = CONFIG.get_int("maxSize") or 1
AMI_ID = CONFIG.get("amiId")
ADVERTISE_TAGS = CONFIG.get_object("advertiseTags") or ["tag:subnet-router"]
RELAY_SERVER_PORT = CONFIG.get_int("relayServerPort")
TRACK = CONFIG.get("track") or "stable"
ENABLE_TAILSCALE_SSH = CONFIG.get_bool("enableTailscaleSsh") or False
TAILSCALE_ISSUER = CONFIG.get("tailscaleIssuer")
if TAILSCALE_ISSUER in (None, "", "default", "https://sts.amazonaws.com"):
    raise pulumi.RunError(
        "`tailscaleIssuer` must be the AWS OIDC issuer URL shown by the "
        "Tailscale trust credentials UI, for example "
        "`https://abc123-def456-ghi789-jkl012.tokens.sts.global.api.aws`. "
        "`https://sts.amazonaws.com` is the STS API endpoint, not an OIDC issuer."
    )
TAILSCALE_SCOPES = CONFIG.get_object("tailscaleScopes") or ["auth_keys", "devices:core"]

TAGS = {
    "environment": STACK,
    "project": PROJECT_NAME,
    "owner": "lbriggs",
    "deployed_by": "pulumi",
    "org": "lbrlabs",
}

vpc_stack = pulumi.StackReference(VPC_STACK)
vpc_id = vpc_stack.require_output("vpc_id")
vpc_cidr_block = vpc_stack.require_output("cidr_block")
subnet_ids = vpc_stack.require_output("private_subnet_ids")

if AMI_ID is None:
    ami_id = aws.ec2.get_ami(
        most_recent=True,
        owners=["amazon"],
        filters=[
            aws.ec2.GetAmiFilterArgs(
                name="name",
                values=["al2023-ami-2023*-kernel-*-arm64"],
            ),
            aws.ec2.GetAmiFilterArgs(name="architecture", values=["arm64"]),
            aws.ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
        ],
    ).id
else:
    ami_id = AMI_ID
resource_name = f"{RESOURCE_PREFIX}-vpn-{REGION_SHORT_NAME}"
vpn = pulumi.ComponentResource("tailscale-demo:aws:Vpn", resource_name)

context.resource_name = resource_name
context.parent = vpn
context.tags = TAGS
context.advertise_tags = ADVERTISE_TAGS
context.tailscale_issuer = TAILSCALE_ISSUER
context.tailscale_scopes = TAILSCALE_SCOPES

import iam  # noqa: E402
import identity  # noqa: E402

security_group = aws.ec2.SecurityGroup(
    f"{resource_name}-sg",
    description="Tailscale subnet router and peer relay security group",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="Tailscale WireGuard direct connections",
            protocol="udp",
            from_port=41641,
            to_port=41641,
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            description="Allow outbound traffic",
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
        ),
    ],
    tags={**TAGS, "Name": f"{resource_name}-sg"},
    opts=pulumi.ResourceOptions(parent=vpn),
)

cloudinit = cloudinit_tailscale.Module(
    f"{resource_name}-cloudinit",
    accept_dns=True,
    advertise_routes=[vpc_cidr_block],
    advertise_tags=ADVERTISE_TAGS,
    audience=identity.federated_identity.audience,
    base64_encode=True,
    client_id=identity.federated_identity.id,
    enable_ssh=ENABLE_TAILSCALE_SSH,
    hostname=resource_name,
    id_token=identity.federated_identity.audience.apply(
        lambda audience: (
            "command:aws sts get-web-identity-token "
            f"--audience {audience} "
            "--duration-seconds 300 "
            "--signing-algorithm RS256 "
            "--query WebIdentityToken "
            "--output text"
        )
    ),
    relay_server_port=RELAY_SERVER_PORT,
    snat_subnet_routes=True,
    track=TRACK,
    opts=pulumi.ResourceOptions(parent=vpn),
)
user_data = cloudinit.rendered.apply(lambda rendered: str(rendered or ""))

router_instances = AutoScalingEC2(
    resource_name,
    AutoScalingEC2Args(
        ami_id=ami_id,
        associate_public_ip_address="true",
        desired_capacity=DESIRED_CAPACITY,
        instance_profile_name=iam.instance_profile.name,
        instance_type=INSTANCE_TYPE,
        max_size=MAX_SIZE,
        min_size=MIN_SIZE,
        resource_name=resource_name,
        security_group_ids=[security_group.id],
        subnet_ids=subnet_ids,
        tags=TAGS,
        user_data=user_data,
    ),
    opts=pulumi.ResourceOptions(
        parent=vpn,
        depends_on=[iam.ssm_policy_attachment, identity.web_identity_policy],
    ),
)

vpn.register_outputs(
    {
        "autoscaling_group_name": router_instances.autoscaling_group_name,
        "federated_identity_audience": identity.federated_identity.audience,
        "federated_identity_client_id": identity.federated_identity.id,
        "federated_identity_subject": identity.federated_identity.subject,
        "instance_profile_name": iam.instance_profile.name,
        "launch_template_id": router_instances.launch_template_id,
        "security_group_id": security_group.id,
        "subnet_ids": subnet_ids,
        "vpc_id": vpc_id,
    }
)

pulumi.export("autoscaling_group_name", router_instances.autoscaling_group_name)
pulumi.export("federated_identity_audience", identity.federated_identity.audience)
pulumi.export("federated_identity_client_id", identity.federated_identity.id)
pulumi.export("federated_identity_subject", identity.federated_identity.subject)
pulumi.export("instance_profile_name", iam.instance_profile.name)
pulumi.export("launch_template_id", router_instances.launch_template_id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("subnet_ids", subnet_ids)
pulumi.export("vpc_id", vpc_id)
