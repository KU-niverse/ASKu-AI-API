import os
import pickle
from typing import Union

from langchain.retrievers import MultiVectorRetriever
from langchain.storage.in_memory import InMemoryBaseStore
from langchain.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever


def get_multivector_retriever(
        vectorstore: VectorStore, 
        docstore_path: Union[os.PathLike, str],
        k: int = 4,
    ) -> BaseRetriever:

    with open(docstore_path, "rb") as f:
        docstore: InMemoryBaseStore = pickle.load(f)

    Wiki_retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        id_key=os.getenv("source_id_key"),
        search_kwargs={"k": k},
    )

    return Wiki_retriever
