import re

from collections import defaultdict
from datetime import date, datetime, timedelta as td
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from typing import Iterable
from utils import config, take

REGEX = re.compile(r"""
    (?P<month>[A-Za-z]{3,20})?\s*
    (?P<date>\d{1,2})\s*
    [,]*\s*  # for comma before year
    (?P<year>\d{4})?\s*  # not used anywhere
    \((?P<wday>[A-Za-z]{1,2})\)""", flags=re.VERBOSE)
WEEKDAYS = {d: i for i, d in enumerate(('M', 'T', 'W', 'Th', 'F', 'S', 'Su'))}
RFC_WEEKDAYS = {
    "Monday": 'MO',
    "Tuesday": 'TU',
    "Wednesday": 'WE',
    "Thursday": 'TH',
    "Friday": 'FR',
    "Saturday": 'SA',
    "Sunday": 'SU'
}
today = date.today().replace(year=2019)


class InvalidDateError(ValueError):
    pass


def match_wday(dd: date, wday: int) -> date:
    """Try changing year/month from dd to make it match Weekday"""
    if dd.weekday() == wday:  # weekday is correct
        return dd
    dd = dd.replace(year=today.year - 1)
    if dd.weekday() == wday:
        return dd
    dd = dd.replace(year=today.year + 1)
    if dd.weekday() == wday:
        return dd

    # still not matched, try changing months
    if today.month != 1:
        dd = dd.replace(month=today.month - 1)
    else:  # wrap around to December
        dd = dd.replace(year=today.year - 1, month=12)

    if dd.weekday() == wday:
        return dd

    if today.month != 12:
        dd = dd.replace(month=today.month + 1)
    else:  # wrap around to January
        dd = dd.replace(year=today.year + 1, month=1)

    if dd.weekday() == wday:
        return dd

    raise InvalidDateError("Unable to match with weekday")


def parse_date_str(date_str: str) -> tuple[date]:
    """Parse the dates from events table.
    Eg:
    Simple date: 'January 12 (T)'
    Date range: 'March 1 (M) ‐ 6 (S)'

    # F*ck the TD. They've used 'S' for both saturday and sunday -_-
    Wrong input for year 2021: 'April 25 (S)'
    """

    # if the date range goes over this limit, we made an error in match_wday
    MAX_DELTA = td(weeks=12)

    dates = []
    for match in REGEX.finditer(date_str):
        data = match.groupdict()
        wday = WEEKDAYS[match['wday']]
        if not data.get('month'):
            if dates:
                data['month'] = dates[-1].strftime("%B")
            else:
                raise InvalidDateError(date_str)
        dd = (datetime
              .strptime("{month} {date}".format(**data), "%B %d")
              .replace(year=today.year)
              .date())
        try:
            dd = match_wday(dd, wday)
        except InvalidDateError:
            if match['wday'] == 'S':
                try:
                    # try matching with Sunday
                    dd = match_wday(dd, wday + 1)
                except InvalidDateError:
                    raise InvalidDateError(date_str)
            else:
                raise InvalidDateError(date_str)
        # Ensure that the dates are not too far apart
        if dates and not (-MAX_DELTA < dates[-1] - dd < MAX_DELTA):
            # Maybe we made a mistake in match_wday
            raise InvalidDateError(date_str)
        dates.append(dd)
    if not dates:
        raise InvalidDateError(date_str)
    return tuple(dates)


def parse_file(events_rows) -> dict:
    """Parses the events table and returns a mapping from date to events on that date

    events_rows should contain the tab separated export of the events table.

    date1 \t event_name1 \t date2 \t event_name2
    date3 \t event_name3 \t date4 \t event_name4
    date5 \t event_name5 \t date6 \t event_name6
    ...
    """
    events = defaultdict(list)
    for row in events_rows:
        cells = iter(row.split("\t"))
        # consider pairs of cells at a time: (date, name)
        while chunk := tuple(map(str.strip, take(2, cells))):
            try:
                date_str, name = chunk
            except ValueError:
                print(f"Invalid row {chunk=}")
                break
            if not date_str:
                continue
            events[parse_date_str(date_str)].append(name)
    return events


def get_holidays(events: dict) -> Iterable[date]:
    for dates, names in events.items():
        if any(name.endswith("(H)") for name in names):
            yield from dates


def get_day_changes(events: dict) -> dict[date, str]:
    """Get map of timetable day overrides (X-day's timetable to be followed)"""
    changes = {}
    matcher = SequenceMatcher(lambda x: x == ' ', "", "timetable to be followed")
    for dates, names in events.items():
        for name in names:
            matcher.set_seq1(name)
            if matcher.ratio() > 0.8:
                for block in matcher.matching_blocks:
                    if block.size < 5:
                        continue
                    day = get_close_matches(name[:block.a], RFC_WEEKDAYS, n=1)
                    for date_ in dates:
                        changes[date_] = RFC_WEEKDAYS[day[0]]
                    break
    return changes


if __name__ == '__main__':
    dates_file = Path(config["DATES"]["dates_file"])
    with open(dates_file) as f:
        events = parse_file(f)
    print(events)
    print(*get_holidays(events))
    a = get_day_changes(events)
