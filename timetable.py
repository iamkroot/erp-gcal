import bisect
from datetime import datetime as dt, timedelta as td, time, date, tzinfo
from functools import partial
from parse_excel import get_course_db

courses_data = get_course_db()
ISO_WDAY = {d: i for i, d in enumerate(('M', 'T', 'W', 'Th', 'F', 'S'), 1)}


class IST(tzinfo):
    def utcoffset(self, dt):
        return td(hours=5, minutes=30)

    def dst(self, dt):
        return td(0)


def combine(e_date, e_time):
    return dt.combine(e_date, e_time, IST())


def calc_start_date(wdays, skip_today=False):
    today = dt.today()
    if not skip_today and today.isoweekday() in wdays:
        return today
    lower = bisect.bisect(wdays, today.isoweekday())
    return today + td(
        days=wdays[lower % len(wdays)] - today.isoweekday(),
        weeks=(lower == len(wdays))
    )


def parse_sched(sched):
    weekdays = tuple(ISO_WDAY[day] for day in sched['days'])
    start_time = time(hour=sched['hours'][0] + 7)
    end_time = time(hour=sched['hours'][-1] + 7, minute=50)
    start_date = calc_start_date(weekdays, end_time < dt.now().time())
    return {
        'room': sched['room'],
        'start': combine(start_date, start_time),
        'end': combine(start_date, end_time),
        'wdays': weekdays
    }


def parse_section(section):
    return {
        'num': section['num'],
        'instructors': ', '.join(section['instructors']),
        'sched': tuple(map(parse_sched, section['sched']))
    }


def parse_compre(compre):
    if not compre:
        return
    dd, mm = map(int, compre['date'].split('/'))
    today = date.today()
    compre_date = today.replace(day=dd, month=mm)
    if today > compre_date:
        compre_date = compre_date.replace(year=today.year + 1)

    def comb(hour):
        return combine(compre_date, time(hour=hour))

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
    course = courses_data.get(course_code)
    if not course:
        return
    get_sec_data = partial(get_section, course['sections'])
    return {
        'code': course_code,
        'name': course['name'],
        'sections': tuple(filter(None, map(get_sec_data, sel_sections))),
        'compre': parse_compre(course.get('compre'))
    }