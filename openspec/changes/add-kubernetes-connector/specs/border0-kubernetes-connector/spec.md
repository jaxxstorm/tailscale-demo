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

### Requirement: Tailzero invite code is secret config
The Tailzero Kubernetes connector SHALL receive its invite code from Pulumi
secret config.

#### Scenario: Invite code configured
- **WHEN** the Helm release is declared
- **THEN** chart value `config.inviteCode` is populated from
  `demo-aws-connectors:kubernetesInviteCode`
