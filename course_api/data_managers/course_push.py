from course_api.data_managers.course_pull import UCMercedClassParser
from django_bulk_update.helper import bulk_update
from course_api.models import Course, SubjectCourse
from course_planner.settings import DEBUG
from course_api.utils.simplified_course_name import get_simple
from django.db.models import Q


class UCMercedCoursePush(object):
    def __init__(self):
        self.data = UCMercedClassParser(terms=["201830", "201810"]).parse_terms()

    def push_courses(self):
        current_courses = Course.objects.all()
        current_course_crn = {str(course.crn): course for course in current_courses}
        need_added = list()
        need_update = list()
        for course in self.data:
            course['units'] = int(course['units'])
            course['capacity'] = int(course['capacity'])
            course['enrolled'] = int(course['enrolled'])
            course['simple_name'] = get_simple(course['course_id'])
            if course['available'] == 'Closed':
                course['available'] = 0
            else:
                course['available'] = int(course['available'])
            course_obj = Course(**course)

            if str(course['crn']) not in current_course_crn:
                need_added.append(course_obj)
            else:
                # TODO could check the fields to only update if something changed but for now...
                need_update.append(course_obj)
        Course.objects.bulk_create(need_added)
        if DEBUG:
            # in debug sqlite doesnt like big batches
            bulk_update(need_update, batch_size=10)
        else:
            bulk_update(need_update, batch_size=1000)

        # associate foreign keys
        lectures = {course.crn: course for course in Course.objects.filter(type='LECT')}
        other_classes = {course.crn: course for course in Course.objects.filter(~Q(type='LECT'))}
        updated_others = list()
        for crn, course in other_classes.items():
            lecture = lectures.get(course.lecture_crn)
            if course.lecture_crn and lecture:
                course.lecture = lecture
                updated_others.append(course)
        if DEBUG:
            # in debug sqlite doesnt like big batches
            bulk_update(updated_others, batch_size=10)
        else:
            bulk_update(updated_others, batch_size=1000)


class SubjectClassUpdate(object):
    def get_courses_lectures(self):
        courses = dict()
        for course in Course.objects.all():
            simplified_name = get_simple(course.course_id)
            if not courses.get(simplified_name):
                course_obj = {
                    'course_name': simplified_name,
                    'term': course.term,
                }
                course_obj = SubjectCourse(**course_obj)
                courses[simplified_name] = course_obj
        return courses

    def update_lectures(self):
        # screw it for this one we actually don't need to update anything so lets just get all delete and the place all
        SubjectCourse.objects.all().delete()
        courses = self.get_courses_lectures()
        courses = [course for key, course in courses.items()]
        SubjectCourse.objects.bulk_create(courses)

# SubjectClassUpdate().update_lectures()
# UCMercedCoursePush().push_courses()
