from datetime import timedelta
from timetable import combine
from utils import config


RFC_WDAY = ('MO', 'TU', 'WE', 'TH', 'FR', 'SA')
LAST_DATE = config['DATES']['last_date'].strftime('%Y%m%d')
COLORS = {'event': {'L': '9', 'P': '6', 'T': '10'},
          'midsem': '4', 'compre': '7'}
MIDSEM_DATES = config['DATES']['midsem']


def make_section_events(course_name, section):
    for event in section['sched']:
        rrule = {
            'FREQ': 'WEEKLY',
            'BYDAY': ','.join(RFC_WDAY[day - 1] for day in event['wdays']),
            'UNTIL': LAST_DATE
        }
        exdates = []
        midsem_date = MIDSEM_DATES['start']
        while midsem_date <= MIDSEM_DATES['end']:
            if midsem_date.isoweekday() in event['wdays']:
                exclude_dt = combine(midsem_date, event['start'].time())
                exdates.append(exclude_dt.strftime('%Y%m%dT%H%M%S'))
            midsem_date = midsem_date + timedelta(days=1)
        yield {
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
                'EXDATE;TZID=Asia/Kolkata:' + ','.join(exdates),
                'RRULE:' + ";".join(f"{k}={v}" for k, v in rrule.items())
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
