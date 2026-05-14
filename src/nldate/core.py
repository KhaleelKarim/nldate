import calendar
import re
from datetime import date, timedelta


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
    "twenty-first": 21,
    "twenty-second": 22,
    "twenty-third": 23,
    "twenty-fourth": 24,
    "twenty-fifth": 25,
    "twenty-sixth": 26,
    "twenty-seventh": 27,
    "twenty-eighth": 28,
    "twenty-ninth": 29,
    "thirtieth": 30,
    "thirty-first": 31,
}


def _parse_day(s: str) -> int:
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?", s.strip())
    if m:
        return int(m.group(1))
    if s in ORDINALS:
        return ORDINALS[s]
    raise ValueError(f"Cannot parse day: {s!r}")


def _add_months(d: date, n: int) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _apply_delta(anchor: date, parts: list[tuple[int, str]], sign: int) -> date:
    result = anchor
    for n, unit in parts:
        n *= sign
        if unit == "year":
            result = _add_months(result, n * 12)
        elif unit == "month":
            result = _add_months(result, n)
        elif unit == "week":
            result += timedelta(weeks=n)
        elif unit == "day":
            result += timedelta(days=n)
    return result


def _parse_delta_parts(s: str) -> list[tuple[int, str]]:
    parts = re.split(r"\s+and\s+", s.strip())
    result = []
    for part in parts:
        m = re.fullmatch(r"(\d+)\s+(year|month|week|day)s?", part.strip())
        if not m:
            raise ValueError(f"Cannot parse delta component: {part!r}")
        result.append((int(m.group(1)), m.group(2)))
    return result


def _parse_explicit_date(s: str) -> date:
    # "Month [ordinal], Year" — ordinal may be numeric (1st) or word (first, twenty-third)
    m = re.fullmatch(r"(\w+)\s+([\w-]+),?\s+(\d{4})", s.strip())
    if m:
        month_name = m.group(1)
        if month_name in MONTHS:
            return date(int(m.group(3)), MONTHS[month_name], _parse_day(m.group(2)))
    raise ValueError(f"Cannot parse explicit date: {s!r}")


def _resolve_anchor(s: str, today: date) -> date:
    if s == "today":
        return today
    if s == "yesterday":
        return today - timedelta(days=1)
    if s == "tomorrow":
        return today + timedelta(days=1)
    return _parse_explicit_date(s)


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural language date string and return the corresponding date.

    Args:
        s: A natural language string describing a date, such as "2 days from now",
           "yesterday", "next Monday", or "March 5th".
        today: The reference date to resolve relative expressions against.
               If None, defaults to the current date (date.today()).

    Returns:
        A date object representing the date described by the input string.

    Raises:
        ValueError: If the string cannot be interpreted as a date.
    """
    if today is None:
        today = date.today()

    t = s.strip().lower()

    if t == "yesterday":
        return today - timedelta(days=1)
    if t == "tomorrow":
        return today + timedelta(days=1)
    if t == "today":
        return today

    m = re.fullmatch(
        r"(next|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", t
    )
    if m:
        direction = m.group(1)
        target_wd = WEEKDAYS[m.group(2)]
        current_wd = today.weekday()
        if direction == "next":
            offset = (target_wd - current_wd) % 7 or 7
            return today + timedelta(days=offset)
        else:
            offset = (current_wd - target_wd) % 7 or 7
            return today - timedelta(days=offset)

    m = re.fullmatch(r"(.+?)\s+(before|after)\s+(.+)", t)
    if m:
        delta_str, direction, anchor_str = m.group(1), m.group(2), m.group(3)
        anchor = _resolve_anchor(anchor_str.strip(), today)
        parts = _parse_delta_parts(delta_str)
        sign = 1 if direction == "after" else -1
        return _apply_delta(anchor, parts, sign)

    # "the [ordinal] of Month[,] Year"
    m = re.fullmatch(r"the\s+([\w-]+)\s+of\s+(\w+),?\s+(\d{4})", t)
    if m:
        month_name = m.group(2)
        if month_name not in MONTHS:
            raise ValueError(f"Unknown month: {month_name!r}")
        return date(int(m.group(3)), MONTHS[month_name], _parse_day(m.group(1)))

    # "Year[,] the [ordinal] of Month"
    m = re.fullmatch(r"(\d{4}),?\s+the\s+([\w-]+)\s+of\s+(\w+)", t)
    if m:
        month_name = m.group(3)
        if month_name not in MONTHS:
            raise ValueError(f"Unknown month: {month_name!r}")
        return date(int(m.group(1)), MONTHS[month_name], _parse_day(m.group(2)))

    # standalone "Month [ordinal], Year"
    try:
        return _parse_explicit_date(t)
    except ValueError:
        pass

    # YYYY[-/]MM[-/]DD  (ISO 8601 and its slash variant)
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # MM[-/]DD[-/]YYYY  (US month-first with slashes or dashes)
    m = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", t)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    raise ValueError(f"Cannot parse date string: {s!r}")
