import requests


# def timed_job():
#     url = "https://cse120-course-planner.herokuapp.com/course_pull"
#     requests.get(url=url)
#     print('Course Pull Ran')
def course_pull_201930():
    url = "https://cse120-course-planner.herokuapp.com/course_pull/?pull=True&term=201930"
    requests.get(url=url)
    print('Course Pull 201930 Ran')


course_pull_201930()
