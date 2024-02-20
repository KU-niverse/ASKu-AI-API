import os
from django.apps import AppConfig
from langchain.embeddings import OpenAIEmbeddings
from chatbot.utils.utils import RedisVectorstore


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        if not os.environ.get('ChatbotAPP'):
            os.environ['ChatbotAPP'] = 'True'

            # Run the below codes everytime server starts
            RedisVectorstore(
                embedding=OpenAIEmbeddings(),
                index_name=os.getenv("INDEX_NAME"),
                redis_url=os.getenv("REDIS_URL"),
                index_schema={
                    "text": [
                        {'name': 'doc_id'}  # MUST be SAME with source_id_key
                    ]
                }
            )


