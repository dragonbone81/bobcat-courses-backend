from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    data = dictionary.get(key)
    if data:
        data['exists'] = True

    else:
        data = {'length': 1, 'exists': False}
    return data
