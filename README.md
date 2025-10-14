# clarity_epp

Clarity LIMS epp scripts

## Week of Refactor

This branch contains all work for the Week of Refactor.

During this week, we’ll focus on modernizing and improving [`clarity_epp`](https://github.com/UMCUGenetics/clarity_epp) — transforming it into a maintainable, testable, and modular Python package that can be reused as a library in other applications.

### Preparation

To prepare for the week of code some changes have already been applied to this repo to make life easier and/or not pose a distraction during the week of code.

- [x] Add UV for dependency management
- [x] Split out development dependencies
- [x] Upgraded dependencies to latest versions
- [x] Removed legacy `requirements.txt`
- [ ] Fix GitHub Actions

### Refactor Tasks

The following task could be taken up during the week of refactor (in random/undecided order).

#### Code Quality & Structure

- [ ] Apply [general](https://github.com/UMCUGenetics/BioinformaticsQMS/blob/develop/docs/procedures/coding-guidelines/general.md) and [Python](https://github.com/UMCUGenetics/BioinformaticsQMS/blob/develop/docs/procedures/coding-guidelines/python.md) coding guidelines.
- [ ] Unravel large or monolithic functions, for example:
  - [ ] Separate LIMS queries
  - [ ] Isolate data calculations
  - [ ] Split output / reporting logic
- [ ] Move code into `src/` layout
- [ ] Discuss package structure, currently organized by functionality and machine/process
- [ ] Add or update unit tests (`pytest`)
- [ ] Add or update docstrings (and type hints)

#### CLI & Configuration

- [ ] Replace `argparse` with [typer](https://typer.tiangolo.com)
  - [ ] Move CLI command definitions closer to their logic modules
  - [ ] Review [Typer subcommands pattern](https://typer.tiangolo.com/tutorial/subcommands/)
- [ ] Refactor `config.py` to [pydantic_settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
  - [ ] Support variable overrides using `.env` or `.json` config files.
  - [ ] Add type validation and default settings

#### Logging & Error Handling

- [ ] Structured logging using [Loguru](https://loguru.readthedocs.io)
- [ ] Capture and log exceptions
- [ ] Store logs on the LIMS server for debugging
