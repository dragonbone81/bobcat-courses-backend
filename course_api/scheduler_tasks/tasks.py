import requests


# def timed_job():
#     url = "https://cse120-course-planner.herokuapp.com/course_pull"
#     requests.get(url=url)
#     print('Course Pull Ran')
def course_pull_201910():
    url = "https://cse120-course-planner.herokuapp.com/course_pull/?pull=True&term=201910"
    requests.get(url=url)
    print('Course Pull 201910 Ran')


course_pull_201910()
