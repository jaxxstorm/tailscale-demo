## Context

The AWS VPN project currently owns the full EC2 launch template and Auto Scaling
Group definitions inline in `projects/aws/vpn/__main__.py`. Those resources are
not VPN-specific; they combine a launch template, network interface settings,
instance/volume tagging, ASG sizing, and ASG tag propagation around caller-owned
values such as AMI, user data, security groups, subnets, and instance profile.

The repository uses Pulumi Python programs from a shared root dependency set.
The reusable component can therefore live in a top-level Python package without
adding a new Pulumi project, uv dependency, or deployment configuration.

## Goals / Non-Goals

**Goals:**

- Provide a reusable `AutoScalingEC2` component in a top-level `components`
  package.
- Keep the component input surface compact and oriented around values that vary
  between call sites.
- Preserve useful defaults for launch template and ASG behavior so callers do
  not need to pass every AWS option.
- Update the VPN project as a concrete local usage example.

**Non-Goals:**

- Model every launch template or Auto Scaling Group option.
- Preserve physical resource names for the existing VPN launch template and
  Auto Scaling Group.
- Move VPN-specific IAM, security group, Tailscale identity, or cloud-init
  resources into the shared component.
- Add package publishing, a separate Python distribution, or a new Pulumi
  project.

## Decisions

- Create `components/autoscaling_ec2.py` plus `components/__init__.py`.
  This keeps shared local infrastructure components importable from Pulumi
  programs that run from subdirectories without introducing a new dependency.
  Alternative considered: keep the component under `projects/aws`, but that
  would make a shared primitive look provider-project-local.

- Use a typed args object for the component input surface.
  Required inputs are AMI ID, instance type, subnet IDs, security group IDs,
  user data, and an optional instance profile name. Capacity values, health
  check type, public IP association, tags, and resource name defaults live in
  the component. Alternative considered: accept raw dictionaries, but typed
  fields make Pulumi call sites easier to inspect and update.

- Keep caller-owned dependencies at the component boundary.
  The VPN project passes resource options with `depends_on` for IAM and identity
  readiness instead of the component knowing about those concepts. Alternative
  considered: add dependency input fields, but Pulumi already models this in
  `ResourceOptions`.

- Export component child outputs directly.
  `AutoScalingEC2` exposes `launch_template`, `autoscaling_group`,
  `launch_template_id`, and `autoscaling_group_name` so existing projects can
  keep exporting stable useful values without reaching into private state.

## Risks / Trade-offs

- Existing AWS resources may be replaced because the component introduces a new
  parent hierarchy or logical names. This is acceptable because the VPN
  resources are disposable and the proposal explicitly allows recreation.
- The compact input surface may omit a future ASG or launch template option.
  The mitigation is to add specific fields when a second real use case needs
  them, rather than designing a broad wrapper up front.
- Python imports from nested Pulumi projects need the repository root on
  `sys.path`. The VPN project already runs from a nested directory, so the
  entrypoint will add the repository root before importing `components`.

## Migration Plan

1. Add the shared component package.
2. Replace inline VPN launch template and ASG declarations with
   `AutoScalingEC2`.
3. Keep VPN exports for launch template ID and Auto Scaling Group name.
4. Validate with Python compile checks and, when credentials/config are
   available, Pulumi preview for `projects/aws/vpn`.
