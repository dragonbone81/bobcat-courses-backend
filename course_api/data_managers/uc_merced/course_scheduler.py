from course_api.utils.get_courses_base_on_simple_name import get_courses
from operator import itemgetter
from collections import OrderedDict


class CourseScheduler(object):
    def __init__(self, term, earliest_time=None, latest_time=None, gaps='asc', days='asc', search_full=False,
                 filters=False, bad_crns=None):
        self.term = term
        self.earliest_time = earliest_time
        self.latest_time = latest_time
        self.gaps = gaps
        self.days = days
        self.search_full = search_full
        self.filters = filters
        self.bad_crns = bad_crns

    @staticmethod
    def convertTime(s):
        t = s.split("-")  # separate start and end times
        startTime = t[0].split(":")
        endTime = t[1].split(":")
        if "pm" in endTime[1]:  # if pm appears in the end time
            if endTime[0] != "12":  # if the end time is not 12:xx
                endTime[0] = str(int(endTime[0]) + 12)  # add 12 hours
            if startTime[0] != "12":  # if the start time is not 12
                startTime[0] = str(int(startTime[0]) + 12)  # add 12 hours
        endTime[1] = endTime[1][0:2]  # cut out the am or pm
        if int(startTime[0]) > int(endTime[0]):  # if for some reason it starts (it means it started in the morning
            startTime[0] = str(int(startTime[0]) - 12)  # remove 12 hours
        return {"start": int(startTime[0] + startTime[1]), "end": int(endTime[0] + endTime[1])}  # return {start, end}

    def getCourse(self, crn, courses):  # Is there a better way?
        for c in courses:
            if crn == c["crn"]:
                return c

    def getSections(self, courses):
        sections = {}  # Create a dictionary of sections
        for c in courses:  # Go through all the courses of one class
            if c["type"] != "LECT":  # If it is not a lecture
                classid = c["course_id"].split("-")[2][0:2]  # Calculate the section ID
                if classid not in sections:  # If no section exists for this ID,
                    sections[classid] = {}  # Create it
                sections[classid][c["type"]] = c  # Add this course to the section
        for sKey in sections:  # Go through all sections
            section = sections[sKey]
            if "DISC" in section:  # if there is a disc or lab in the section link its lecture
                section["LECT"] = self.getCourse(section["DISC"]["lecture_crn"], courses)
            elif "LAB" in section:
                section["LECT"] = self.getCourse(section["LAB"]["lecture_crn"], courses)
        if sections == {}:
            for c in courses:
                classid = c["course_id"].split("-")[2][0:2]
                sections[classid] = {"LECT": c}
        return sections  # return the sections

    @staticmethod
    def getNthPermutation(classes, i):
        permutation = {}
        multiplier = 1
        for class_id, data in classes.items():  # Go through all classes and add the relevant section
            section = list(data)[int((i / multiplier + (i if multiplier > 1 else 0)) % len(data))]
            permutation[class_id] = data[section]
            multiplier *= len(data)
        return permutation

    @staticmethod
    def dayConflicts(time, day, is_event=False):
        for t in day:  # Go though all the times that are already in the day
            if is_event:
                if time["start"] >= t["start"] and time["start"] < t["end"]:
                    return True  # if the course we want to add starts during a registered course -> Conflict
                if time["end"] > t["start"] and time["end"] < t["end"]:
                    return True  # if the course we want to add ends during a registered course -> Conflict
                if t["start"] >= time["start"] and t["start"] < time["end"]:
                    return True  # if a registered course starts during the course we want to add -> Conflict
                if t["end"] > time["start"] and t["end"] < time["end"]:
                    return True  # if a registered course ends during the course we want to add -> Conflict
            else:
                if time["start"] >= t["start"] and time["start"] <= t["end"]:
                    return True  # if the course we want to add starts during a registered course -> Conflict
                if time["end"] >= t["start"] and time["end"] <= t["end"]:
                    return True  # if the course we want to add ends during a registered course -> Conflict
                if t["start"] >= time["start"] and t["start"] <= time["end"]:
                    return True  # if a registered course starts during the course we want to add -> Conflict
                if t["end"] >= time["start"] and t["end"] <= time["end"]:
                    return True  # if a registered course ends during the course we want to add -> Conflict
        return False  # No conflict

    @staticmethod
    def hasConflict(schedule):
        times = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        finals = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        allCourses = []
        for c in schedule:
            for type in schedule[c]:
                return_val = schedule[c][type]
                if return_val:
                    allCourses.append(return_val)
        for c in allCourses:
            if not c.get('hours') and c.get('start_time') and c.get('end_time'):
                for day in c.get("days"):
                    time = {"start": c["start_time"], "end": c["end_time"]}
                    if not CourseScheduler.dayConflicts(time, times[day], is_event=True):
                        times[day].append(time)
                    else:
                        return True
            elif c["hours"] != "TBD-TBD":
                for day in c.get("days"):
                    time = CourseScheduler.convertTime(c["hours"])
                    if not CourseScheduler.dayConflicts(time, times[day]):
                        times[day].append(time)
                    else:
                        return True
        return False

    @staticmethod
    def hasConflictingFinals(schedule):
        times = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        finals = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        allCourses = []
        for c in schedule:
            for type in schedule[c]:
                return_val = schedule[c][type]
                if return_val:
                    allCourses.append(return_val)
        for c in allCourses:
            if not c.get('final_days'):
                c['final_days'] = []
            for day in c.get("final_days", []):
                time = CourseScheduler.convertTime(c["final_hours"])
                if not CourseScheduler.dayConflicts(time, finals[day]):
                    finals[day].append(time)
                else:
                    return True
            c['final_days'] = ''.join(c['final_days'])
            if c['final_days'] == "":
                c['final_days'] = None
        return False

    @staticmethod
    def getInfoForSchedule(schedule):
        times = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        earliest = 2400
        latest = 0000

        for key, section in schedule.items():
            for key, course in section.items():
                if course and course.get("hours") != "TBD-TBD" or course and course.get('start_time') and course.get(
                        'end_time'):
                    for day in course["days"]:
                        if course.get('start_time') and course.get('end_time'):
                            time = {"start": course["start_time"], "end": course["end_time"]}
                        else:
                            time = CourseScheduler.convertTime(course["hours"])
                        times[day].append(time)
                        if time["start"] < earliest:
                            earliest = time["start"]
                        if time["end"] > latest:
                            latest = time["end"]

        gapSize = 0
        numOfDays = 0

        for day in times:
            list = sorted(times[day], key=lambda x: x["start"], reverse=False)
            if len(list) > 0:
                numOfDays = numOfDays + 1
            for i in range(1, len(list)):
                gapSize = gapSize + list[i]["start"] - list[i - 1]["end"]

        info = {"number_of_days": numOfDays, "earliest": earliest, "latest": latest, "gaps": gapSize,
                "hasConflictingFinals": CourseScheduler.hasConflictingFinals(schedule)}
        return info

    # @staticmethod
    # def get_full_permutation(filters, earliest_time, latest_time, ordered_classes, i):
    #     permutation = CourseScheduler.getNthPermutation(ordered_classes, i)
    #     if not CourseScheduler.hasConflict(permutation):
    #         info = CourseScheduler.getInfoForSchedule(permutation)
    #         if filters:
    #             if earliest_time and info.get('earliest') < earliest_time:
    #                 return False
    #             if latest_time and info.get('latest') > latest_time:
    #                 return False
    #         schedule = dict()
    #         schedule["schedule"] = permutation
    #         schedule["info"] = info
    #         # sorry max I need this for sorting :*(
    #         if filters:
    #             schedule['number_of_days'] = info['number_of_days']
    #             schedule['earliest'] = info['earliest']
    #             schedule['latest'] = info['latest']
    #             schedule['gaps'] = info['gaps']
    #         return schedule
    #     return False

    def get_valid_schedules(self, courses, custom_events=list()):
        schedules = list()
        classes = {}
        course_data = get_courses(courses, self.term, search_full=self.search_full, bad_crns=self.bad_crns)
        for id in courses:  # Create a dictionary that contains all classes (each contains all their sections)
            subCourses = course_data[id]  #
            classes[id] = self.getSections(subCourses)  #
        del course_data
        if len(custom_events) > 0:
            classes['custom_events'] = {'0': {}}
            for event in custom_events:
                classes['custom_events']['0'][event['event_name']] = event
        ordered_classes = OrderedDict(
            sorted(sorted(classes.items(), key=lambda course: len(course[1].keys())), key=lambda course: course[0],
                   reverse=True))  # sorted first by length of keys then alphabetical
        maxNumberOfPerms = 1
        for class_id, data in ordered_classes.items():  # Calculate number of possible permutations
            maxNumberOfPerms *= len(data)

        numberOfValidSchedules = 50
        # schedules = self.get_full_permutation(numberOfValidSchedules, maxNumberOfPerms, ordered_classes)
        i = 0
        actualLength = 0
        from multiprocessing import Pool
        pool = Pool(100)
        from course_api.data_managers.uc_merced.test import get_full_permutation
        while actualLength < numberOfValidSchedules and i < maxNumberOfPerms:
            while len(schedules) < 1000 and i < maxNumberOfPerms:
                # print(i)
                schedule = pool.apply_async(get_full_permutation,
                                            (self.filters, self.earliest_time, self.latest_time, ordered_classes, i))
                # print(schedule.get())
                # schedule = self.get_full_permutation(ordered_classes, i)
                if schedule:
                    schedules.append(schedule)
                i = i + 1
            # print(schedules)
            schedules = [schedule.get() if not isinstance(schedule, dict) else schedule for schedule in schedules]
            schedules = [schedule for schedule in schedules if schedule]
            actualLength = len(schedules)
            print(actualLength)
            # print(schedules)
        if self.filters:
            if self.days == 'desc' and not self.gaps:
                schedules = sorted(schedules, key=itemgetter('number_of_days'), reverse=True)
            elif self.days == 'asc' and not self.gaps:
                schedules = sorted(schedules, key=itemgetter('number_of_days'), reverse=False)
            elif self.gaps == 'desc' and not self.days:
                schedules = sorted(schedules, key=itemgetter('gaps'), reverse=True)
            elif self.gaps == 'asc' and not self.days:
                schedules = sorted(schedules, key=itemgetter('gaps'), reverse=False)
            elif self.days == 'desc' and self.gaps == 'desc':
                schedules = sorted(schedules, key=itemgetter('number_of_days', 'gaps'), reverse=True)
            elif self.days == 'asc' and self.gaps == 'desc':
                schedules = sorted(schedules, key=itemgetter('gaps'), reverse=True)
                schedules = sorted(schedules, key=itemgetter('number_of_days'), reverse=False)
            elif self.days == 'desc' and self.gaps == 'asc':
                schedules = sorted(schedules, key=itemgetter('gaps'), reverse=False)
                schedules = sorted(schedules, key=itemgetter('number_of_days'), reverse=True)
            elif self.days == 'asc' and self.gaps == 'asc':
                schedules = sorted(schedules, key=itemgetter('number_of_days', 'gaps'), reverse=False)
        schedule_output = []
        for schedule in schedules:
            courses = {key: [sections_object for type_key, sections_object in course.items() if sections_object] for
                       key, course in
                       schedule.get('schedule').items() if key != 'custom_events'}
            schedule_output.append({'schedule': courses, 'info': schedule['info'],
                                    'custom_events': [sections_object for type_key, sections_object in
                                                      schedule['schedule'].get('custom_events', {}).items() if
                                                      sections_object]})
        return schedule_output
