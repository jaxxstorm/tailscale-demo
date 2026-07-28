# AWS Tailzero Connectors

This Pulumi project deploys a Tailzero SSH connector host into the AWS demo VPC.

It creates:

- a Border0 connector
- a Border0 connector token for Tailzero bootstrap
- a Border0 built-in SSH socket for the connector VM
- a Border0 AWS S3 socket using the connector instance role
- a private SSM-managed EC2 target with a Border0 AWS SSM SSH socket
- a Tailzero Kubernetes connector Helm release in the `tailzero` namespace
- a Border0 Kubernetes socket for the EKS API server
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
```

Enable connector groups by keeping their imports in `__main__.py`:

```python
import ec2
import kubernetes
```

Remove or comment either import to disable that connector group for the stack.
Each module owns its connector-specific config, so disabled modules do not load
or require their config values.
The instance runs the Tailzero installer with the provider-created connector
token and Tailscale auth key. The EC2 Tailzero service hostname defaults to the
connector resource name and can be overridden if needed:

```sh
pulumi config set demo-aws-connectors:tailzeroHostname <hostname>
```

The Kubernetes connector uses the EKS stack's `kubeconfig` output and installs
the `tailzero-connector` chart from
`https://jaxxstorm.github.io/border0-helm-charts` outside the default namespace.
It creates a dedicated Border0 connector token and passes that token plus the
connector's Tailscale auth key to the chart, so no invite code is required. The
Kubernetes connector has its own Border0 connector identity and only receives
the Kubernetes socket.
The Kubernetes connector hostname defaults to `eks-connector-<region-short-name>`,
for example `eks-connector-us-west`. Override the namespace or hostname if
needed:

```sh
pulumi config set demo-aws-connectors:kubernetesNamespace <namespace>
pulumi config set demo-aws-connectors:kubernetesHostname <hostname>
```
