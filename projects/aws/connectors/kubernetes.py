from __future__ import annotations

import pulumi
import pulumi_border0 as border0
import pulumi_kubernetes as k8s

import context

required_context = {
    "connectors": context.connectors,
    "region": context.region,
    "region_short_name": context.region_short_name,
    "resource_name": context.resource_name,
    "stack": context.stack,
}
missing_context = [name for name, value in required_context.items() if value is None]
if missing_context:
    raise RuntimeError(f"connectors context is missing: {', '.join(missing_context)}")

assert context.connectors is not None
assert context.region is not None
assert context.region_short_name is not None
assert context.resource_name is not None
assert context.stack is not None

connectors = context.connectors
config = pulumi.Config()
eks_stack_name = config.get("eksStack", "lbrlabs/demo-aws-eks/west")
eks_stack = pulumi.StackReference(eks_stack_name)
namespace_name = config.get("kubernetesNamespace") or "tailzero"
kubernetes_hostname = config.get("kubernetesHostname") or f"eks-connector-{context.region_short_name}"
resource_name = context.resource_name
region = context.region
tags = context.tags

cluster_name = eks_stack.require_output("cluster_name")
kubeconfig = eks_stack.require_output("kubeconfig")

provider = k8s.Provider(
    f"{resource_name}-tailzero",
    kubeconfig=kubeconfig,
    opts=pulumi.ResourceOptions(parent=connectors),
)

namespace = k8s.core.v1.Namespace(
    f"{resource_name}-tailzero",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=namespace_name,
        labels=tags,
    ),
    opts=pulumi.ResourceOptions(
        parent=connectors,
        provider=provider,
    ),
)

kubernetes_connector = border0.Connector(
    kubernetes_hostname,
    built_in_ssh_service_enabled=False,
    description=f"Tailzero Kubernetes connector for EKS in {region}",
    name=kubernetes_hostname,
    opts=pulumi.ResourceOptions(parent=connectors),
)

kubernetes_connector_token = border0.ConnectorToken(
    f"{resource_name}-kubernetes-token",
    connector_id=kubernetes_connector.id,
    name=f"{resource_name}-kubernetes-token",
    opts=pulumi.ResourceOptions(parent=kubernetes_connector),
)

kubernetes_socket = border0.Socket(
    f"{resource_name}-kubernetes",
    connector_ids=[kubernetes_connector.id],
    display_name=f"EKS Kubernetes ({region})",
    kubernetes_configurations=[
        border0.SocketKubernetesConfigurationArgs(
            certificate_authority="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
            impersonation_enabled=False,
            server="https://kubernetes.default.svc",
            service_type="standard",
            token_file="/var/run/secrets/kubernetes.io/serviceaccount/token",
        )
    ],
    name=f"eks-kubernetes-{context.region_short_name}",
    recording_enabled=True,
    socket_type="kubernetes",
    tags={
        "border0_client_category": "Infrastructure",
        "border0_client_subcategory": region,
        "border0_client_icon": "logos:kubernetes",
        "border0_client_icon_text": f"EKS Kubernetes {region}",
        "env": context.stack,
        "region": region,
        "socket_type": "kubernetes",
        "provider_type": "aws",
    },
    opts=pulumi.ResourceOptions(parent=kubernetes_connector),
)

tailzero_connector = k8s.helm.v3.Release(
    "tailzero-connector",
    chart="tailzero-connector",
    name="tailzero-connector",
    namespace=namespace_name,
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://jaxxstorm.github.io/border0-helm-charts",
    ),
    version="0.4.0",
    values={
        "config": {
            "hostname": kubernetes_hostname,
            "token": kubernetes_connector_token.token,
            "tsAuthKey": kubernetes_connector.tailscale_auth_key,
        },
    },
    opts=pulumi.ResourceOptions(
        parent=namespace,
        provider=provider,
        depends_on=[kubernetes_connector_token, kubernetes_socket],
    ),
)

context.kubernetes_outputs = {
    "border0_kubernetes_connector_id": kubernetes_connector.id,
    "border0_kubernetes_socket_id": kubernetes_socket.id,
    "eks_cluster_name": cluster_name,
    "tailzero_kubernetes_connector_token_id": kubernetes_connector_token.id,
    "tailzero_kubernetes_hostname": kubernetes_hostname,
    "tailzero_kubernetes_namespace": namespace_name,
    "tailzero_kubernetes_release_name": tailzero_connector.name,
}
