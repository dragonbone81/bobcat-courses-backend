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
                if not dayConflicts(time, times[day], is_event=True):
                    times[day].append(time)
                else:
                    return True
        elif c["hours"] != "TBD-TBD":
            for day in c.get("days"):
                time = convertTime(c["hours"])
                if not dayConflicts(time, times[day]):
                    times[day].append(time)
                else:
                    return True
    return False


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
            time = convertTime(c["final_hours"])
            if not dayConflicts(time, finals[day]):
                finals[day].append(time)
            else:
                return True
        c['final_days'] = ''.join(c['final_days'])
        if c['final_days'] == "":
            c['final_days'] = None
    return False



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
                        time = convertTime(course["hours"])
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
            "hasConflictingFinals": hasConflictingFinals(schedule)}
    return info


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


def getNthPermutation(classes, i):
    permutation = {}
    multiplier = 1
    for class_id, data in classes.items():  # Go through all classes and add the relevant section
        section = list(data)[int((i / multiplier + (i if multiplier > 1 else 0)) % len(data))]
        permutation[class_id] = data[section]
        multiplier *= len(data)
    return permutation


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


def get_full_permutation(filters, earliest_time, latest_time, ordered_classes, i):
    permutation = getNthPermutation(ordered_classes, i)
    if not hasConflict(permutation):
        info = getInfoForSchedule(permutation)
        if filters:
            if earliest_time and info.get('earliest') < earliest_time:
                return False
            if latest_time and info.get('latest') > latest_time:
                return False
        schedule = dict()
        schedule["schedule"] = permutation
        schedule["info"] = info
        # sorry max I need this for sorting :*(
        if filters:
            schedule['number_of_days'] = info['number_of_days']
            schedule['earliest'] = info['earliest']
            schedule['latest'] = info['latest']
            schedule['gaps'] = info['gaps']
        return schedule
    return False
