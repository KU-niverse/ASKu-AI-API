from abc import ABC, abstractmethod
import os

from langchain.vectorstores.redis import Redis
from langchain_openai.embeddings import OpenAIEmbeddings


class RedisStore(ABC):
    redis_url = os.getenv("REDIS_URL")
    embedding = OpenAIEmbeddings()
    
    @abstractmethod
    def get_redis_store(self) -> Redis:
        pass


class RuleRedisStore(RedisStore):
    schema = {}

    def get_redis_store(self, index_name) -> Redis:
        rule_redis = Redis(
            redis_url=RedisStore.redis_url,
            embedding=RedisStore.embedding,
            index_name=index_name,
            index_schema=self.schema
        )
        return rule_redis


class WikiRedisStore(RedisStore):
    schema = {
            "text": [
                {'name': os.getenv("source_id_key")},
                {'name': 'title'},
            ]  
        }
    
    def get_redis_store(self, index_name) -> Redis:
        wiki_redis = Redis(
            redis_url=RedisStore.redis_url,
            embedding=RedisStore.embedding,
            index_name=index_name,
            index_schema=self.schema
        )
        return wiki_redis
