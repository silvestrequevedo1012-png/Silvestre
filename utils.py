"""
utils.py
Shared utility functions.
"""

import datetime
import random
import string
import os


# ── ID Generator ──────────────────────────────────────────────────────────────
def generate_id(prefix: str) -> str:
    year = datetime.datetime.now().strftime("%Y")
    rand = "".join(random.choices(string.digits, k=5))
    return f"{prefix}-{year}-{rand}"


# ── Time Utilities ────────────────────────────────────────────────────────────
def now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


_DAY_MAP = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday",
    3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday",
}


def _parse_time(time_str: str):
    """Parse time string supporting both 24h (08:00) and 12h (8:00 AM) formats."""
    time_str = time_str.strip()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.datetime.strptime(time_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse time: {time_str!r}")


def check_schedule(schedules: list[dict]) -> tuple[bool, str, dict, str]:
    """
    Returns (has_schedule, sched_start_time_str, schedule_dict, denial_reason).
    - has_schedule=True  : user has a schedule active right now
    - denial_reason      : "NO_SCHEDULE_TODAY" | "NOT_IN_WINDOW" | ""
    Checks if any schedule matches today and current time is within entry window.
    Entry window: 30 min before start up to end time.
    """
    now = datetime.datetime.now()
    today = _DAY_MAP[now.weekday()]
    now_mins = now.hour * 60 + now.minute

    has_today = False
    for s in schedules:
        if s.get("day", "").strip().lower() != today.lower():
            continue
        has_today = True
        start_raw = s.get("start_time", "")
        end_raw   = s.get("end_time", "")
        try:
            start_dt     = _parse_time(start_raw)
            end_dt       = _parse_time(end_raw)
            start_mins   = start_dt.hour * 60 + start_dt.minute
            end_mins     = end_dt.hour  * 60 + end_dt.minute
            window_start = start_mins - 30  # allow 30 min early entry
            if window_start <= now_mins <= end_mins:
                return True, start_raw, s, ""
        except ValueError:
            pass

    if not has_today:
        return False, "", {}, "NO_SCHEDULE_TODAY"
    return False, "", {}, "NOT_IN_WINDOW"


def is_late(start_time_str: str) -> bool:
    """Returns True if current time is past the schedule start time."""
    try:
        now = datetime.datetime.now()
        now_mins = now.hour * 60 + now.minute
        start_dt = _parse_time(start_time_str)
        start_mins = start_dt.hour * 60 + start_dt.minute
        return now_mins > start_mins
    except Exception:
        return False


# ── Photo Utilities ───────────────────────────────────────────────────────────
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def save_photo(src_path: str, id_number: str) -> str:
    """Copy uploaded photo into uploads/ and return stored path."""
    import shutil
    ext = os.path.splitext(src_path)[1] or ".jpg"
    dst = os.path.join(UPLOADS_DIR, f"{id_number}{ext}")
    shutil.copy2(src_path, dst)
    return dst