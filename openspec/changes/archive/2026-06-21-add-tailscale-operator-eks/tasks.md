## Tasks

- [x] Add EKS shared context for provider, parent, stack, resource name, tags,
  and cluster OIDC issuer.
- [x] Add `projects/aws/eks/tailscale.py` with the Tailscale namespace, OIDC
  discovery ClusterRoleBinding, federated identity, and Helm release.
- [x] Import the Tailscale module from the EKS entrypoint after context is
  populated.
- [x] Export Tailscale Operator federated identity values from the EKS stack.
- [x] Validate the OpenSpec change and compile the EKS Python project.
