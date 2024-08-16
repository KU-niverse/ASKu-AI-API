import argparse
import os

from dotenv import load_dotenv
import requests
import yaml

from utils.parser import Wikiparser


load_dotenv(dotenv_path="./.env")
parser = argparse.ArgumentParser(description="ASKu-AI: SETUP Vectorstore FROM Wiki data.")
parser.add_argument("-SETUP", default=False, help="If True, then creates an index in Vectorstore and InMemoryStore Object.")


if __name__ == '__main__':
    # ---------- < Configuration > ----------
    exec_args = parser.parse_args()
    
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Wiki":
                data_config = config
                wiki_vars = data_config["Variables"]
                wiki_meta = data_config["Metadata"]    

    wiki_url = wiki_vars["setup_url"]
    source_id_key = wiki_vars["source_id_key"]
    wiki_schema = wiki_meta["schema"]

    # ---------- < Load > ----------
    response = requests.get(wiki_url)
    wiki_all = [dict(zip(wiki_schema, map(item.get, wiki_schema))) for item in response.json()["docs"]]

    # ---------- < Parsing > ----------
    parents, children = Wikiparser(config=data_config).parse(items=wiki_all)
    
    # ---------- < hook1 > -----------
    if not exec_args.SETUP: quit()
    
    with open(os.getenv("MANAGE_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "WIKI_SETUP": 
                wiki_config = config
    
    index_name = wiki_config["Vectorstore"]["index_name"]
    index_schema = wiki_config["Vectorstore"]["index_schema"]
    redis_url = wiki_config["Vectorstore"]["url"]
    InMemoryStore_dir = wiki_config["InMemoryStore_dir"]
    RecordManager_dir = wiki_config["RecordManager_dir"]
    
    # ---------- < InMemoryStore > ----------
    import time, pickle
    from langchain.storage.in_memory import InMemoryStore    
    
    
    new_InMemoryStore = InMemoryStore()
    new_InMemoryStore.mset([(parent.metadata[source_id_key], parent) for parent in parents])

    # ---------- < Indexing > ----------
    from langchain_community.vectorstores.redis import Redis
    from langchain.indexes import SQLRecordManager, index
    from langchain_openai.embeddings import OpenAIEmbeddings


    Embedding = OpenAIEmbeddings()
    RecordManager = SQLRecordManager(namespace="redis",
                                     db_url=f"sqlite:///{os.path.join(RecordManager_dir, 'RecordManager_'+index_name)}.sql")
    RecordManager.create_schema()
    rds = Redis(redis_url=redis_url,
                index_name=index_name,
                embedding=Embedding,
                index_schema=index_schema,
                )

    indexing_result = index(docs_source=children,
                            vector_store=rds,
                            record_manager=RecordManager,
                            cleanup="full",
                            source_id_key=source_id_key,
                            )
    print(indexing_result)

    # ---------- < Saving > ----------
    # Save timing of InMemoryStore is intentionally delayed for synchronizing with RecordManager
    with open(os.path.join(InMemoryStore_dir, "docstore_wiki")+".pickle", 'wb') as f:
        pickle.dump(new_InMemoryStore, f, pickle.HIGHEST_PROTOCOL)

    timestamp = time.strftime('%Y%m%d-%I%M%S', time.localtime())
    file_path = os.path.join(InMemoryStore_dir, "docstore/docstore_" + timestamp + ".pickle")
    with open(file_path, 'wb') as f:
        pickle.dump(new_InMemoryStore, f, pickle.HIGHEST_PROTOCOL)
