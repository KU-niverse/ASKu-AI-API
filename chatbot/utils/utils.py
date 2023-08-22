import os
from dotenv import load_dotenv

import openai
from langchain.vectorstores.redis import Redis
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

from chatbot.utils.roBERTa_Embedding import roBERTa_Embedding

vectorstores = ["Redis"]
embedding = OpenAIEmbeddings  # OpenAIEmbeddings, roBERTa_Embedding
index_name = 'ku_rule'  # 'ku_rule', 'KU_RULE_05', 'ku_rule_index'
load_dotenv()

def createVectorstoreIndex(database: str, texts, index_name: str) -> None:
    if database not in vectorstores:
        raise ValueError(f"{database} does not exist in vectorstores list in utils.py")
    if database == "Redis":
        Redis.from_texts(
            texts=texts,
            embedding=embedding(),
            index_name=index_name,
            redis_url=os.getenv("REDIS_URL")
        )
    return None


def dropVectorstoreIndex(database: str, index_name: str) -> None:
    if database not in vectorstores:
        raise ValueError(f"{database} does not exist in vectorstores list in utils.py")

    if database == "Redis":
        result = Redis.drop_index(
            index_name=index_name,
            delete_documents=False,
            redis_url=os.getenv("REDIS_URL")
        )

    if not result:
        raise Exception("The index does not exist in the Vector Database.")

    return None


def getVectorStore(database: str, index_name: str = "KU_RULE_05") -> Redis:
    if database not in vectorstores:
        raise ValueError(f"{database} does not exist in vectorstores list in utils.py")

    if database == "Redis":
        VectorStore = Redis.from_existing_index(
            embedding=embedding(),
            redis_url=os.getenv("REDIS_URL"),
            index_name=index_name)

    return VectorStore


def getRelatedDocs(content: str, database="Redis"):
    VectorStore = getVectorStore(database=database, index_name=index_name)
    RelatedDocs = []

    for index, documents in enumerate(VectorStore.similarity_search(query=content)):
        # RelatedDocs.append(documents.page_content)
        RelatedDocs.append("{}: {}".format(index+1, documents.page_content))
    return RelatedDocs


def getCompletion(query: str, relatedDocs):
    docs = []
    for i in relatedDocs:
        docs.append({"role": "user", "content": i})
    messages = docs[:]
    messages.append({"role": "user", "content": query})
    messages.append({"role": "system", "content": " \
        1. 너는 고려대학교 학생들의 학교 학칙에 대한 질문에 대답해주는 ai챗봇이다. \
        2. 주어지는 내용은 모두 고려대학교의 학칙 문서이다. \
        3. 주어지는 내용과 비슷하거나 관련된 내용은 최대한 대답에 포함해야 한다. \
        4. 주어진 내용과 질문이 관련이 없다면 모른다고 대답해야만 한다. \
        5. '고려대학교의 학칙을 참고하라'는 내용을 최대한 포함하지 않고 대답해야 한다."})

    assistant_content = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    messages.append({"role": "assistant", "content": assistant_content})
    return messages
