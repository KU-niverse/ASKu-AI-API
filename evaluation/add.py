import argparse
import os
from typing import List, Union

from langfuse import Langfuse
import yaml


parser = argparse.ArgumentParser(description="ASKu-AI-LangFuse: Add items into the LangFuse Dataset.")
parser.add_argument("name", help="The name of LangFuse dataset which the items are added into.")
parser.add_argument("path", help="The path of original items that you want to add.")


if __name__ == '__main__':
    # ---------- < Configuration > ---------- 
    exec_args = parser.parse_args()
    dataset_name: str = exec_args.name
    item_path: Union[str|os.PathLike] = exec_args.path
    
    langfuse = Langfuse(); langfuse.auth_check()

    # ---------- < Validation > ----------
    # TODO: Notion API 연동으로 변경
    # item 파일(.yaml)의 형식은 고정되어 있습니다. 아래 Notion 페이지에서 확인가능합니다.
    # https://www.notion.so/034179/LangFuse-b654dacc89714db7a12fa00fc999b585?pvs=4#bae7954f4bdf4d9092117fbca04f78cb
    input: List[str] = []
    expected_output: List[str] = []
    skipped: List[dict] = []
    item: dict[str, str]
    with open(item_path, "r", encoding="utf-8") as f:
        for item in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            try:
                assert item.get("Q")
                assert item.get("G")
                input.append(item["Q"])
                expected_output.append(item["G"])
            except:
                skipped.append(item)

    if skipped: 
        print(f"Validation Failed: {len(skipped)} original items have invalid schema. Check the keys of original items.")
        raise(KeyError)

    # ---------- < Add > ----------
    langfuse.create_dataset(name=dataset_name)
    for q, e in list(zip(input, expected_output)):
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=q,
            expected_output=e,
        )
