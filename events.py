from utils import config


RFC_WDAY = ('MO', 'TU', 'WE', 'TH', 'FR', 'SA')
LAST_DATE = config['DATES']['last_date'].strftime('%Y%m%d')
COLORS = {'event': {'L': '9', 'P': '6', 'T': '10'}, 'compre': '11'}


def make_section_events(course_name, section):
    for event in section['sched']:
        rrule = {
            'FREQ': 'WEEKLY',
            'BYDAY': ','.join(RFC_WDAY[day - 1] for day in event['wdays']),
            'UNTIL': LAST_DATE
        }
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


def make_compre_event(course_name, compre):
    return {
        'summary': course_name + " Compre",
        'start': {
            'dateTime': compre['start'].isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'end': {
            'dateTime': compre['end'].isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'colorId': COLORS['compre']
    }


def make_course_events(course):
    for section in course['sections']:
        yield from make_section_events(course['name'], section)
    if course.get('compre'):
        yield make_compre_event(course['name'], course['compre'])
