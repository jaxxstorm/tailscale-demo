## Context

`projects/aws/connectors/__main__.py` currently declares shared project config,
Border0 connector resources, EC2 targets, IAM policies, sockets, cloud-init, and
exports in one file. The EKS project already exports `cluster_name` and
`kubeconfig`, and the generated Border0 SDK supports Kubernetes sockets through
`kubeconfig`. The Tailzero Kubernetes connector is installed through the
`border0/tailzero-connector` Helm chart and requires an invite code.

The connectors project should grow to manage both EC2-oriented sockets and an
EKS Kubernetes connector without making the entrypoint harder to reason about.

## Goals / Non-Goals

**Goals:**

- Split existing EC2 connector resources into `projects/aws/connectors/ec2.py`.
- Add `projects/aws/connectors/kubernetes.py` for the EKS-backed Tailzero Helm
  release.
- Use a Pulumi `StackReference` to the EKS stack for cluster identity.
- Keep `__main__.py` responsible for config, shared context, module import
  ordering, and output aggregation.

**Non-Goals:**

- Do not create a new Pulumi project.
- Do not change the EKS cluster implementation.
- Do not install the Tailzero chart into the `default` namespace.
- Do not replace existing EC2, S3, or EC2 SSM sockets.

## Decisions

- Use project-local `context.py` for shared values. This follows the repository
  convention already used by other multi-file Pulumi projects and avoids passing
  a large argument object between modules.
- Keep EC2 Border0 resources and Kubernetes Tailzero resources separate. The EC2
  connector remains the runtime for EC2/S3/SSM sockets, while the Kubernetes
  connector is installed in-cluster via Helm.
- Reference the EKS stack from the connectors project using configurable
  `eksStack`, defaulting to `lbrlabs/demo-aws-eks/west`. This mirrors the
  existing `vpcStack` pattern and keeps stack wiring explicit.
- Install the Helm release into a dedicated `tailzero` namespace. This follows
  the user's requirement to avoid the `default` namespace and keeps connector
  resources easy to inspect.
- Configure the Helm release with `config.inviteCode` from secret Pulumi config
  `demo-aws-connectors:kubernetesInviteCode`. The invite code must not be
  hardcoded into source files.

## Risks / Trade-offs

- The Tailzero chart repository must be pinned in code rather than relying on a
  preconfigured Helm alias. Mitigation: use
  `https://borderzero.github.io/helm-charts` as the Helm repository URL and
  `tailzero-connector` as the chart name.
- Splitting an existing untracked connectors program can obscure exports if the
  modules do not expose outputs clearly. Mitigation: each module exports a
  dictionary of resource outputs for `__main__.py` to register and export.
- The EKS stack reference default assumes the current `west` stack naming.
  Mitigation: expose `demo-aws-connectors:eksStack` config so other stacks can
  override it.
