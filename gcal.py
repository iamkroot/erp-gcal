import httplib2
import os

from apiclient.discovery import build
from oauth2client import client, tools
from oauth2client.file import Storage
from googleapiclient.errors import HttpError

from utils import find_entity

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'ERP to Google Calendar'


def get_credentials(new_creds=False):
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'erp-gcal-creds.json')

    store = Storage(credential_path)
    credentials = None if new_creds else store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        args = tools.argparser.parse_known_args()[0]
        credentials = tools.run_flow(flow, store, args)
        print('Storing credentials to ' + credential_path)
        print("Pass '-n' next time if you want to run with another account.")
    return credentials


def create_cal_serv(new_creds=False):
    credentials = get_credentials(new_creds)
    http = credentials.authorize(httplib2.Http())
    return build('calendar', 'v3', http=http)


class GCal:
    def __init__(self, new_creds=False, cal_id='primary'):
        self.cal_id = cal_id
        self.service = create_cal_serv(new_creds)

    def get_all_entities(self, entity_name, **kwargs):
        page_token = None
        entity_serv = getattr(self.service, entity_name)
        if not entity_serv:
            print("Invalid entity name")
            return
        while True:
            entities = entity_serv().list(
                pageToken=page_token, **kwargs).execute()
            for entity in entities['items']:
                yield entity
            page_token = entities.get('nextPageToken')
            if not page_token:
                break

    def get_all_cals(self):
        return self.get_all_entities('calendarList')

    def get_all_events(self):
        return self.get_all_entities('events', calendarId=self.cal_id)

    def delete_event(self, event):
        return self.service.events().delete(
            calendarId=self.cal_id, eventId=event['id']).execute()

    def create_event(self, event):
        return self.service.events().insert(
            calendarId=self.cal_id, body=event).execute()

    def patch_event(self, event, data):
        return self.service.events().patch(
            calendarId=self.cal_id, eventId=event['id'], body=data).execute()

    def create_cal(self, calendar):
        return self.service.calendars().insert(body=calendar).execute()

    def find_event(self, event):
        events = self.get_all_events()
        fields = ('summary', 'description', 'location')
        return find_entity(event, events, fields)

    def find_cal(self, cal):
        cals = self.get_all_cals()
        fields = ('summary', 'description')
        return find_entity(cal, cals, fields)

    def set_cal(self, summary, description=None):
        calendar = {'summary': summary}
        if description:
            calendar['description'] = description
        cal = self.find_cal(calendar)
        if cal:
            self.cal_id = cal['id']
            return True
        cal = self.create_cal(calendar)
        if not cal:
            print("Failed to find or create calendar", calendar)
            return
        self.cal_id = cal['id']

    def clear_cal(self):
        for event in self.get_all_events():
            self.print_event(event, "Deleting")
            try:
                self.delete_event(event)
            except HttpError as err:
                if err.resp.status != 410:
                    raise err

    @staticmethod
    def print_event(event, prefix="", suffix=""):
        if prefix:
            print(prefix, end=' ')
        print(event.get('summary', event), end=' ' if suffix else '\n')
        if suffix:
            print(suffix)


if __name__ == '__main__':
    gcal = GCal()
    for cal in gcal.get_all_cals():
        print(cal)
    for event in gcal.get_all_events():
        gcal.print_event(event)
