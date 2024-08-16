import os
import yaml
from dotenv import load_dotenv


load_dotenv()


if __name__ == '__main__':
    # ---------- < Configuration > ----------
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Question":
                data_config: dict = config
                question_vars: dict = data_config["Variables"]
                question_meta: dict = data_config["Metadata"]

    question_file: str = question_vars["question_file"]

    # ---------- < Load > ----------
    file_path = question_file
    questions = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line:
                questions.append(line)

    # ---------- < hook1 > -----------
    with open(os.getenv("MANAGE_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Question_SETUP":
                question_config = config

    # ---------- < Indexing > ----------
    from langchain_community.vectorstores.redis import Redis
    from langchain_openai.embeddings import OpenAIEmbeddings

    Embedding = OpenAIEmbeddings()

    Redis.from_texts(
        texts=questions,
        redis_url=question_config["Vectorstore"]["url"],
        index_name=question_config["Vectorstore"]["index_name"],
        embedding=Embedding,
        index_schema=question_config["Vectorstore"]["index_schema"]
    )
