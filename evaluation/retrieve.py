import argparse
import asyncio
import json
import os
from typing import List

from datasets import Dataset
from langchain.schema import Document
from langchain.retrievers import MergerRetriever
from langfuse import Langfuse
from ragas import evaluate
from ragas.metrics import context_relevancy
from ragas.metrics.base import MetricWithLLM

from tools.vectorstores.redis_store import RuleRedisStore, WikiRedisStore
from tools.retrievers.multivector_retriever import get_multivector_retriever
from tools.utils import batch


parser = argparse.ArgumentParser(description="Evaluate retrieval capability using LangFuse and Ragas.")
parser.add_argument("-dataset", type=str, default="RAG_v1.1", help="LangFuse dataset name.")


if __name__ == '__main__':
    # ---------- < Configuration > ---------- 
    exec_args = parser.parse_args()
    dataset_name: str = exec_args.dataset

    langfuse = Langfuse(); langfuse.auth_check()
    metrics: List[MetricWithLLM] = [context_relevancy]
    async_concurrency_level = 3
    
    # ---------- < Load > ----------
    dataset = langfuse.get_dataset(name=dataset_name)
    
    # TODO: dataset 유효성 검사
    items: List[dict] = [json.loads(item.input) for item in dataset.items]
    question: List[str] = [item["Q"] for item in items]
    ground_truth: List[str] = [item["C"] for item in items]
    # ground_truth: List[str] = [item.expected_output for item in dataset.items]

    # Tracing
    trace = langfuse.trace(name = "Retrieval")

    # ---------- < STEP1: Retrieval > ----------
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

    # ---------- < STEP2: Experiment > ----------
    # Calculate scores
    dataset = Dataset.from_dict(
        {
            'question': question,
            'ground_truth': ground_truth,
            'contexts': contexts,
        }
    )
    scores = evaluate(dataset, metrics=metrics)

    # Tracing
    for m, k in scores.items():
        trace.score(name=m, value=f"{k:0.4f}")
