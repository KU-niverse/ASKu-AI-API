import argparse
import os
from typing import List
import warnings

from dotenv import load_dotenv
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_core.documents import Document
import yaml

from utils.parser import Calenderparser


load_dotenv(dotenv_path="./.env")
parser = argparse.ArgumentParser(description="ASKu-AI: Add calender items into the rule index of redis vectorstore.")
parser.add_argument("-SETUP", default=False, help="If True, then adds calender items into rule index.")


if __name__ == '__main__':
    # ---------- < Configuration > ----------
    exec_args = parser.parse_args()
    
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Calender":
                data_config: dict = config
                calender_vars: dict = data_config["Variables"]
                calender_meta: dict = data_config["Metadata"]
    
    calender_dir: str = calender_vars["calender_dir"]
    
    # ---------- < Load > ----------
    calender_all: List[Document] = []
    for file_name in os.listdir(calender_dir):
        calender_contents = UnstructuredExcelLoader(file_path=os.path.join(calender_dir, file_name)).load()
        calender_contents = calender_contents[0].page_content
        calender_all.append(Document(page_content=calender_contents, metadata={"file_name": file_name}))

    # ---------- < Parsing > ----------
    calender_parsed = Calenderparser(config=data_config).parse(items=calender_all)
    
    # ---------- < hook1 > -----------
    if not exec_args.SETUP: quit()
    
    with open(os.getenv("MANAGE_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "RULE_SETUP": 
                calender_config = config

    # ---------- < Indexing > ----------
    from langchain_community.vectorstores.redis import Redis
    from langchain_openai.embeddings import OpenAIEmbeddings


    embedding = OpenAIEmbeddings()
    Redis.from_texts(texts=calender_parsed,
                     redis_url=calender_config["Vectorstore"]["url"],
                     index_name=calender_config["Vectorstore"]["index_name"],
                     embedding=embedding,
                     index_schema=calender_config["Vectorstore"]["index_schema"]
                    )
