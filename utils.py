import json
import re
from datetime import date, datetime, time, timedelta, tzinfo
from difflib import SequenceMatcher

import requests
import toml


def read_toml(path):
    try:
        with open(path) as f:
            return toml.load(f)
    except FileNotFoundError:
        print(f"Missing toml file at {path}.")
        quit()
    except toml.TomlDecodeError as e:
        print(f"Invalid TOML in file: {path}")
        print(f"Error (probably) in line {e.lineno}.")
        quit()


config = read_toml('config.toml')


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Missing json file at {path}.")
        quit()
    except json.JSONDecodeError:
        print(f"Invalid json file at {path}.")
        quit()


def write_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)


def get_weekday(isoweekday):
    today = date.today()
    return today - timedelta(days=today.weekday() + isoweekday - 1)


class IST(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=5, minutes=30)

    def dst(self, dt):
        return timedelta(0)


def combine_dt(date_, time_=time(0, 0), tz=IST):
    return datetime.combine(date_, time_, tz())


def retry_on_conn_error(func):
    def wrapper(*args, **kwargs):
        for _ in range(5):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                print("Connection Error. Retrying.")
                continue
            except KeyboardInterrupt:
                print("Error")
                quit()
        else:
            print("Connection Error! Maximum retries exceeded.")
            quit()
    return wrapper


def pprint_json(data):
    print(json.dumps(data, indent=4))


def to_title(s, exceptions=('I', 'II', 'III', 'IV')):
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


def fuzzymatch_dicts(target, source, fields=None, thresh=0.8):
    total = 0
    num = 0
    for k, v in target.items():
        if fields and k not in fields:
            continue
        if not isinstance(v, str):
            continue
        orig = source.get(k)
        if not orig:
            continue
        matcher = SequenceMatcher(None, v, orig)
        total += matcher.ratio()
        num += 1
    try:
        ratio = total / num
        return ratio if ratio >= thresh else 0
    except ZeroDivisionError:
        return 0


def find_entity(entity, entities, fields):
    max_ratio = 0
    best_match = None
    for e in entities:
        ratio = fuzzymatch_dicts(entity, e, fields)
        if max_ratio < ratio:
            max_ratio = ratio
            best_match = e
    return best_match


def get_cal_name():
    today = date.today()
    sem = 2 if 1 <= today.month <= 5 else 1
    year = today.year - sem + 1
    return f"Timetable Sem {sem}, {year}-{year + 1 - 2000}"
