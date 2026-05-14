from datetime import date, timedelta

from nldate.core import parse


# --- "N units before/after <explicit date>" ---


def test_5_days_before_december_1():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_3_weeks_after_july_4():
    assert parse("3 weeks after July 4th, 2024") == date(2024, 7, 25)


def test_10_days_after_new_years():
    assert parse("10 days after January 1st, 2025") == date(2025, 1, 11)


def test_1_day_before_march_15():
    assert parse("1 day before March 15th, 2026") == date(2026, 3, 14)


def test_2_months_before_october_31():
    assert parse("2 months before October 31st, 2025") == date(2025, 8, 31)


# same expressions with an explicit today — result must be unaffected since the
# reference date is absolute, not relative to today


def test_5_days_before_december_1_with_today():
    assert parse("5 days before December 1st, 2025", today=date(2024, 1, 1)) == date(
        2025, 11, 26
    )


def test_10_days_after_new_years_with_today():
    assert parse("10 days after January 1st, 2025", today=date(2023, 6, 15)) == date(
        2025, 1, 11
    )


def test_2_months_before_october_31_with_today():
    assert parse("2 months before October 31st, 2025", today=date(2026, 3, 1)) == date(
        2025, 8, 31
    )


# --- "next / last <weekday>" ---

# today=Wednesday May 13 2026 → next Monday is May 18, last Friday is May 8


def test_next_monday_with_today():
    assert parse("next Monday", today=date(2026, 5, 13)) == date(2026, 5, 18)


def test_last_friday_with_today():
    assert parse("last Friday", today=date(2026, 5, 13)) == date(2026, 5, 8)


# without today — expected value is computed relative to date.today() so the
# test stays correct regardless of when it runs


def test_next_thursday_no_today():
    today = date.today()
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    assert parse("next Thursday") == today + timedelta(days=days_ahead)


def test_last_tuesday_no_today():
    today = date.today()
    days_behind = (today.weekday() - 1) % 7
    if days_behind == 0:
        days_behind = 7
    assert parse("last Tuesday") == today - timedelta(days=days_behind)


# --- "N units and M units before/after <explicit date>" ---


def test_1_year_and_2_months_after_july_4():
    # July 4 2024 + 1 year + 2 months = September 4, 2025
    assert parse("1 year and 2 months after July 4th, 2024") == date(2025, 9, 4)


def test_3_months_and_5_days_before_march_1():
    # March 1 2026 - 3 months = December 1 2025, - 5 days = November 26, 2025
    assert parse("3 months and 5 days before March 1st, 2026") == date(2025, 11, 26)


def test_2_weeks_and_3_days_after_february_14():
    # February 14 2026 + 14 days + 3 days = March 3, 2026
    assert parse("2 weeks and 3 days after February 14th, 2026") == date(2026, 3, 3)


def test_1_year_and_3_months_before_december_25():
    # December 25 2025 - 1 year = December 25 2024, - 3 months = September 25, 2024
    assert parse("1 year and 3 months before December 25th, 2025") == date(2024, 9, 25)


# --- "N units before/after today/yesterday/tomorrow" ---

# today=Wednesday May 13 2026
# yesterday=May 12, tomorrow=May 14


def test_single_delta_after_yesterday_with_today():
    assert parse("6 days after yesterday", today=date(2026, 5, 13)) == date(2026, 5, 18)


def test_single_delta_before_tomorrow_with_today():
    assert parse("3 weeks before tomorrow", today=date(2026, 5, 13)) == date(
        2026, 4, 23
    )


def test_combined_delta_after_yesterday_with_today():
    # yesterday = May 12 2026, + 1 year + 2 months = July 12, 2027
    assert parse(
        "1 year and 2 months after yesterday", today=date(2026, 5, 13)
    ) == date(2027, 7, 12)


def test_combined_delta_before_tomorrow_with_today():
    # tomorrow = May 14 2026, - 3 days - 1 week (10 days) = May 4, 2026
    assert parse("3 days and 1 week before tomorrow", today=date(2026, 5, 13)) == date(
        2026, 5, 4
    )


def test_combined_delta_after_today_with_today():
    # May 13 2026 + 2 months + 10 days = July 23, 2026
    assert parse("2 months and 10 days after today", today=date(2026, 5, 13)) == date(
        2026, 7, 23
    )


# without today — anchor resolves against date.today() at runtime


def test_single_delta_after_today_no_today():
    assert parse("5 days after today") == date.today() + timedelta(days=5)


def test_single_delta_before_yesterday_no_today():
    assert parse("3 weeks before yesterday") == date.today() - timedelta(days=22)


# --- "yesterday" / "tomorrow" as the entire expression ---


def test_yesterday_with_today():
    assert parse("yesterday", today=date(2026, 5, 13)) == date(2026, 5, 12)


def test_tomorrow_with_today():
    assert parse("tomorrow", today=date(2026, 5, 13)) == date(2026, 5, 14)


