from course_api.models import Course
from course_api.serializers import CourseSerializer


def get_courses(courses_to_search, term, search_full=False):
    courses = dict()
    for course in courses_to_search:
        if not search_full:
            courses[course] = [CourseSerializer(course).data for course in
                               Course.objects.filter(simple_name__iexact=course, term=term, available__gt=0)]
        else:
            courses[course] = [CourseSerializer(course).data for course in
                               Course.objects.filter(simple_name__iexact=course, term=term)]
    return courses
