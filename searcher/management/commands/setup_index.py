from django.core.management.base import BaseCommand
from searcher.backends import CustomElasticsearchSearchBackend

class Command(BaseCommand):
    help = 'Setup the Elasticsearch index'

    def handle(self, *args, **kwargs):
        backend = CustomElasticsearchSearchBackend()
        backend.setup_index()
        self.stdout.write(self.style.SUCCESS('Index setup complete'))
