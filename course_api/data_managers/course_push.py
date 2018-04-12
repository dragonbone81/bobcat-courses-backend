from course_api.data_managers.course_pull import UCMercedClassParser
from django_bulk_update.helper import bulk_update
from course_api.models import Course, SubjectCourse
from course_planner.settings import DEBUG
from course_api.utils.simplified_course_name import get_simple
from django.db.models import Q


class UCMercedCoursePush(object):
    def __init__(self, terms=None):
        if not terms:
            terms = ["201830", "201810"]
        self.data = UCMercedClassParser(terms=terms).parse_terms()

    def delete_courses(self):
        current_courses = Course.objects.all()
        new_course_crn_list = [str(course['crn']) for course in self.data]
        current_course_crn_list = [str(course.crn) for course in current_courses]
        need_deleted = list(set(current_course_crn_list) - set(new_course_crn_list))
        Course.objects.filter(crn__in=need_deleted).delete()  # delete courses that don't exists anymore

    def push_courses(self):
        current_courses = Course.objects.all()
        current_course_crn = {str(course.crn): course for course in current_courses}
        need_added = list()
        need_update = list()
        for course in self.data:
            course['units'] = int(course['units'])
            course['capacity'] = int(course['capacity'])
            course['enrolled'] = int(course['enrolled'])
            while course['course_name'].endswith('\\t'):
                course['course_name'] = course['course_name'][:-2]
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
        self.link_labs()

    def link_labs(self):
        for course in Course.objects.filter(type='LAB'):
            if course.attached_crn:
                discussion = Course.objects.get(crn=course.attached_crn)
                discussion.attached_crn = course.crn
                discussion.save()


class SubjectClassUpdate(object):
    def get_courses_lectures(self):
        courses = dict()
        all_courses = Course.objects.all()
        for course in all_courses:
            simplified_name = get_simple(course.course_id)
            if not courses.get("{}:{}".format(simplified_name, course.term)):
                course_obj = {
                    'course_name': simplified_name,
                    'term': course.term,
                    'course_subject': course.subject,
                    'course_description': course.course_name,
                }
                course_obj = SubjectCourse(**course_obj)
                courses["{}:{}".format(simplified_name, course.term)] = course_obj
        return courses

    def update_lectures(self):
        SubjectCourse.objects.all().delete()
        courses = self.get_courses_lectures()
        courses = [course for key, course in courses.items()]
        SubjectCourse.objects.bulk_create(courses)

# SubjectClassUpdate().update_lectures()
# UCMercedCoursePush().push_courses()
