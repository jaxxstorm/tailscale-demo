## Why

The AWS connectors project currently manages EC2-oriented Border0/Tailzero
resources in one entrypoint, which makes it awkward to add additional connector
types cleanly. We need a Kubernetes connector that references the existing EKS
cluster stack while keeping EC2 and Kubernetes connector resources separated.

## What Changes

- Install the Tailzero Kubernetes connector Helm chart into the existing AWS EKS
  cluster.
- Reference the EKS Pulumi stack from the connectors project to read cluster
  identity such as `cluster_name`.
- Split connector resources into `ec2.py` and `kubernetes.py`, with
  `__main__.py` acting as shared config/context setup and output aggregation.
- Keep the existing EC2 connector, EC2 SSM socket, S3 socket, IAM policy
  attachments, and Tailzero bootstrap behavior.

## Capabilities

### New Capabilities

- `border0-kubernetes-connector`: Defines how the AWS connectors project installs
  the Tailzero Kubernetes connector chart into EKS using stack-reference data.
- `border0-aws-connectors`: Defines the AWS connectors project resource layout
  and the separation between EC2 and Kubernetes connector modules.

### Modified Capabilities

- None.

## Impact

- Affects `projects/aws/connectors`, including its entrypoint and new resource
  modules.
- Uses the existing generated `pulumi_border0` provider SDK, the Pulumi
  Kubernetes provider, and root uv-managed dependencies.
- Depends on outputs from `projects/aws/eks`, especially `kubeconfig` and
  `cluster_name`, via a Pulumi `StackReference`.
- No new Pulumi project or pedloy deployment file is required.
