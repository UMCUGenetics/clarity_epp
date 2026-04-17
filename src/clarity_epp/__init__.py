import typer

from clarity_epp.services import ClarityFactory

app = typer.Typer(no_args_is_help=True)

# Hello World, placeholder, see for example setup with import typer apps: https://github.com/UMCUGenetics/clarity_epp/blob/feature/week_of_refactor_robert/src/clarity_epp/__init__.py
@app.command("hello")
def hello():
    typer.echo("Hello World!")

    clarity = ClarityFactory.get_instance()
    typer.echo(clarity.versions)


def main() -> None:
    app()
