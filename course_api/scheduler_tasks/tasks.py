import requests


# def timed_job():
#     url = "https://cse120-course-planner.herokuapp.com/course_pull"
#     requests.get(url=url)
#     print('Course Pull Ran')
def course_pull_201030():
    url = "https://cse120-course-planner.herokuapp.com/course_pull/?pull=True&term=201830"
    requests.get(url=url)
    print('Course Pull 201830 Ran')


course_pull_201030()
