import os
from typing import List

from dotenv import load_dotenv
import yaml

from utils.kopas_parser import extract_QA, save_txt


load_dotenv()


if __name__ == '__main__':
    # ---------- < Configuration > ----------
    with open(os.getenv("DATA_SCHEMA_PATH"), "r+", encoding="utf-8") as f:
        for config in yaml.load_all(stream=f.read(), Loader=yaml.FullLoader):
            if config["Name"] == "Kopas":
                data_config = config
                kopas_vars = data_config["Variables"]
                kopas_meta = data_config["Metadata"]

    ext_dir: str = kopas_vars["kopas_ext_dir"]
    keywords: List[str] = kopas_vars["keywords"]
    out_dir: str = kopas_vars["kopas_out_dir"]
    raw_dir: str = kopas_vars["kopas_raw_dir"]

    if not os.path.exists(raw_dir): raise FileNotFoundError
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    if not os.path.exists(ext_dir): os.makedirs(ext_dir)

    # ---------- [ Extraction ] ----------
    for txt_name in os.listdir(raw_dir):
        for keyword in keywords:
            QA_ext = extract_QA(
                txt_path=os.path.join(raw_dir, txt_name),
                keyword=keyword,
            )

            save_name = txt_name.rstrip(".txt") + f"_{keyword}.txt"

            if not os.path.exists(os.path.join(ext_dir, txt_name.rstrip(".txt"))):
                os.makedirs(os.path.join(ext_dir, txt_name.rstrip(".txt")))

            save_txt(
                path=os.path.join(ext_dir, txt_name.rstrip(".txt"), save_name),
                texts=QA_ext,
            )

    # ---------- [ Merge ] ----------
    for keyword in keywords:
        merged = []
        for raw_name in os.listdir(ext_dir):
            with open(os.path.join(ext_dir, raw_name, f'{raw_name}_{keyword}.txt'), "r+", encoding="utf-8") as f:
                merged.extend(f.readlines())

        save_txt(
            path=os.path.join(out_dir, f'{keyword}.txt'),
            texts=merged)
