import asyncio
from typing import List, Coroutine

from langchain_core.runnables import Runnable
from langchain.schema import Document, BaseRetriever
from tqdm import tqdm

async def retrieval_batch(
        retriever: BaseRetriever, 
        question: List[str], 
        concurrency_level: int = 3
    ) -> List[List[Document]]:
    results: List[List[Document]] = []
    batch_list: List[Coroutine] = []
    batch_results: List[List[Document]]
    for item in tqdm(question):        
        batch_list.append(retriever.ainvoke(item))

        if len(batch_list) < concurrency_level: continue
        
        batch_results = await asyncio.gather(*batch_list, return_exceptions=True)
        results.extend(batch_results)
        batch_list = []
    
    if batch_list:
        batch_results = await asyncio.gather(*batch_list, return_exceptions=True)
        results.extend(batch_results)
    
    return results


async def generation_batch(
        generator: Runnable, 
        question: List[str], 
        contexts: List[List[Document]], 
        concurrency_level: int = 3
    ) -> List[str]:
    results: List[str] = []
    batch_list: List[Coroutine] = []
    batch_results: List[str]
    for q, c in tqdm(list(zip(question, contexts))):        
        batch_list.append(generator.ainvoke({"input": q, "context": c}))
    
        if len(batch_list) < concurrency_level: continue

        batch_results = await asyncio.gather(*batch_list, return_exceptions=True)
        results.extend(batch_results)
        batch_list = []
    
    if batch_list:
        batch_results = await asyncio.gather(*batch_list, return_exceptions=True)
        results.extend(batch_results)
    
    return results