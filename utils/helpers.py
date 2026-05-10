"""
utils/helpers.py
Shared utility functions: ID generation, time helpers, schedule matching.
"""

import random
import string
from datetime import datetime, timedelta


COURSES = ["BSCS", "BSIT", "BSED", "BSHM", "BSN", "BSBA", "BSCE", "BSCpE"]
BLOCKS  = ["A", "B", "C", "D", "E"]
YEARS   = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
DAYS    = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def generate_id(prefix: str) -> str:
    year = datetime.now().year
    nums = "".join(random.choices(string.digits, k=6))
    return f"{prefix}-{year}-{nums}"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_name() -> str:
    return datetime.now().strftime("%A")


def current_time():
    return datetime.now().time()


def _parse_time_str(time_str: str):
    """
    Parse a time string in any common format.
    Supports: '8:00 AM', '8:00AM', '8:00am', '08:00', '8:00 PM', etc.
    Returns a datetime.time object, or raises ValueError.
    """
    s = time_str.strip().upper().replace("\u202f", " ")  # normalize narrow space
    # Normalise: insert space before AM/PM if missing (e.g. "8:00AM" -> "8:00 AM")
    import re
    s = re.sub(r'(\d)(AM|PM)', r'\1 \2', s)
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            pass
    raise ValueError(f"Cannot parse time: {time_str!r}")


def check_schedule(schedules: list[dict]) -> tuple[bool, object, dict | None, str]:
    """
    Returns (has_schedule, sched_start_time, sched_dict, denial_reason).
    - has_schedule=True  : user has a schedule active right now
    - denial_reason      : "NO_SCHEDULE_TODAY" | "NOT_IN_WINDOW" | ""
    Entry is allowed 30 minutes before the schedule starts.
    """
    today = today_name()
    now   = current_time()

    has_today = False
    for sched in schedules:
        if sched.get("day", "").strip().lower() != today.lower():
            continue
        has_today = True
        try:
            start = _parse_time_str(sched["start_time"])
            end   = _parse_time_str(sched["end_time"])
            allow = (
                datetime.combine(datetime.today(), start) - timedelta(minutes=30)
            ).time()
            if allow <= now <= end:
                return True, start, sched, ""
        except (ValueError, KeyError) as e:
            print(f"[check_schedule] skipping bad schedule row: {sched} — {e}")
            continue

    if not has_today:
        return False, None, None, "NO_SCHEDULE_TODAY"
    return False, None, None, "NOT_IN_WINDOW"


def is_late(sched_start) -> bool:
    """Returns True if current time is past sched_start (a datetime.time object)."""
    try:
        return current_time() > sched_start
    except Exception:
        return False
