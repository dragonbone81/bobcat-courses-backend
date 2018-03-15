import requests
import lxml.html

"""
Thank you my dude :D https://brennan.io/2016/03/02/logging-in-with-requests/
"""


class CourseRegistration(object):
    def __init__(self, course_crns, term, auth):
        self.session = requests.session()
        self.service = 'https://my.ucmerced.edu/uPortal/Login'
        self.login_url = 'https://cas.ucmerced.edu/cas/login'
        self.auth = auth
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
        self.cas_login()

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
        self.session.get(
            'https://mystudentrecord.ucmerced.edu/pls/PROD/twbkwbis.P_WWWLogin?ret_code=R')  # gotta go here first'

    def register(self):
        response = self.session.post('https://mystudentrecord.ucmerced.edu/pls/PROD/bwckcoms.P_Regs',
                                     data=self.form_data).text
        if "If no options are listed in the" in response and "DOES NOT EXIST" not in response:
            return True
        else:
            return False
