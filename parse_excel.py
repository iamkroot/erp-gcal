import json
from pathlib import Path
from openpyxl import load_workbook
from utils import to_title


ROWS = {  # 0 indexed column indices
    'c_num': 1,
    'c_title': 2,
    'sec_num': 6,
    'instr_name': 7,
    'room': 8,
    'days': 9,
    'hours': 10,
    'compre': 12
}


def parse(wb):
    course_db = []
    for sheet in wb:
        rows = sheet.rows
        next(rows)  # skip header row
        for row in rows:
            if not row:
                continue
            data = {name: row[num].value for name, num in ROWS.items()}
            if not data['instr_name']:
                continue  # blank row
            # new Course
            if data['c_num']:
                course = {
                    'code': data['c_num'],
                    'name': to_title(data['c_title']),
                    'sections': [],
                }
                if data['compre']:
                    date, sess = data['compre'].split()
                    course['compre'] = {'date': date, 'session': sess}
                course_db.append(course)  # add to course
                sec_type = 'L'
                sec_num_counter = 1

            # new Tutorial or Practical section
            if not data['c_num'] and data['c_title']:
                sec_type = data['c_title'][0]
                sec_num_counter = 1

            # new Section
            if (data['instr_name'] and data['room'] and not sec_type == 'L' or
                    data['sec_num']) or data['c_title']:
                sec_num = int(data['sec_num'] or sec_num_counter)
                section = {
                    'type': sec_type,
                    'num': sec_num,
                    'instructors': [],
                    'sched': []
                }
                course['sections'].append(section)
                sec_num_counter += 1
                instructors = set()  # keep track of unique instructors

            if isinstance(data.get('hours'), (float, int)):
                data['hours'] = str(int(data['hours']))
            if data.get('days'):
                hours = tuple(map(int, data['hours'].split()))
                days = data['days'].split()
                sched = {'room': data['room'], 'days': days}
                if len(hours) == hours[-1] - hours[0] + 1:  # continuous hours
                    section['sched'].append(dict(**sched, hours=hours))
                else:
                    for hour in hours:  # separate sched for each hour
                        section['sched'].append(dict(**sched, hours=(hour,)))
            if data['instr_name'].lower() not in instructors:
                section['instructors'].append(data['instr_name'])
                instructors.add(data['instr_name'].lower())
    return course_db


def main():
    file = Path('TT/TIMETABLE 1ST SEM 2019-20.xlsx')
    wb = load_workbook(filename=file, read_only=True)

    course_db = parse(wb)
    with open(file.with_suffix('.json'), 'w') as f:
        f.write(json.dumps(course_db, indent=4))


if __name__ == '__main__':
    main()
