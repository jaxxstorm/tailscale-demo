## 1. Package And Configuration

- [x] 1.1 Add package-added Tailscale provider support to the VPN Pulumi project.
- [x] 1.2 Replace static auth-key stack/docs guidance with identity federation configuration.

## 2. Federated Identity

- [x] 2.1 Create a Tailscale federated identity for the AWS router role.
- [x] 2.2 Export the federated identity client ID, audience, and subject.

## 3. AWS IAM And Cloud-Init

- [x] 3.1 Add an inline IAM policy granting bounded `sts:GetWebIdentityToken`.
- [x] 3.2 Update the Tailscale cloud-init module to use client ID, audience, and a runtime AWS STS id-token command.
- [x] 3.3 Remove static Tailscale auth-key usage from the VPN program.

## 4. Validation

- [x] 4.1 Validate the Python program compiles.
- [x] 4.2 Run `uv lock` or equivalent dependency validation for the VPN project.
- [x] 4.3 Run a Pulumi preview or document why it could not be run in the current environment.

Pulumi preview note: `pulumi preview --stack west` could not be completed in
this environment because sandboxed DNS could not resolve `api.pulumi.com`, and
the requested network escalation for preview was declined.
