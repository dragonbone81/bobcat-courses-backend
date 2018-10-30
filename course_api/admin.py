from django.contrib import admin
from course_api.models import Course, Schedule, SubjectCourse, Terms, School, Notifications, Waitlist, Statistics
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from course_api.models import ScheduleUser


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class ScheduleUserInline(admin.StackedInline):
    model = ScheduleUser
    can_delete = False
    verbose_name_plural = 'Schedule Users'
    verbose_name = 'Schedule User'


class NotificationsInline(admin.StackedInline):
    model = Notifications
    can_delete = False
    verbose_name_plural = 'Notifications'
    verbose_name = 'Notification'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ScheduleUserInline, NotificationsInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    list_display = ('crn', 'subject', 'type', 'course_name', 'course_id', 'course_name', 'course_name', 'term')
    search_fields = ['crn', 'subject', 'type', 'course_name', 'course_id', 'course_name', 'course_name', 'term']


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'term')
    search_fields = ['user__username', 'user__first_name', 'user__last_name', ]


class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('course', 'get_users')
    search_fields = ['school', 'course', 'users__username', ]


class SubjectClassAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'term')
    search_fields = ('course_name', 'term')


class TermsAdmin(admin.ModelAdmin):
    list_display = ('school',)
    search_fields = ('school',)


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('school_id',)
    search_fields = ('school_id',)


admin.site.register(Course, CourseAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(SubjectCourse, SubjectClassAdmin)
admin.site.register(Terms, TermsAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Waitlist, WaitlistAdmin)
admin.site.register(Statistics)
