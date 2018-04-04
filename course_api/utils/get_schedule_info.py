def getInfoForSchedule(schedule):
    times = {"M": [], "T": [], "W": [], "R": [], "F": [], "S": []}
    earliest = 2400
    latest = 0000

    for key, section in schedule.items():
        for key, course in section.items():
            if course and course["hours"] != "TBD-TBD":
                for day in course["days"]:
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

    info = {"number_of_days": numOfDays, "earliest": earliest, "latest": latest, "gaps": gapSize}
    return info


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
