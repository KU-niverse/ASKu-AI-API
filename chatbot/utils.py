import openai
from langchain.vectorstores.redis import Redis as RedisVectorStore
from langchain.embeddings import OpenAIEmbeddings

vectorstores = ["Redis"]

def getVectorStore(database: str):
    if database not in vectorstores:
        raise ValueError(f"{database} does not exist in vectorstores list")
    
    if database == "Redis":
        VectorStore = RedisVectorStore.from_existing_index(
            embedding=OpenAIEmbeddings(),
            redis_url="redis://localhost:6379",
            index_name="ku_rule")
    
    return VectorStore

def getRelatedDocs(content: str, database="Redis"):
    VectorStore = getVectorStore(database=database)
    
    RelatedDocs = []
    for documents in VectorStore.similarity_search(query=content):
        RelatedDocs.append({"role": "user", "content": documents.page_content})
    
    return RelatedDocs
    
def getCompletion(query: str, relatedDocs):
    messages = relatedDocs[:]
    messages.append({"role": "user", "content": query})
    
    assistant_content = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    messages.append({"role": "assistant", "content": assistant_content})
    return messages