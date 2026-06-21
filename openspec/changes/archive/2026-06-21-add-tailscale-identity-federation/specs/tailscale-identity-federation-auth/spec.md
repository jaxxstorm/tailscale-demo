## ADDED Requirements

### Requirement: AWS VPN clients authenticate with Tailscale identity federation

The AWS VPN project SHALL authenticate Tailscale router clients with workload
identity federation instead of requiring a static Tailscale auth key.

#### Scenario: Cloud-init uses workload identity inputs

- **WHEN** the AWS VPN launch template user data is generated
- **THEN** the Tailscale cloud-init module receives a federated identity
  `client_id`, `audience`, and runtime `id_token` command

### Requirement: Tailscale federated identity is managed by Pulumi

The AWS VPN project SHALL manage a Tailscale federated identity whose subject is
the AWS instance role ARN and whose tags/scopes allow tagged router clients to
join the tailnet. Stack configuration SHALL set `tailscaleIssuer` to the AWS
OIDC issuer URL shown by Tailscale for AWS trust credentials, such as a
`https://*.tokens.sts.global.api.aws` URL.

#### Scenario: Federated identity matches instance role

- **WHEN** the AWS VPN project is previewed
- **THEN** the Tailscale federated identity subject matches the EC2 instance role
  ARN

#### Scenario: STS API endpoint is rejected as issuer

- **WHEN** the AWS VPN stack config sets `tailscaleIssuer` to `default` or
  `https://sts.amazonaws.com`
- **THEN** the program fails with a message requiring the AWS OIDC issuer URL
  shown by the Tailscale trust credentials UI

### Requirement: Instance role can request bounded AWS web identity tokens

The AWS VPN project SHALL attach an inline IAM policy to the router instance
role allowing `sts:GetWebIdentityToken` only for the Tailscale audience and a
maximum token duration of 300 seconds, while keeping identity/IAM-related
resource declarations outside the entrypoint module.

#### Scenario: IAM policy restricts token audience and duration

- **WHEN** the router role policy is inspected
- **THEN** it contains `sts:IdentityTokenAudience` and `sts:DurationSeconds`
  conditions for the Tailscale federated identity exchange
- **THEN** the policy is declared in a dedicated resource module rather than
  inline in `__main__.py`

### Requirement: Static auth-key config is not required for VPN bootstrap

The AWS VPN stack configuration SHALL NOT require `lbrlabs-aws-vpn:authKey` when
identity federation is enabled.

#### Scenario: Stack config omits auth key

- **WHEN** the AWS VPN stack config is inspected
- **THEN** it contains identity federation inputs rather than a static Tailscale
  auth key
