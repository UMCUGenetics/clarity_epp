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

## Application structure

With v2 we update the application structure to better fit all the functionality available in clarity_epp. This is WIP and can/should be update during the v2 refactor.

```tree
├── LICENSE
├── README.md
├── config.toml                     # Application config, using pydantic-settings
├── pyproject.toml
├── src
│   └── clarity_epp
│       ├── __init__.py
│       ├── cli.py                  # Typer cli config
│       ├── core
│       │   ├── __init__.py
│       │   └── config.py           # pydantic-settings models
│       ├── instruments             # Code for interacting with lab instruments, combines export / upload from v1
│       │   ├── __init__.py
│       │   └── tecan.py
│       ├── qc                      # QC calculations
│       │   ├── __init__.py
│       │   ├── bioinformatics.py
│       │   └── fragment_length.py
│       ├── services                # Service classes to interact with (external) systems
│       │   ├── __init__.py
│       │   └── clarity.py
│       └── utils                   # Utility functions
│           ├── __init__.py
│           ├── container.py
│           └── process.py
├── tests
│   └── core
│       └── test_config.py
└── uv.lock

```
