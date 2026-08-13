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
