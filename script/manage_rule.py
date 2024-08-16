import argparse
import os
from typing import List

from dotenv import load_dotenv
import yaml

from langchain_community.document_loaders.pdf import PDFMinerLoader
from langchain_core.documents import Document

from utils.parser import Ruleparser


load_dotenv(dotenv_path="./.env")
parser = argparse.ArgumentParser(description="ASKu-AI: SETUP Vectorstore FROM Rule data.")
parser.add_argument("-SETUP", default=False, help="If True, then creates an index in Vectorstore")


if __name__ == '__main__':
    # ---------- < Configuration > ----------
    exec_args = parser.parse_args()
    
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Rule":
                data_config: dict = config
                rule_vars: dict = data_config["Variables"]
                rule_meta: dict = data_config["Metadata"]
    
    rule_dir: str = rule_vars["rule_dir"]
    
    # ---------- < Load > ----------
    rule_all: List[Document] = []
    for subrule_dir in os.listdir(rule_dir):
        for file_name in os.listdir(os.path.join(rule_dir, subrule_dir)):
            rule_pages: List[Document] = PDFMinerLoader(file_path=os.path.join(rule_dir, subrule_dir, file_name)).load()
            # rule_pages: List[Document] = [(page1), (page2), (page3), ...]
            rule_contents = ''.join([page.page_content for page in rule_pages])
            rule_all.append(Document(page_content=rule_contents, metadata={"file_name": file_name}))

    # ---------- < Parsing > ----------
    rule_parsed = Ruleparser(config=data_config).parse(items=rule_all)

    # ---------- < hook1 > -----------
    if not exec_args.SETUP: quit()
    
    with open(os.getenv("MANAGE_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "RULE_SETUP": 
                rule_config = config

    # ---------- < Indexing > ----------
    from langchain_community.vectorstores.redis import Redis
    from langchain_openai.embeddings import OpenAIEmbeddings

    Embedding = OpenAIEmbeddings()
    Redis.from_texts(texts=rule_parsed,
                     redis_url=rule_config["Vectorstore"]["url"],
                     index_name=rule_config["Vectorstore"]["index_name"],
                     embedding=Embedding,
                     index_schema=rule_config["Vectorstore"]["index_schema"]
                     )
