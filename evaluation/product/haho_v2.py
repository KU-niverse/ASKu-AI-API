import os

from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.retrievers import ContextualCompressionRetriever, MergerRetriever
from langchain.retrievers.document_compressors import FlashrankRerank, LLMChainExtractor
from langchain_openai.embeddings import OpenAIEmbeddings

from ..tools.generators.llm import get_OPENAI_llm
from ..tools.generators.prompt import load_prompt
from ..tools.retrievers.multivector_retriever import get_multivector_retriever
from ..tools.vectorstores.redis_store import RuleRedisStore, WikiRedisStore


load_dotenv()


def ready_chain():
    embedding = OpenAIEmbeddings(model="text-embedding-3-large")

    # Vectorstore
    rule_redis = RuleRedisStore().get_redis_store(
        index_name=os.getenv('RULE_INDEX'), 
        embedding=embedding)
    wiki_redis = WikiRedisStore().get_redis_store(
        index_name=os.getenv('WIKI_INDEX'),
        embedding=embedding)

    # Retrievers
    rule_retriever = rule_redis.as_retriever(
        search_type="similarity_distance_threshold", 
        search_kwargs={"distance_threshold": 0.3},
    )
    wiki_retriever_small = get_multivector_retriever(
        vectorstore=wiki_redis,
        docstore_path=os.getenv("PICKLE_PATH"),
        k=1
        )
    wiki_retriever = get_multivector_retriever(
        vectorstore=wiki_redis,
        docstore_path=os.getenv("PICKLE_PATH"),
        k=5
        )

    compressor = LLMChainExtractor.from_llm(get_OPENAI_llm(model="gpt-4o-mini", temperature=0))
    compressed_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=wiki_retriever
    )

    merger_retriever = MergerRetriever(
        retrievers=[rule_retriever, wiki_retriever_small, compressed_retriever]
    )

    reranker = FlashrankRerank()
    retrieval_chain = ContextualCompressionRetriever(
        base_compressor=reranker, base_retriever=merger_retriever
    )

    # Prompt
    prompt = load_prompt(prompt_name="RAG_Instructed_ThoT", prompt_version=6)
    
    # LLM
    llm = get_OPENAI_llm(model="gpt-4o-mini", temperature=0.7)
    
    # Generators
    generation_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    return create_retrieval_chain(retriever=retrieval_chain, combine_docs_chain=generation_chain)
