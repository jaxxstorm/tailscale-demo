import json

import pulumi
import pulumi_aws as aws
import pulumi_tailscale as tailscale

import context
import iam

if (
    context.resource_name is None
    or context.parent is None
    or context.advertise_tags is None
    or context.tailscale_issuer is None
    or context.tailscale_scopes is None
):
    raise pulumi.RunError(
        "`identity` must be imported after the Tailscale identity fields are "
        "set in `context` and after `iam` is importable."
    )

federated_identity = tailscale.FederatedIdentity(
    f"{context.resource_name}-federated-identity",
    description=f"{context.resource_name} AWS router role",
    issuer=context.tailscale_issuer,
    scopes=context.tailscale_scopes,
    subject=iam.instance_role.arn,
    tags=context.advertise_tags,
    opts=pulumi.ResourceOptions(parent=iam.instance_role),
)

web_identity_policy = aws.iam.RolePolicy(
    f"{context.resource_name}-web-identity",
    role=iam.instance_role.id,
    policy=federated_identity.audience.apply(
        lambda audience: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowGetWebIdentityTokenForTailscale",
                        "Effect": "Allow",
                        "Action": "sts:GetWebIdentityToken",
                        "Resource": "*",
                        "Condition": {
                            "ForAnyValue:StringEquals": {
                                "sts:IdentityTokenAudience": [audience],
                            },
                            "NumericLessThanEquals": {
                                "sts:DurationSeconds": "300",
                            },
                        },
                    }
                ],
            }
        )
    ),
    opts=pulumi.ResourceOptions(parent=iam.instance_role),
)
