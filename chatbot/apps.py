from django.apps import AppConfig
from django.conf import settings

from evaluation.product.haho import ready_chain


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        query_chain = ready_chain()
        setattr(settings, "query_chain", query_chain)
