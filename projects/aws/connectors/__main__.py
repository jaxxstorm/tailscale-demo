import sys
from pathlib import Path

import pulumi
import pulumi_aws as aws

import context

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

PROJECT_NAME = pulumi.get_project()
STACK = pulumi.get_stack()

AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")
REGION_SHORT_NAME = "-".join(REGION.split("-")[:2])

CONFIG = pulumi.Config()
PULUMI_CONFIG = pulumi.Config("pulumi")

RESOURCE_PREFIX = PULUMI_CONFIG.require("resourcePrefix")
VPC_STACK = CONFIG.get("vpcStack", "lbrlabs/demo-aws-vpc/west")
EKS_STACK = CONFIG.get("eksStack", "lbrlabs/demo-aws-eks/west")
INSTANCE_TYPE = CONFIG.get("instanceType") or "t4g.nano"
AMI_ID = CONFIG.get("amiId")
KUBERNETES_INVITE_CODE = CONFIG.require_secret("kubernetesInviteCode")
KUBERNETES_NAMESPACE = CONFIG.get("kubernetesNamespace") or "tailzero"

TAGS = {
    "environment": STACK,
    "project": PROJECT_NAME,
    "owner": "lbriggs",
    "deployed_by": "pulumi",
    "org": "lbrlabs",
}

vpc_stack = pulumi.StackReference(VPC_STACK)
eks_stack = pulumi.StackReference(EKS_STACK)

vpc_id = vpc_stack.require_output("vpc_id")
public_subnet_ids = vpc_stack.require_output("public_subnet_ids")
private_subnet_ids = vpc_stack.require_output("private_subnet_ids")
target_subnet_id = private_subnet_ids.apply(lambda ids: ids[0])

if AMI_ID is None:
    ami_id = aws.ec2.get_ami(
        most_recent=True,
        owners=["amazon"],
        filters=[
            aws.ec2.GetAmiFilterArgs(
                name="name",
                values=["al2023-ami-2023*-kernel-*-arm64"],
            ),
            aws.ec2.GetAmiFilterArgs(name="architecture", values=["arm64"]),
            aws.ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
        ],
    ).id
else:
    ami_id = AMI_ID

resource_name = f"{RESOURCE_PREFIX}-tailzero-ssh-{REGION_SHORT_NAME}"
connectors = pulumi.ComponentResource(
    "tailscale-demo:aws:TailzeroConnectors",
    resource_name,
)

context.project_name = PROJECT_NAME
context.stack = STACK
context.region = REGION
context.region_short_name = REGION_SHORT_NAME
context.resource_prefix = RESOURCE_PREFIX
context.resource_name = resource_name
context.vpc_stack_name = VPC_STACK
context.eks_stack_name = EKS_STACK
context.instance_type = INSTANCE_TYPE
context.ami_id = ami_id
context.kubernetes_invite_code = KUBERNETES_INVITE_CODE
context.kubernetes_namespace = KUBERNETES_NAMESPACE
context.tags = TAGS
context.connectors = connectors
context.vpc_stack = vpc_stack
context.eks_stack = eks_stack
context.vpc_id = vpc_id
context.public_subnet_ids = public_subnet_ids
context.private_subnet_ids = private_subnet_ids
context.target_subnet_id = target_subnet_id

import ec2  # noqa: E402,F401
import kubernetes  # noqa: E402,F401

outputs = {
    **context.ec2_outputs,
    **context.kubernetes_outputs,
}

connectors.register_outputs(outputs)

for name, value in outputs.items():
    pulumi.export(name, value)
