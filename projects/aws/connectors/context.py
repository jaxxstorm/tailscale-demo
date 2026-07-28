from __future__ import annotations

from typing import Any

import pulumi

project_name: str | None = None
stack: str | None = None
region: str | None = None
region_short_name: str | None = None
resource_prefix: str | None = None
resource_name: str | None = None
tags: dict[str, pulumi.Input[str]] = {}

connectors: pulumi.ComponentResource | None = None

border0_connector_id: pulumi.Input[str] | None = None
border0_connector_tailscale_auth_key: pulumi.Input[str] | None = None

ec2_outputs: dict[str, pulumi.Input[Any]] = {}
kubernetes_outputs: dict[str, pulumi.Input[Any]] = {}
