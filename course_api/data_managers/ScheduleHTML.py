from course_api.utils.convert_24h import convertTime, colorscale
import dateutil.parser as dparser
from colorhash import ColorHash
from math import ceil
import random
import string
from course_api.data_managers.course_scheduler import CourseScheduler


def create_schedules(request):
    courses = request.POST.getlist('courses')
    term = request.POST.get('term')
    selected_classes = courses
    earliest = request.POST.get('earliest')
    if earliest == 'any':
        earliest = None
    else:
        earliest = int(earliest)
    latest = request.POST.get('latest')
    if latest == 'any':
        latest = None
    else:
        latest = int(latest)
    filters = request.POST.getlist('filters')
    try:
        gaps = filters[0]
    except IndexError:
        gaps = None
    try:
        days = filters[1]
    except IndexError:
        days = None
    if days == 'min_days':
        days = 'asc'
    else:
        days = 'desc'
    if gaps == 'gaps_min':
        gaps = 'asc'
    else:
        gaps = 'desc'
    generator = CourseScheduler(term, earliest_time=earliest, latest_time=latest, days=days, gaps=gaps)
    courses = generator.get_valid_schedules(courses)
    schedules = list()
    all_schedule_ids = []
    for schedule in courses:
        course_by_times = {'M': {}, 'T': {}, 'W': {}, 'R': {}, 'F': {}}
        classes = schedule.get('schedule')
        courses = []
        for course, data in classes.items():
            for section, section_data in data.items():
                if section_data:
                    if section_data.get('lecture_crn'):
                        section_data['color'] = colorscale(
                            ColorHash(''.join(section_data.get('course_id').split('-')[0:2]) + section_data.get(
                                'subject')).hex, 1.5)

                    else:
                        section_data['color'] = colorscale(
                            ColorHash(''.join(section_data.get('course_id').split('-')[0:2]) + section_data.get(
                                'subject')).hex, 1.5)
                    courses.append(section_data)

        for course in courses:
            course_days = list(course.get('days'))

            hours = convertTime(course.get('hours'))
            start_hour = str(hours.get('start'))
            end_hour = str(hours.get('end'))

            if len(start_hour) == 3:
                start_hour = "{}:{}".format(start_hour[0], start_hour[1:3])
            else:
                start_hour = '{}:{}'.format(start_hour[0:2], start_hour[2:4])
            if len(end_hour) == 3:
                end_hour = "{}:{}".format(end_hour[0], end_hour[1:3])
            else:
                end_hour = '{}:{}'.format(end_hour[0:2], end_hour[2:4])

            start_date = dparser.parse(start_hour)
            end_date = dparser.parse(end_hour)
            total_time = end_date - start_date

            course['length'] = (ceil((total_time.seconds / 60 / 60) * 2))
            for day in course_days:
                course_by_times[day][start_hour] = course
        course_by_times['unique_name'] = ''.join(
            [random.choice(string.ascii_letters + string.digits) for n in range(16)])
        schedules.append(course_by_times)
        all_schedule_ids.append(course_by_times['unique_name'])
        schedules = schedules[:65]
        all_schedule_ids = all_schedule_ids[:65]
    return schedules, all_schedule_ids, selected_classes
