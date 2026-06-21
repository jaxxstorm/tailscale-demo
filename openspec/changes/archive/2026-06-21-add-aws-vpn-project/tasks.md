## 1. Project Configuration

- [x] 1.1 Replace the `projects/aws/vpn` template program with stack-configured AWS VPN inputs and exports.
- [x] 1.2 Add dependencies for AWS and Tailscale cloud-init package support to the VPN project package metadata.
- [x] 1.3 Add stack configuration for resource prefix, VPC/subnet lookup, EC2 settings, and Tailscale bootstrap settings.

## 2. AWS Router Infrastructure

- [x] 2.1 Add IAM role, SSM managed policy attachment, and instance profile for router instances.
- [x] 2.2 Add Tailscale cloud-init user data sourced from the package-added Terraform provider.
- [x] 2.3 Add EC2 launch template configured with the generated Tailscale user data.
- [x] 2.4 Add Auto Scaling Group using the launch template and configured subnets.

## 3. Deployment Wiring

- [x] 3.1 Add root-level pedloy YAML deployment configuration for `projects/aws/vpn`.

## 4. Validation

- [x] 4.1 Validate the Python program compiles.
- [x] 4.2 Run `uv lock` or equivalent dependency validation for the VPN project when dependencies are available.
- [x] 4.3 Run a Pulumi preview or document why it could not be run in the current environment.

Pulumi preview note: `pulumi preview --stack west` could not be completed in
this environment because the sandbox cannot read `/Users/lbriggs/.pulumi`, and
the requested escalation to access local Pulumi credentials was declined.
