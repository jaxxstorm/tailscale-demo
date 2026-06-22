from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence, cast

import pulumi
import pulumi_aws as aws
import pulumi_border0 as border0
import pulumi_cloudinit as cloudinit

import context

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from components import AutoScalingEC2, AutoScalingEC2Args  # noqa: E402

required_context = {
    "ami_id": context.ami_id,
    "connectors": context.connectors,
    "instance_type": context.instance_type,
    "private_subnet_ids": context.private_subnet_ids,
    "public_subnet_ids": context.public_subnet_ids,
    "region": context.region,
    "resource_name": context.resource_name,
    "stack": context.stack,
    "target_subnet_id": context.target_subnet_id,
    "vpc_id": context.vpc_id,
}
missing_context = [name for name, value in required_context.items() if value is None]
if missing_context:
    raise RuntimeError(f"connectors context is missing: {', '.join(missing_context)}")

resource_name = cast(str, context.resource_name)
region = cast(str, context.region)
stack = cast(str, context.stack)
connectors = cast(pulumi.ComponentResource, context.connectors)
ami_id = cast(pulumi.Input[str], context.ami_id)
instance_type = cast(pulumi.Input[str], context.instance_type)
public_subnet_ids = cast(
    pulumi.Input[Sequence[pulumi.Input[str]]],
    context.public_subnet_ids,
)
target_subnet_id = cast(pulumi.Input[str], context.target_subnet_id)
vpc_id = cast(pulumi.Input[str], context.vpc_id)
tags = cast(dict[str, pulumi.Input[str]], context.tags)

connector = border0.Connector(
    resource_name,
    built_in_ssh_service_enabled=True,
    description=f"Tailzero SSH connector on AWS EC2 in {region}",
    name=resource_name,
    opts=pulumi.ResourceOptions(parent=connectors),
)

connector_token = border0.ConnectorToken(
    f"{resource_name}-token",
    connector_id=connector.id,
    name=f"{resource_name}-token",
    opts=pulumi.ResourceOptions(parent=connector),
)

connector_ssh_socket = border0.Socket(
    f"{resource_name}-ssh",
    connector_ids=[connector.id],
    display_name=f"AWS Connector SSH ({region})",
    name=resource_name,
    recording_enabled=True,
    socket_type="ssh",
    ssh_configurations=[
        border0.SocketSshConfigurationArgs(
            service_type="connector_built_in_ssh_service",
            username_provider="use_connector_user",
        )
    ],
    tags={
        "border0_client_category": "Infrastructure",
        "border0_client_subcategory": region,
        "border0_client_icon": "logos:aws",
        "border0_client_icon_text": f"AWS Connector SSH {region}",
        "env": stack,
        "region": region,
        "socket_type": "ssh",
        "ssh_type": "built_in",
    },
    opts=pulumi.ResourceOptions(parent=connector),
)

connector_s3_socket = border0.Socket(
    f"{resource_name}-s3",
    aws_s3_configurations=[border0.SocketAwsS3ConfigurationArgs()],
    connector_ids=[connector.id],
    display_name=f"AWS S3 ({region})",
    name=f"{resource_name}-s3",
    recording_enabled=True,
    socket_type="aws_s3",
    tags={
        "border0_client_category": "Infrastructure",
        "border0_client_subcategory": region,
        "border0_client_icon": "logos:aws-s3",
        "border0_client_icon_text": f"AWS S3 {region}",
        "env": stack,
        "region": region,
        "socket_type": "aws_s3",
        "provider_type": "aws",
    },
    opts=pulumi.ResourceOptions(parent=connector),
)

instance_role = aws.iam.Role(
    f"{resource_name}-role",
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
    tags=tags,
    opts=pulumi.ResourceOptions(parent=connectors),
)

ssm_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{resource_name}-ssm",
    role=instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    opts=pulumi.ResourceOptions(parent=instance_role),
)

ssm_session_policy = aws.iam.RolePolicy(
    f"{resource_name}-ssm-session",
    role=instance_role.id,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "StartStopSession",
                    "Effect": "Allow",
                    "Action": [
                        "ssm:ResumeSession",
                        "ssm:StartSession",
                        "ssm:TerminateSession",
                    ],
                    "Resource": [
                        "arn:aws:ec2:*:*:instance/*",
                        "arn:aws:ssm:*:*:document/AWS-StartSSHSession",
                        "arn:aws:ssm:*:*:document/SSM-SessionManagerRunShell",
                    ],
                },
                {
                    "Sid": "DescribeForTargeting",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:DescribeInstances",
                        "ssm:DescribeInstanceInformation",
                        "ssm:DescribeSessions",
                    ],
                    "Resource": "*",
                },
            ],
        }
    ),
    opts=pulumi.ResourceOptions(parent=instance_role),
)

s3_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{resource_name}-s3-access",
    role=instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess",
    opts=pulumi.ResourceOptions(parent=instance_role),
)

instance_profile = aws.iam.InstanceProfile(
    f"{resource_name}-profile",
    role=instance_role.name,
    tags=tags,
    opts=pulumi.ResourceOptions(parent=instance_role),
)

security_group = aws.ec2.SecurityGroup(
    f"{resource_name}-sg",
    description="Tailzero connector outbound access",
    vpc_id=vpc_id,
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            description="Allow outbound traffic",
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
        ),
    ],
    tags={**tags, "Name": f"{resource_name}-sg"},
    opts=pulumi.ResourceOptions(parent=connectors),
)

