# Generated by Django 2.0.3 on 2018-04-02 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_api', '0015_scheduleuser_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='subjectcourse',
            name='course_description',
            field=models.CharField(db_index=True, max_length=256, null=True, verbose_name='Course Description'),
        ),
    ]
