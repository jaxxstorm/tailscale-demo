## ADDED Requirements

### Requirement: Connector resources are split by domain
The AWS connectors project SHALL separate EC2-oriented resources and
Kubernetes-oriented resources into distinct project-local modules.

#### Scenario: EC2 resources live in EC2 module
- **WHEN** EC2 connector resources are declared
- **THEN** the EC2 connector, EC2 SSM target, S3 socket, IAM resources, cloud-init,
  and Auto Scaling Group are declared from `ec2.py`

#### Scenario: Kubernetes resources live in Kubernetes module
- **WHEN** Kubernetes connector resources are declared
- **THEN** the EKS stack reference, Kubernetes provider, namespace, and Tailzero
  Helm release are declared from `kubernetes.py`

### Requirement: Entrypoint remains orchestration only
The AWS connectors project entrypoint SHALL initialize shared configuration,
populate context, import resource modules, and export module outputs.

#### Scenario: Main imports resource modules
- **WHEN** the connectors project entrypoint runs
- **THEN** it imports both `ec2.py` and `kubernetes.py` and exports their module
  outputs
