import os, pickle
from django.apps import AppConfig



class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        if not os.environ.get('ChatbotAPP'):
            os.environ['ChatbotAPP'] = 'True'

            from django.conf import settings
            from langchain_openai.embeddings import OpenAIEmbeddings
            from langchain.vectorstores.redis import Redis
            from langchain_openai import ChatOpenAI
            from langchain.chains import create_retrieval_chain
            from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
            from langchain.retrievers import MergerRetriever, MultiVectorRetriever
            from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
            from langchain.storage.in_memory import InMemoryStore

            # Construct MergerRetriever
            # MergerRetriever 
            # ├ MultiVectorRetriever
            # └ VectorstoreRetriever
            with open("C:\Repo\ASKu-AI-API\docstore_20240225-021040.pickle", "rb") as f:
                docstore: InMemoryStore = pickle.load(f)

            Wiki_Redis = Redis.from_existing_index(
                redis_url=os.getenv("REDIS_URL"),
                index_name=os.getenv("WIKI_INDEX"),
                embedding=OpenAIEmbeddings(),
                schema={
                    "text": [{'name': 'doc_id'}]  # MUST be SAME with source_id_key
                })

            Wiki_retriever = MultiVectorRetriever(
                vectorstore=Wiki_Redis,
                docstore=docstore,
                id_key="doc_id",
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
            with open("C:\Repo\ASKu-AI-API\systemprompt.txt", "r", encoding="utf-8") as f:
                template = f.read()
            Systemprompt = SystemMessagePromptTemplate.from_template(template=template)
            chat_prompt = ChatPromptTemplate.from_messages([Systemprompt])
            llm_chain = create_stuff_documents_chain(llm=llm, prompt=chat_prompt)

            # Construct create_retrieval_chain(name: QueryChain)
            # ├ MergerRetriever(name: contextRetriever)
            # └ create_stuff_document_chain(name: llm_chain)

            QueryChain = create_retrieval_chain(retriever=contextRetriever, combine_docs_chain=llm_chain)
            setattr(settings, "QueryChain", QueryChain)
