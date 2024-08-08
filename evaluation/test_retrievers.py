import argparse
import asyncio
import json
import os
from typing import List

from datasets import Dataset
from dotenv import load_dotenv
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.retrievers import MergerRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.schema import Document
from langfuse import Langfuse
from ragas import evaluate
from ragas.metrics import faithfulness, answer_correctness, context_relevancy, answer_similarity
from ragas.metrics.base import MetricWithLLM

from tools.generators.prompt import load_prompt
from tools.generators.llm import get_OPENAI_llm
from tools.retrievers.multivector_retriever import get_multivector_retriever
from tools.utils import batch
from tools.vectorstores.redis_store import RuleRedisStore, WikiRedisStore


load_dotenv()
parser = argparse.ArgumentParser(description="Evaluate RAG Pipeline using LangFuse and Ragas.")
parser.add_argument("-dataset", type=str, default="RAG_v1.1", help="LangFuse dataset name.")
parser.add_argument("-prompt_name", type=str, default="RAG", help="LangFuse prompt name.")
parser.add_argument("-prompt_version", type=int, default=1, help="LangFuse prompt version.")


if __name__ == '__main__':
    # ---------- < Configuration > ---------- 
    exec_args = parser.parse_args()
    dataset_name: str = exec_args.dataset
    prompt_name: str = exec_args.prompt_name
    prompt_version: int = exec_args.prompt_version

    langfuse = Langfuse(); langfuse.auth_check()
    metrics: List[MetricWithLLM] = [faithfulness, answer_correctness, context_relevancy, answer_similarity]
    async_concurrency_level = 3
    
    # ---------- < Load > ----------
    dataset = langfuse.get_dataset(name=dataset_name)
    
    # TODO: dataset 유효성 검사
    items: List[dict] = [json.loads(item.input) for item in dataset.items]
    question: List[str] = [item["Q"] for item in items]
    # contexts: List[List[str]] = [[item["C"]] for item in items]
    ground_truth: List[str] = [item.expected_output for item in dataset.items]

    # Tracing
    trace = langfuse.trace(name = "RAG")
    
    # ---------- < STEP1: Retrieval > ----------
    # Vectorstore
    rule_redis = RuleRedisStore().get_redis_store(index_name=os.getenv("RULE_INDEX"))
    wiki_redis = WikiRedisStore().get_redis_store(index_name=os.getenv("WIKI_INDEX"))

    # Retrievers
    
    # Possible retrievers
    compressor = LLMChainExtractor.from_llm(get_OPENAI_llm())

    rule_retrievers = []

    for k in range(3, 6):
        rule_retriever = rule_redis.as_retriever(
            search_kwargs={"k": k}
        )
        rule_retrievers.append(rule_retriever)
        rule_compressed_retriever = ContextualCompressionRetriever(
            base_retriever=rule_retriever,
            base_compressor=compressor
        )
        rule_retrievers.append(rule_compressed_retriever)
    
    for score in range(0.2, 0.45, 0.05):
        rule_retriever = rule_redis.as_retriever(
            search_type="similarity_score_threshold", 
            search_kwargs={"score_threshold": score},
        )
        rule_retrievers.append(rule_retriever)
        rule_compressed_retriever = ContextualCompressionRetriever(
            base_retriever=rule_retriever,
            base_compressor=compressor
        )
        rule_retrievers.append(rule_compressed_retriever)

    wiki_retrievers = []

    for k in range(3, 6):
        wiki_retriever = get_multivector_retriever(
            vectorstore=wiki_redis,
            docstore_path=os.getenv("PICKLE_PATH"),
            k=k
        )
        wiki_retrievers.append(wiki_retriever)
        wiki_compressed_retriever = ContextualCompressionRetriever(
            base_retriever=wiki_retriever,
            base_compressor=compressor
        )
        wiki_retrievers.append(wiki_compressed_retriever)


    # Loop over all possible retrievers
    for rule_retriever in rule_retrievers:
        for wiki_retriever in wiki_retrievers:

            retrieval_chain = MergerRetriever(retrievers=[rule_retriever, wiki_retriever])

            # Retrieval
            raw_contexts: List[List[Document]] = asyncio.run(
                batch.retrieval_batch(
                    retriever=retrieval_chain,
                    question=question,
                    concurrency_level=async_concurrency_level
                )
            )
            contexts: List[List[str]] = []
            for raw_context in raw_contexts:
                contexts.append(list(map(lambda x: x.page_content, raw_context)))

            # Tracing
            trace.span(
                name = "retrieval", input={'question': question}, output={'contexts': contexts}
            )
            
            # ---------- < STEP2: Generation > ----------
            # Prompt
            prompt = load_prompt(prompt_name=prompt_name, prompt_version=prompt_version)
            
            # LLM
            llm = get_OPENAI_llm(temperature=0.7)
            
            # Generators
            generation_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

            # Generation
            answer: List[str] = asyncio.run(
                batch.generation_batch(
                    generator=generation_chain,
                    question=question,
                    contexts=raw_contexts,
                    concurrency_level=async_concurrency_level
                )
            )

            # Tracing
            trace.span(
                name = "generation", input={'question': question, 'contexts': contexts}, output={'answer': answer}
            )

            # ---------- < STEP3: Experiment > ----------
            # Calculate scores
            dataset = Dataset.from_dict(
                {
                    'question': question,
                    'ground_truth': ground_truth,
                    'answer': answer,
                    'contexts': contexts,
                }
            )
            scores = evaluate(dataset, metrics=metrics)

            # Tracing
            for m, k in scores.items():
                trace.score(name=m, value=f"{k:0.4f}")
