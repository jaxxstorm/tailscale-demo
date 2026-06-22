import pulumi
import pulumi_kubernetes as k8s
import pulumi_tailscale as tailscale_provider

import context

if (
    context.resource_name is None
    or context.parent is None
    or context.provider is None
    or context.stack is None
    or context.tags is None
    or context.cluster_issuer is None
):
    raise pulumi.RunError(
        "`tailscale` must be imported after `context.resource_name`, "
        "`context.parent`, `context.provider`, `context.stack`, `context.tags`, "
        "and `context.cluster_issuer` are set in the entrypoint."
    )

TAILSCALE_NAMESPACE = "tailscale"
TAILSCALE_OPERATOR_SUBJECT = f"system:serviceaccount:{TAILSCALE_NAMESPACE}:operator"

operator_tags = [
    "tag:k8s-operator",
    f"tag:{context.stack}",
]

tailscale_ns = k8s.core.v1.Namespace(
    "tailscale-ns",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=TAILSCALE_NAMESPACE,
        labels=context.tags,
    ),
    opts=pulumi.ResourceOptions(provider=context.provider, parent=context.parent),
)

oidc_discovery = k8s.rbac.v1.ClusterRoleBinding(
    f"{context.resource_name}-oidc-discovery",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=f"{context.resource_name}-oidc-discovery",
        labels=context.tags,
    ),
    role_ref=k8s.rbac.v1.RoleRefArgs(
        api_group="rbac.authorization.k8s.io",
        kind="ClusterRole",
        name="system:service-account-issuer-discovery",
    ),
    subjects=[
        k8s.rbac.v1.SubjectArgs(
            api_group="rbac.authorization.k8s.io",
            kind="Group",
            name="system:unauthenticated",
        )
    ],
    opts=pulumi.ResourceOptions(provider=context.provider, parent=context.parent),
)

federated_identity = tailscale_provider.FederatedIdentity(
    f"{context.resource_name}-operator-federated-identity",
    description=f"{context.resource_name} Kubernetes operator ServiceAccount",
    issuer=context.cluster_issuer,
    scopes=["auth_keys", "devices:core", "services"],
    subject=TAILSCALE_OPERATOR_SUBJECT,
    tags=operator_tags,
    opts=pulumi.ResourceOptions(parent=context.parent),
)

tailscale_operator = k8s.helm.v3.Release(
    "tailscale",
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://pkgs.tailscale.com/helmcharts",
    ),
    namespace=tailscale_ns.metadata.name,
    chart="tailscale-operator",
    values={
        "oauth": {
            "clientId": federated_identity.id,
            "audience": federated_identity.audience,
        },
        "apiServerProxyConfig": {
            "mode": "true",
        },
        "operatorConfig": {
            "defaultTags": operator_tags,
            "hostname": f"eks-operator-{context.stack}",
            "tolerations": [
                {
                    "key": "node.lbrlabs.com/system",
                    "operator": "Equal",
                    "value": "true",
                    "effect": "NoSchedule",
                },
            ],
        },
    },
    opts=pulumi.ResourceOptions(
        provider=context.provider,
        parent=tailscale_ns,
        depends_on=[oidc_discovery, federated_identity],
    ),
)
