from course_api.models import Terms
import json


class UpdateTerms(object):
    def __init__(self, school_id, terms):
        self.school_id = school_id
        self.terms = terms

    def update_model(self):
        terms_obj, created = Terms.objects.get_or_create(school=self.school_id)
        terms_obj.terms = json.dumps(list(set(self.terms)))
        terms_obj.save()
