from django.apps import AppConfig

from chatbot.utils.chain import ready_chain


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        ready_chain()
