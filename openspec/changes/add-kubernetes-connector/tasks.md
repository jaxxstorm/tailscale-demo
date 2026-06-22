## 1. Connector Project Structure

- [x] 1.1 Add `projects/aws/connectors/context.py` for shared config, stack references, tags, and reusable resource handles.
- [x] 1.2 Move existing EC2 connector resources from `__main__.py` into `projects/aws/connectors/ec2.py`.
- [x] 1.3 Update `projects/aws/connectors/__main__.py` to populate context, import `ec2.py` before `kubernetes.py`, and export module outputs.
- [x] 1.4 Confirm no root-level pedloy YAML change is needed because this updates an existing Pulumi project.

## 2. Kubernetes Connector

- [x] 2.1 Add `demo-aws-connectors:eksStack` config with default `lbrlabs/demo-aws-eks/west`.
- [x] 2.2 Add `demo-aws-connectors:kubernetesInviteCode` secret config input for the Tailzero Helm chart.
- [x] 2.3 Add `projects/aws/connectors/kubernetes.py` that reads the EKS stack via `pulumi.StackReference`.
- [x] 2.4 Create a Kubernetes provider from the referenced EKS stack's `kubeconfig` output.
- [x] 2.5 Create a dedicated `tailzero` namespace.
- [x] 2.6 Install the `tailzero-connector` Helm chart from `https://borderzero.github.io/helm-charts` as `tailzero-connector` with `config.inviteCode` set from secret config.

## 3. IAM and Outputs

- [x] 3.1 Export Tailzero Kubernetes namespace, Helm release name, and referenced EKS cluster name.
- [x] 3.2 Preserve existing EC2, EC2 SSM, S3, connector, instance, and target outputs.

## 4. Validation

- [x] 4.1 Run Python compile validation for `projects/aws/connectors/__main__.py`, `ec2.py`, `kubernetes.py`, and `context.py`.
- [x] 4.2 Run an import smoke check for Pulumi Kubernetes Helm release types.
- [x] 4.3 Run OpenSpec validation for `add-kubernetes-connector`.
- [ ] 4.4 Run `pulumi preview` when the target stack, Border0 provider credentials, and Kubernetes invite code are available.
