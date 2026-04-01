from datetime import datetime, timedelta, date


def format_date(d: date) -> str:
    """Convert a datetime.date to a readable string for display.
    Example: date(2026, 3, 31) -> 'March 31, 2026'
    """
    return d.strftime("%B %d, %Y")


def add_minutes(time_str: str, minutes: int) -> str:
    """Add minutes to a time string and return a new time string.
    Example: add_minutes("9:00 AM", 20) -> "09:20 AM"
    """
    t = datetime.strptime(time_str, "%I:%M %p")
    t += timedelta(minutes=minutes)
    return t.strftime("%-I:%M %p")