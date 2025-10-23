from pydantic import BaseModel, SecretStr, ValidationError
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource


class ClaritySettings(BaseModel):
    baseuri: str
    username: str
    password: SecretStr
    api_timeout: int


class Settings(BaseSettings):
    """Application settings."""

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


try:
    settings = Settings()
except ValidationError as validation_error:
    print("Error in configuration (config.toml) file:")
    for error in validation_error.errors():
        print(f"{error['loc'][0]}: {error['msg']}, {error['type']}.")
    exit(1)
