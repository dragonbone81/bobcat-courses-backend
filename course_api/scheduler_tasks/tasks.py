from apscheduler.schedulers.blocking import BlockingScheduler
import requests

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    # Todo prob move this to data_managers and figure this out
    response = requests.get(url="https://cse120-course-planner.herokuapp.com/course_pull", params={'pull': True}).json()
    if response.get('success'):
        print('Course Pull Ran')
    else:
        print('Course Pull Failed')


sched.start()
