import requests

from functools import lru_cache
from utils import config, pprint_json

MOODLE_URL = f"https://{config['MOODLE']['address']}/moodle"
REST_URL = MOODLE_URL + "/webservice/rest/server.php"


def make_req(verb, params={}, data=None):
    query_params = {
        "wstoken": config['MOODLE']['wstoken'],
        "moodlewsrestformat": "json",
    }
    query_params.update(params)
    return requests.request(verb, REST_URL, params=query_params, data=data)


def get(wsfunc, params={}):
    params['wsfunction'] = wsfunc
    return make_req('get', params)


def post(wsfunc, params={}, data={}):
    params['wsfunction'] = wsfunc
    return make_req('post', params, data)


@lru_cache()
def get_siteinfo():
    r = get('core_webservice_get_site_info')
    return r.json()


@lru_cache()
def get_userid():
    return get_siteinfo()['userid']


def get_enrolled_courses():
    r = get('core_enrol_get_users_courses', {'userid': get_userid()})
    return r.json()


def search_course(name):
    r = get('core_course_search_courses',
            {'criterianame': 'search', 'criteriavalue': name})
    data = r.json()
    if data['total']:
        return data['courses'][0]


def enrol(courseid):
    r = post('enrol_self_enrol_user', data={'courseid': courseid})
    return r.json()['status']


if __name__ == '__main__':
    pprint_json(get_enrolled_courses())
