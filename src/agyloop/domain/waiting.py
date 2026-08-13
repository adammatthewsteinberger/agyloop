"""Waiting helpers. The adaptive probe policy lands in a later task."""

from __future__ import annotations

from datetime import datetime

from agyloop.domain.quota import next_pt_midnight


def next_pacific_midnight(now: datetime) -> datetime:
    """Return the next midnight in America/Los_Angeles after ``now``."""
    return next_pt_midnight(now)
