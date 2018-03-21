from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item_dict(dictionary, key):
    return {'data': dictionary.get(key)}
