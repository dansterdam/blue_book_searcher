# cases/search_indexes.py
from haystack import indexes
from .models import Case


class CaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    location = indexes.CharField(model_attr="location")
    date = indexes.CharField(model_attr="date")
    witness_description = indexes.CharField(model_attr="witness_description")


    def get_model(self):
        return Case

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
