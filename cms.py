import requests
from bs4 import BeautifulSoup

sess = requests.Session()
moodle_url = 'http://id.bits-hyderabad.ac.in/moodle/'


def post_form(src, form_id, post_data=None):
    """Post a form after changing some of its fields."""
    soup = BeautifulSoup(src.text, 'html.parser')
    form = soup.find('form', id=form_id)
    form_url = form['action']
    payload = {}
    for field in form.find_all('input'):
        try:
            payload[field['name']] = field['value']
        except KeyError:
            pass
    if post_data:
        for key, value in post_data.items():
            payload[key] = value
    return sess.post(form_url, payload)


def login_google(email=None, password=None):
    url = moodle_url + 'login/index.php'
    r = sess.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    auth_link = soup.find('div', {'class': 'potentialidp'}).a['href']
    google_email = sess.get(auth_link)
    google_pwd = post_form(google_email, 'gaia_loginform', {'Email': email})
    moodle_dash = post_form(google_pwd, 'gaia_loginform', {'Passwd': password})
    if 'Dashboard' in moodle_dash.text:
        print('Login successful for CMS.')
    elif 'Wrong password' in moodle_dash.text:
        print('Wrong password for CMS. Edit the config.ini file.')
        exit(0)


def course_search(name):
    search_url = moodle_url + "course/search.php"
    code = sess.get(search_url, params={'search': name})
    soup = BeautifulSoup(code.text, 'html.parser')
    res = soup.find('span', id='maincontent').next_sibling.text

    if 'No courses were found' in res:
        print(res)
        return
    else:
        class_name = 'coursebox clearfix odd first'
        main_div = soup.find('div', {'class': class_name})
        if not main_div:
            main_div = soup.find('div', {'class': class_name + ' last'})
        course_id = main_div['data-courseid']
        # print("The course id for {} is {}.".format(name, course_id))
        return course_id


def get_attr(src, param, offset=0, end_ch='"'):
    x = src.find(param) + offset
    if x == offset - 1:
        raise EOFError
    y = src[x:].find(end_ch)
    if y == -1:
        y = len(src[x:])
    return src[x:][:y]


def course_enrol(c_id):
    """Enrol into a course."""
    c_url = moodle_url + 'course/view.php'
    c = sess.get(c_url, params={'id': c_id})
    if c.text[77:84] == 'Course:':
        print(f'Already enrolled to {c_id}.')
        return 1
    result = post_form(c, 'mform1')
    if result.text[77:84] != 'Course:':
        print(f'Enrollment unsuccessful for {c_id}.')
        return -1
    else:
        print(f'Enrolled to {c_id}.')
        return 0


def course_unenrol(c_id):
    """Unenrol from a course."""
    print(f'Unenrolling from {c_id}.', end='\n')
    course_url = moodle_url + 'course/view.php'
    c = sess.get(course_url, params={'id': c_id})
    if c.text[77:84] != 'Course:':
        print(f'Not enrolled to {c_id}.')
        return
    enrolid = get_attr(c.text, 'enrolid', 8)
    sesskey = get_attr(c.text, 'sesskey', 10)
    unenrol_url = moodle_url + 'enrol/self/unenrolself.php'
    payload = {'enrolid': enrolid, 'confirm': '1', 'sesskey': sesskey}
    sess.post(unenrol_url, data=payload)
    print('Done.')
