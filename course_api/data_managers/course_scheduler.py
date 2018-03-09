def convert2400(s):
    time = s.split(":")
    hour = time[0]
    minute = time[1]
    if "pm" in minute and hour != "12":
        hour = str(int(hour) + 12)
    elif "am" in minute and hour == "12":
        hour = str(int(hour) - 12)
    minute = minute[0:2]
    return int(hour + minute)

def generateSections(courses):
    sections = {} # { math-022: {02: {}, 03: {}, 21: {}, 22: {}}, phys-008: {02: {}, 03: {}, 21: {}, 22: {}} }
    for courseID in courses:
        dict = {}
        types = []
        for c in courses[courseID]:
            if c['type'] not in types:
                types.append(c['type'])
        print(types)









courses = {
    "CSE-120": [
                {
                "crn": "15911",
                "subject": "Computer Science & Engineering",
                "course_id": "CSE-120-02L",
                "course_name": "Software Engineering",
                "units": 0,
                "type": "LAB",
                "days": "M",
                "hours": "7:30-10:20am",
                "room": "CLSSRM 281",
                "dates": "16-JAN 04-MAY",
                "instructor": "Lee",
                "lecture_crn": "15910",
                "discussion_crn": None,
                "term": "201810",
                "capacity": 20,
                "enrolled": 16,
                "available": 4,
                "final_type": None,
                "final_days": None,
                "final_hours": None,
                "final_room": None,
                "final_dates": None,
                "final_type_2": None,
                "final_days_2": None,
                "final_hours_2": None,
                "final_room_2": None,
                "final_dates_2": None,
                "lecture": None,
                "discussion": None
                },
                {
                "crn": "15910",
                "subject": "Computer Science & Engineering",
                "course_id": "CSE-120-01",
                "course_name": "Software Engineering",
                "units": 4,
                "type": "LECT",
                "days": "WF",
                "hours": "12:00-1:15pm",
                "room": "COB2 140",
                "dates": "16-JAN 04-MAY",
                "instructor": "Leung",
                "lecture_crn": None,
                "discussion_crn": None,
                "term": "201810",
                "capacity": 40,
                "enrolled": 22,
                "available": 18,
                "final_type": "EXAM",
                "final_days": "M",
                "final_hours": "3:00-6:00pm",
                "final_room": "COB2 140",
                "final_dates": "07-MAY 07-MAY",
                "final_type_2": None,
                "final_days_2": None,
                "final_hours_2": None,
                "final_room_2": None,
                "final_dates_2": None,
                "lecture": None,
                "discussion": None
                },
                {
                "crn": "15912",
                "subject": "Computer Science & Engineering",
                "course_id": "CSE-120-03L",
                "course_name": "Software Engineering",
                "units": 0,
                "type": "LAB",
                "days": "M",
                "hours": "10:30-1:20pm",
                "room": "CLSSRM 281",
                "dates": "16-JAN 04-MAY",
                "instructor": "Rakhmetulla",
                "lecture_crn": "15910",
                "discussion_crn": None,
                "term": "201810",
                "capacity": 20,
                "enrolled": 6,
                "available": 14,
                "final_type": None,
                "final_days": None,
                "final_hours": None,
                "final_room": None,
                "final_dates": None,
                "final_type_2": None,
                "final_days_2": None,
                "final_hours_2": None,
                "final_room_2": None,
                "final_dates_2": None,
                "lecture": None,
                "discussion": None
                }
                ]
}
generateSections(courses)
