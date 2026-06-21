## Why

AWS VPN/router clients currently depend on a static Tailscale auth key, which
creates secret rotation and state-handling friction. Tailscale workload identity
federation lets these EC2 instances authenticate from their AWS IAM role instead,
matching the Terraform approach that has already worked for this environment.

## What Changes

- Add Tailscale federated identity support for the AWS VPN Pulumi project.
- Create a Tailscale federated identity whose subject matches the AWS instance
  role ARN and whose scopes/tags permit auth-key generation for tagged devices.
- Add an inline IAM policy allowing the EC2 instance role to call
  `sts:GetWebIdentityToken` for the federated identity audience with short token
  duration.
- Update Tailscale cloud-init configuration to use workload identity
  credentials instead of a static `authKey`.
- Keep AWS SSM debugging access attached to the instance role.
- Update VPN stack configuration and docs for audience/client-id based auth.

## Capabilities

### New Capabilities

- `tailscale-identity-federation-auth`: Defines workload identity federation
  authentication for AWS VPN/router clients.

### Modified Capabilities

- None.

## Impact

- Affected Pulumi project directory: `projects/aws/vpn`.
- Affected dependencies: the VPN project may need a package-added Tailscale
  Terraform provider SDK in addition to the existing cloud-init package.
- Affected systems: Tailscale federated identity, AWS IAM instance role policy,
  AWS STS web identity tokens, and Tailscale cloud-init user data.
