import httplib2
import os

from apiclient.discovery import build
from oauth2client import client, tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Timetable for BPHC'


def get_credentials():
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
    return build('calendar', 'v3', http=http)


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


def print_event(event, *args, **kwargs):
    print(event.get('summary', event))


def all_events(service, callback, **kwargs):
    page_token = None
    while True:
        events = service.events().list(calendarId='primary',
                                       pageToken=page_token).execute()
        for event in events['items']:
            callback(event, service, **kwargs)
        page_token = events.get('nextPageToken')
        if not page_token:
            break


if __name__ == '__main__':
    service = create_cal_serv()
    all_events(service, print_event)
