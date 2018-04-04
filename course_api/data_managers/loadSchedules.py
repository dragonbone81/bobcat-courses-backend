from course_api.models import Course
from course_api.serializers import CourseSerializer
import random
import string
from course_api.utils.convert_24h import convertTime, colorscale
import dateutil.parser as dparser
from datetime import datetime, timedelta
from colorhash import ColorHash
from math import ceil


class GetSchedules(object):
    def __init__(self, schedule_crns):
        self.schedule_crns = schedule_crns

    def get_data_object(self):
        schedules = list()
        all_schedule_ids = list()
        all_schedule_crns = dict()
        all_schedule_terms = list()
        for schedule in self.schedule_crns:
            all_schedule_terms.append(schedule.get('term'))
            schedule['earliest'] = 99999
            schedule['latest'] = -99999
            courses = []
            actual_schedule = dict()
            actual_schedule['unique_name'] = ''.join(
                [random.choice(string.ascii_letters + string.digits) for n in range(16)])
            all_schedule_ids.append(actual_schedule['unique_name'])
            course_data = []
            # for course, data in schedule.get('schedule').items():
            for course in [CourseSerializer(course).data for course in
                           Course.objects.filter(crn__in=schedule.get('courses'))]:
                if course.get('lecture_crn'):
                    course['color'] = colorscale(
                        ColorHash(''.join(course.get('course_id').split('-')[0:2]) + course.get(
                            'subject')).hex, 1.5)

                else:
                    course['color'] = colorscale(
                        ColorHash(''.join(course.get('course_id').split('-')[0:2]) + course.get(
                            'subject')).hex, 1.5)
                courses.append(course)
                if course['hours'] == 'TBD-TBD':
                    length = 0
                else:
                    length = 9
                course_data.append(
                    {'crn': course.get('crn'), 'course_id': course.get('course_id'),
                     'color': course['color'], 'length': length})
                all_schedule_crns[actual_schedule['unique_name']] = course_data
            for course in courses:
                course_days = list(course.get('days'))
                if course.get('hours') == "TBD-TBD":
                    course['length'] = 0
                else:
                    hours = convertTime(course.get('hours'))
                    start_hour = str(hours.get('start'))
                    end_hour = str(hours.get('end'))
                    if schedule.get('earliest') > int(start_hour):
                        schedule['earliest'] = int(start_hour)
                    if schedule.get('latest') < int(end_hour):
                        schedule['latest'] = int(end_hour)
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

                    course['start_str'] = hours.get('start')
                    course['end_str'] = hours.get('end')
                    course['start'] = "{}{}".format(ceil_dt(start_date, timedelta(minutes=30)).hour,
                                                    ceil_dt(start_date, timedelta(minutes=30)).minute)
                    if ceil_dt(start_date,
                               timedelta(minutes=30)).minute == 0:
                        course['start'] += "0"

                    course['end'] = "{}{}".format(ceil_dt(end_date, timedelta(minutes=30)).hour,
                                                  ceil_dt(end_date, timedelta(minutes=30)).minute)
                    if ceil_dt(end_date,
                               timedelta(minutes=30)).minute == 0:
                        course['end'] += "0"
                    course['length'] = (ceil((total_time.seconds / 60 / 60) * 2))
            times = ['700', '730', '800', '830', '900', '930', '1000', '1030', '1100', '1130', '1200', '1230', '1300',
                     '1330',
                     '1400', '1430', '1500', '1530', '1600', '1630', '1700', '1730', '1800', '1830', '1900', '1930',
                     '2000', '2030', '2100', '2130', '2200', '2230', '2300']
            times_dict = {'700': 0, '730': 1, '800': 2, '830': 3, '900': 4, '930': 5, '1000': 6, '1030': 7, '1100': 8,
                          '1130': 9,
                          '1200': 10, '1230': 11, '1300': 12,
                          '1330': 13,
                          '1400': 14, '1430': 15, '1500': 16, '1530': 17, '1600': 18, '1630': 19, '1700': 20,
                          '1730': 21,
                          '1800': 22, '1830': 23, '1900': 24, '1930': 25,
                          '2000': 26, '2030': 27, '2100': 28, '2130': 29, '2200': 30, '2230': 31, '2300': 32}
            if len(str(schedule.get('latest'))) == 3:
                latest_hour = "{}:{}".format(str(schedule.get('latest'))[0], str(schedule.get('latest'))[1:3])
            else:
                latest_hour = '{}:{}'.format(str(schedule.get('latest'))[0:2], str(schedule.get('latest'))[2:4])

            if len(str(schedule.get('earliest'))) == 3:
                earliest_hour = "{}:{}".format(str(schedule.get('earliest'))[0], str(schedule.get('earliest'))[1:3])
            else:
                earliest_hour = '{}:{}'.format(str(schedule.get('earliest'))[0:2], str(schedule.get('earliest'))[2:4])
            latest_hour_str = "{}{}".format(ceil_dt(dparser.parse(latest_hour), timedelta(minutes=30)).hour,
                                            ceil_dt(dparser.parse(latest_hour), timedelta(minutes=30)).minute)
            if ceil_dt(dparser.parse(latest_hour), timedelta(minutes=30)).minute == 0:
                latest_hour_str += "0"

            earliest_hour_str = "{}{}".format(ceil_dt(dparser.parse(earliest_hour), timedelta(minutes=30)).hour,
                                              ceil_dt(dparser.parse(earliest_hour), timedelta(minutes=30)).minute)
            if ceil_dt(dparser.parse(earliest_hour), timedelta(minutes=30)).minute == 0:
                earliest_hour_str += "0"
            lower_bound = times_dict[earliest_hour_str] - 1
            if lower_bound < 0:
                lower_bound = 0
            for time in times[lower_bound:times_dict[latest_hour_str] + 1]:
                actual_schedule[time] = {'M': {}, 'T': {}, 'W': {}, 'R': {}, 'F': {}}
            for course in courses:
                if course['length'] != 0:
                    for day in list(course['days']):
                        list_times_course = []
                        for time in times:
                            if int(time) >= int(course['start']) and int(time) < int(course['end']):
                                list_times_course.append(time)
                        for time in list_times_course:
                            new_course = course.copy()
                            if int(new_course['start']) == int(time):
                                new_course['next'] = False
                            else:
                                new_course['next'] = True
                                new_course['time'] = time
                            actual_schedule[time][day] = new_course

            schedules.append(actual_schedule)
            all_schedule_crns[actual_schedule['unique_name']] = course_data
        return schedules, all_schedule_ids, all_schedule_crns, all_schedule_terms


def ceil_dt(dt, delta):
    return dt + (datetime.min - dt) % delta
