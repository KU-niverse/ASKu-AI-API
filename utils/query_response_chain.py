import os, re, time
import pickle, uuid
from typing import Literal, List
from typing import Optional

from dotenv import load_dotenv, set_key
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import SQLRecordManager, index
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.schema import Document
from langchain.storage import InMemoryStore
from langchain.vectorstores.redis import Redis

from singleton import singleton

load_dotenv()
embedding = OpenAIEmbeddings()
source_id_key = "doc_id"

@singleton
class RedisVectorstore(Redis):
    """
    Singleton Redis Object.
    
    Must be Initialized in ./connfig/settings.py to call singleton object by RedisVectorstore().
    ```
        RedisVectorstore(
            embedding=OpenAIEmbeddings(),
            index_name="test_index",
            redis_url=os.getenv("REDIS_URL"),
        )
    ```
    Once create the RedisVectorstore class, the created RedisVectorstore can be called by RedisVectorstore().
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@singleton
class retriever(MultiVectorRetriever):
    """
    Singleton MultiVectorRetriever Object.
    
    Must be Initialized in ./connfig/settings.py to call singleton object by retriever().
    ```
        docstore = loadObjectFromPickle(file_path="./docstore_20231125-011508")
        retriever(
            vectorstore=RedisVectorstore(),
            docstore=docstore,
            id_key=source_id_key
            )
    ```
    Once create the retriever class, the created retriever can be called by retriever().
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # Override
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get documents relevant to a query.
        Args:
            query: String to find relevant documents for
            run_manager: The callbacks handler to use
        Returns:
            List of relevant documents
        """
        sub_docs = self.vectorstore.similarity_search(query, **self.search_kwargs)
        # We do this to maintain the order of the ids that are returned
        print(sub_docs[0]); input()
        ids = []
        for d in sub_docs:
            if d.metadata[self.id_key] not in ids:
                ids.append(d.metadata[self.id_key])
        print(ids)
        keys = []
        for (idx, key) in enumerate(self.docstore.yield_keys()):
            print(idx, '\n', 
                  "key=", key, '\n', self.docstore.mget(keys=[key]), '\n')
            keys.append(key)
        print(keys)
        docs = self.docstore.mget(ids)
        return [d for d in docs if d is not None]


def saveObjectToPickle(
        object: object,
        save_dir: str, 
        name: str, 
        addTimeSuffix: bool = True) -> None:
    """
    Save a Python object to a file using the pickle module.

    Parameters:
    - object: The Python object to be saved.
    - savedir: The directory path where the object will be saved.
    - name: The name of file to be saved.
    - addTimeSuffix: If true, then suffix indicating the savetime will be added to back of file name.
    """
    try:
        if addTimeSuffix:
            timeSuffix = time.strftime('%Y%m%d-%I%M%S', time.localtime())
            save_name = f"{name}_{timeSuffix}.pickle"
        else:
            save_name = f"{name}.pickle"
        
        with open(os.path.join(save_dir, save_name), 'wb') as f:
            pickle.dump(object, f, pickle.HIGHEST_PROTOCOL)
    
    except FileNotFoundError:
        print(f"Directory Not Found: {save_dir}")
    except Exception as e:
        print(f"An Error occured: {e}")
    
    return timeSuffix if addTimeSuffix else None
        
def loadObjectFromPickle(
        file_path: str) -> object:
    """
    Load a Python object from a pickle file using the pickle module.

    Parameters:
    - filepath: The file path where the object is located.
    
    Returns:
    - object
    """
    file_path = f"{file_path}.pickle"
    try:
        with open(file_path, 'rb') as f:
            object = pickle.load(f)
        return object
    except FileNotFoundError:
        print(f"File Not Found: {file_path}")
    except Exception as e:
        print(f"An Error Occured: {e}")

def transformWikidocsToParentdocs(
        data_dir) -> List[Document]:
    """
    Transform Wiki Document to the list of parent_docs of the type Document.
    
    Parameters:
    - datadir: The directory where the wiki documents are located.

    Returns:
    - List[Document]: The list of parent document of the type Document. 
    """
    index_pat = re.compile(r"==\s*([^=(\\n)]+)\s*==(?!=)")
    doc_name = ""
    parent_docs = []
    for i, doc in enumerate(os.listdir(data_dir)):
        with open(os.path.join(data_dir, doc), mode="r+", encoding="utf-8") as f:
            docs = f.readlines()
            
        sections = re.split(pattern=index_pat, string=docs[0])
        indexes = sections[1::2] 
        contents = sections[2::2]
        
        for idx_name, content in list(zip(indexes, contents)):
            content = content.replace("\\n", "")
            content = content.replace("  ", " ")
            parent_docs.append(Document(
                page_content=content,
                metadata={
                    "doc_name": f"{doc_name}",
                    "index_name": f"{idx_name.rstrip()}",
                    source_id_key: str(uuid.uuid4())}
                )
            )
    return parent_docs

def mapSourceIdKey():
    
    return

def saveDocstore(
        parent_docs: List[Document], 
        save_dir: str) -> None:
    """
    Save a InMemoryStore object to a file using the pickle module.

    Args:
    - parent_docs: Parent document list of Document Type to be used to construct Docstore.
    - save_dir: The directory path where the object will be saved.
    """
    docstore = InMemoryStore()
    _id_docs = [(_doc.metadata[source_id_key], _doc) for _doc in parent_docs]
    docstore.mset(_id_docs)
    timestamp = saveObjectToPickle(
        object=docstore,
        save_dir=save_dir,
        name="docstore", 
        addTimeSuffix=True)
    set_key(dotenv_path="./.env", key_to_set="docstoreTimestamp", value_to_set=timestamp)
    
    return timestamp

def transformParentdocsToChilddocs(
        parent_docs: List[Document]) -> List[Document]:
    """
    Transform parent_docs to the list of child_docs of the type Document.

    Parameters:
    - parent_docs: The List of parent documents of Type Document to be transformed to child docuemnts.

    Returns:
    - List[Document]: The list of child document of the type Document. 
    """
    index_pat = re.compile(r'={3,}\s*([^=]+)\s*={3,}')
    splitter = RecursiveCharacterTextSplitter()
    
    sections = re.split(pattern=index_pat, string=parent_docs.page_content)
    _sections = [sections[0]]
    for i in range(2, len(sections), 2):
        _sections.append(f"[[{sections[i-1].rstrip()}]] " + sections[i])
    sections = [Document(page_content=section, metadata={source_id_key: parent_docs.metadata[source_id_key]})
                         for section in _sections]

    docs = splitter.split_documents(sections)
    child_docs = splitter.split_documents(docs) 
    return child_docs

def initRecordManager(
        index_name: str) -> None:
    """
    Initialize a RecordManager, a SQLalchemy engine obejct conneted with sqlite3.

    Args:
    index_name: The name of index in Redis vectorstore to be managed by RecordManager.
    """
    namespace = f"redis/{index_name}"
    recordManager = SQLRecordManager(
        namespace=namespace,
        db_url=f"sqlite:///./data/recordManager_{index_name}.sql")
    recordManager.create_schema()

def addDocumentToRedis(
        documents: List[Document], 
        index_name: str,
        cleanup: Optional[Literal["incremental", "full"]]=None) -> None:
    """
    Add documents to Redis vectorstore using langchain indexing API.

    Args:
    - document : The list of document of the type Document to be added to Reids vectorstore
    - cleanup : "none", "incremental", or "full"
    """
    recordManager = SQLRecordManager(
        namespace=f"redis/{index_name}",
        db_url=f"sqlite:///./data/recordManager_{index_name}.sql"
    )
    print(index(
        docs_source=documents,
        vector_store=RedisVectorstore(),
        record_manager=recordManager,
        cleanup=cleanup,
        source_id_key=source_id_key
        ))

index_name = "test_index_10"
RedisVectorstore(
    embedding=OpenAIEmbeddings(),
    index_name=index_name,
    redis_url=os.getenv("REDIS_URL"),
    index_schema={
        "text":[
            {'name': 'doc_id'}
        ]
    }
)

# # Batch Code

# initRecordManager(index_name=index_name)

# parent_docs = transformWikidocsToParentdocs("./data/wikidocs")
# timestamp = saveDocstore(parent_docs=parent_docs, save_dir="./data")
# child_docs = []
# for _parent_docs in parent_docs:
#     for _child_docs in transformParentdocsToChilddocs(parent_docs=_parent_docs):
#         child_docs.append(_child_docs)
#         print(_child_docs); input()
# addDocumentToRedis(documents=child_docs, index_name=index_name, cleanup=None)

# docstore = loadObjectFromPickle(file_path=f"./data/docstore_{timestamp}")

# Retriever Code

docstore = loadObjectFromPickle(file_path=f"./data/docstore_{os.getenv(key='docstoreTimestamp')}")
# for key in docstore.yield_keys():
#     print(key); input()

mv_retriever = retriever(
    vectorstore=RedisVectorstore(),
    docstore=docstore,
    id_key=source_id_key
    )

relevant_docs = mv_retriever.vectorstore.similarity_search(query="의료공제")
print(relevant_docs[0].page_content)
print("-----")
relevant_docs = mv_retriever.get_relevant_documents(query="의료공제")
print(relevant_docs)