import cms
import erp
import gcal
import utils

courses_data = utils.read_json('TT/TIMETABLE 2ND SEM 2018-19.json')


def enrol_all(courses):
    cms.login_google(**utils.get_config()['CMS_CREDS'])
    for course_code, sections in courses.items():
        for sec_code in sections.values():
            print(course_code, sec_code)
            general_sec_id = cms.course_search(f"{course_code} {sec_code[0]}")
            cms.course_enrol(general_sec_id)
            section_id = cms.course_search(f"{course_code} {sec_code}")
            cms.course_enrol(section_id)


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


def specific_courses(courses={}):
    for course_code, sections in reg_sections.items():
        sections.update(courses.get(course_code, {}))
        yield course_code, sections

def is_event(event, service, summary):
    if summary in event['summary']:
        print(event)

def main():
    service = gcal.create_cal_serv()
    courses = {'CS F222': {'T': 'T3'}}
    for course_code, sections in specific_courses(courses):
        course = get_course(course_code, sections)
        for section_event in make_section_events(course):
            gcal.create_event(section_event, service)
        compre_event = make_compre_event(course)
        if compre_event:
            gcal.create_event(compre_event, service)


if __name__ == '__main__':
    # gcal.all_events(gcal.delete_event)
    # print(dict(specific_courses({'CS F111': {'T': 'T2', 'L': 'L1'}})))
    # enrol_all(erp.get_reg_sections())
    gcal.all_events(is_event, {'summary': 'Discrete'})
    # gcal.all_events(lambda a, b: print(a))
    # main()
