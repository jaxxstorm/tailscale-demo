import json

import pulumi
import pulumi_aws as aws

import context

if context.resource_name is None or context.parent is None or context.tags is None:
    raise pulumi.RunError(
        "`iam` must be imported after `context.resource_name`, "
        "`context.parent`, and `context.tags` are set in the entrypoint."
    )

instance_role = aws.iam.Role(
    f"{context.resource_name}-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                }
            ],
        }
    ),
    tags=context.tags,
    opts=pulumi.ResourceOptions(parent=context.parent),
)

ssm_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{context.resource_name}-ssm",
    role=instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    opts=pulumi.ResourceOptions(parent=instance_role),
)

instance_profile = aws.iam.InstanceProfile(
    f"{context.resource_name}-profile",
    role=instance_role.name,
    tags=context.tags,
    opts=pulumi.ResourceOptions(parent=instance_role),
)
