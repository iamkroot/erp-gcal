from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache, partial
from itertools import chain

from utils import combine_dt, config, cur_sem

DATE_FMT = '%Y%m%dT%H%M%S'
RFC_WDAY = ('MO', 'TU', 'WE', 'TH', 'FR', 'SA')
COLORS = {'event': {'L': '9', 'P': '6', 'T': '10'},
          'midsem': '4', 'compre': '7'}

MIDSEM_DATES = config['DATES'].get("midsem")
if MIDSEM_DATES:
    assert isinstance(MIDSEM_DATES["start"], date)
    assert MIDSEM_DATES["start"] >= date.today(), "Midsem start date is in the past"

HOLIDAYS = set(config['DATES'].get('holidays', []))

INCLUDE_DATES = defaultdict(list)
for change_date, day in config['DATES'].get('day_change', {}).items():
    assert day in RFC_WDAY, f"Invalid day '{day}' in 'day_change' config"
    change_date = date.fromisoformat(change_date)
    INCLUDE_DATES[day].append(change_date)
CHANGE_DATES = tuple(chain.from_iterable(INCLUDE_DATES.values()))


@lru_cache()
def get_last_date():
    default_last_date = date(date.today().year, 11 if cur_sem() == 1 else 4, 29)
    last_date = config['DATES'].get('last_date', default_last_date) + timedelta(days=1)
    if last_date < date.today():
        last_date = default_last_date
    return last_date.strftime('%Y%m%d')


def join_event_dt(event, date):
    return combine_dt(date, event['start'].time()).strftime(DATE_FMT)


def get_indates(event):
    indates = set()
    for wday in event['wdays']:
        dates = INCLUDE_DATES.get(RFC_WDAY[wday - 1], [])
        indates.update(dates)
    return indates


def get_exdates(event, indates):
    exdates = HOLIDAYS.copy()
    if MIDSEM_DATES:
        midsem_date = MIDSEM_DATES['start']
        while midsem_date <= MIDSEM_DATES['end']:
            if midsem_date.isoweekday() in event['wdays']:
                exdates.add(midsem_date)
            midsem_date = midsem_date + timedelta(days=1)
    for change_date in CHANGE_DATES:
        if change_date.isoweekday() in event['wdays'] and change_date not in indates:
            exdates.add(change_date)
    return exdates


def make_section_events(course_name, section):
    for event in section['sched']:
        rrule = {
            'FREQ': 'WEEKLY',
            'BYDAY': ','.join(RFC_WDAY[day - 1] for day in event['wdays']),
            'UNTIL': get_last_date()
        }
        get_dt = partial(join_event_dt, event)
        indates = get_indates(event)
        exdates = get_exdates(event, indates)

        gcal_event = {
            'summary': f"{course_name} {section['num']}",
            'description': section['instructors'],
            'location': event['room'],
            'start': {
                'dateTime': event['start'].isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': event['end'].isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'recurrence': [
                'RRULE:' + ";".join(f"{k}={v}" for k, v in rrule.items()),
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {
                        'method': 'popup',
                        'minutes': 10
                    }
                ]
            },
            'colorId': COLORS['event'][section['num'][0]]
        }
        if indates:
            gcal_event['recurrence'].append(
                'RDATE;TZID=Asia/Kolkata:' + ','.join(map(get_dt, indates)))
        if exdates:
            gcal_event['recurrence'].append(
                'EXDATE;TZID=Asia/Kolkata:' + ','.join(map(get_dt, exdates)))
        yield gcal_event


def make_event(title, start, end, color):
    return {
        'summary': title,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'colorId': color
    }


def make_midsem_event(course_name, midsem):
    return make_event(course_name + ' Midsem', midsem['start'],
                      midsem['end'], COLORS['midsem'])


def make_compre_event(course_name, compre):
    return make_event(course_name + ' Compre', compre['start'],
                      compre['end'], COLORS['compre'])


def make_course_events(course):
    name = course['name']
    for section in course['sections']:
        yield from make_section_events(name, section)
    midsem = course.get('midsem')
    if midsem:
        yield make_midsem_event(name, midsem)
    compre = course.get('compre')
    if compre:
        yield make_compre_event(name, compre)
