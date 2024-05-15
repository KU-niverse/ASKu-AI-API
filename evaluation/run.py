import argparse
import asyncio
from typing import List

from datasets import Dataset
from langchain.schema import Document
from langfuse import Langfuse
from ragas import evaluate
from ragas.metrics import faithfulness, answer_correctness, context_relevancy, answer_similarity
from ragas.metrics.base import MetricWithLLM

from utils.chain import retrievel_chain, prompt_chain, llm_chain
from utils.batch import retrieval_batch, generation_batch

parser = argparse.ArgumentParser(description="ASKu-AI-LangFuse: Run LangFuse experiment.")
parser.add_argument("dataset", help="The name of LangFuse dataset for running LangFuse experiment.")
parser.add_argument("prompt", help="The version of Prompt that will be injected in Generation step.")


if __name__ == '__main__':
    # ---------- < Configuration > ---------- 
    exec_args = parser.parse_args()
    dataset_name: str = exec_args.dataset
    prompt_version: str = exec_args.prompt

    langfuse = Langfuse(); langfuse.auth_check()
    metrics: List[MetricWithLLM] = [faithfulness, answer_correctness, context_relevancy, answer_similarity]
    concurrency_level=3
    
    # ---------- < Load > ----------
    try:
        dataset = langfuse.get_dataset(name=dataset_name)
    except:
        print("Can not find LangFuse dataset. Check the name of dataset")
    
    # TODO: dataset 유효성 검사
    question: List[str] = [item.input for item in dataset.items]
    ground_truth: List[str] = [item.expected_output for item in dataset.items]

    trace = langfuse.trace(name = "RAG")
    
    # ---------- < STEP1: Retrieval > ----------
    ## Retriever
    retrieval_chain = retrievel_chain()

    ## Retrieval
    raw_contexts: List[List[Document]] = asyncio.run(
        retrieval_batch(
            retriever=retrieval_chain,
            question=question,
            concurrency_level=concurrency_level
        )
    )
    contexts: List[List[str]] = []
    for raw_context in raw_contexts:
         contexts.append(list(map(lambda x: x.page_content, raw_context)))

    trace.span(
        name = "retrieval", input={'question': question}, output={'contexts': contexts}
    )
    
    # ---------- < STEP2: Generation > ----------
    ## Prompt Injection
    prompt = prompt_chain(prompt_version=prompt_version)

    ## Generation Chain
    generation_chain = llm_chain(prompt_chain=prompt)

    ## Generation
    answer: List[str] = asyncio.run(
        generation_batch(
            generator=generation_chain,
            question=question,
            contexts=raw_contexts,
            concurrency_level=concurrency_level
        )
    )

    trace.span(
        name = "generation", input={'question': question, 'contexts': contexts}, output={'answer': answer}
    )

    # ---------- < STEP3: Experiment > ----------
    dataset = Dataset.from_dict(
        {
            'question': question,
            'ground_truth': ground_truth,
            'answer': answer,
            'contexts': contexts,
        }
    )
    scores = evaluate(dataset, metrics=metrics)

    for m, k in scores.items():
        trace.score(name=m, value=f"{k:0.4f}")
