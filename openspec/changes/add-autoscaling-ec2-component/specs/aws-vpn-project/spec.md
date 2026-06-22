## MODIFIED Requirements

### Requirement: Router instance uses launch template and autoscaling group

The AWS VPN project SHALL define an EC2 launch template and Auto Scaling Group
for the Tailscale subnet router and peer relay instance lifecycle by using the
shared `AutoScalingEC2` component from the top-level `components` package.

#### Scenario: Auto Scaling Group launches router instance

- **WHEN** the Pulumi project is previewed
- **THEN** the plan includes an Auto Scaling Group that uses the launch template
  for router instances
- **THEN** the launch template and Auto Scaling Group are created through the
  shared `AutoScalingEC2` component
