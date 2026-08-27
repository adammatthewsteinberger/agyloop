# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Pacific-time quota boundary arithmetic and quota-id vocabulary."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def next_pt_midnight(now: datetime) -> datetime:
    """Return the next midnight in America/Los_Angeles after ``now``.

    Naive datetimes are treated as UTC. An instant that is already Pacific
    midnight advances to the following day — the quota just reset.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    pacific_now = now.astimezone(PACIFIC)
    next_date = pacific_now.date() + timedelta(days=1)
    return datetime.combine(next_date, time.min, tzinfo=PACIFIC)
