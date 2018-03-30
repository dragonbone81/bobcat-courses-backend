from django.db import models
from django.contrib.auth.models import User


class ScheduleUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='profiles/images', blank=True, null=True)

    def __str__(self):
        return self.user.username


class SubjectClass(models.Model):
    class Meta:
        verbose_name = "Subject Class"
        verbose_name_plural = "Subject Classes"

    course_name = models.CharField(
        verbose_name="Course Name",
        max_length=256,
        primary_key=True,
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
    course_subject = models.CharField(
        verbose_name="Course Subject",
        max_length=256,
        db_index=True,
        null=True,
    )


class Schedule(models.Model):
    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"

    courses = models.TextField(
        verbose_name="Courses",
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
    discussion_crn = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Discussion CRN",
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
    final_type_2 = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_days_2 = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_hours_2 = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_room_2 = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    final_dates_2 = models.CharField(
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

    def __str__(self):
        return self.course_id or self.crn
