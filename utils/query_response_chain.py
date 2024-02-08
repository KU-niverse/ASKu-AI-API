import os, re, time
import pickle, uuid
from typing import Literal, List, Tuple

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

# wiki_data_loder
from django.http import JsonResponse
import requests

def wiki_data_load():
    response = requests.get('https://asku.wiki/api/wiki/pipeline')
    if response.status_code == 200:
        wiki_data = [[item['id'], item['text']] for item in response.json().get('docs', [])]
        return wiki_data
    else:
        return None  # 요청 실패 처리

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

def transform_WikiToParent(
        wiki_id: int, wiki_content: str) -> list[Document]:
    """
    Transform Wiki Document to the list of parent_docs of the type Document.
    
    Parameters:
    - wiki_id: the id number of wiki document data
    - wiki_content: contents string of wiki document data

    Returns:
    - List[Document]: The list of parent document of the type Document. 
    """    
    index_pat = re.compile(r"==\s*([^=(\\n)]+)\s*==(?!=)")
            
    sections = re.split(pattern=index_pat, string=wiki_content)
    section_title = sections[1::2] 
    section_content = sections[2::2]
    
    parents = []
    for idx, (_title, _content) in enumerate(list(zip(section_title, section_content))):
        parent_content = _content.replace("\\n", "")
        parent_content = parent_content.replace("  ", " ")
        parents.append(Document(
            page_content=parent_content,
            metadata={
                # "section_title": f"{_title}",
                source_id_key: f"{wiki_id}-{idx}",}
            )
        )
        
    return parents

def saveDocstore(
        parent_docs: list[Document], 
        save_dir: str) -> (str, dict):
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
    
    return (timestamp, docstore)

def transform_ParentToChild(
        parent: list[Document]) -> list[Document]:
    """
    Transform parent_docs to the list of child_docs of the type Document.

    Parameters:
    - parent_docs: The List of parent documents of Type Document to be transformed to child docuemnts.

    Returns:
    - List[Document]: The list of child document of the type Document. 
    """
    index_pat = re.compile(r'={3,}\s*([^=]+)\s*={3,}')
    splitter = RecursiveCharacterTextSplitter()
    
    sections = re.split(pattern=index_pat, string=parent.page_content)
    _sections = [sections[0]]
    for i in range(2, len(sections), 2):
        _sections.append(f"[[{sections[i-1].rstrip()}]] " + sections[i])
    sections = [Document(page_content=section, metadata={source_id_key: parent.metadata[source_id_key]})
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
        documents: list[Document], 
        index_name: str,
        cleanup: Literal["incremental", "full"] | None=None) -> None:
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


# -------------------------------------- < Test Code > --------------------------------------
# Configuration
index_name = "test_index_9"
source_id_key = "doc_id" # NEVER EDIT the source_id_key

# ONLY once run the below codes at building server
initRecordManager(index_name=index_name)

# Run the below codes everytime server starts
RedisVectorstore(
    embedding=OpenAIEmbeddings(),
    index_name=index_name,
    redis_url=os.getenv("REDIS_URL"),
    index_schema={
        "text":[
            {'name': 'doc_id'} # MUST be SAME with source_id_key
        ]
    }
)   

# Wiki document processing batch code
_batchDocs = wiki_data_load()

_parentDocs, _childDocs = [], []
for _document in _batchDocs:
    _id, _content = int(_document[0]), _document[1]

    _parent = transform_WikiToParent(wiki_id=_id, wiki_content=_content)
    _parentDocs += _parent

    for parent in _parent:
        _child = transform_ParentToChild(parent=parent)
        _childDocs += _child

## Save Docstore at "./data/docstore_{timestamp}".
timestamp, Docstore = saveDocstore(parent_docs=_parentDocs, save_dir="./data")

## If need to clear the Redis index, then run the below
addDocumentToRedis(documents=[], index_name=index_name, cleanup='full')
## Update Redis
addDocumentToRedis(documents=_childDocs, index_name=index_name, cleanup="incremental")

# Initialize the MultiVector-Retreiever
docstore_timestamp = os.getenv("docstoreTimestamp")
docstore = loadObjectFromPickle(file_path=f"./data/docstore_{docstore_timestamp}")

mv_retriever = retriever(
    vectorstore=RedisVectorstore(),
    docstore=docstore,
    id_key=source_id_key
    )

# Test code for retriever
relevant_docs = mv_retriever.vectorstore.similarity_search(query="의료공제")
print(f"Retreiever Test Result for similiarity_search: {relevant_docs[0].page_content}")
print("-----")
relevant_docs = mv_retriever.get_relevant_documents(query="의료공제")
print(f"Retreiever Test Result for get_relevant_documents: {relevant_docs}")