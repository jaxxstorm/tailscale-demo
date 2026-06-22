## Why

The AWS VPN project currently declares EC2 launch template and Auto Scaling
Group resources inline, which makes the same pattern hard to reuse in other
Pulumi programs. Extracting that shape into a shared component keeps the VPN
project focused on VPN-specific inputs while making the EC2 autoscaling pattern
available elsewhere.

## What Changes

- Add a top-level Python `components` package with an `AutoScalingEC2` Pulumi
  component.
- Move reusable launch template and Auto Scaling Group wiring behind a compact
  input surface for frequently changed values such as AMI, user data, security
  groups, subnets, instance profile, and capacity.
- Preserve sane defaults for common values such as EC2 health checks, launch
  template latest-version usage, propagated tags, instance/volume tag
  specifications, and private ASG sizing defaults.
- Update `projects/aws/vpn` to consume the local component while leaving
  VPN-specific resources such as IAM, security groups, Tailscale identity, and
  cloud-init in the VPN project.
- **BREAKING**: The VPN project may replace existing launch template and Auto
  Scaling Group resources because resource names and parent hierarchy can change
  while the reusable component is introduced.

## Capabilities

### New Capabilities

- `pulumi-autoscaling-ec2-component`: Shared Pulumi component for EC2 launch
  template and Auto Scaling Group infrastructure.

### Modified Capabilities

- `aws-vpn-project`: The VPN project uses the shared AutoScalingEC2 component
  for router instance lifecycle resources.

## Impact

- Affected code: new top-level `components` package and
  `projects/aws/vpn/__main__.py`.
- Affected systems: AWS EC2 launch template and Auto Scaling Group resources
  created by the VPN Pulumi project.
- Dependencies/providers: no new uv package or provider dependency is expected;
  the component uses the existing Pulumi AWS dependency.
- Deployment configuration: no new Pulumi project is added, so no new root-level
  pedloy YAML is required.
