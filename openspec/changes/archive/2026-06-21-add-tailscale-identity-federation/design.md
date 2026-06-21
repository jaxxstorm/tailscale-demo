## Context

The AWS VPN Pulumi project uses `tailscale/terraform-cloudinit-tailscale` through
Pulumi package-add support to generate EC2 user data. That module supports
workload identity federation by passing `audience` and `client_id`, plus an
`id_token` value that may use a `command:` prefix. The AWS instance role can
obtain that token with `aws sts get-web-identity-token` when the role has a
policy permitting the requested audience.

## Goals / Non-Goals

**Goals:**

- Replace static Tailscale auth-key bootstrap for AWS VPN instances with
  workload identity federation.
- Manage the Tailscale federated identity from Pulumi.
- Restrict AWS STS web identity token issuance to the configured Tailscale
  audience and a short duration.
- Keep the instance role usable for SSM debugging.

**Non-Goals:**

- Define tailnet ACL policy or tag ownership.
- Change VPC routing, subnet selection, or Auto Scaling behavior.
- Add non-AWS identity providers.

## Decisions

- Use Tailscale federated identity rather than static auth keys.
  - Rationale: the instance can authenticate from its AWS role and avoid storing
    reusable Tailscale auth keys in Pulumi stack config.
  - Alternative considered: keep auth keys as Pulumi secrets, but that still
    requires key creation and rotation outside the instance identity lifecycle.

- Use the AWS IAM role ARN as the Tailscale federated identity subject.
  - Rationale: this matches the known Terraform implementation and gives a
    stable per-role identity boundary for the router clients.
  - Alternative considered: wildcard subjects, but they are broader than needed
    for this single role.

- Require the AWS OIDC issuer URL from Tailscale's AWS trust credential UI.
  - Rationale: `aws sts get-web-identity-token` returns a JWT whose issuer is a
    discoverable `https://*.tokens.sts.global.api.aws` URL. The STS API endpoint
    `https://sts.amazonaws.com` does not serve OIDC discovery metadata and
    cannot be used as the Tailscale federated identity issuer.
  - Alternative considered: map `default` to `https://sts.amazonaws.com`, but
    Tailscale then fails JWT verification because that endpoint has no
    `/.well-known/openid-configuration` document.

- Use the cloud-init module's `command:` id-token support.
  - Rationale: the token should be minted on the instance at boot, not generated
    during Pulumi deployment.
  - Alternative considered: Pulumi-generated token, but that would bind runtime
    authentication to deployment-time credentials.

- Keep SSM as an AWS managed policy and add web identity token permissions as an
  inline role policy.
  - Rationale: SSM remains a standard managed policy, while the Tailscale token
    permission needs audience and duration conditions.

## Risks / Trade-offs

- Incorrect audience/client ID values will prevent Tailscale login. -> Export
  the generated federated identity values and wire them into cloud-init directly.
- Tailscale provider credentials are required to manage the federated identity.
  -> Keep provider configuration in stack config/environment and validate with
  Pulumi preview where credentials are available.
- IAM wildcard resource is required for `sts:GetWebIdentityToken` in the known
  Terraform pattern. -> Restrict by `sts:IdentityTokenAudience` and
  `sts:DurationSeconds`.

## Migration Plan

1. Add the package-added Tailscale Terraform provider SDK if it is not already
   available.
2. Create the Tailscale federated identity for the AWS instance role.
3. Add the inline AWS IAM policy granting `sts:GetWebIdentityToken` for the
   federated identity audience.
4. Update cloud-init inputs to pass `client_id`, `audience`, and a
   `command:aws sts get-web-identity-token ...` id-token command.
5. Remove the static `authKey` requirement from VPN stack config and docs.
6. Validate Python compilation, dependency lock, and Pulumi preview where
   credentials are available.
