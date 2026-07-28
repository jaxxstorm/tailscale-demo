import pulumi

import context

PROJECT_NAME = pulumi.get_project()
STACK = pulumi.get_stack()

AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")
REGION_SHORT_NAME = "-".join(REGION.split("-")[:2])

PULUMI_CONFIG = pulumi.Config("pulumi")

RESOURCE_PREFIX = PULUMI_CONFIG.require("resourcePrefix")

TAGS = {
    "environment": STACK,
    "project": PROJECT_NAME,
    "owner": "lbriggs",
    "deployed_by": "pulumi",
    "org": "lbrlabs",
}

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
context.tags = TAGS
context.connectors = connectors

# Import the connector modules you want this stack to manage.
import ec2  # noqa: E402,F401
import kubernetes  # noqa: E402,F401

outputs = {
    **context.ec2_outputs,
    **context.kubernetes_outputs,
}

connectors.register_outputs(outputs)

for name, value in outputs.items():
    pulumi.export(name, value)
