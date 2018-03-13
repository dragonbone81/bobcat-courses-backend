from course_api.utils.get_courses_base_on_simple_name import get_courses

class CourseScheduler(object):
    def convertTime(self, s):       # Good to go
        t = s.split("-")
        startTime = t[0].split(":")
        endTime = t[1].split(":")
        if "pm" in endTime[1]:
            if endTime[0] != "12":
                endTime[0] = str(int(endTime[0]) + 12)
            if int(startTime[0]) < 10 and startTime[0] != "12":
                startTime[0] = str(int(startTime[0]) + 12)
        endTime[1] = endTime[1][0:2]
        if int(startTime[0]) > int(endTime[0]):
            startTime[0] = str(int(startTime[0]) - 12)
        return {"start": int(startTime[0] + startTime[1]), "end": int(endTime[0] + endTime[1])}



    def getCourse(self, crn, courses):  # Is there a better way?
        for c in courses:
            if crn == c["crn"]:
                return c



    def getSections(self, courses):
        sections = {}
        for c in courses:
            if c["type"] != "LECT":
                classid = c["course_id"].split("-")[2][0:2]
                if classid not in sections:
                    sections[classid] = {}
                if c["type"] == "DISC":
                    sections[classid]["DISC"] = c
                elif c["type"] == "LAB":
                    sections[classid]["LAB"] = c
                else:
                    sections[classid][c["type"]] = c
            for sKey in sections:
                section = sections[sKey]
                if "DISC" in section:
                    section["LECT"] = self.getCourse(section["DISC"]["lecture_crn"], courses)
                elif "LAB" in section:
                    section["LECT"] = self.getCourse(section["LAB"]["lecture_crn"], courses)
        return sections



    def generateSchedules(self, courseIDs):
        classes = {}
        course_data = get_courses(courseIDs)
        for id in courseIDs:
            subCourses = course_data[id]
            classes[id] = self.getSections(subCourses)
        n = 1
        for class_id, data in classes.items():  # calculate number of permutations
            n *= len(data)

        permutations = [{} for i in range(n)]

        for i in range(len(permutations)):  # this is what makes all possible combinations
            n = 1
            for class_id, data in classes.items():
                section = list(classes[class_id].items())[int(i / n % len(classes[class_id]))]
                permutations[i][class_id] = classes[class_id][section[0]]
                n *= len(classes[class_id])
        return permutations



    def dayConflicts(self, time, day):      # Good to go
        for t in day:
            if time["start"] >= t["start"] and time["start"] <= t["end"]:
                return True
            if time["end"] >= t["start"] and time["end"] <= t["end"]:
                return True
        return False



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



    def get_valid_schedules(self, courses):
        schedules = list()
        permutations = self.generateSchedules(courses)
        for permutation in permutations:
            if not self.hasConflict(permutation):
                schedules.append(permutation)
        return schedules
