import argparse

import cms
import erp
from events import make_course_events
from gcal import GCal, tools
from timetable import get_course
from utils import config, get_cal_name


def override_sections(sections):
    overrides = config['COURSES'].get('overrides')
    if not overrides:
        return sections
    for course_code, course_sections in overrides.items():
        course = sections.get(course_code)
        if not course:
            print("Unknown course in overrides:", course_code)
            continue
        for orig_sec, new_sec in course_sections.items():
            try:
                course.remove(orig_sec)
            except KeyError:
                print(f"Unknown old section in overrides of {course_code}: {orig_sec}")
            else:
                course.add(new_sec)
    return sections


def enrol_cms(course_code, sections):
    enrolled = cms.get_enrolled_courses()
    for sec_code in sections:
        if any(course_code in c['fullname'] and sec_code in c['fullname']
               for c in enrolled):
            print("Already enrolled to", course_code, sec_code)
            continue
        print("Enrolling to", course_code, sec_code)
        section = cms.search_course(f"{course_code} {sec_code}")
        if not section:
            print("Not found.")
            continue
        resp = cms.enrol(section['id'])
        if resp.get('status') not in (True, 'true'):
            print("error while enrolling")
            print(resp)


def set_cal(gcal: GCal):
    cal_name = get_cal_name()
    print("Creating calendar for", cal_name)
    if gcal.set_cal(cal_name):
        print("Calendar", cal_name, "already exists. Clearing old events.")
        gcal.clear_cal()


def main():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument(
        '-n', '--new-creds',
        action='store_true', default=False,
        help="Clear previously saved Google credentials")
    cms_group = parser.add_mutually_exclusive_group()
    cms_group.add_argument(
        '-s', '--skip-cms',
        action='store_true', default=False,
        help="Skip enrolling to CMS courses")
    cms_group.add_argument(
        '-o', '--only-cms',
        action='store_true', default=False,
        help="Only enrol to CMS courses")
    args = parser.parse_args()

    if not args.only_cms:
        gcal = GCal(args.new_creds)
        set_cal(gcal)

    reg_sections = erp.get_reg_sections()
    print("Fetched registered courses from ERP.")
    final_secions = override_sections(reg_sections)

    for course_code, sections in final_secions.items():
        course = get_course(course_code, sections)
        if not args.skip_cms:
            enrol_cms(course_code, sections)
        if not args.only_cms:
            for event in make_course_events(course):
                gcal.create_event(event)
                gcal.print_event(event, "Created", "in GCal.")


if __name__ == '__main__':
    main()
