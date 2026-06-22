from __future__ import annotations

from typing import cast

import pulumi
import pulumi_kubernetes as k8s

import context

required_context = {
    "connectors": context.connectors,
    "eks_stack": context.eks_stack,
    "kubernetes_invite_code": context.kubernetes_invite_code,
    "region": context.region,
    "resource_name": context.resource_name,
    "stack": context.stack,
}
missing_context = [name for name, value in required_context.items() if value is None]
if missing_context:
    raise RuntimeError(f"connectors context is missing: {', '.join(missing_context)}")

connectors = cast(pulumi.ComponentResource, context.connectors)
eks_stack = cast(pulumi.StackReference, context.eks_stack)
invite_code = cast(pulumi.Input[str], context.kubernetes_invite_code)
namespace_name = context.kubernetes_namespace
resource_name = cast(str, context.resource_name)
tags = cast(dict[str, pulumi.Input[str]], context.tags)

cluster_name = eks_stack.require_output("cluster_name")
kubeconfig = cast(pulumi.Input[str], eks_stack.require_output("kubeconfig"))

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

tailzero_connector = k8s.helm.v3.Release(
    "tailzero-connector",
    chart="tailzero-connector",
    name="tailzero-connector",
    namespace=namespace_name,
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://borderzero.github.io/helm-charts",
    ),
    values={
        "config": {
            "inviteCode": invite_code,
        },
    },
    opts=pulumi.ResourceOptions(
        parent=namespace,
        provider=provider,
    ),
)

context.kubernetes_outputs = {
    "eks_cluster_name": cluster_name,
    "tailzero_kubernetes_namespace": namespace_name,
    "tailzero_kubernetes_release_name": tailzero_connector.name,
}
