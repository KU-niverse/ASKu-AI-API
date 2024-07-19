import os

from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.retrievers import MergerRetriever

from ..tools.generators.prompt import load_prompt
from ..tools.generators.llm import get_OPENAI_llm
from ..tools.retrievers.multivector_retriever import get_multivector_retriever
from ..tools.vectorstores.redis_store import RuleRedisStore, WikiRedisStore


load_dotenv()

def ready_chain():    
    # Vectorstore
    rule_redis = RuleRedisStore().get_redis_store(index_name=os.getenv("RULE_INDEX"))
    wiki_redis = WikiRedisStore().get_redis_store(index_name=os.getenv("WIKI_INDEX"))

    # Retrievers
    rule_retriever = rule_redis.as_retriever(
        search_type="similarity_distance_threshold", 
        search_kwargs={"distance_threshold": 0.3},
    )
    wiki_retriever = get_multivector_retriever(
        vectorstore=wiki_redis,
        docstore_path=os.getenv("PICKLE_PATH")
        )
    retrieval_chain = MergerRetriever(retrievers=[rule_retriever, wiki_retriever])

    # Prompt
    prompt = load_prompt(prompt_name="RAG", prompt_version=1)
    
    # LLM
    llm = get_OPENAI_llm(temperature=0.7)
    
    # Generators
    generation_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    return create_retrieval_chain(retriever=retrieval_chain, combine_docs_chain=generation_chain)
