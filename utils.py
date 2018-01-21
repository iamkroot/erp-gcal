import configparser
from datetime import date, timedelta
import os
import json

today = date.today()


def get_config(path='config.ini'):
    """Load the config using configparser."""
    if not os.path.exists(path):
        print(f'{path} not found!')
        exit(0)
    config = configparser.ConfigParser()
    config.read(path)
    return config


def read_json(path, no_file=exit):
    """Properly handle reading a json."""
    if not os.path.isfile(path):
        print(f'{path} not found!')
        return no_file()
    with open(path, 'r') as f:
        data = f.read()
        if not data:  # in case the file is empty
            print(f'{path} is empty.')
            return no_file()
        return json.loads(data)


def get_weekday(isoweekday):
    return today - timedelta(days=today.weekday() + isoweekday - 1)
