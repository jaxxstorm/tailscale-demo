# AWS VPN

Pulumi project for the AWS Tailscale subnet router and peer relay.

## Layout

`__main__.py` reads stack config, populates shared `context`, imports resource
modules in dependency order, and exports outputs. IAM resources live in
`iam.py`; Tailscale identity federation resources live in `identity.py`.

Dependencies are managed by the repository root `pyproject.toml` and `uv.lock`.
Do not add project-local uv package files.

## Configuration

The stack references the matching AWS VPC stack for VPC and private subnet
outputs:

```bash
pulumi config set lbrlabs-aws-vpn:vpcStack lbrlabs58/lbrlabs-demo-aws-vpc/west
```

The project manages a Tailscale federated identity for the EC2 instance role.
Configure the Tailscale provider with deploy-time credentials before previewing
or deploying, for example:

```bash
export TAILSCALE_API_KEY=<tskey-api-...>
export TAILSCALE_TAILNET=<tailnet-id>
```

Set `tailscaleIssuer` to the AWS issuer URL shown by Tailscale when creating an
AWS federated identity, for example:

```bash
pulumi config set lbrlabs-aws-vpn:tailscaleIssuer https://abc123-def456-ghi789-jkl012.tokens.sts.global.api.aws
```

Do not use `https://sts.amazonaws.com`; that is the STS API endpoint, not an
OIDC issuer with a discovery document.

The router advertises the VPC CIDR exported by the configured `vpcStack` and
enables peer relay advertisement with `relayServerPort`. At boot, cloud-init
uses the federated identity client ID and audience with:

```bash
aws sts get-web-identity-token --audience <audience> --duration-seconds 300 --signing-algorithm RS256 --query WebIdentityToken --output text
```
