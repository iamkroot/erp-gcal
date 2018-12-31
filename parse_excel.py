from openpyxl import load_workbook
import json
import re
from pathlib import Path


def title_except(s, exceptions=['I', 'II', 'III', 'IV']):
    """Convert string to Title Case"""
    word_list = re.split(' ', s)
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)


TOP_LEFT_CELL = 'A2'
LAST_COL = 'M'
ROWS = {  # 0 indexed column indices
    'C_NUM': 1,
    'C_TITLE': 2,
    'SEC_NUM': 6,
    'INSTR_NAME': 7,
    'ROOM': 8,
    'DAYS': 9,
    'HOURS': 10,
    'COMPRE': 12
}


def parse(sheet):
    req_area = sheet[TOP_LEFT_CELL: LAST_COL + str(sheet.max_row)]
    course_db = {}

    for row in req_area:
        if not row[ROWS['INSTR_NAME']].value:
            continue  # blank row

        # new Course
        if row[ROWS['C_NUM']].value:
            compre = row[ROWS['COMPRE']].value
            course = {
                'name': title_except(row[ROWS['C_TITLE']].value),
                'sections': {},
                'compre': {
                    'date': compre.split()[0] if compre else None,
                    'session': compre.split()[1] if compre else None
                }
            }
            course_db[row[ROWS['C_NUM']].value] = course  # add to course
            sec_type = 'L'
            sec_num_counter = 1

        # new Tutorial or Practical section
        if not row[ROWS['C_NUM']].value and row[ROWS['C_TITLE']].value:
            sec_type = row[ROWS['C_TITLE']].value[0]
            sec_num_counter = 1

        # new Section
        if (row[ROWS['INSTR_NAME']].value and row[ROWS['ROOM']].value) or \
                row[ROWS['C_TITLE']].value:
            sec_num = row[ROWS['SEC_NUM']].value or sec_num_counter
            section = {
                'instructors': []
            }
            course['sections'][sec_type + str(sec_num)] = section
            sec_num_counter += 1

        for ind, key in enumerate(['room', 'days', 'hours'], ROWS['ROOM']):
            if key not in section:
                section[key] = str(row[ind].value) if row[ind].value else None

        section['instructors'].append(row[ROWS['INSTR_NAME']].value)
    return course_db


def main():
    file = Path('TT/TIMETABLE 2ND SEM 2018-19.xlsx')
    sheet = load_workbook(filename=file).active
    course_db = parse(sheet)

    with open(file.with_suffix('.json'), 'w') as f:
        f.write(json.dumps(course_db, indent=4))


if __name__ == '__main__':
    main()
