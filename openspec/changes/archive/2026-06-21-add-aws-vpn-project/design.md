## Context

`projects/aws/vpn` exists as a Pulumi Python project scaffold, but it still
contains the default S3 template. The project needs to become the deployable AWS
home for Tailscale subnet router and peer relay instances associated with the
AWS VPCs. The repo uses Pulumi Python, uv, pedloy deployment YAML, and Pulumi's
Terraform-provider bridge where provider functionality is sourced from
Terraform packages.

## Goals / Non-Goals

**Goals:**

- Replace the default scaffold with AWS resources for a Tailscale subnet router
  and peer relay.
- Create a launch template that uses Tailscale cloud-init user data sourced via
  Pulumi package-add support for `tailscale/terraform-cloudinit-tailscale`.
- Create an Auto Scaling Group for the instance lifecycle.
- Create an IAM role and instance profile with SSM managed policy attachment for
  debugging access.
- Add the root pedloy YAML deployment entry for the new Pulumi project.

**Non-Goals:**

- Define Tailscale ACLs, auth keys, or tailnet policy in this project.
- Deploy application workloads behind the router.
- Change the existing AWS VPC project behavior.

## Decisions

- Use a dedicated `projects/aws/vpn` Pulumi project.
  - Rationale: the VPN/router lifecycle is separate from the VPC definition and
    can be deployed independently by pedloy.
  - Alternative considered: adding the resources to `projects/aws/vpc`, but that
    would couple network foundation changes to Tailscale node lifecycle changes.

- Model the node as an Auto Scaling Group with a launch template.
  - Rationale: an ASG can keep the router/relay instance present after instance
    failure while the launch template owns repeatable EC2 boot configuration.
  - Alternative considered: a single `aws.ec2.Instance`, but it would lack native
    replacement behavior.

- Use the Tailscale cloud-init Terraform provider through Pulumi package-add.
  - Rationale: this keeps user-data generation aligned with Tailscale's supported
    Terraform module/provider behavior while staying in Pulumi Python.
  - Alternative considered: hand-writing cloud-init, but that is easier to drift
    from the supported Tailscale bootstrap flow.

- Attach AWS SSM managed instance core policy to the instance role.
  - Rationale: SSM gives debug access without opening inbound SSH.
  - Alternative considered: SSH ingress, but it creates avoidable network access
    surface for a routing instance.

- Use an explicit VPN component parent for concrete VPN resources, with IAM
  attachments, instance profile, identity federation, and inline role policy
  parented to the router instance role.
  - Rationale: Pulumi preview and update output should render the VPN project as
    a readable hierarchy, while role-bound resources appear under the role they
    extend.
  - Alternative considered: leaving resources at stack scope, but that makes
    updates harder to scan as the project grows.

## Risks / Trade-offs

- Auth key handling leaks sensitive material into config or state if not marked
  secret. -> Require any Tailscale auth key config to be Pulumi secret config.
- A single-instance ASG is simple but still one active router per stack. ->
  Configure desired/min/max capacity explicitly so higher availability can be
  added later with a deliberate subnet and routing design.
- Generated cloud-init support depends on the package-add provider being present
  in Python dependencies. -> Keep dependency and lockfile updates with the
  project/root uv package definitions.
- pedloy config format is repository-specific. -> Add a minimal root deployment
  YAML and keep it easy to adjust if local pedloy conventions evolve.

## Migration Plan

1. Update `projects/aws/vpn` from the S3 template to the launch template, ASG,
   IAM role, instance profile, and Tailscale cloud-init implementation.
2. Add stack configuration for AWS region, resource prefix, the VPC stack
   reference, AMI/instance settings, and Tailscale bootstrap settings. The VPN
   project reads the VPC CIDR and private subnet IDs from that stack reference.
3. Add or update Python dependencies for AWS and Tailscale cloud-init provider
   support.
4. Add the root-level pedloy YAML for the new project.
5. Validate with Python compilation and Pulumi preview where credentials/config
   are available.
