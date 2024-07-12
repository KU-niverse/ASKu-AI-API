import os
import regex as re
from typing import List, Union


# --------------- [ Configuration ] ---------------
rm_search_pat = [
    r"님이 들어왔습니다.", # 입장 메시지
    r"님이 나갔습니다.", # 퇴장 메시지
    r"오픈채팅봇", # 오픈채팅봇 메시지
    r"방장봇", # 방장봇 메시지
    r"삭제된 메시지입니다.", # 삭제된 메시지
    r"사진", # 사진 전송
    r"이모티콘", # 이모티콘 전송
    r"노크", # 노크 기능
]

rm_match_pat = [
    r"-*\s\d{4}년\s\d{1,2}월\s\d{1,2}일\s(월|화|수|목|금|토|일)요일\s-*\n", # 날짜 변경 메시지
    r"채팅방 관리자가 메시지를 가렸습니다.", # 가려진 메시지
]

question_pat = [
    r"(나요|가요|까요)",
]

response_pat = [
    r"(감사|넵|알겠습니다)",
]

# -------------------------------------------------

def load_txt(txt_path: Union[os.PathLike, str]) -> List[str]:
    with open(txt_path, "r+", encoding="utf-8") as f:
        texts = f.readlines() 

    return texts

def remove_lines(texts: List[str]) -> List[str]:
    # texts_cut = texts[cut:] # Remove first 'cut' lines
    texts_rm = []
    for line in texts:
        searched = False
        for search_pattern in rm_search_pat:
            if re.search(search_pattern, line):
                searched = True; break
        
        matched = False
        for match_pattern in rm_match_pat:
            if re.match(match_pattern, line):
                matched = True; break
        
        if searched or matched: continue
        texts_rm.append(line)

    return texts_rm

def merge_lines(texts: List[str]) -> List[str]:
    texts_mg = []
    for line in texts:
        if len(re.findall(r'\[(.*?)\]', line)) != 2:
            if not texts_mg: continue
            texts_mg[-1] += " " + line; continue
        texts_mg.append(line)
    
    return texts_mg

def replace_lines(texts: List[str]) -> List[str]:
    texts_repl = []
    for line in texts:
        repl_line = line.replace("\n", " ").replace("  ", " ")
        texts_repl.append(repl_line + "\n")
    
    return texts_repl

def extract_QA(
        txt_path: Union[os.PathLike, str], 
        keyword: str,
        window_size: int = 20,
        ) -> List[str]:
    
    texts = load_txt(txt_path)
    texts = remove_lines(texts=texts)
    texts = merge_lines(texts=texts)
    texts = replace_lines(texts=texts)

    # save_txt(path="QA24_processed.txt", texts=texts)

    QA_ext = []; line_num = -1
    questions = [("", "")]*window_size; pointer = 0 # Using circular queue
    for line in texts:
        line_num += 1

        # Extract line information
        nickname, time = re.findall(r'\[(.*?)\]', line)[:2]
        # Question matching
        for question_pattern in question_pat:
            if re.search(question_pattern, line) and re.search(keyword, line):
                questions[pointer] = (nickname, line_num); pointer = (pointer+1) % window_size
                break

        # Response matching
        for response_pattern in response_pat:
            if not re.search(response_pattern, line): continue

            cq_indexes = [i for i, (name, _) in enumerate(questions) if name == nickname]
            if not cq_indexes: continue

            question_index = cq_indexes[0]
            line_start = questions[question_index][1]
            line_end = line_num

            if line_end - line_start > window_size: continue
            QA_ext.extend(texts[line_start:line_end+1]); QA_ext.append("\n")

    QA_ext = remove_times(QA_ext)
    QA_ext = replace_names(QA_ext)

    return QA_ext

def remove_times(texts: List[str]) -> List[str]:
    result = []
    for line in texts:
        if line == "\n": 
            result.append("\n"); continue
        _, time = re.findall(r'\[(.*?)\]', line)[:2]
        time_removal_pat = re.escape(f"[{time}]")
        result.append(re.sub(time_removal_pat, "", line).replace("  ", " "))
    
    return result

def replace_names(texts: List[str]) -> List[str]:
    result = []
    stack = []; nicknames = []
    for line in texts:

        if line == "\n": 
            nicknames = list(set(nicknames))
            mapping = {nickname: f"[{i}]" for i, nickname in enumerate(nicknames)}
            for _line in stack:
                _nickname = re.findall(r'\[(.*?)\]', _line)[:1][0]
                name_repl_pat = re.escape(f"[{_nickname}]")
                result.append(re.sub(name_repl_pat, mapping[_nickname], _line).lstrip(" "))

            result.append("\n")

            stack = []; nicknames = []
            continue
        
        nickname = re.findall(r'\[(.*?)\]', line)[:1][0]
        nicknames.append(nickname)
        stack.append(line)
    
    return result

def save_txt(path: Union[os.PathLike, str], texts: List[str]) -> None:
    with open(path, "w+", encoding="utf-8") as f:
        for line in texts: 
            f.write(line)

