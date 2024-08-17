import os
from time import sleep
from typing import List

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langfuse import Langfuse
import yaml

from utils.kopas_parser import save_txt


load_dotenv()


if __name__ == '__main__':
    # ---------- < Configuration > ----------
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Kopas":
                data_config = config
                kopas_vars = data_config["Variables"]
                kopas_meta = data_config["Metadata"]

    keywords: List[str] = kopas_vars["keywords"]
    model_name: str = kopas_vars["model_name"]
    out_dir: str = kopas_vars["kopas_out_dir"]
    prompt_name: str = kopas_vars["prompt_name"]
    prompt_version: int = kopas_vars["prompt_version"]
    sum_dir: str = kopas_vars["kopas_sum_dir"]
    temperature: float = kopas_vars["temperature"]
    txt_cut: int = kopas_vars["txt_cut"]

    if not os.path.exists(out_dir): raise FileNotFoundError
    if not os.path.exists(sum_dir): os.makedirs(sum_dir)

    langfuse = Langfuse(); langfuse.auth_check()
    system_template = langfuse.get_prompt(name=prompt_name, version=prompt_version).prompt
    system_message_prompt = SystemMessagePromptTemplate.from_template(template=system_template)

    llm = ChatOpenAI(model=model_name, temperature=temperature)

    # ---------- < Construct Chain > ----------
    chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            MessagesPlaceholder("text")
    ])

    chain = chat_prompt | llm | StrOutputParser()

    # ---------- < Summarize > ----------
    for keyword in keywords:
        with open(os.path.join(out_dir, f'{keyword}.txt'), "r+", encoding="utf-8") as f:
            text = f.read()[:txt_cut]

        summary = chain.invoke({
                "keyword": keyword,
                "text": [HumanMessage(content=text)],
            })

        save_txt(
            path=os.path.join(sum_dir, f'{keyword}_sum.txt'),
            texts=[summary]
        )

        sleep(60) # OpenAI API Rate Limits
