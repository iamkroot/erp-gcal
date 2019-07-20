from openpyxl import load_workbook
import json
import re
from pathlib import Path


def title_except(s, exceptions=['I', 'II', 'III', 'IV']):
    """Convert string to Title Case"""
    word_list = re.split(' ', s)
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        if not word:
            continue
        if word.lower() in ('and', 'of', 'in', 'to', 'its'):
            word = word.lower()
        elif word not in exceptions:
            word = word.capitalize()
        final.append(word)
    return " ".join(final)


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
    course_db = {}
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
                compre = data['compre']
                compre = compre.split() if compre else (None, None)
                course = {
                    'name': title_except(data['c_title']),
                    'sections': {},
                    'compre': {
                        'date': compre[0],
                        'session': compre[1]
                    }
                }
                course_db[data['c_num']] = course  # add to course
                sec_type = 'L'
                sec_num_counter = 1

            # new Tutorial or Practical section
            if not data['c_num'] and data['c_title']:
                sec_type = data['c_title'][0]
                sec_num_counter = 1

            # new Section
            if (data['instr_name'] and data['room']) or \
                    data['c_title']:
                sec_num = int(data['sec_num'] or sec_num_counter)
                section = {'instructors': []}
                course['sections'][sec_type + str(sec_num)] = section
                sec_num_counter += 1

            for key in ('room', 'days', 'hours'):
                section.setdefault(key, data[key])
            if isinstance(section.get('hours'), float):
                section['hours'] = str(int(section['hours']))
            section['instructors'].append(data['instr_name'])
    return course_db


def main():
    file = Path('TT/TIMETABLE 1ST SEM 2019-20.xlsx')
    wb = load_workbook(filename=file, read_only=True)

    course_db = parse(wb)
    with open(file.with_suffix('.json'), 'w') as f:
        f.write(json.dumps(course_db, indent=4))


if __name__ == '__main__':
    main()
