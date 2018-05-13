import requests
from bs4 import BeautifulSoup
from course_api.data_managers.update_terms import UpdateTerms


def update_terms():
    terms_url = "https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.p_selectsubject"
    html = requests.get(url=terms_url).text
    soup = BeautifulSoup(html, "html.parser")
    html = soup.find('form', attrs={'action': 'xhwschedule.P_ViewSchedule'})
    inputs = html.findAll('input', attrs={'name': 'validterm'})
    terms = [input_div.get('value') for input_div in inputs if input_div.get('value') if
             ' ' not in input_div.get('value')]

    UpdateTerms(school_id='uc_merced', terms=terms).update_model()