def test_yesterday_no_today():
    assert parse("yesterday") == date.today() - timedelta(days=1)


def test_tomorrow_no_today():
    assert parse("tomorrow") == date.today() + timedelta(days=1)


# --- mixed capitalisation ---


def test_mixed_caps_days_before_explicit_date():
    assert parse("5 DAYS beFORE december 1ST, 2025") == date(2025, 11, 26)


def test_mixed_caps_next_weekday_with_today():
    assert parse("NEXT monday", today=date(2026, 5, 13)) == date(2026, 5, 18)


def test_mixed_caps_combined_delta_after_explicit_date():
    assert parse("1 Year AND 2 Months AFTER july 4th, 2024") == date(2025, 9, 4)


def test_mixed_caps_combined_delta_after_yesterday_with_today():
    assert parse(
        "1 YEAR and 2 months After Yesterday", today=date(2026, 5, 13)
    ) == date(2027, 7, 12)


# --- numerical date formats ---


def test_numeric_iso_dash():
    assert parse("2025-11-26") == date(2025, 11, 26)


def test_numeric_iso_dash_leading_zeros():
    assert parse("2025-01-05") == date(2025, 1, 5)


def test_numeric_iso_dash_no_leading_zeros():
    assert parse("2025-1-5") == date(2025, 1, 5)


def test_numeric_iso_slash():
    assert parse("2025/11/26") == date(2025, 11, 26)


def test_numeric_iso_slash_leading_zeros():
    assert parse("2025/01/05") == date(2025, 1, 5)


def test_numeric_us_slash():
    assert parse("11/26/2025") == date(2025, 11, 26)


def test_numeric_us_slash_leading_zeros():
    assert parse("01/05/2025") == date(2025, 1, 5)


def test_numeric_us_slash_no_leading_zeros():
    assert parse("1/5/2025") == date(2025, 1, 5)


def test_numeric_us_dash():
    assert parse("11-26-2025") == date(2025, 11, 26)


def test_numeric_us_dash_no_leading_zeros():
    assert parse("1-5-2025") == date(2025, 1, 5)


# --- named dates: standalone "Month ordinal, Year" ---


def test_standalone_month_numeric_ordinal_year():
    assert parse("December 1st, 2005") == date(2005, 12, 1)


def test_standalone_month_word_ordinal_year():
    assert parse("December first, 2005") == date(2005, 12, 1)


def test_standalone_month_word_ordinal_year_mid():
    assert parse("March fifteenth, 2024") == date(2024, 3, 15)


def test_standalone_month_word_ordinal_year_high():
    assert parse("January thirty-first, 2023") == date(2023, 1, 31)


# --- named dates: "the ordinal of Month, Year" ---


def test_the_numeric_ordinal_of_month_year():
    assert parse("the 1st of December, 2005") == date(2005, 12, 1)


def test_the_word_ordinal_of_month_year():
    assert parse("the first of December, 2005") == date(2005, 12, 1)


def test_the_word_ordinal_of_month_year_mid():
    assert parse("the fifteenth of March, 2024") == date(2024, 3, 15)


def test_the_numeric_ordinal_of_month_year_no_comma():
    assert parse("the 20th of November 2022") == date(2022, 11, 20)


# --- named dates: "Year, the ordinal of Month" ---


def test_year_the_word_ordinal_of_month():
    assert parse("2005, the first of December") == date(2005, 12, 1)


def test_year_the_numeric_ordinal_of_month():
    assert parse("2024, the 15th of March") == date(2024, 3, 15)


def test_year_the_word_ordinal_of_month_high():
    assert parse("2023, the thirty-first of January") == date(2023, 1, 31)


# --- abbreviated month names ---


def test_abbrev_month_no_ordinal():
    assert parse("Dec 1, 2025") == date(2025, 12, 1)


def test_abbrev_month_with_ordinal_suffix():
    assert parse("Dec 1st, 2025") == date(2025, 12, 1)


def test_abbrev_month_word_ordinal():
    assert parse("Dec first, 2025") == date(2025, 12, 1)


def test_abbrev_month_jan():
    assert parse("Jan 5, 2026") == date(2026, 1, 5)


def test_abbrev_month_feb():
    assert parse("Feb 28, 2024") == date(2024, 2, 28)


def test_abbrev_month_sep():
    assert parse("Sep 15, 2023") == date(2023, 9, 15)


def test_abbrev_month_sept():
    assert parse("Sept 15, 2023") == date(2023, 9, 15)


def test_abbrev_month_oct():
    assert parse("Oct 31, 2025") == date(2025, 10, 31)


def test_abbrev_the_ordinal_of_abbrev_month():
    assert parse("the 1st of Dec, 2025") == date(2025, 12, 1)


def test_abbrev_in_delta_expression():
    assert parse("5 days before Dec 1st, 2025") == date(2025, 11, 26)
