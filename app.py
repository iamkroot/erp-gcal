import cms
import erp
import gcal
import utils


def enrol_all(courses):
    cms.login_google(**utils.get_config()['CMS_CREDS'])
    for course, sections in courses.items():
        for section in sections:
            course_id = cms.course_search(" ".join(course, section))
            cms.course_enrol(course_id)


def get_section(sec_num, sections):
    section = sections.get(sec_num)
    if not section:
        if all([sec_code[0] == 'L' for sec_code in sections.keys()]):
            section = sections.get('L' + sec_num[1:])
        elif not section:
            print(f'No section {sec_num} found.')
            return
    section['num'] = sec_num
    return gcal.parse_section(section)


def get_course(course_code, secs):
    courses_data = utils.read_json('timetable.json')
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
LAST_DATE = gcal.get_last_date().strftime('%Y%m%d')
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


def main():
    service = gcal.create_cal_serv()
    for course, sections in erp.get_reg_sections().items():
        course = get_course(course, sections)
        for section_event in make_section_events(course):
            gcal.create_event(section_event, service)
        compre_event = make_compre_event(course)
        if compre_event:
            gcal.create_event(compre_event, service)


if __name__ == '__main__':
    gcal.all_events(gcal.delete_event)
    main()
