from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

FROZEN_NOW = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)


@pytest.fixture
def fake_now() -> Iterator[datetime]:
    """Freeze the classifier clock so RPD reset arithmetic is deterministic."""
    with patch("agyloop.domain.classify._current_time", return_value=FROZEN_NOW):
        yield FROZEN_NOW


def pytest_configure(config: pytest.Config) -> None:
    """Let ``pytest -m system`` override addopts' default marker exclusion."""
    cli_markers: list[str] = []
    args = config.invocation_params.args
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-m" and index + 1 < len(args):
            cli_markers.append(args[index + 1])
            index += 2
            continue
        if arg.startswith("-m") and arg != "-m":
            cli_markers.append(arg[2:])
        index += 1
    if cli_markers:
        config.option.markexpr = " and ".join(cli_markers)
