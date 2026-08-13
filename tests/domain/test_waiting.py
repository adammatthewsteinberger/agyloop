from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from agyloop.domain.quota import next_pt_midnight
from agyloop.domain.waiting import next_pacific_midnight

PACIFIC = ZoneInfo("America/Los_Angeles")


def test_next_pacific_midnight_is_alias_of_next_pt_midnight() -> None:
    now = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    assert next_pacific_midnight(now) == next_pt_midnight(now)


def test_next_pacific_midnight_from_afternoon_utc() -> None:
    now = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    reset = next_pacific_midnight(now)
    pacific = reset.astimezone(PACIFIC)
    assert pacific.hour == 0
    assert pacific.minute == 0
    assert pacific.second == 0
    assert pacific.date().isoformat() == "2026-08-14"


def test_next_pacific_midnight_treats_naive_as_utc() -> None:
    naive = datetime(2026, 8, 13, 18, 0)
    aware = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    assert next_pacific_midnight(naive) == next_pacific_midnight(aware)


def test_next_pacific_midnight_across_spring_forward() -> None:
    # US DST 2026 starts 2026-03-08 02:00 PST → 03:00 PDT.
    before = datetime(2026, 3, 7, 23, 30, tzinfo=PACIFIC)
    reset = next_pacific_midnight(before)
    assert reset.astimezone(PACIFIC).isoformat() == "2026-03-08T00:00:00-08:00"

    after = datetime(2026, 3, 8, 12, 0, tzinfo=PACIFIC)
    reset_after = next_pacific_midnight(after)
    assert reset_after.astimezone(PACIFIC).isoformat() == "2026-03-09T00:00:00-07:00"


def test_next_pacific_midnight_across_fall_back() -> None:
    # US DST 2026 ends 2026-11-01 02:00 PDT → 01:00 PST.
    before = datetime(2026, 10, 31, 23, 30, tzinfo=PACIFIC)
    reset = next_pacific_midnight(before)
    assert reset.astimezone(PACIFIC).isoformat() == "2026-11-01T00:00:00-07:00"

    after = datetime(2026, 11, 1, 12, 0, tzinfo=PACIFIC)
    reset_after = next_pacific_midnight(after)
    assert reset_after.astimezone(PACIFIC).isoformat() == "2026-11-02T00:00:00-08:00"


def test_exact_pacific_midnight_advances_to_following_day() -> None:
    midnight = datetime(2026, 8, 13, 0, 0, tzinfo=PACIFIC)
    reset = next_pacific_midnight(midnight)
    assert reset.astimezone(PACIFIC).isoformat() == "2026-08-14T00:00:00-07:00"
