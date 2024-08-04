from django.core.management.base import BaseCommand
from your_app.backends import CustomElasticsearchSearchBackend

class Command(BaseCommand):
    help = 'Setup the Elasticsearch index'

    def handle(self, *args, **kwargs):
        connection_alias = 'default'  # Adjust if you have a different alias
        backend = CustomElasticsearchSearchBackend(connection_alias)
        backend.setup_index()
        self.stdout.write(self.style.SUCCESS('Index setup complete'))
