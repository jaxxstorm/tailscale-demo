import pulumi
import pulumi_awsx as awsx

PROJECT_NAME = pulumi.get_project()
STACK = pulumi.get_stack()

AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")
NAME = "-".join(REGION.split("-")[:2])
CONFIG = pulumi.Config()
CIDR_BLOCK = CONFIG.require("cidr_block")

PULUMI_CONFIG = pulumi.Config("pulumi")
RESOURCE_PREFIX = PULUMI_CONFIG.require("resourcePrefix")


TAGS = {
    "environment": STACK,
    "project": PROJECT_NAME,
    "owner": "lbriggs",
    "deployed_by": "pulumi",
    "org": "lbrlabs",
}

CONFIG = pulumi.Config()

vpc = awsx.ec2.Vpc(
    f"{RESOURCE_PREFIX}-vpc-{NAME}",
    cidr_block=CIDR_BLOCK,
    subnet_strategy="Auto",
    subnet_specs=[
        awsx.ec2.SubnetSpecArgs(
            type=awsx.ec2.SubnetType.PUBLIC,
            cidr_mask=20,
            tags={"kubernetes.io/role/elb": "1", **TAGS},
        ),
        awsx.ec2.SubnetSpecArgs(
            type=awsx.ec2.SubnetType.PRIVATE,
            cidr_mask=19,
            tags={"kubernetes.io/role/internal-elb": "1", **TAGS},
        ),
    ],
    enable_dns_hostnames=True,
    enable_dns_support=True,
    number_of_availability_zones=2,
    nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
        strategy=awsx.ec2.NatGatewayStrategy.ONE_PER_AZ
    ),
    tags=TAGS,
)


pulumi.export(f"vpc_id", vpc.vpc_id)
pulumi.export(f"cidr_block", CIDR_BLOCK)
pulumi.export(f"public_subnet_ids", vpc.public_subnet_ids)
pulumi.export(f"private_subnet_ids", vpc.private_subnet_ids)
