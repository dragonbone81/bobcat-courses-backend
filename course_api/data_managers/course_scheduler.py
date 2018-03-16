from course_api.utils.get_courses_base_on_simple_name import get_courses


class CourseScheduler(object):
    def __init__(self, term, earliest_time=None, latest_time=None, gaps='asc', days='asc'):
        self.term = term
        self.earliest_time = earliest_time
        self.latest_time = latest_time
        self.gaps = gaps
        self.days = days

    def convertTime(self, s):
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

    def generateSchedules(self, courseIDs):
        classes = {}
        course_data = get_courses(courseIDs, self.term)  #
        for id in courseIDs:  # Create a dictionary that contains all classes (each contains all their sections)
            subCourses = course_data[id]  #
            classes[id] = self.getSections(subCourses)  #
        n = 1
        for class_id, data in classes.items():  # Calculate number of possible permutations
            n *= len(data)

        permutations = [{} for i in range(n)]  # Create an array to contain all possible schedules

        for i in range(len(permutations)):  # This is what makes all possible combinations
            n = 1
            for class_id, data in classes.items():  # Go through all classes and add the relevant section
                section = list(classes[class_id].items())[int(i / n % len(classes[class_id]))]
                permutations[i][class_id] = classes[class_id][section[0]]
                n *= len(classes[class_id])
        return permutations

    def dayConflicts(self, time, day):
        for t in day:  # Go though all the times that are already in the day
            if time["start"] >= t["start"] and time["start"] <= t["end"]:
                return True  # if the course we want to add starts during a registered course -> Conflict
            if time["end"] >= t["start"] and time["end"] <= t["end"]:
                return True  # if the course we want to add ends during a registered course -> Conflict
        return False  # No conflict

    def hasConflict(self, schedule):
        times = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        finals = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        allCourses = []
        for c in schedule:
            for type in schedule[c]:
                allCourses.append(schedule[c][type])

        for c in allCourses:
            for day in c["days"]:
                time = self.convertTime(c["hours"])
                if not self.dayConflicts(time, times[day]):
                    times[day].append(time)
                else:
                    return True
            if not c['final_days']:
                c['final_days'] = []
            for day in c.get("final_days", []):
                time = self.convertTime(c["final_hours"])
                if not self.dayConflicts(time, finals[day]):
                    finals[day].append(time)
                else:
                    return True
        return False

    def getInfoForSchedule(self, schedule):
        times = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
        earliest = 2400
        latest = 0000

        for key, section in schedule.items():
            for key, course in section.items():
                for day in course["days"]:
                    time = self.convertTime(course["hours"])
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

        info = {"number_of_days": numOfDays, "earliest": earliest, "latest": latest, "gaps": gapSize}
        return info

    def get_valid_schedules(self, courses):
        schedules = list()
        permutations = self.generateSchedules(courses)
        for permutation in permutations:
            if not self.hasConflict(permutation):
                info = self.getInfoForSchedule(permutation)
                if self.earliest_time and info.get('earliest') < self.earliest_time:
                    continue
                if self.latest_time and info.get('latest') > self.latest_time:
                    continue
                schedule = {"schedule": permutation, "info": info}
                schedules.append(schedule)
        if self.days == 'desc' and self.gaps == 'desc':
            schedules = sorted(schedules,
                               key=lambda info_dict: (info_dict['info']['gaps'], info_dict['info']['number_of_days']),
                               reverse=False)
        elif self.days == 'asc' and self.gaps == 'desc':
            schedules = sorted(schedules,
                               key=lambda info_dict: (info_dict['info']['gaps'], -info_dict['info']['number_of_days']))
        elif self.days == 'desc' and self.gaps == 'asc':
            schedules = sorted(schedules,
                               key=lambda info_dict: (-info_dict['info']['gaps'], info_dict['info']['number_of_days']))
        elif self.days == 'asc' and self.gaps == 'asc':
            schedules = sorted(schedules,
                               key=lambda info_dict: (info_dict['info']['gaps'], info_dict['info']['number_of_days']),
                               reverse=False)

        return schedules
