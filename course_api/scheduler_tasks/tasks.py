import requests


def timed_job():
    url = "https://cse120-course-planner.herokuapp.com/course_pull"
    requests.get(url=url)
    print('Course Pull Ran')


timed_job()
