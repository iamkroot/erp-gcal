from openpyxl import load_workbook
import json
import re


def title_except(s, exceptions=['I', 'II', 'III', 'IV']):
    word_list = re.split(' ', s)
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)


file = 'tt.xlsx'

sheet = load_workbook(filename=file).active
req_area = sheet['A2':'H1055']
course_db = {}
for row in req_area:
    if not row[3].value:
        continue
    if row[0].value:
        course = {
            'name': title_except(row[1].value),
            'sections': {},
            'compre': {
                'date': row[7].value.split()[0] if row[7].value else None,
                'session': row[7].value.split()[1] if row[7].value else None
            }
        }
        course_db[row[0].value] = course
        sec_type = 'L'

    if not row[0].value and row[1].value:
        sec_type = row[1].value[0]

    if row[4].value or row[1].value:
        sec_num = row[2].value or 1
        section = {
            'instructors': []
        }
        course['sections'][sec_type + str(sec_num)] = section

    section['instructors'].append(row[3].value)

    for ind, key in enumerate(['room', 'days', 'hours'], 4):
        if key not in section:
            section[key] = str(row[ind].value) if row[ind].value else None

with open('timetable.json', 'w') as f:
    f.write(json.dumps(course_db, indent=4))
