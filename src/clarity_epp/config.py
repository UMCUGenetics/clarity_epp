import typer
from pydantic import BaseModel, SecretStr, ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class ClaritySettings(BaseModel):
    """Clarity settings."""

    base_url: str
    username: str
    password: SecretStr
    timeout: int = 60


class Settings(BaseSettings):
    """Clarity_epp settings."""

    clarity: ClaritySettings

    model_config = SettingsConfigDict(toml_file="config.toml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)


def load_settings(settings_class: type[BaseSettings] = Settings) -> BaseSettings:
    """Load settings from config.toml file.

    Args:
        settings_class: Settings class to use.

    Returns:
        Settings object.
    """
    try:
        return settings_class()
    except ValidationError as validation_error:
        typer.echo("Error in configuration (config.toml) file:", err=True)
        for error in validation_error.errors():
            typer.echo(
                f"{' > '.join(str(loc) for loc in error['loc'])}: {error['msg']}, {error['type']}.",
                err=True,
            )
        raise typer.Exit(code=1) from None


# Load settings at module level
settings = load_settings()
