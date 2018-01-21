import requests
from bs4 import BeautifulSoup
import re
import utils

sess = requests.Session()

ADDRESS = utils.get_config()['ERP_URL']['address']


def login(username, password):
    login_url = f'http://{ADDRESS}/psp/hcsprod/?cmd=login&languageCd=ENG'
    payload = {'userid': username, 'pwd': password}
    r = sess.post(login_url, data=payload)
    if r.url[-1] == 'T':
        print('Logged in to ERP.')
    else:
        print('Login unsuccessful for ERP.')


def post_form(src, **kwargs):
    """Post a form after changing some of its fields."""
    soup = BeautifulSoup(src.text, 'html.parser')
    form = soup.find('form', id=kwargs.get('form_id'))
    form_url = kwargs.get('form_url') or form['action']
    payload = {}
    for field in form.find_all('input'):
        try:
            payload[field['name']] = field['value']
        except KeyError:
            pass
    for key, value in kwargs.get('post_data', {}).items():
        payload[key] = value
    return sess.post(form_url, payload)


def get_weekly_sched(start_date=None):
    if not start_date:
        start_date = utils.get_weekday(1).strftime('%d/%m/%Y')
    url = (f'http://{ADDRESS}/psc/hcsprod/EMPLOYEE/HRMS/c/'
           'SA_LEARNER_SERVICES.SSR_SSENRL_SCHD_W.GBL')
    r = sess.get(url)
    payload = {
        'DERIVED_CLASS_S_START_DT': start_date,
        'DERIVED_CLASS_S_MEETING_TIME_END': '4:00PM',
        'DERIVED_CLASS_S_SUNDAY_LBL': 'N',
        'ICAction': 'DERIVED_CLASS_S_SSR_REFRESH_CAL'
    }
    response = post_form(r, post_data=payload, form_url=r.url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find('table', id='WEEKLY_SCHED_HTMLAREA').find_all('tr')
    return [[cell.text for cell in row.find_all('td')[1:]] for row in rows[1:]]


def parse_tt(week):
    pattern = re.compile(r'(\S+)\s+(\S+) - ([A-Z]+\d+)')
    courses = {}
    for time_slot in week:
        for cell in time_slot:
            m = pattern.match(cell)
            if not m:
                continue
            course_code = f'{m[1]} {m[2]}'
            courses.setdefault(course_code, set())
            courses[course_code].add(m[3])
    return courses


def get_reg_sections():
    config = utils.get_config()
    login(**config['ERP_CREDS'])
    return parse_tt(get_weekly_sched())


if __name__ == '__main__':
    print(get_reg_sections())
