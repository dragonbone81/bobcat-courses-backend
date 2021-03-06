from django.db import models
from django.contrib.auth.models import User
from json import loads as json_loads


class Statistics(models.Model):
    schedules_generated = models.IntegerField(
        verbose_name="Schedules Generated",
        db_index=True,
    )


class ScheduleUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='profiles/images', blank=True, null=True)

    def get_profile_image_url(self):
        url = None
        if self.profile_image:
            url = self.profile_image.url
        return url

    def __str__(self):
        return self.user.username


class SubjectCourse(models.Model):
    class Meta:
        verbose_name = "Subject Class"
        verbose_name_plural = "Subject Classes"
        unique_together = ("course_name", "term")

    course_name = models.CharField(
        verbose_name="Course Name",
        max_length=256,
        db_index=True,
    )
    term = models.CharField(
        null=False,
        blank=False,
        db_index=True,
        max_length=32,
        verbose_name="Term",
        default="201810",
    )
    course_description = models.CharField(
        verbose_name="Course Description",
        max_length=256,
        db_index=True,
        null=True,
    )
    course_subject = models.CharField(
        verbose_name="Course Subject",
        max_length=256,
        db_index=True,
        null=True,
    )

    def __str__(self):
        return "{}:{}".format(self.course_name, self.term)


class Schedule(models.Model):
    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"

    courses = models.TextField(
        verbose_name="Courses",
        default='[]',
    )
    user_events = models.TextField(
        verbose_name="User Events",
        default='[]',
    )
    user = models.ForeignKey(
        User,
        verbose_name="Schedule User",
        null=False,
        blank=False,
        db_index=True,
        on_delete=models.CASCADE,
    )
    term = models.CharField(
        null=False,
        blank=False,
        db_index=True,
        max_length=32,
        verbose_name="Term",
        default="201810",
    )
    created = models.DateTimeField(
        verbose_name="Created",
        db_index=True,
        auto_now_add=True,
    )
    finals_conflict = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Finals Conflict?',
    )
    enrolled = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Enrolled',
    )

    def __str__(self):
        return "Schedule: {} - {}".format(self.user, self.pk)


class Course(models.Model):
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    crn = models.CharField(
        primary_key=True,
        max_length=32,
        db_index=True,
        verbose_name="CRN",
    )
    subject = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Subject",
    )
    course_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Course ID",
    )
    course_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Course Name",
    )
    units = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Units",
    )
    type = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Type",
    )
    days = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
    )
    hours = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
    )
    room = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
    )
    dates = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    instructor = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Instructor",
    )
    # TODO needs work
    lecture = models.ForeignKey(
        'Course',
        related_name='course_lecture',
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Associated Lecture",
        on_delete=models.CASCADE
    )
    lecture_crn = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Lecture CRN",
    )
    discussion = models.ForeignKey(
        'Course',
        related_name='course_discussion',
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Associated Discussion",  # Used for linked labs
        on_delete=models.CASCADE
    )
    attached_crn = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Attached CRN",
    )
    term = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Term",
    )
    capacity = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Capacity",
    )
    enrolled = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Enrolled",
    )
    available = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Available",
    )
    # TODO needs be reworked for labs
    final_type = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_days = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_hours = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_room = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_dates = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    simple_name = models.CharField(
        verbose_name="Simple Name",
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    linked_courses = models.TextField(
        verbose_name="Linked Courses",
        default='[]',
    )

    def to_dict(self):
        return {
            'crn': self.crn,
            'subject': self.subject,
            'course_id': self.course_id,
            'course_name': self.course_name,
            'units': self.units,
            'type': self.type,
            'days': self.days,
            'hours': self.hours,
            'room': self.room,
            'dates': self.dates,
            'instructor': self.instructor,
            'lecture_crn': self.lecture_crn,
            'attached_crn': self.attached_crn,
            'term': self.term,
            'capacity': self.capacity,
            'enrolled': self.enrolled,
            'available': self.available,
            'simple_name': self.simple_name,
            'final_days': self.final_days,
            'final_hours': self.final_hours,
            'linked_courses': json_loads(self.linked_courses),
        }

    def __str__(self):
        return self.course_id or self.crn


class Terms(models.Model):
    class Meta:
        verbose_name = "Term"
        verbose_name_plural = "Terms"

    terms = models.TextField(
        verbose_name="Terms",
        default='[]',
    )
    school = models.CharField(
        verbose_name="School",
        max_length=64,
        primary_key=True,
    )


class School(models.Model):
    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

    school_id = models.CharField(
        verbose_name="School",
        max_length=64,
        primary_key=True,
    )


class Notifications(models.Model):
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    user = models.OneToOneField(
        User,
        verbose_name="User",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    # max of 20, will overwrite when new is made?
    notifications = models.TextField(
        verbose_name="Notifications",
        default='[]',
        # {'seen': False,'email_sent':False, 'type': 'some_type'
        # , 'id': 0, 'time': 'now()', 'data': {'message': 'whatevs' or 'crn': '12345'}}
    )
    email_alerts = models.BooleanField(
        verbose_name="Email Alerts",
        default=True,
    )


class Waitlist(models.Model):
    class Meta:
        verbose_name = "Waitlist"
        verbose_name_plural = "Waitlists"
        unique_together = ('school', 'course')

    school = models.CharField(
        max_length=64,
        verbose_name='School',
        null=False,
        blank=False,
    )
    course = models.OneToOneField(
        'Course',
        verbose_name='Course',
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    users = models.ManyToManyField(
        User,
        verbose_name='Subscribed Users',
    )
    expired = models.BooleanField(  # alerted when waitlist is finished
        default=False,
        verbose_name='Expired',
    )

    def get_users(self):
        return self.users.count()

    def __str__(self):
        return f"{self.school}:{self.course.crn}"
