import os
from django.apps import AppConfig
from django.conf import settings

from evaluation.product.haho_v2 import ready_chain
from evaluation.tools.vectorstores.redis_store import QuestionRedisStore


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        from langchain_openai.embeddings import OpenAIEmbeddings

        query_chain = ready_chain()
        setattr(settings, "query_chain", query_chain)

        question_redis = QuestionRedisStore().get_redis_store(
            index_name=os.getenv('QUESTION_INDEX'),
            embedding = OpenAIEmbeddings(model="text-embedding-3-large"))
        high_similarity_question_retriever = question_redis.as_retriever(
            search_type="similarity",
            search_kwargs={"distance_threshold": 0.08},
        )
        lower_similarity_question_retriever = question_redis.as_retriever(
            search_type="similarity",
            search_kwargs={"distance_threshold": 0.35},
        )
        setattr(settings, "question_redis", question_redis)
        setattr(settings, "high_similarity_question_retriever", high_similarity_question_retriever)
        setattr(settings, "lower_similarity_question_retriever", lower_similarity_question_retriever)
