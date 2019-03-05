import json
from datetime import date, timedelta
import requests
import toml


def read_toml(path):
    try:
        with open(path) as f:
            return toml.load(f)
    except FileNotFoundError:
        print(f"Missing toml file at {path}.")
        quit()
    except toml.TomlDecodeError:
        print(f"Invalid toml file at {path}.")
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


def get_weekday(isoweekday):
    today = date.today()
    return today - timedelta(days=today.weekday() + isoweekday - 1)


def retry_on_conn_error(func, max_retries=5):
    def wrapper(*args, **kwargs):
        for _ in range(max_retries):
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
