# AWS VPC

Pulumi project for AWS VPC networking in the demo environment.

## Layout

This project is currently small enough to keep its resources in `__main__.py`.
As new resource groups are added, split them into distinct files and have
`__main__.py` populate shared context, import resource modules in dependency
order, and export stack outputs.

Dependencies are managed by the repository root `pyproject.toml` and `uv.lock`.
Do not add project-local uv package files.

## Outputs

- `vpc_id`
- `cidr_block`
- `public_subnet_ids`
- `private_subnet_ids`
