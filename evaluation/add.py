import argparse
import json
import os
from typing import List, Union

from langfuse import Langfuse
from tqdm import tqdm
import yaml


parser = argparse.ArgumentParser(description="ASKu-AI-LangFuse: Add items into the LangFuse Dataset.")
parser.add_argument("name", type=str, help="The name of LangFuse dataset which the items are added into.")
parser.add_argument("path", type=str, help="The path of original items that you want to add.")


if __name__ == '__main__':
    # ---------- < Configuration > ---------- 
    exec_args = parser.parse_args()
    dataset_name: str = exec_args.name
    item_path: Union[str|os.PathLike] = exec_args.path
    
    langfuse = Langfuse(); langfuse.auth_check()

    # ---------- < Validation > ----------
    # item 파일(.yaml)의 형식은 고정되어 있습니다. 아래 Notion 페이지에서 확인가능합니다.
    # https://www.notion.so/034179/AI-Data-62f2bb5ec98e4830a2d7c7e50e9cd836
    input: List[str] = []
    expected_output: List[str] = []
    skipped: List[dict] = []
    item: dict[str, str]
    with open(item_path, "r", encoding="utf-8") as f:
        for item in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            input.append(json.dumps({"Q": item["Q"], "C": item["C"]}))
            expected_output.append(item["E"])

    # ---------- < Add > ----------
    langfuse.create_dataset(name=dataset_name)
    for q, e in tqdm(list(zip(input, expected_output))):
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=q,
            expected_output=e,
        )
