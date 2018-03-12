def convertTime(s):
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
    return { "start": int(startTime[0] + startTime[1]), "end": int(endTime[0] + endTime[1]) }

def getAllCoursesForCourseID(id):
    courses = { "cse120":[{"course_id": "cse-120-01", "type": "LECT", "crn": 1}, {"course_id": "cse-120-02L", "type": "LAB", "crn": 2, "lecture_crn":1}, {"course_id": "cse-120-03L", "type": "LAB", "crn": 3, "lecture_crn":1}], "cse150":[{"course_id": "cse-150-01", "type": "LECT", "crn": 4}, {"course_id": "cse-150-02L", "type": "LAB", "crn": 5, "lecture_crn":4}, {"course_id": "cse-150-03L", "type": "LAB", "crn": 6, "lecture_crn":4}]}
    return courses[id]

def getCourse(crn, courses):
    for c in courses:
        if crn == c["crn"]:
            return c

def getSections(courses):
    sections = {}
    for c in courses:
        if c["type"] != "LECT":
            classid = c["course_id"].split("-")[2][0:2]
            if  classid not in sections:
                sections[classid] = {"LECT": None, "DISC": None, "LAB": None}
            if c["type"] == "DISC":
                sections[classid]["DISC"] = c
            elif c["type"] == "LAB":
                sections[classid]["LAB"] = c
    for sKey in sections:
        section = sections[sKey]
        if section["DISC"] != None:
            section["LECT"] = getCourse(section["DISC"]["lecture_crn"], courses)
        elif section["LAB"] != None:
            section["LECT"] = getCourse(section["LAB"]["lecture_crn"], courses)
    return sections

def generateSchedules(courseIDs):
    classes = {}
    
    for id in courseIDs:
        subCourses = getAllCoursesForCourseID(id)
        classes[id] = getSections(subCourses)
    # classes = ["id1":{02:{Lect, Lab, Disc}, 03:{Lect, Lab, Disc}}, "id2":{02:{Lect, Lab, Disc}, 03:{Lect, Lab, Disc}}]

    n=1
    for c in classes:    # calculate number of permutations
        n *= len(classes[c])

    permutations = [{} for i in range(n)]

    for i in range(len(permutations)):        # this is what makes all possible combinations
        n=1
        for c in classes:
            sectionKey = classes[c].keys()[i/n % len(classes[c])]
            permutations[i][c] = classes[c][sectionKey]
            n *= len(c)
    return permutations

perms = generateSchedules(["cse120", "cse150"])
for p in perms:
    print p
