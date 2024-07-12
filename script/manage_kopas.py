import os

from utils.kopas_parser import extract_QA, save_txt


keywords = [
    '학생증',    '졸업',     '대학원',   '휴학',         '전과',     '자퇴', 
    '퇴학',      '징계',     '학식',     '수면실',   '스터디룸',     '열람실',
    '도서관',    '프린터',   '와이파이', '셔틀버스',     '기숙사',   '수강신청',
    '초과학점',  '수희등',   '전필',     '교양',         '결석',     '선수강',
    '계절학기',  '폐강',     '지하철',   '밥약',         '보은',     '고연전',
    '동아리',    '장학금',   '근장',     '교환학생',     '이중전공', '심전'
]

txt_names = [
    "QA24_1.txt", "QA24_0.txt", "QA23.txt", "QA22.txt"
]


# ---------- [ Extraction ] ----------

if not os.path.exists("./output/"): os.mkdir("./output/")

for idx in range(len(txt_names)):
    txt_name = txt_names[idx]
    for keyword in keywords:
        QA_ext = extract_QA(
            txt_path=os.path.join("data", txt_name),
            keyword=keyword,
        )

        save_dir = f'./output/{txt_name[:-4]}_ext/'
        save_name = f'{txt_name[:-4]}_{keyword}.txt'
        if not os.path.exists(save_dir): os.mkdir(save_dir)

        save_txt(
            path=os.path.join(save_dir, save_name),
            texts=QA_ext,
        )

# ---------- [ Merge ] ----------

if not os.path.exists("./output/QA_ext/"): os.mkdir("./output/QA_ext/")

for keyword in keywords:
    ext = []
    for txt_name in txt_names:
        with open(f"./output/{txt_name[:-4]}_ext/{txt_name[:-4]}_{keyword}.txt", "r+", encoding="utf-8") as f:
            ext.extend(f.readlines())

    with open(f"./output/QA_ext/{keyword}.txt", "w+", encoding="utf-8") as f:
        for line in ext: f.write(line)

