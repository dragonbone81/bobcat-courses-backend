from course_api.models import Course
from django.db.models import Q


def get_courses(courses_to_search, term, search_full=False, bad_crns=None):
    courses = {course: [] for course in courses_to_search}
    if not bad_crns:
        bad_crns = list()
    crn_dict = dict()
    if not search_full:
        total_courses = Course.objects.filter(~Q(crn__in=bad_crns), simple_name__in=courses_to_search, term=term,
                                              available__gt=0)
    else:
        total_courses = Course.objects.filter(~Q(crn__in=bad_crns), simple_name__in=courses_to_search, term=term)
    for course in total_courses:
        crn_dict[course.crn] = course.simple_name
        courses[course.simple_name].append(course.to_dict())
    return courses
