# from apscheduler.schedulers.blocking import BlockingScheduler
import requests


# scheduler = BlockingScheduler()


# @scheduler.scheduled_job('interval', minutes=35)  # TODO figure this out so that it will run often during high demand
# # TODO idk how to do this using real scheduling and it times out
def timed_job():
    # Todo prob move this to data_managers and figure this out
    url = "https://cse120-course-planner.herokuapp.com/course_pull"
    requests.get(url=url, params={'pull': True})
    url = "https://cse120-course-planner.herokuapp.com/course_pull"
    requests.get(url=url, params={'simple': True})
    print('Course Pull Ran')


timed_job()
# scheduler.start()
