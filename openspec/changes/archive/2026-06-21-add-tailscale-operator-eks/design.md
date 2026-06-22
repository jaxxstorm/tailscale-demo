## Overview

Add the Tailscale Kubernetes Operator to the AWS EKS project as a dedicated
resource module. The operator will run in the `tailscale` namespace and use
Tailscale workload identity federation rather than a static OAuth client secret.

The EKS entrypoint remains responsible for creating the cluster, Kubernetes
provider, and shared project context. The new `tailscale.py` module validates
that context has been populated before declaring Kubernetes and Tailscale
resources.

## Decisions

- Use the stable Tailscale Helm chart repository
  `https://pkgs.tailscale.com/helmcharts` rather than the unstable repository.
- Manage the Tailscale federated identity with `pulumi_tailscale.FederatedIdentity`.
- Use the Kubernetes ServiceAccount subject
  `system:serviceaccount:tailscale:operator`, matching the operator's default
  Helm-created ServiceAccount in the `tailscale` namespace.
- Bind `system:unauthenticated` to the Kubernetes
  `system:service-account-issuer-discovery` ClusterRole so Tailscale can read
  the cluster's OIDC discovery document.
- Pass `oauth.clientId` and `oauth.audience` into the Helm release, and do not
  configure `oauth.clientSecret`.
- Keep the operator configuration close to the user-provided desired shape:
  API server proxy enabled, default tags include `tag:k8s-operator` and the
  stack tag, hostname includes the stack, and tolerations target system nodes.

## Resource Model

- `context.py`
  - Stores shared values for `resource_name`, `parent`, `provider`, `stack`,
    `cluster_issuer`, and tags.
- `tailscale.py`
  - Creates the `tailscale` namespace.
  - Creates the OIDC discovery ClusterRoleBinding.
  - Creates the Tailscale federated identity.
  - Installs the `tailscale-operator` Helm chart using workload identity
    federation.

## Configuration

The operator uses sensible defaults and should not require a client secret.
Optional stack configuration can be added later for chart version pinning or
additional operator values, but the initial implementation keeps the surface
small.

## Risks

- The Kubernetes cluster issuer must be available as a Pulumi output from the
  EKS component. If the component does not expose it directly, the program must
  derive it from the EKS control plane identity output.
- Tailscale must be able to reach the Kubernetes OIDC discovery endpoint.
  Private-only API endpoint configurations may need additional consideration.
- Tailnet policy must allow the operator tag ownership expected by Tailscale.
