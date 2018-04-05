from html.parser import HTMLParser
from urllib.request import urlopen


# moisonmaxime
class UCMercedParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.starts = []
        self.data = []
        self.toIgnore = ['CRN', 'Course #', 'Course Title', 'Units', 'Actv', 'Days', 'Time', 'Bldg/Rm', 'Start - End',
                         'Instructor', 'Max Enrl', 'Act Enrl', 'Seats Avail', 'Skip to top of page', 'Search Courses']
        self.passes = 0

    def handle_starttag(self, tag, attrs):
        self.starts.append(tag)

    def handle_endtag(self, tag):
        self.starts.pop()

    def handle_data(self, data):
        if len(self.starts) < 1:
            return
        if data in self.toIgnore:
            return

        if self.starts[len(self.starts) - 1] == 'h3':
            if data == "&":
                self.data[len(self.data) - 1][0] = self.data[len(self.data) - 1][0] + data
                self.passes = 1
            else:
                if self.passes == 0:
                    self.data.append(["startsubject", "separator"])
                    self.data.append([data, "subject"])
                else:
                    self.data[len(self.data) - 1][0] = self.data[len(self.data) - 1][0] + data
                    self.passes -= 1

        if self.starts[len(self.starts) - 1] == 'a':
            self.data.append(["startcourse", "separator"])
            self.data.append([data, "crn"])

        if self.starts[len(self.starts) - 1] == 'small':
            if data == "&":
                self.data[len(self.data) - 1][0] = self.data[len(self.data) - 1][0] + data
                self.passes = 1
            else:
                if self.passes == 0:
                    self.data.append([data, "info"])
                else:
                    self.data[len(self.data) - 1][0] = self.data[len(self.data) - 1][0] + data
                    self.passes -= 1


class UCMercedClassParser(object):
    def __init__(self, terms):
        self.parser = UCMercedParser()
        self.terms = terms  # I guess its year|semester (201810, 201730)

    def parse_terms(self):
        data = list()
        for term in self.terms:
            data += self.parse(term)
        return data

    def parse(self, term):
        self.parser.data = []
        """
        OK this is FUCKING CRAZY the data from the parser stays even if we make a new instance 
        even if we make a new instance of ClassParser...the most bizarre thing ever
        """
        s = urlopen(
            "https://mystudentrecord.ucmerced.edu/pls/PROD/xhwschedule.P_ViewSchedule?validterm={}&openclasses=N".format(
                term)).read()  # Extract from html file
        self.parser.feed(str(s))  # Parse it into data elements (subject, crn, or info)
        column = 0
        data = []
        subject = None
        previous_discussion = None  # for lab discussion correlation
        header = ["subject", "crn", "course_id", "course_name", "units", "type", "days", "hours", "room", "dates",
                  "instructor", "capacity", "enrolled", "available", "final_type", "final_days", "final_hours",
                  "final_room",
                  "final_dates", "final_type_2", "final_days_2", "final_hours_2", "final_room_2", "final_dates_2"]
        for info in self.parser.data:

            if info[1] == 'subject':
                subject = info[0]

            if info[1] == 'crn':
                data.append([subject])
                data[-1].append(info[0])
                column = 0

            if info[1] == 'info':
                if column == 2:
                    if len(info[0]) > 1:
                        continue
                if column == 0:
                    info[0] = info[0].replace(" ", "")
                data[-1].append(info[0].replace(",", ""))
                column += 1
                if info[0] == "TBD-TBD":
                    column += 1
        data = [dict(zip(header, line)) for line in data]
        current_lect = None
        for line in data:
            if line['type'] != 'LAB':
                previous_discussion = None
            line['term'] = term
            if line['type'] == 'DISC':
                previous_discussion = line['crn']
            if line.get('type') == 'LECT':
                current_lect = line.get('crn')
            elif line.get('type') == 'INI' or line.get('type') == 'SEM' or line.get('type') == 'FLDW':
                pass
            else:
                idParts = line['course_id'].split('-')
                if 'L' not in idParts[1]:
                    line['lecture_crn'] = current_lect
                    # this is for lab discussion linking idk if this works
                    if line['type'] == 'LAB' and previous_discussion:
                        line['attached_crn'] = previous_discussion
        return data

# print(len(UCMercedClassParser(terms=["201830", "201810", "201830", "201830"]).parse_terms()))
