import argparse
import copy
import os

from dotenv import load_dotenv
import requests
import yaml

from utils.parser import Wikiparser


def manage_wiki_update(update: bool = False):
    # ---------- < Configuration > ----------
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Wiki":
                data_config = config
                wiki_vars = data_config["Variables"]
                wiki_meta = data_config["Metadata"]

    updated_wiki_url = wiki_vars["updated_url"]
    source_id_key = wiki_vars["source_id_key"]
    wiki_schema = wiki_meta["schema"]

    # ---------- < Load > ----------
    response = requests.get(updated_wiki_url)
    updated_wiki_all = [dict(zip(wiki_schema, map(item.get, wiki_schema))) for item in response.json()["docs"]]
    updated_wiki_ids = [updated_wiki_item["id"] for updated_wiki_item in updated_wiki_all]

    # ---------- < Parsing > ----------
    parents, children = Wikiparser(config=data_config).parse(items=updated_wiki_all)

    # ---------- < hook1 > -----------
    if not update: quit()

    with open(os.getenv("MANAGE_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "WIKI_SETUP":
                wiki_config = config

    index_name = wiki_config["Vectorstore"]["index_name"]
    index_schema = wiki_config["Vectorstore"]["index_schema"]
    redis_url = wiki_config["Vectorstore"]["url"]
    prevInMemoryStore_path = os.getenv("PICKLE_PATH")
    InMemoryStore_dir = wiki_config["InMemoryStore_dir"]
    RecordManager_path = os.path.join(wiki_config["RecordManager_dir"], 'RecordManager_' + index_name) + ".sql"

    # ---------- < Updating InMemoryStore > ----------
    import time, pickle
    from langchain.storage.in_memory import InMemoryStore

    with open(prevInMemoryStore_path, "rb") as f:
        prev_InMemoryStore: InMemoryStore = pickle.load(f)
    new_InMemoryStore = copy.deepcopy(prev_InMemoryStore)

    for id_updated in updated_wiki_ids:
        for prev_id in prev_InMemoryStore.yield_keys(prefix=str(id_updated)):
            new_InMemoryStore.mdelete(keys=str(prev_id))

    new_InMemoryStore.mset([(parent.metadata[source_id_key], parent) for parent in parents])

    # ---------- < Indexing > ----------
    from langchain_community.vectorstores.redis import Redis
    from langchain.indexes import SQLRecordManager, index
    from langchain_openai.embeddings import OpenAIEmbeddings

    embedding = OpenAIEmbeddings()
    record_manager = SQLRecordManager(namespace="redis",
                                     db_url=f"sqlite:///{RecordManager_path}")

    rds = Redis(redis_url=redis_url,
                index_name=index_name,
                embedding=embedding,
                index_schema=index_schema,
                )

    indexing_result = index(docs_source=children,
                            vector_store=rds,
                            record_manager=record_manager,
                            cleanup="incremental",
                            source_id_key=source_id_key,
                            )
    print(indexing_result)

    # ---------- < Saving > ----------
    # Save timing of InMemoryStore is intentionally delayed for synchronizing with RecordManager
    with open(os.path.join(InMemoryStore_dir, 'docstore_wiki') + '.pickle', 'wb') as f:
        pickle.dump(new_InMemoryStore, f, pickle.HIGHEST_PROTOCOL)

    timestamp = time.strftime('%Y%m%d-%I%M%S', time.localtime())
    # with open(os.path.join(InMemoryStore_dir, "docstore_"+timestamp)+".pickle", 'wb') as f:
    #     pickle.dump(new_InMemoryStore, f, pickle.HIGHEST_PROTOCOL)
    file_path = os.path.join(InMemoryStore_dir, "docstore/docstore_" + timestamp + ".pickle")
    with open(file_path, 'wb') as f:
        pickle.dump(new_InMemoryStore, f, pickle.HIGHEST_PROTOCOL)


load_dotenv(dotenv_path="./.env")
parser = argparse.ArgumentParser(description="ASKu-AI: UPDATE Vectorstore FROM MODIFIED Wiki data.")
parser.add_argument("-UPDATE", default=False,
                    help="If True, then updates an existing index in Vectorstore and InMemoryStore Object.")

if __name__ == '__main__':
    exec_args = parser.parse_args()

    manage_wiki_update(update=exec_args.UPDATE)
