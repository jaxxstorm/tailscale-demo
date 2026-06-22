from __future__ import annotations

from typing import Any

import pulumi

project_name: str | None = None
stack: str | None = None
region: str | None = None
region_short_name: str | None = None
resource_prefix: str | None = None
resource_name: str | None = None
vpc_stack_name: str | None = None
eks_stack_name: str | None = None
instance_type: str | None = None
ami_id: pulumi.Input[str] | None = None
kubernetes_invite_code: pulumi.Output[str] | None = None
kubernetes_namespace: str = "tailzero"
tags: dict[str, pulumi.Input[str]] = {}

connectors: pulumi.ComponentResource | None = None
vpc_stack: pulumi.StackReference | None = None
eks_stack: pulumi.StackReference | None = None

vpc_id: pulumi.Output[Any] | None = None
public_subnet_ids: pulumi.Output[Any] | None = None
private_subnet_ids: pulumi.Output[Any] | None = None
target_subnet_id: pulumi.Output[Any] | None = None

ec2_outputs: dict[str, pulumi.Input[Any]] = {}
kubernetes_outputs: dict[str, pulumi.Input[Any]] = {}
