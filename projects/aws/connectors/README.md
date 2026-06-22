# AWS Tailzero Connectors

This Pulumi project deploys a Tailzero SSH connector host into the AWS demo VPC.

It creates:

- a Border0 connector
- a Border0 connector token for Tailzero bootstrap
- a Border0 built-in SSH socket for the connector VM
- a Border0 AWS S3 socket using the connector instance role
- a private SSM-managed EC2 target with a Border0 AWS SSM SSH socket
- a Tailzero Kubernetes connector Helm release in the `tailzero` namespace
- an SSM-enabled EC2 instance profile
- SSM Session Manager permissions for the connector instance role
- an S3 access policy for the connector instance role
- an outbound-only security group
- a one-instance EC2 Auto Scaling Group through the shared `AutoScalingEC2`
  component
- cloud-init user data rendered with `pulumi-cloudinit`

Configure Border0 provider credentials before previewing:

```sh
pulumi config set --secret border0:token <border0-token>
pulumi config set --secret demo-aws-connectors:kubernetesInviteCode <invite-code>
```

The instance runs the Tailzero installer with the provider-created connector
token and Tailscale auth key.

The Kubernetes connector uses the EKS stack's `kubeconfig` output and installs
the `tailzero-connector` chart from `https://borderzero.github.io/helm-charts`
outside the default namespace. Override the namespace with
`demo-aws-connectors:kubernetesNamespace` if needed.
