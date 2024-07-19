import argparse
import asyncio
import json
from typing import List

from datasets import Dataset
from langchain_core.output_parsers import StrOutputParser
from langfuse import Langfuse
from ragas import evaluate
from ragas.metrics import faithfulness, answer_correctness, answer_similarity
from ragas.metrics.base import MetricWithLLM

from tools.generators.llm import get_OPENAI_llm
from tools.generators.prompt import load_prompt
from tools.utils import batch


parser = argparse.ArgumentParser(description="Evaluate generation capability using LangFuse and Ragas.")
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
    metrics: List[MetricWithLLM] = [faithfulness, answer_correctness, answer_similarity]
    async_concurrency_level = 3
    
    # ---------- < Load > ----------
    dataset = langfuse.get_dataset(name=dataset_name)
    
    # TODO: dataset 유효성 검사
    items: List[dict] = [json.loads(item.input) for item in dataset.items]
    question: List[str] = [item["Q"] for item in items]
    contexts: List[List[str]] = [[item["C"]] for item in items]
    ground_truth: List[str] = [item.expected_output for item in dataset.items]

    # Tracing
    trace = langfuse.trace(name = "Generation")

    # ---------- < STEP2: Generation > ----------
    # Prompt
    prompt = load_prompt(prompt_name=prompt_name, prompt_version=prompt_version)
    
    # LLM
    llm = get_OPENAI_llm(temperature=0.7)

    # Generators
    generation_chain = prompt | llm | StrOutputParser()

    # Generation
    answer: List[str] = asyncio.run(
        batch.generation_batch(
            generator=generation_chain,
            question=question,
            contexts=contexts,
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
