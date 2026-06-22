from typing import Any

import pulumi

resource_name: str | None = None
parent: pulumi.Resource | None = None
tags: dict[str, str] | None = None
advertise_tags: Any = None
tailscale_issuer: str | None = None
tailscale_scopes: Any = None
