import bisect
import re
from datetime import date, time, timedelta as td
from functools import partial

from parse_excel import course_db
from utils import combine_dt
from dates import first_workday

ISO_WDAY = {d: i for i, d in enumerate(('M', 'T', 'W', 'Th', 'F', 'S'), 1)}
MIDSEM_PAT = re.compile(r'(\d{1,2})\.(\d{1,2})\s*-+\s*(\d{1,2})\.(\d{1,2})\s*(\w{2})')


def calc_start_date(wdays):
    start_day = first_workday.isoweekday()
    if start_day in wdays:
        return first_workday
    lower = bisect.bisect(wdays, start_day)
    return first_workday + td(
        days=wdays[lower % len(wdays)] - start_day,
        weeks=(lower == len(wdays))
    )


def parse_sched(sched):
    weekdays = tuple(ISO_WDAY[day] for day in sched['days'])
    start_time = time(hour=sched['hours'][0] + 7)
    end_time = time(hour=sched['hours'][-1] + 7, minute=50)
    start_date = calc_start_date(weekdays)
    return {
        'room': sched['room'],
        'start': combine_dt(start_date, start_time),
        'end': combine_dt(start_date, end_time),
        'wdays': weekdays
    }


def parse_section(section):
    return {
        'num': section['num'],
        'instructors': ', '.join(section['instructors']),
        'sched': tuple(map(parse_sched, section['sched']))
    }


def parse_date(raw_date):
    dd, mm = map(int, raw_date.split('/'))
    today = date.today()
    parsed_date = today.replace(day=dd, month=mm)
    if today > parsed_date:
        parsed_date = parsed_date.replace(year=today.year + 1)
    return parsed_date


def parse_midsem(midsem):
    if not midsem:
        return
    midsem_date = parse_date(midsem['date'])
    match = MIDSEM_PAT.match(midsem['time'])
    is_pm = match.group(5) == 'PM' and match.group(1) != '11'
    times = tuple(map(int, match.groups()[:-1]))
    start = time(hour=times[0] + 12 * is_pm, minute=times[1])
    end = time(hour=times[2] + 12 * is_pm, minute=times[3])
    return {
        'start': combine_dt(midsem_date, start),
        'end': combine_dt(midsem_date, end)
    }


def parse_compre(compre):
    if not compre:
        return
    compre_date = parse_date(compre['date'])

    def comb(hour):
        return combine_dt(compre_date, time(hour=hour))

    start = 9 if compre['session'] == 'FN' else 14
    return {'start': comb(start), 'end': comb(start + 3)}


def get_section(sections, sec_num):
    section = sections.get(sec_num)
    if not section:
        if all(sec_code[0] == 'L' for sec_code in sections.keys()):
            section = sections.get('L' + sec_num[1:])
        if not section:
            print(f'No section {sec_num} found.')
            return
    section['num'] = sec_num
    return parse_section(section)


def get_course(course_code, sel_sections):
    course = course_db[course_code]
    if not course:
        return
    get_sec_data = partial(get_section, course['sections'])
    return {
        'code': course_code,
        'name': course['name'],
        'sections': tuple(filter(None, map(get_sec_data, sel_sections))),
        'midsem': parse_midsem(course.get('midsem')),
        'compre': parse_compre(course.get('compre'))
    }


def validate_db():
    for course, data in course_db.timetable.items():
        try:
            get_course(course, data["sections"])
        except Exception as e:
            print(f"Invalid data in '{course}'")
            print(data)
            raise e
    print("The parsed data is (probably) valid!")


if __name__ == '__main__':
    validate_db()
