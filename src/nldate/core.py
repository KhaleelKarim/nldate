import calendar
import re
from datetime import date, timedelta

MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
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

WORD_NUMBERS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

_UNIT = r"(year|month|week|day)s?"
_WEEKDAY = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"


def _parse_day(s: str) -> int:
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?", s.strip())
    if m:
        return int(m.group(1))
    if s in ORDINALS:
        return ORDINALS[s]
    raise ValueError(f"Cannot parse day: {s!r}")


def _parse_quantity(s: str) -> int:
    if re.fullmatch(r"\d+", s):
        return int(s)
    if s in WORD_NUMBERS:
        return WORD_NUMBERS[s]
    raise ValueError(f"Cannot parse quantity: {s!r}")


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
        m = re.fullmatch(r"(\w+)\s+" + _UNIT, part.strip())
        if not m:
            raise ValueError(f"Cannot parse delta component: {part!r}")
        result.append((_parse_quantity(m.group(1)), m.group(2)))
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

    # strip trailing periods from alphabetic abbreviations (Dec. → dec, Oct. → oct)
    t = re.sub(r"([a-z]+)\.", r"\1", s.strip().lower())

    # --- standalone relative anchors ---
    if t == "yesterday":
        return today - timedelta(days=1)
    if t == "tomorrow":
        return today + timedelta(days=1)
    if t == "today":
        return today

    # --- multi-step relative: must come before the generic before/after pattern ---
    m = re.fullmatch(r"the\s+day\s+(after|before)\s+(tomorrow|yesterday)", t)
    if m:
        direction, ref = m.group(1), m.group(2)
        anchor = today + timedelta(1) if ref == "tomorrow" else today - timedelta(1)
        return anchor + timedelta(1) if direction == "after" else anchor - timedelta(1)

    if re.fullmatch(r"the\s+week\s+before\s+last", t):
        return today - timedelta(weeks=2)

    # --- next / last <weekday> ---
    m = re.fullmatch(r"(next|last)\s+" + _WEEKDAY, t)
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

    # --- this <weekday> (same ISO week) ---
    m = re.fullmatch(r"this\s+" + _WEEKDAY, t)
    if m:
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week + timedelta(days=WEEKDAYS[m.group(1)])

    # --- next / last week / month / year ---
    m = re.fullmatch(r"(next|last)\s+(week|month|year)", t)
    if m:
        direction, unit = m.group(1), m.group(2)
        sign = 1 if direction == "next" else -1
        if unit == "week":
            return today + timedelta(weeks=sign)
        if unit == "month":
            return _add_months(today, sign)
        return _add_months(today, sign * 12)

    # --- delta before/after anchor (supports word numbers via _parse_delta_parts) ---
    m = re.fullmatch(r"(.+?)\s+(before|after)\s+(.+)", t)
    if m:
        delta_str, direction, anchor_str = m.group(1), m.group(2), m.group(3)
        anchor = _resolve_anchor(anchor_str.strip(), today)
        parts = _parse_delta_parts(delta_str)
        sign = 1 if direction == "after" else -1
        return _apply_delta(anchor, parts, sign)

    # --- N units ago ---
    m = re.fullmatch(r"([\w]+)\s+" + _UNIT + r"\s+ago", t)
    if m:
        return _apply_delta(today, [(_parse_quantity(m.group(1)), m.group(2))], -1)

    # --- N units from now / from <relative anchor> ---
    m = re.fullmatch(
        r"([\w]+)\s+" + _UNIT + r"\s+from\s+(now|today|yesterday|tomorrow)", t
    )
    if m:
        anchor = _resolve_anchor(m.group(3) if m.group(3) != "now" else "today", today)
        return _apply_delta(anchor, [(_parse_quantity(m.group(1)), m.group(2))], 1)

    # --- in N units ---
    m = re.fullmatch(r"in\s+([\w]+)\s+" + _UNIT, t)
    if m:
        return _apply_delta(today, [(_parse_quantity(m.group(1)), m.group(2))], 1)

    # --- "the [ordinal] of Month[,] Year" ---
    m = re.fullmatch(r"the\s+([\w-]+)\s+of\s+(\w+),?\s+(\d{4})", t)
    if m:
        month_name = m.group(2)
        if month_name not in MONTHS:
            raise ValueError(f"Unknown month: {month_name!r}")
        return date(int(m.group(3)), MONTHS[month_name], _parse_day(m.group(1)))

    # --- "Year[,] the [ordinal] of Month" ---
    m = re.fullmatch(r"(\d{4}),?\s+the\s+([\w-]+)\s+of\s+(\w+)", t)
    if m:
        month_name = m.group(3)
        if month_name not in MONTHS:
            raise ValueError(f"Unknown month: {month_name!r}")
        return date(int(m.group(1)), MONTHS[month_name], _parse_day(m.group(2)))

    # --- "the [ordinal] of Month" — no year, use today's year ---
    m = re.fullmatch(r"the\s+([\w-]+)\s+of\s+(\w+)", t)
    if m and m.group(2) in MONTHS:
        return date(today.year, MONTHS[m.group(2)], _parse_day(m.group(1)))

    # --- standalone "Month [ordinal], Year" and "Month [ordinal]" (no year) ---
    try:
        return _parse_explicit_date(t)
    except ValueError:
        pass

    # "Month [ordinal]" with no year — use today's year
    m = re.fullmatch(r"(\w+)\s+([\w-]+)", t)
    if m and m.group(1) in MONTHS:
        try:
            return date(today.year, MONTHS[m.group(1)], _parse_day(m.group(2)))
        except ValueError:
            pass

    # --- "Month Year" — no day, default to 1st ---
    m = re.fullmatch(r"(\w+)\s+(\d{4})", t)
    if m and m.group(1) in MONTHS:
        return date(int(m.group(2)), MONTHS[m.group(1)], 1)

    # --- YYYY[-/]MM[-/]DD  (ISO 8601 and slash variant) ---
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # --- MM[-/]DD[-/]YYYY  (US default); if first part > 12 treat as DD/MM/YYYY ---
    m = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", t)
    if m:
        a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(year, b, a) if a > 12 else date(year, a, b)

    # --- YYYY.MM.DD ---
    m = re.fullmatch(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # --- DD.MM.YYYY or MM.DD.YYYY (first > 12 → European DD.MM) ---
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", t)
    if m:
        a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(year, b, a) if a > 12 else date(year, a, b)

    raise ValueError(f"Cannot parse date string: {s!r}")
