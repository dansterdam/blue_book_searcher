from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from elasticsearch_dsl import connections

class CustomElasticsearchSearchBackend(ElasticsearchSearchBackend):
    def __init__(self, connection_alias, **kwargs):
        super().__init__(connection_alias, **kwargs)
        self.setup_index()

    def setup_index(self):
        es = connections.get_connection()
        index_name = 'haystack'

        index_body = {
            "settings": {
                "analysis": {
                    "tokenizer": {
                        "edge_ngram_tokenizer": {
                            "type": "edge_ngram",
                            "min_gram": 1,
                            "max_gram": 20,
                            "token_chars": ["letter", "digit"]
                        }
                    },
                    "analyzer": {
                        "edge_ngram_analyzer": {
                            "type": "custom",
                            "tokenizer": "edge_ngram_tokenizer",
                            "filter": ["lowercase"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "your_field": {
                        "type": "text",
                        "analyzer": "edge_ngram_analyzer",
                        "fields": {
                            "exact": {
                                "type": "keyword"
                            }
                        }
                    }
                }
            }
        }

        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)

        es.indices.create(index=index_name, body=index_body)
