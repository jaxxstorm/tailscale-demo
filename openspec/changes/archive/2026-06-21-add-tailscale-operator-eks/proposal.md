## Why

The EKS demo cluster should expose the Tailscale Kubernetes Operator as part of
the managed infrastructure so the cluster can participate in the tailnet without
manually installed Helm releases or long-lived OAuth client secrets.

Using workload identity federation lets the operator authenticate with its
Kubernetes ServiceAccount OIDC token, matching the repository's direction of
using federated identities for Tailscale clients.

## What Changes

- Add a Tailscale Operator installation to the AWS EKS Pulumi project.
- Place operator resources in a dedicated `tailscale.py` resource module.
- Configure Kubernetes OIDC discovery access required by Tailscale workload
  identity federation.
- Manage a Tailscale federated identity for the operator ServiceAccount subject.
- Configure the Helm release to use the federated identity client ID and
  audience instead of an OAuth client secret.
- Export the operator federated identity values for inspection.

## Capabilities

### New Capabilities

- `eks-tailscale-operator`: Installs the Tailscale Kubernetes Operator on the
  EKS cluster and authenticates it using Kubernetes workload identity
  federation.

### Modified Capabilities

None.

## Impact

- Affects `projects/aws/eks`, including the Pulumi entrypoint and new
  project-local resource modules.
- Uses existing root-level dependencies: `pulumi`, `pulumi-kubernetes`, and
  `pulumi-tailscale`; no new uv package is required.
- Adds Tailscale resources through the existing Terraform-backed Pulumi provider
  package.
- Requires Tailscale tailnet policy/tag ownership to allow `tag:k8s-operator`
  and any stack tag used by the operator.
