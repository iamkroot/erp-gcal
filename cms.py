import requests

from functools import lru_cache
from utils import config, pprint_json

REST_URL = config['MOODLE']['address'] + "/webservice/rest/server.php"


def make_req(verb, params={}, data=None):
    query_params = {
        "wstoken": config['MOODLE']['wstoken'],
        "moodlewsrestformat": "json",
    }
    query_params.update(params)
    resp = requests.request(verb, REST_URL, params=query_params, data=data)
    resp = resp.json()
    if 'exception' in resp:
        raise Exception('CMS error: ' + resp['message'])
    return resp


def get(wsfunc, params={}):
    params['wsfunction'] = wsfunc
    return make_req('get', params)


def post(wsfunc, params={}, data={}):
    params['wsfunction'] = wsfunc
    return make_req('post', params, data)


@lru_cache()
def get_siteinfo():
    return get('core_webservice_get_site_info')


@lru_cache()
def get_userid():
    return get_siteinfo()['userid']


@lru_cache()
def get_enrolled_courses():
    return get('core_enrol_get_users_courses', {'userid': get_userid()})


def search_course(name):
    data = get('core_course_search_courses',
               {'criterianame': 'search', 'criteriavalue': name})
    if data['total']:
        return data['courses'][0]


def enrol(courseid):
    return post('enrol_self_enrol_user', data={'courseid': courseid})


if __name__ == '__main__':
    pprint_json(get_enrolled_courses())
