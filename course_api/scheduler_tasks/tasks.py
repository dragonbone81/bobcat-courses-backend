from apscheduler.schedulers.blocking import BlockingScheduler
import requests

scheduler = BlockingScheduler()


@scheduler.scheduled_job('interval', hours=6)  # TODO figure this out so that it will run often during high demand
# TODO idk how to do this using real scheduling and it times out
def timed_job():
    # Todo prob move this to data_managers and figure this out
    url = "https://cse120-course-planner.herokuapp.com/course_pull"
    response = requests.get(url=url, params={'pull': True}).json()
    url = "https://cse120-course-planner.herokuapp.com/course_pull"
    response = requests.get(url=url, params={'simple': True}).json()
    if response.get('success'):
        print('Course Pull Ran')
    else:
        print('Course Pull Failed')


scheduler.start()
