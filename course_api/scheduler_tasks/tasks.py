from apscheduler.schedulers.background import BackgroundScheduler
import requests

scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval', hours=6, id="course_update")  # to not annoy or whatever
def timed_job():
    # Todo prob move this to data_managers and figure this out
    url = "https://cse120-course-planner.herokuapp.com/course_pull"
    response = requests.get(url=url, params={'pull': True}).json()
    if response.get('success'):
        print('Course Pull Ran')
    else:
        print('Course Pull Failed')


scheduler.start()
