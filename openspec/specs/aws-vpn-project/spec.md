## Purpose

Define the AWS Pulumi VPN project that deploys Tailscale subnet router and peer
relay infrastructure for AWS VPCs.

## Requirements

### Requirement: AWS VPN project defines Tailscale router infrastructure

The system SHALL provide a Pulumi Python project at `projects/aws/vpn` that
defines AWS infrastructure for a Tailscale subnet router and peer relay.

#### Scenario: Project replaces template resources

- **WHEN** the AWS VPN Pulumi program is inspected
- **THEN** it defines router/relay infrastructure instead of the default S3
  template resources

### Requirement: Router instance uses launch template and autoscaling group

The AWS VPN project SHALL define an EC2 launch template and Auto Scaling Group
for the Tailscale subnet router and peer relay instance lifecycle.

#### Scenario: Auto Scaling Group launches router instance

- **WHEN** the Pulumi project is previewed
- **THEN** the plan includes an Auto Scaling Group that uses the launch template
  for router instances

### Requirement: Router instance has SSM debugging access

The AWS VPN project SHALL define an IAM role and instance profile for the router
instance, attach the AWS SSM managed instance core policy, and keep IAM resource
declarations in a distinct project resource file.

#### Scenario: SSM policy is attached

- **WHEN** the Pulumi project is previewed
- **THEN** the plan includes an instance role with the SSM managed policy
  attached
- **THEN** IAM role, policy attachment, and instance profile declarations are
  separated from the entrypoint module

### Requirement: Project resources are organized by resource group

The AWS VPN project SHALL keep `__main__.py` focused on configuration,
context population, module imports, and exports, while resource groups are
declared in distinct files. Concrete VPN resources SHALL set explicit Pulumi
`parent` options so preview and update output renders under a coherent VPN
resource hierarchy.

#### Scenario: Entrypoint imports resource modules

- **WHEN** the AWS VPN Pulumi program is inspected
- **THEN** `__main__.py` populates shared context and imports resource modules
  in dependency order
- **THEN** grouped resources such as IAM are declared outside `__main__.py`

#### Scenario: VPN resources render under parent hierarchy

- **WHEN** the AWS VPN Pulumi program is inspected
- **THEN** VPN resources use explicit `pulumi.ResourceOptions(parent=...)`
  inheritance
- **THEN** IAM children are parented by the router instance role where
  applicable

### Requirement: Router user data comes from Tailscale cloud-init package

The AWS VPN project SHALL generate launch template user data from
`tailscale/terraform-cloudinit-tailscale` through Pulumi package-add provider
support, and SHALL advertise the VPC CIDR obtained from the configured VPC stack
reference.

#### Scenario: Tailscale cloud-init config is used

- **WHEN** the Pulumi project creates the launch template
- **THEN** the launch template user data is derived from the Tailscale cloud-init
  provider output
- **THEN** the advertised subnet route is sourced from the VPC stack reference

### Requirement: Project is deployable by pedloy

The repository SHALL include root-level pedloy YAML deployment configuration for
the AWS VPN Pulumi project.

#### Scenario: New project has deployment configuration

- **WHEN** the AWS VPN project is added
- **THEN** a root-level YAML file includes the deployment configuration needed
  for pedloy to deploy `projects/aws/vpn`
