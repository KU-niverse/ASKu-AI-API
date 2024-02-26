import os
import pickle

from django.conf import settings
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.retrievers import MergerRetriever, MultiVectorRetriever
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.storage.in_memory import InMemoryStore


def ready_chain():
    # Construct MergerRetriever
    # MergerRetriever
    # ├ MultiVectorRetriever
    # └ VectorstoreRetriever
    pickle_path = os.getenv("PICKLE_PATH")
    with open(pickle_path, "rb") as f:
        docstore: InMemoryStore = pickle.load(f)

    Wiki_Redis = Redis.from_existing_index(
        redis_url=os.getenv("REDIS_URL"),
        index_name=os.getenv("WIKI_INDEX"),
        embedding=OpenAIEmbeddings(),
        schema={
            "text": [{'name': os.getenv("source_id_key")}, {'name': 'title'}]  # MUST be SAME with source_id_key
        })

    Wiki_retriever = MultiVectorRetriever(
        vectorstore=Wiki_Redis,
        docstore=docstore,
        id_key=os.getenv("source_id_key"),
    )
    Rule_retriever = Redis(
        redis_url=os.getenv("REDIS_URL"),
        index_name=os.getenv("RULE_INDEX"),
        embedding=OpenAIEmbeddings()).as_retriever()

    contextRetriever = MergerRetriever(retrievers=[Wiki_retriever, Rule_retriever])

    # Construct create_stuff_document_chain(name: llm_chain)
    # create_stuff_document_chain
    # ├ ChatPromptTemplate
    # ├─ SystemPromptTemplate
    # └ ChatOpenAI
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    with open("systemprompt.txt", "r", encoding="utf-8") as f:
        template = f.read()
    Systemprompt = SystemMessagePromptTemplate.from_template(template=template)
    chat_prompt = ChatPromptTemplate.from_messages([Systemprompt])
    llm_chain = create_stuff_documents_chain(llm=llm, prompt=chat_prompt)

    # Construct create_retrieval_chain(name: QueryChain)
    # ├ MergerRetriever(name: contextRetriever)
    # └ create_stuff_document_chain(name: llm_chain)
    QueryChain = create_retrieval_chain(retriever=contextRetriever, combine_docs_chain=llm_chain)
    setattr(settings, "QueryChain", QueryChain)
