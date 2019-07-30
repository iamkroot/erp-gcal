import cms
import erp
from datetime import date
from gcal import GCal
from events import make_course_events
from timetable import get_course
from utils import config


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


def enrol_cms(course_code, sections):
    for sec_code in sections:
        print("Enrolling to", course_code, sec_code)
        section = cms.search_course(f"{course_code} {sec_code}")
        resp = cms.enrol(section['id'])
        if resp.get('status') != 'true':
            print("error while enrolling")
            print(resp)


def get_cal_name():
    today = date.today()
    sem = 2 if 1 <= today.month <= 5 else 1
    year = today.year - sem + 1
    return f"Timetable Sem {sem}, {year}-{year + 1 - 2000}"


def main():
    events = []
    for course_code, sections in get_sections().items():
        course = get_course(course_code, sections)
        events.extend(make_course_events(course))
        enrol_cms(course_code, sections)
    gcal = GCal()
    gcal.set_cal(get_cal_name())
    for event in events:
        gcal.create_event(event)
        print("Created", event['summary'])


if __name__ == '__main__':
    main()
