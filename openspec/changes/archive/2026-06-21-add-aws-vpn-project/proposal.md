## Why

The AWS VPCs need a managed Tailscale presence that can route private subnet
traffic and act as a peer relay without relying on manually maintained hosts.
Adding a dedicated `projects/aws/vpn` Pulumi project makes this infrastructure
repeatable, deployable, and consistent with the rest of the repo.

## What Changes

- Add a new AWS Pulumi project under `projects/aws/vpn` for a Tailscale subnet
  router and peer relay.
- Define an EC2 launch template with Tailscale cloud-init user data.
- Define an Auto Scaling Group to keep the relay/router instance available.
- Define an IAM role and instance profile with the AWS SSM managed policy
  attached for debugging access.
- Use Pulumi package-add mechanisms for the
  `tailscale/terraform-cloudinit-tailscale` Terraform provider integration.
- Add the root-level pedloy YAML deployment configuration required for the new
  Pulumi project.

## Capabilities

### New Capabilities

- `aws-vpn-project`: Defines the AWS VPN Pulumi project that deploys a
  Tailscale subnet router and peer relay for AWS VPCs.

### Modified Capabilities

- None.

## Impact

- Affected Pulumi project directory: `projects/aws/vpn`.
- Affected root deployment configuration: root-level pedloy YAML for the new
  project.
- Affected dependencies: root-level uv package definitions and lockfile may need
  updates for AWS, AWSX, and Terraform-provider-backed cloud-init support.
- Affected systems: AWS EC2, Auto Scaling, IAM, SSM, VPC networking, and
  Tailscale routing/relay infrastructure.
