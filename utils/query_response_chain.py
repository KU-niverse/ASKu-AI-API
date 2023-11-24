import os, re, time
import pickle, uuid
from typing import Literal

from dotenv import load_dotenv
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
source_id_key = "source_id"

@singleton
class RedisVectorstore(Redis):
    """
    Singleton Redis Object.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@singleton
class retriever(MultiVectorRetriever):
    """
    Singleton MultiVectorRetriever Object.
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
        data_dir) -> list[Document]:
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

def saveDocstore(
        parent_docs: list[Document], 
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
    saveObjectToPickle(
        obejct=docstore,
        save_dir=save_dir,
        name="docstore", 
        addTimeSuffix=True)
    
def transformParentdocsToChilddocs(
        parent_docs: list[Document]) -> list[Document]:
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
    indexes = sections[1::2] 
    contents = sections[2::2]
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
        db_url=f"sqlite:///recordManager_{index_name}.sql")
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
    try:
        recordManager = SQLRecordManager(
            namespace=f"redis/{index_name}",
            db_url=f"sqlite:///recordManager_{index_name}.sql"
        )
        index(
            docs_source=documents,
            vector_store=RedisVectorstore(),
            record_manager=recordManager,
            cleanup=cleanup,
            source_id_key=source_id_key
            )
    except Exception as e:
        print(f'An Error Occured: {e}')
