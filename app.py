import cms
import erp
import gcal
from utils import config, read_json

courses_data = read_json('TT/TIMETABLE 2ND SEM 2018-19.json')


def whitelist_sections(orig_sections):
    whitelist = config['COURSES'].get('whitelist')
    if not whitelist:
        return orig_sections
    sections = {}
    for course_code, sec_types in whitelist.items():
        course = orig_sections.get(course_code)
        if not course:
            print("Unknown course in whitelist:", course_code)
            continue
        if sec_types == "all":
            sections[course_code] = course
        elif isinstance(sec_types, list):
            sections[course_code] = {
                sec_type: course[sec_type] for sec_type in sec_types}
        else:
            print("Invalid section for {course_code} in whitelist:", sec_types)
    return sections


def override_sections(sections):
    overrides = config['COURSES'].get('overrides')
    if not overrides:
        return sections
    for course_code, course_sections in overrides.items():
        course = sections.get(course_code)
        if not course:
            print("Unknown course in overrides:", course_code)
            continue
        for sec_code, sec in course_sections.items():
            if sec_code not in course:
                print(f"Unknown section in overrides of {course_code}:", sec)
                continue
            course[sec_code] = sec
    return sections


def get_sections():
    reg_sections = erp.get_reg_sections()
    return override_sections(whitelist_sections(reg_sections))


def enrol_all(courses):
    for course_code, sections in courses.items():
        for sec_code in sections.values():
            print(course_code, sec_code)
            general_section = cms.search_course(f"{course_code} {sec_code[0]}")
            if general_section:
                cms.enrol(general_section['id'])
            section = cms.search_course(f"{course_code} {sec_code}")
            print(cms.enrol(section['id']))


def get_section(sec_num, sections):
    section = sections.get(sec_num)
    if not section:
        if all([sec_code[0] == 'L' for sec_code in sections.keys()]):
            section = sections.get('L' + sec_num[1:])
        if not section:
            print(f'No section {sec_num} found.')
            return
    section['num'] = sec_num
    return gcal.parse_section(section)


def get_course(course_code, secs):
    course = courses_data.get(course_code)
    if not course:
        return
    sections = [get_section(num, course['sections']) for num in secs.values()]
    return {
        'code': course_code,
        'name': course['name'],
        'sections': sections,
        'compre': gcal.parse_compre(course['compre'])
    }


WEEK = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA']
LAST_DATE = config['DATES']['last_date'].strftime('%Y%m%d')
COLORS = {'event': {'L': '9', 'P': '6', 'T': '10'}, 'compre': '11'}


def make_section_events(course):
    for section in course['sections']:
        rrule = {
            'FREQ': 'WEEKLY',
            'BYDAY': ','.join([WEEK[day - 1] for day in section['wdays']]),
            'UNTIL': LAST_DATE
        }
        event = {
            'summary': f"{course['name']} {section['num']}",
            'description': section['instructors'],
            'location': section['room'],
            'start': {
                'dateTime': section['start'].isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': section['end'].isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'recurrence': [
                f'RRULE:{";".join([f"{k}={v}" for k, v in rrule.items()])}'
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
        yield event
    return


def make_compre_event(course):
    if not course['compre']:
        return
    return {
        'summary': f"{course['name']} Compre",
        'start': {
            'dateTime': course['compre']['start'].isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'end': {
            'dateTime': course['compre']['end'].isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'colorId': COLORS['compre']
    }


def is_event(event, service, summary):
    if summary in event['summary']:
        print(event)


def main():
    service = gcal.create_cal_serv()
    for course_code, sections in get_sections().items():
        course = get_course(course_code, sections)
        for section_event in make_section_events(course):
            gcal.create_event(section_event, service)
        compre_event = make_compre_event(course)
        if compre_event:
            gcal.create_event(compre_event, service)


if __name__ == '__main__':
    main()
