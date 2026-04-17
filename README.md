# clarity_epp
Clarity LIMS epp scripts

## Usage
```bash
uv run clarity_epp
```

## Development environment
The following command will install a development environment using [uv](https://docs.astral.sh/uv/) and setup the [Ruff](https://docs.astral.sh/ruff/) [pre-commit](https://pre-commit.com) hook.

```bash
uv sync
pre-commit install
```

### Lint and test
In this project we use [Ruff](https://docs.astral.sh/ruff/) to (automatically) lint and format the code. Tests are implemented using the [pytest](https://docs.pytest.org) package.

```bash
uv run ruff check --select I --fix
uv run pytest
```
