## Purpose

Define how the AWS EKS project installs and authenticates the Tailscale
Kubernetes Operator.

## Requirements

### Requirement: EKS installs the Tailscale Kubernetes Operator

The AWS EKS project SHALL install the Tailscale Kubernetes Operator into a
`tailscale` namespace using the Tailscale Helm chart.

#### Scenario: Operator Helm release is declared

- **WHEN** the EKS Pulumi program is previewed
- **THEN** it declares a Kubernetes namespace named `tailscale`
- **THEN** it declares a Helm release for the `tailscale-operator` chart

### Requirement: Operator authentication uses workload identity federation

The AWS EKS project SHALL authenticate the Tailscale Kubernetes Operator with a
Tailscale federated identity and the operator ServiceAccount OIDC token instead
of an OAuth client secret.

#### Scenario: Federated identity matches operator ServiceAccount

- **WHEN** the EKS Pulumi program is previewed
- **THEN** it declares a Tailscale federated identity whose subject is
  `system:serviceaccount:tailscale:operator`
- **THEN** the Helm release receives the federated identity ID as
  `oauth.clientId`
- **THEN** the Helm release receives the federated identity audience as
  `oauth.audience`
- **THEN** the Helm release does not require `oauth.clientSecret`

### Requirement: Cluster OIDC discovery is accessible

The AWS EKS project SHALL configure Kubernetes OIDC issuer discovery so
Tailscale can validate the operator ServiceAccount token.

#### Scenario: OIDC discovery ClusterRoleBinding exists

- **WHEN** the EKS Pulumi program is previewed
- **THEN** it declares a ClusterRoleBinding from `system:unauthenticated` to
  the `system:service-account-issuer-discovery` ClusterRole

### Requirement: Operator resources are isolated in a resource module

The AWS EKS project SHALL keep Tailscale Operator resources in a dedicated
`tailscale.py` module imported after the Kubernetes provider and shared context
are populated.

#### Scenario: Entry point imports Tailscale module after context setup

- **WHEN** the EKS project source is inspected
- **THEN** `__main__.py` populates shared context with the Kubernetes provider
  and cluster issuer
- **THEN** `__main__.py` imports `tailscale`
- **THEN** Tailscale Operator resources are not declared inline in
  `__main__.py`
