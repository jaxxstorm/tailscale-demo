from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

import pulumi
import pulumi_aws as aws


@dataclass
class AutoScalingEC2Args:
    ami_id: pulumi.Input[str]
    instance_type: pulumi.Input[str]
    security_group_ids: pulumi.Input[Sequence[pulumi.Input[str]]]
    subnet_ids: pulumi.Input[Sequence[pulumi.Input[str]]]
    user_data: pulumi.Input[str]
    associate_public_ip_address: pulumi.Input[str] = "false"
    desired_capacity: pulumi.Input[int] = 1
    health_check_type: pulumi.Input[str] = "EC2"
    instance_profile_name: Optional[pulumi.Input[str]] = None
    max_size: pulumi.Input[int] = 1
    min_size: pulumi.Input[int] = 1
    resource_name: Optional[str] = None
    tags: Mapping[str, pulumi.Input[str]] = field(default_factory=dict)


class AutoScalingEC2(pulumi.ComponentResource):
    launch_template: aws.ec2.LaunchTemplate
    autoscaling_group: aws.autoscaling.Group
    launch_template_id: pulumi.Output[str]
    autoscaling_group_name: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        args: AutoScalingEC2Args,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__(
            "tailscale-demo:components:AutoScalingEC2",
            name,
            None,
            opts,
        )

        resource_name = args.resource_name or name
        tags: dict[str, pulumi.Input[str]] = {**args.tags, "Name": resource_name}
        child_opts = pulumi.ResourceOptions(
            parent=self,
            depends_on=opts.depends_on if opts is not None else None,
        )

        iam_instance_profile = None
        if args.instance_profile_name is not None:
            iam_instance_profile = aws.ec2.LaunchTemplateIamInstanceProfileArgs(
                name=args.instance_profile_name,
            )

        self.launch_template = aws.ec2.LaunchTemplate(
            f"{name}-lt",
            name_prefix=f"{resource_name}-",
            image_id=args.ami_id,
            instance_type=args.instance_type,
            iam_instance_profile=iam_instance_profile,
            network_interfaces=[
                aws.ec2.LaunchTemplateNetworkInterfaceArgs(
                    associate_public_ip_address=args.associate_public_ip_address,
                    delete_on_termination="true",
                    security_groups=args.security_group_ids,
                )
            ],
            user_data=args.user_data,
            tag_specifications=[
                aws.ec2.LaunchTemplateTagSpecificationArgs(
                    resource_type="instance",
                    tags=tags,
                ),
                aws.ec2.LaunchTemplateTagSpecificationArgs(
                    resource_type="volume",
                    tags=tags,
                ),
            ],
            tags={**args.tags, "Name": f"{resource_name}-lt"},
            opts=child_opts,
        )

        self.autoscaling_group = aws.autoscaling.Group(
            f"{name}-asg",
            desired_capacity=args.desired_capacity,
            health_check_type=args.health_check_type,
            launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
                id=self.launch_template.id,
                version="$Latest",
            ),
            max_size=args.max_size,
            min_size=args.min_size,
            tags=[
                aws.autoscaling.GroupTagArgs(
                    key=key,
                    value=value,
                    propagate_at_launch=True,
                )
                for key, value in tags.items()
            ],
            vpc_zone_identifiers=args.subnet_ids,
            opts=child_opts,
        )

        self.launch_template_id = self.launch_template.id
        self.autoscaling_group_name = self.autoscaling_group.name

        self.register_outputs(
            {
                "autoscaling_group_name": self.autoscaling_group_name,
                "launch_template_id": self.launch_template_id,
            }
        )
