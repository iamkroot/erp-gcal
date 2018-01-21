import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from datetime import datetime as dt, timedelta as td, time, date, tzinfo
import bisect
import utils

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Timetable for BPHC'
WEEK = ['M', 'T', 'W', 'Th', 'F', 'S']


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'erp-calendar-creds.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def create_cal_serv():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    return discovery.build('calendar', 'v3', http=http)


def delete_event(event, service, **kwargs):
    service.events().delete(calendarId='primary',
                            eventId=event['id']).execute()
    print('deleted.')


def create_event(event, service, **kwargs):
    resp = service.events().insert(calendarId='primary', body=event).execute()
    print(resp['summary'], 'created.')


def patch_event(event, service, data, **kwargs):
    service.events().patch(calendarId='primary',
                           eventId=event['id'], body=data).execute()


def all_events(callback, **kwargs):
    page_token = None
    service = create_cal_serv()
    while True:
        events = service.events().list(calendarId='primary',
                                       pageToken=page_token).execute()
        print(events['items'])
        for event in events['items']:
            if not event.get('summary'):
                print(event)
                break
            print(event['summary'], end=' ')
            callback(event, service, **kwargs)
        page_token = events.get('nextPageToken')
        if not page_token:
            break


class IST(tzinfo):
    def utcoffset(self, dt):
        return td(hours=5, minutes=30)


def calc_start_date(wdays):
    today = dt.today()
    if today.isoweekday() in wdays:
        return today
    lower = bisect.bisect(wdays, today.isoweekday())
    return today + td(
        days=wdays[lower % len(wdays)] - today.isoweekday(),
        weeks=(lower == len(wdays))
    )


def get_last_date():
    return dt.strptime(utils.get_config()['DATES']['last_date'], '%d/%m/%Y')


def parse_times(hours):
    hours = hours.split()
    start_times = [time(hour=h) for h in range(7, 18)]
    start = start_times[int(hours[0])]
    return (start, start.replace(hour=start.hour + len(hours) - 1, minute=50))


def combine(e_date, e_time):
    return dt.combine(e_date, e_time, IST())


def parse_compre(compre):
    if not compre['date']:
        return None
    dd, mm = map(int, compre['date'].split('/'))
    today = date.today()
    compre_date = today.replace(day=dd, month=mm)
    if today > compre_date:
        compre_date = compre_date.replace(year=today.year + 1)

    def comb(hour):
        return combine(compre_date, time(hour=hour))

    sessions = {
        'FN': {'start': comb(9), 'end': comb(12)},
        'AN': {'start': comb(14), 'end': comb(17)}
    }
    return {key: sessions[compre['session']][key] for key in ['start', 'end']}


def parse_section(section):
    weekdays = [WEEK.index(day) + 1 for day in section['days'].split()]
    start_date = calc_start_date(weekdays)
    times = parse_times(section['hours'])
    return {
        'num': section['num'],
        'instructors': ', '.join(section['instructors']),
        'room': section['room'],
        'start': combine(start_date, times[0]),
        'end': combine(start_date, times[1]),
        'wdays': weekdays
    }


if __name__ == '__main__':
    pass
