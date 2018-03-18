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


def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return int(minimum)
    if val > maximum:
        return int(maximum)
    return int(val)


def colorscale(hexstr, scalefactor):
    hexstr = hexstr.strip('#')

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)

    return "#%02x%02x%02x" % (r, g, b)