target_instance_role = aws.iam.Role(
    f"{resource_name}-target-role",
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
    tags=tags,
    opts=pulumi.ResourceOptions(parent=connectors),
)

target_ssm_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{resource_name}-target-ssm",
    role=target_instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    opts=pulumi.ResourceOptions(parent=target_instance_role),
)

target_instance_profile = aws.iam.InstanceProfile(
    f"{resource_name}-target-profile",
    role=target_instance_role.name,
    tags=tags,
    opts=pulumi.ResourceOptions(parent=target_instance_role),
)

target_security_group = aws.ec2.SecurityGroup(
    f"{resource_name}-target-sg",
    description="SSM-managed EC2 target outbound access",
    vpc_id=vpc_id,
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            description="Allow outbound traffic",
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
        ),
    ],
    tags={**tags, "Name": f"{resource_name}-target-sg"},
    opts=pulumi.ResourceOptions(parent=connectors),
)

target_instance = aws.ec2.Instance(
    f"{resource_name}-target",
    ami=ami_id,
    iam_instance_profile=target_instance_profile.name,
    instance_type=instance_type,
    metadata_options=aws.ec2.InstanceMetadataOptionsArgs(
        http_endpoint="enabled",
        http_tokens="required",
    ),
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=20,
        volume_type="gp3",
    ),
    subnet_id=target_subnet_id,
    tags={**tags, "Name": f"{resource_name}-target"},
    vpc_security_group_ids=[target_security_group.id],
    opts=pulumi.ResourceOptions(
        parent=connectors,
        depends_on=[target_ssm_policy_attachment],
    ),
)

ec2_ssm_socket = border0.Socket(
    f"{resource_name}-ec2-ssm",
    connector_ids=[connector.id],
    display_name=f"AWS EC2 SSM ({region})",
    name=f"{resource_name}-ec2-ssm",
    recording_enabled=True,
    socket_type="ssh",
    ssh_configurations=[
        border0.SocketSshConfigurationArgs(
            ec2_instance_id=target_instance.id,
            ec2_instance_region=region,
            service_type="aws_ssm",
            ssm_target_type="ec2",
        )
    ],
    tags={
        "border0_client_category": "Infrastructure",
        "border0_client_subcategory": region,
        "border0_client_icon": "bitcoin-icons:linux-terminal-outline",
        "border0_client_icon_text": f"AWS EC2 SSM {region}",
        "env": stack,
        "region": region,
        "socket_type": "ssh",
        "ssh_type": "aws_ssm",
        "provider_type": "aws",
    },
    opts=pulumi.ResourceOptions(
        parent=connector,
        depends_on=[ssm_session_policy, target_instance],
    ),
)

cloudinit_parts = pulumi.Output.all(
    connector_token.token,
    connector.tailscale_auth_key,
).apply(
    lambda credentials: [
        cloudinit.GetConfigPartArgs(
            content=f"""#!/bin/bash -xe
export AWS_REGION="{region}"
curl -fsSL https://tailscale.border0.com/tailzero/install.sh | sh

install -d -m 0755 /etc/border0
cat > /etc/border0/tailzero.env <<'CREDSEOF'
TS_AUTH_KEY={credentials[1]}
BORDER0_TOKEN={credentials[0]}
CREDSEOF
chmod 0600 /etc/border0/tailzero.env

/usr/local/bin/tailzero install
""",
            content_type="text/x-shellscript",
            filename="tailzero-connector.sh",
        )
    ]
)
connector_cloudinit = cloudinit.get_config_output(
    base64_encode=True,
    gzip=False,
    parts=cloudinit_parts,
)
user_data = pulumi.Output.secret(connector_cloudinit.rendered)

connector_instances = AutoScalingEC2(
    resource_name,
    AutoScalingEC2Args(
        ami_id=ami_id,
        desired_capacity=1,
        instance_profile_name=instance_profile.name,
        instance_type=instance_type,
        max_size=1,
        min_size=1,
        resource_name=resource_name,
        security_group_ids=[security_group.id],
        subnet_ids=public_subnet_ids,
        tags=tags,
        user_data=user_data,
        associate_public_ip_address="true",
    ),
    opts=pulumi.ResourceOptions(
        parent=connectors,
        depends_on=[
            connector_token,
            s3_policy_attachment,
            ssm_policy_attachment,
            ssm_session_policy,
        ],
    ),
)

context.ec2_outputs = {
    "autoscaling_group_name": connector_instances.autoscaling_group_name,
    "border0_connector_id": connector.id,
    "border0_connector_name": connector.name,
    "border0_connector_ec2_ssm_socket_id": ec2_ssm_socket.id,
    "border0_connector_s3_socket_id": connector_s3_socket.id,
    "border0_connector_ssh_socket_id": connector_ssh_socket.id,
    "border0_connector_token_id": connector_token.id,
    "instance_profile_name": instance_profile.name,
    "launch_template_id": connector_instances.launch_template_id,
    "security_group_id": security_group.id,
    "subnet_ids": public_subnet_ids,
    "target_instance_id": target_instance.id,
    "target_instance_private_ip": target_instance.private_ip,
    "vpc_id": vpc_id,
}
