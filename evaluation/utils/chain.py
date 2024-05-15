import os
import pickle

from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.retrievers import MergerRetriever, MultiVectorRetriever
from langchain.storage.in_memory import InMemoryStore
from langchain.vectorstores.redis import Redis


load_dotenv()


def rule_retriever():
    # TODO: Schema.yaml 파일과 연동
    retriever = Redis(
        redis_url=os.getenv("REDIS_URL"),
        index_name=os.getenv("RULE_INDEX"),
        embedding=OpenAIEmbeddings()
    ).as_retriever(
        search_type="similarity_distance_threshold", 
        search_kwargs={"distance_threshold": 5},
    )
    
    return retriever


def wiki_retriever():
    # TODO: Schema.yaml 파일과 연동
    Wiki_Redis = Redis.from_existing_index(
        redis_url=os.getenv("REDIS_URL"),
        index_name=os.getenv("WIKI_INDEX"),
        embedding=OpenAIEmbeddings(),
        schema={
            "text": [
                {'name': os.getenv("source_id_key")}, # MUST be SAME with source_id_key
                {'name': 'title'}
            ]  
        }
    )

    with open(os.getenv("PICKLE_PATH"), "rb") as f:
        docstore: InMemoryStore = pickle.load(f)

    Wiki_retriever = MultiVectorRetriever(
        vectorstore=Wiki_Redis,
        docstore=docstore,
        id_key=os.getenv("source_id_key"),
    )

    return Wiki_retriever


def retrievel_chain():
    context_retriever = MergerRetriever(retrievers=[wiki_retriever(), rule_retriever()])

    return context_retriever


def prompt_chain(prompt_version: str = "1.0"):
    # TODO: LangFuse Dataset을 불러오는 기능으로 변경
    # TODO: Default Version 설정
    with open("systemprompt.txt", "r", encoding="utf-8") as f:
        template = f.read()

    Systemprompt = SystemMessagePromptTemplate.from_template(template=template)
    chat_prompt = ChatPromptTemplate.from_messages([Systemprompt])

    return chat_prompt

def llm_chain(prompt_chain):
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    llm_chain = create_stuff_documents_chain(llm=llm, prompt=prompt_chain)

    return llm_chain


def generation_chain():
    return llm_chain(prompt_chain=prompt_chain())


def ready_chain():
    QueryChain = create_retrieval_chain(retriever=retrievel_chain(), combine_docs_chain=generation_chain())
    return QueryChain
