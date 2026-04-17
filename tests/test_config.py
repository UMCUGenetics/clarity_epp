import pytest
import typer
from pydantic_settings import BaseSettings

from clarity_epp.config import load_settings


def test_load_settings() -> None:
    """Test load settings with valid configuration."""

    class ValidSettings(BaseSettings):
        test_field: int = 42

    result = load_settings(ValidSettings)
    assert isinstance(result, ValidSettings)
    assert result.test_field == 42


def test_load_settings_validation_error_prints_errors_and_exits(
    capsys: pytest.CaptureFixture,
) -> None:
    """Test load settings with invalid configuration."""

    class InvalidSettings(BaseSettings):
        test_field: int

    with pytest.raises(typer.Exit) as exit_info:
        load_settings(InvalidSettings)

    # Verify exit code
    assert exit_info.value.exit_code == 1

    # Verify printed error messages
    captured = capsys.readouterr()
    assert "Error in configuration (config.toml) file:" in captured.err
    assert "test_field: Field required" in captured.err
