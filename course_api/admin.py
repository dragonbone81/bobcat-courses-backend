from django.contrib import admin
from course_api.models import Course


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    fields = ['crn', 'subject', 'course_name']
    search_fields = ['crn', 'subject', 'course_name']


admin.site.register(Course, CourseAdmin)
