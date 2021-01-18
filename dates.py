import re

from collections import defaultdict
from datetime import date, datetime, timedelta as td
from difflib import SequenceMatcher, get_close_matches
from functools import lru_cache
from typing import Iterable
from utils import config, take, get_weekday

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
DAY_CHANGE_STR = "timetable to be followed"
WORK_START_STR = "Class work begins"
WORK_LAST_STR = "Last day for class work"
MIDSEM_STR = "Mid‐semester Test (Classwork Suspended)"
today = date.today()


class InvalidDateError(ValueError):
    pass


def _match_wday(dd: date, wday: int) -> date:
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


def _parse_date_str(date_str: str) -> tuple[date]:
    """Parse the dates from events table.
    Eg:
    Simple date: 'January 12 (T)'
    Date range: 'March 1 (M) ‐ 6 (S)'

    # F*ck the TD. They've used 'S' for both saturday and sunday -_-
    Wrong input for year 2021: 'April 25 (S)'
    """

    # if the date range goes over this limit, we made an error in _match_wday
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
            dd = _match_wday(dd, wday)
        except InvalidDateError:
            if match['wday'] == 'S':
                try:
                    # try matching with Sunday
                    dd = _match_wday(dd, wday + 1)
                except InvalidDateError:
                    raise InvalidDateError(date_str)
            else:
                raise InvalidDateError(date_str)
        # Ensure that the dates are not too far apart
        if dates and not (-MAX_DELTA < dates[-1] - dd < MAX_DELTA):
            # Maybe we made a mistake in _match_wday
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
            events[_parse_date_str(date_str)].append(name)
    return events


def parse_holidays(events: dict) -> Iterable[date]:
    for dates, names in events.items():
        if any(name.endswith("(H)") for name in names):
            yield from dates


def parse_day_changes(events: dict) -> dict[date, str]:
    """Get map of timetable day overrides (X-day's timetable to be followed)"""
    changes = {}
    matcher = SequenceMatcher(lambda x: x == ' ', "", DAY_CHANGE_STR)
    for dates, names in events.items():
        for name in names:
            matcher.set_seq1(name.lower())
            if matcher.ratio() > 0.8:
                for block in matcher.matching_blocks:
                    if block.size < 5:
                        continue
                    day = get_close_matches(name[:block.a], RFC_WEEKDAYS, n=1)
                    for date_ in dates:
                        changes[date_] = RFC_WEEKDAYS[day[0]]
                    break
    return changes


def find_event_date(events: dict, name: str, thresh=0.8) -> tuple[date]:
    """Search the event names for the matching name"""
    matcher = SequenceMatcher(lambda x: x == ' ' or x == '-', "", name.lower())
    for dates, names in events.items():
        for name in names:
            matcher.set_seq1(name.lower())
            if matcher.ratio() > thresh:
                return dates


@lru_cache
def calc_sem_start_date():
    """Get first monday of the sem"""

    if cur_sem == 1:
        start = today.replace(month=8, day=1)
        return get_weekday(0, start)  # First week of Aug
    else:
        start = today.replace(month=1, day=1)
        return get_weekday(0, start, future_date=True)  # Second week of Jan


@lru_cache
def calc_sem_last_date():
    return date(today.year, 11 if cur_sem == 1 else 4, 29)


def get_first_workday(events: dict = {}) -> date:
    """Get date when classwork begins"""
    if start_date := config['DATES'].get("classwork", {}).get("start"):
        assert isinstance(start_date, date)
    elif dates := find_event_date(events, WORK_START_STR):
        start_date = dates[0]
    else:
        start_date = calc_sem_start_date()
    assert start_date - today <= td(180), "Classwork start date is too old"
    return start_date


def get_last_workday(events: dict = {}) -> date:
    """Last working day of the sem"""
    if end_date := config['DATES'].get("classwork", {}).get("end"):
        assert isinstance(end_date, date)
    elif dates := find_event_date(events, WORK_LAST_STR):
        end_date = dates[0]
    else:
        end_date = calc_sem_last_date()
    assert end_date >= today, "Classwork end date is in the past"
    return end_date


def get_midsem_dates(events: dict = {}) -> dict[str, date]:
    if midsem := config['DATES'].get("midsem"):
        assert isinstance(midsem["start"], date)
    elif events:
        dates = find_event_date(events, MIDSEM_STR)
        midsem = {"start": dates[0], "end": dates[1]}
    else:
        return None
    assert midsem["start"] >= today, "Midsem start date is in the past"
    return midsem


def get_day_changes(events: dict = {}) -> dict[date, str]:
    day_change_ = config['DATES'].get('day_change') or parse_day_changes(events)
    day_changes = {}
    for change_date, day in day_change_.items():
        assert day in RFC_WEEKDAYS.values(), f"Invalid day={day} in 'day_change' config"
        if not isinstance(change_date, date):
            change_date = date.fromisoformat(change_date)
        day_changes[change_date] = day
    return day_changes


cur_sem = 1 + (1 <= today.month <= 5)
if events_file := config["DATES"].get("events_file"):
    with open(events_file) as f:
        events = parse_file(f)
else:
    events = {}

first_workday = get_first_workday(events)
last_workday = get_last_workday(events)
midsem_dates = get_midsem_dates(events)
holidays = set(config['DATES'].get('holidays') or parse_holidays(events))
day_changes = get_day_changes(events)
