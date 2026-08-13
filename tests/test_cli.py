from typer.testing import CliRunner

from agyloop import __version__
from agyloop.cli.app import app

runner = CliRunner()


def test_version_option_reports_installed_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"agyloop {__version__}"


def test_help_option_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Autonomous Google Antigravity" in result.stdout
