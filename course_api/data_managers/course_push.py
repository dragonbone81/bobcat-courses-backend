from course_api.data_managers.course_pull import UCMercedClassParser
from course_api.models import Course


class UCMercedCoursePush(object):
    def __init__(self):
        self.data = UCMercedClassParser(term="201810").parse()

    def push_courses(self):
        for course in self.data:
            # TODO weird thing with python and not references
            crn = course.get('crn')
            course.pop('crn')
            course['units'] = int(course['units'])
            course['capacity'] = int(course['capacity'])
            course['enrolled'] = int(course['enrolled'])
            if course['available'] == 'Closed':
                course['available'] = 0
            else:
                course['available'] = int(course['available'])
            course_object, created = Course.objects.update_or_create(crn=crn, defaults=course)

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
            # course_object.save()
