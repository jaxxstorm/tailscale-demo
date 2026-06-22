## 1. Shared Component

- [x] 1.1 Create the top-level `components` Python package.
- [x] 1.2 Implement `AutoScalingEC2` with compact typed inputs, sane defaults, child resources, and registered outputs.

## 2. VPN Integration

- [x] 2.1 Update `projects/aws/vpn` to import the local component from the repository root.
- [x] 2.2 Replace inline VPN launch template and Auto Scaling Group declarations with `AutoScalingEC2`.
- [x] 2.3 Preserve VPN exports for Auto Scaling Group name and launch template ID.

## 3. Validation

- [x] 3.1 Run Python compile validation for the shared component and VPN project.
- [x] 3.2 Run an OpenSpec validation for `add-autoscaling-ec2-component`.
