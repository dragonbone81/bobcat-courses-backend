def get_simple(course_id):
    simplified_name = course_id.split("-")
    simplified_name[1] = simplified_name[1].lstrip('0')
    simplified_name = "{course} {id}".format(course=simplified_name[0], id=simplified_name[1])
    return simplified_name
