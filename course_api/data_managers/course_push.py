from course_api.data_managers.course_pull import UCMercedClassParser
from django_bulk_update.helper import bulk_update
from course_api.models import Course
from course_planner.settings import DEBUG


class UCMercedCoursePush(object):
    def __init__(self):
        self.data = UCMercedClassParser(term="201810").parse()

    def push_courses(self):
        current_courses = Course.objects.all()
        current_course_crn = {str(course.crn): course for course in current_courses}
        need_added = list()
        need_update = list()
        for course in self.data:
            course['units'] = int(course['units'])
            course['capacity'] = int(course['capacity'])
            course['enrolled'] = int(course['enrolled'])
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
            bulk_update(need_update, batch_size=10)
        else:
            bulk_update(need_update, batch_size=1000)

        """OLD CODE FOR UPDATE
        # for course in self.data:
        #     crn = course.get('crn')
        #     course.pop('crn')
        #     course['units'] = int(course['units'])
        #     course['capacity'] = int(course['capacity'])
        #     course['enrolled'] = int(course['enrolled'])
        #     if course['available'] == 'Closed':
        #         course['available'] = 0
        #     else:
        #         course['available'] = int(course['available'])
        #     course_object, created = Course.objects.update_or_create(crn=crn, defaults=course)

        # TODO remove to improve performance and speed so the http doesnt time out while we figure out actual tasks
        # course_object.lecture = None
        # course_object.discussion = None
        # if course.get('lecture_crn'):
        #     lecture, created = Course.objects.update_or_create(crn=course.get('lecture_crn'))
        #     course_object.lecture = lecture
        # if course.get('discussion_crn'):
        #     discussion, created = Course.objects.update_or_create(crn=course.get('discussion_crn'))
        #     course_object.discussion = discussion
        # print(course_object.crn)
        # course_object.save()"""
