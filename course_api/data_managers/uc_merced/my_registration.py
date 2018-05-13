import requests
import lxml.html
from dateutil.parser import parse
from django.utils import timezone
from datetime import timedelta
from dateutil.tz import gettz
from bs4 import BeautifulSoup

"""
Thank you my dude :D https://brennan.io/2016/03/02/logging-in-with-requests/
"""


class CourseRegistration(object):
    def __init__(self, course_crns, term, auth):
        self.errors = {}
        self.session = requests.session()
        self.service = 'https://my.ucmerced.edu/uPortal/Login'
        self.login_url = 'https://cas.ucmerced.edu/cas/login'
        self.auth = auth
        self.term = term
        course_crns += [''] * (10 - len(course_crns))  # pad to 10 courses
        # some data that the default form submits not sure if we need everything but I couldn't be bothered to test
        self.form_data = 'term_in={term}&RSTS_IN=DUMMY&assoc_term_in=DUMMY&CRN_IN=' \
                         'DUMMY&start_date_in=DUMMY&end_date_in=DUMMY&SUBJ=DUMMY&CRSE=DUMMY&SEC=DUMMY&LEVL=' \
                         'DUMMY&CRED=DUMMY&GMOD=DUMMY&TITLE=DUMMY&MESG=DUMMY&REG_BTN=DUMMY&RSTS_IN=RW&CRN_IN={course_1}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_2}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_3}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_4}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_5}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_6}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_7}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_8}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_9}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&RSTS_IN=RW&CRN_IN={course_10}' \
                         '&assoc_term_in=&start_date_in=&end_date_in=&regs_row=0&wait_row=0' \
                         '&add_row=10&REG_BTN=Submit+Changes'.format(term=term, course_1=course_crns[0],
                                                                     course_2=course_crns[1],
                                                                     course_3=course_crns[2], course_4=course_crns[3],
                                                                     course_5=course_crns[4], course_6=course_crns[5],
                                                                     course_7=course_crns[6], course_8=course_crns[7],
                                                                     course_9=course_crns[8],
                                                                     course_10=course_crns[9], )
        self.registration_time = ''

    def cas_login(self):
        # Start session and get login form.

        login = self.session.get(self.login_url, params={'service': self.service})

        # Get the hidden elements and put them in our form.
        login_html = lxml.html.fromstring(login.text)
        hidden_elements = login_html.xpath('//form//input[@type="hidden"]')
        form = {x.attrib['name']: x.attrib['value'] for x in hidden_elements}

        # "Fill out" the form.
        form['username'] = self.auth.get('username')
        form['password'] = self.auth.get('password')

        # Finally, login and return the session.

        self.session.post(self.login_url, data=form, params={'service': self.service})
        response = self.session.get(
            'https://mystudentrecord.ucmerced.edu/pls/PROD/twbkwbis.P_WWWLogin?ret_code=R')  # gotta go here first'
        if 'UC Merced Single Sign On - UC Merced CAS - Single Sign-On' in response.text:
            self.errors['login'] = 'failed'
            return self.errors
        else:
            self.registration_time = self.check_registration_time()
            return {'login': 'success'}

    def check_registration_time(self):
        html = self.session.post('https://mystudentrecord.ucmerced.edu/pls/PROD/bwskrsta.P_RegsStatusDisp',
                                 data={'term_in': self.term}).text
        soup = BeautifulSoup(html, "html.parser")
        html = soup.find('table', attrs={'class': 'datadisplaytable'})
        times = html.findAll('td')
        date = times[0].text
        time = times[1].text
        tzinfos = {"PST": gettz("America/Los_Angeles")}
        return parse("{} {} {}".format(date, time, "PST"), tzinfos=tzinfos)

    def register(self):
        if self.registration_time > timezone.now():
            reg_time = self.registration_time.strftime("Your registration time is at %I:%M%p on %x")
            return {'response': 'reg_time_less', 'reg_time': reg_time}
        if self.registration_time > timezone.now() - timedelta(seconds=30):
            return {'response': 'reg_time_almost'}
        response = self.session.post('https://mystudentrecord.ucmerced.edu/pls/PROD/bwckcoms.P_Regs',
                                     data=self.form_data).text
        if 'Closed Section' in response:
            return {'response': 'course_full',
                    'message': 'Sorry, one of the courses is full. Please register manually'}
        if "Prerequisite Not Completed" in response:
            return {'response': 'prereq',
                    'message': 'You have a pre-req that is not completed. Please check in MyRegistration'}
        if "If no options are listed in the" in response and "DOES NOT EXIST" not in response:
            return {'response': 'success'}
        else:
            return {'response': 'fail'}
