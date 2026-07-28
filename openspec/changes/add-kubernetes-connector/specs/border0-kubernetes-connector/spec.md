## ADDED Requirements

### Requirement: Tailzero Helm connector references EKS stack
The AWS connectors project SHALL install the Tailzero Kubernetes connector Helm
chart into the EKS cluster identified by a Pulumi stack reference.

#### Scenario: EKS stack provides kubeconfig
- **WHEN** the connectors project is deployed with a valid `eksStack` reference
- **THEN** the Tailzero Helm release uses the referenced stack's `kubeconfig`
  output to target the EKS cluster

### Requirement: Tailzero connector uses dedicated namespace
The Tailzero Kubernetes connector SHALL be installed into a non-default
namespace managed by the connectors project.

#### Scenario: Namespace is not default
- **WHEN** the connectors project installs the Tailzero connector chart
- **THEN** the Helm release is installed into the `tailzero` namespace

### Requirement: Tailzero connector uses provider-created token
The Tailzero Kubernetes connector SHALL authenticate with a provider-created
Border0 connector token and the connector's Tailscale auth key.

#### Scenario: Connector token configured
- **WHEN** the Helm release is declared
- **THEN** chart value `config.token` is populated from a
  `border0.ConnectorToken`
- **AND** chart value `config.tsAuthKey` is populated from the Border0
  connector's Tailscale auth key
- **AND** chart value `config.inviteCode` is not set

### Requirement: Border0 Kubernetes socket is declared
The AWS connectors project SHALL declare a Border0 Kubernetes socket for the
referenced EKS cluster and attach it to the in-cluster Tailzero connector.

#### Scenario: Kubernetes socket configured
- **WHEN** the Kubernetes connector resources are declared
- **THEN** a `border0.Socket` with `socket_type` `kubernetes` is created
- **AND** the socket is attached to the dedicated Kubernetes Border0 connector
- **AND** the socket uses the in-cluster ServiceAccount CA and token paths
