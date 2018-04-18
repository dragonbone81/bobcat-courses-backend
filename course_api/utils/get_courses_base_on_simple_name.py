from course_api.models import Course
from django.db.models import Q


def get_courses(courses_to_search, term, search_full=False, bad_crns=False):
    courses = {course: [] for course in courses_to_search}
    crn_dict = dict()
    if not search_full:
        total_courses = Course.objects.filter(~Q(crn__in=bad_crns), simple_name__in=courses_to_search, term=term,
                                              available__gt=0)
    else:
        total_courses = Course.objects.filter(~Q(crn__in=bad_crns), simple_name__in=courses_to_search, term=term)
    for course in total_courses:
        crn_dict[course.crn] = course.simple_name
        courses[course.simple_name].append({
            'crn': course.crn,
            'type': course.type,
            'course_id': course.course_id,
            'lecture_crn': course.lecture_crn,
            'hours': course.hours,
            'days': course.days,
            'final_days': course.final_days,
            'final_hours': course.final_hours,
            'simple_name': course.simple_name,
            'subject': course.subject,
            'course_name': course.course_name,
            'term': course.term,
            'capacity': course.capacity,
            'enrolled': course.enrolled,
            'available': course.available,
            'instructor': course.instructor,
            'units': course.units,
        })
    return courses
