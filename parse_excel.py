from pathlib import Path

from openpyxl import load_workbook
from utils import config, read_json, to_title, write_json


def iter_rows(wb, column_map):
    """Generator for all the rows in the workbook"""
    for sheet in wb:
        rows = sheet.rows
        next(rows)
        for row in rows:
            if not row:
                continue
            yield {name: row[col].value for name, col in column_map.items()}


def parse_main_tt(file_path: Path):
    COLUMNS = {  # 0 indexed column indices
        "c_num": 1,
        "c_title": 2,
        "sec_num": 6,
        "instr_name": 7,
        "room": 8,
        "days": 9,
        "hours": 10,
        "compre": 12,
    }
    workbook = load_workbook(file_path, read_only=True)
    course_db = {}
    for data in iter_rows(workbook, COLUMNS):
        if not data["instr_name"]:
            continue  # blank row
        # new Course
        if data["c_num"]:
            course = {
                "name": to_title(data["c_title"]),
                "sections": {},
            }
            if data["compre"]:
                date, sess = data["compre"].split()
                course["compre"] = {"date": date, "session": sess}
            course_db[data["c_num"]] = course  # add to course
            sec_type = "L"
            sec_num_counter = 1

        # new Tutorial or Practical section
        if not data["c_num"] and data["c_title"]:
            sec_type = data["c_title"][0]
            sec_num_counter = 1

        # new Section
        if (
            data["instr_name"]
            and data["room"]
            and not sec_type == "L"
            or data["sec_num"]
        ) or data["c_title"]:
            sec_num = int(data["sec_num"] or sec_num_counter)
            section = {"instructors": [], "sched": []}
            course["sections"][sec_type + str(sec_num)] = section
            sec_num_counter += 1
            instructors = set()  # keep track of unique instructors

        if isinstance(data.get("hours"), (float, int)):
            data["hours"] = str(int(data["hours"]))
        if data.get("days"):
            hours = tuple(map(int, data["hours"].split()))
            days = data["days"].split()
            sched = {"room": data["room"], "days": days}
            if len(hours) == hours[-1] - hours[0] + 1:  # continuous hours
                section["sched"].append(dict(**sched, hours=hours))
            else:
                for hour in hours:  # separate sched for each hour
                    section["sched"].append(dict(**sched, hours=(hour,)))
        if data["instr_name"].lower() not in instructors:
            section["instructors"].append(data["instr_name"])
            instructors.add(data["instr_name"].lower())
    return course_db


def parse_midsem(file_path: Path):
    COLUMNS = {"c_num": 1, "c_title": 2, "date": 3, "time": 4}
    workbook = load_workbook(file_path, read_only=True)
    midsem = {}
    for row in iter_rows(workbook, COLUMNS):
        if "*" in row["time"]:
            continue
        c_dept, c_num = row["c_num"].strip().split()
        midsem[c_dept.strip() + " " + c_num.strip()] = {
            "date": row["date"].strip(),
            "time": row["time"].strip(),
        }
    return midsem


def parse_files(tt_file: Path, midsem_file: Path):
    course_db = parse_main_tt(tt_file)
    midsem = parse_midsem(midsem_file)
    for k, v in midsem.items():
        course_db[k]["midsem"] = v
    return course_db


def get_course_db(tt_file, midsem_file):
    json_file = tt_file.with_suffix(".json")
    if not json_file.exists():
        course_db = parse_files(tt_file, midsem_file)
        write_json(json_file, course_db)
    else:
        course_db = read_json(json_file)
    return course_db


def main():
    tt_file = Path(config["COURSES"]["tt_file"])
    midsem_file = Path(config["COURSES"]["midsem_file"])
    write_json(tt_file.with_suffix(".json"), parse_files(tt_file, midsem_file))


if __name__ == "__main__":
    main()
