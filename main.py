import argparse
from functools import reduce
from operator import ior

import cms
import erp
from dates import cur_sem, today
from events import make_course_events, EventType
from gcal import GCal, tools
from timetable import get_course
from utils import config


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


def set_cal(gcal: GCal, cal_name, clear_old=True):
    print("Creating calendar for", cal_name)
    if gcal.set_cal(cal_name) and clear_old:
        print("Calendar", cal_name, "already exists. Clearing old events.")
        gcal.clear_cal()


def get_cal_name():
    acad_year = today.year - cur_sem + 1
    return f"Timetable Sem {cur_sem}, {acad_year}-{acad_year + 1 - 2000}"


def main():
    parser = argparse.ArgumentParser(
        parents=[tools.argparser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-n', '--new-creds',
        action='store_true', default=False,
        help="Clear previously saved Google credentials")
    parser.add_argument(
        '-t', '--title',
        default=get_cal_name(),
        help="Name of the calendar")
    parser.add_argument(
        '--no-clear-old',
        action='store_true', default=False,
        help="Don't delete the calendar if it exists")
    parser.add_argument(
        '--events',
        nargs='+', default='all',
        choices=list(EventType.__members__.keys()))
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
    args.events = reduce(ior, (getattr(EventType, event) for event in args.events))

    if not args.only_cms:
        gcal = GCal(args.new_creds)
        set_cal(gcal, args.title)

    reg_sections = erp.get_reg_sections()
    print("Fetched registered courses from ERP.")
    final_secions = override_sections(reg_sections)

    for course_code, sections in final_secions.items():
        course = get_course(course_code, sections)
        if not args.skip_cms:
            enrol_cms(course_code, sections)
        if not args.only_cms:
            for event in make_course_events(course, args.events):
                gcal.create_event(event)
                gcal.print_event(event, "Created", "in GCal.")


if __name__ == '__main__':
    main()
