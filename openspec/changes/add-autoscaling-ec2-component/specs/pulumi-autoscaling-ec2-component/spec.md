## ADDED Requirements

### Requirement: Shared AutoScalingEC2 component exists

The system SHALL provide a top-level Python `components` package containing an
`AutoScalingEC2` Pulumi component for reusable EC2 launch template and Auto
Scaling Group infrastructure.

#### Scenario: Component is importable by Pulumi projects

- **WHEN** a Pulumi Python project imports `AutoScalingEC2` from the top-level
  `components` package
- **THEN** the import resolves to a Pulumi `ComponentResource` implementation
  that can be instantiated from that project

### Requirement: Component accepts compact EC2 autoscaling inputs

The `AutoScalingEC2` component SHALL require caller-provided values for AMI ID,
instance type, subnet IDs, security group IDs, and user data, and SHALL allow
callers to provide an instance profile name, desired capacity, minimum size,
maximum size, resource tags, and resource name overrides.

#### Scenario: Caller supplies frequently changing infrastructure values

- **WHEN** a caller instantiates `AutoScalingEC2` with an AMI ID, user data,
  security group IDs, subnet IDs, and instance type
- **THEN** the component uses those values for the launch template and Auto
  Scaling Group resources

### Requirement: Component applies sane defaults

The `AutoScalingEC2` component SHALL default to EC2 health checks, `$Latest`
launch template version selection, propagated Auto Scaling tags, instance and
volume launch template tag specifications, and one-instance desired/minimum/
maximum capacity when callers do not override those values.

#### Scenario: Minimal capacity inputs use defaults

- **WHEN** a caller omits desired capacity, minimum size, and maximum size
- **THEN** the Auto Scaling Group is configured for desired capacity 1, minimum
  size 1, and maximum size 1

### Requirement: Component exposes child resource outputs

The `AutoScalingEC2` component SHALL expose the created launch template and Auto
Scaling Group resources, plus convenient launch template ID and Auto Scaling
Group name outputs.

#### Scenario: Caller exports component outputs

- **WHEN** a Pulumi project exports values from an `AutoScalingEC2` instance
- **THEN** launch template ID and Auto Scaling Group name outputs are available
  without reconstructing child resource references
