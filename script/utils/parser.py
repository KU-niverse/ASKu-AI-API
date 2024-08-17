import copy
import os
import re
from typing import Callable, Dict, List, Pattern, Tuple, Union

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


class Wikiparser():
    parent_sep: Pattern = re.compile(r"(?<!=)==\s*([^=\n]+)\s*==(?!=)")
    child_sep: Pattern = re.compile(r'={3,}\s*([^=]+)\s*={3,}')
    repl_patterns: Dict[str, Tuple[Pattern[str], Union[str, Callable]]] = {
        "url": (re.compile(r"\[\[(?:(?!\]\]).)*\]\]"), ""),
        "bold": (re.compile(r"('''+)(?:(?!''').)*(('''+))"), lambda x: x.group(0)[3:-3]),
    }
    
    def __init__(self, config: dict) -> None:
        self.config = config
        self.schema: List[str] = config["Metadata"]["schema"]
        self.source_id_key: str = config["Variables"]["source_id_key"]
    
    def parse(
        self, items: List[Dict[str, str]]) -> List[List[Document]]:
        wiki_docs = [self.preprocess(item) for item in items]
        
        parent_docs, child_docs = [], []
        for wiki_doc in wiki_docs:
            parents = self.parse_WikiToParent(wiki_doc=wiki_doc)
            parent_docs += parents

            for parent in parents:
                children = self.parse_ParentToChild(parent=parent)
                child_docs += children
        
        return [parent_docs, child_docs]
    
    def preprocess(
        self, wiki_item: Dict[str, str]) -> Document:
        
        text = wiki_item["text"]
        preprcs_seq = Wikiparser.repl_patterns.values()
        for old, new in preprcs_seq:
            text = re.sub(old, new, text)
        
        metadata = copy.deepcopy(wiki_item); del metadata["text"]
        
        return Document(page_content=text, metadata=metadata)
        
    def parse_WikiToParent(
        self, wiki_doc: Document) -> List[Document]:

        # Final sections = ['', (title1), (content1), (title2), (content2), ...]
        sections: List[str] = re.split(pattern=Wikiparser.parent_sep, string=wiki_doc.page_content)

        # Final sections_titles = [(title1), (title2), ...]
        # Final sections_contents = [(content1), (content2), ...]    
        section_titles = sections[1::2]; section_contents = sections[2::2]
        
        parent = []
        for section_num, (section_title, section_content) in enumerate(list(zip(section_titles, section_contents))):
            parent_content = section_content.replace("\\n", "").replace("  ", " ").replace("&amp", "&"
                                                    ).replace("&lt", "<").replace("&gt", ">").strip("\n")
            parent_metadata = {
                self.source_id_key: f"{wiki_doc.metadata['id']}-{section_num}",
                self.config["Variables"]["source"]: section_title,
                "title": wiki_doc.metadata["title"]
            }
            
            parent.append(Document(
                page_content=parent_content,
                metadata=parent_metadata
            ))
            
        return parent
    
    def parse_ParentToChild(
        self, parent: Document) -> List[Document]:
        
        # Final subsections = [(subcontent0), (subtitle1), (subcontent1), (subtitle2), (subcontent2), ...]
        subsections = re.split(pattern=Wikiparser.child_sep, string=parent.page_content)
        
        # Final paragrphs = [(subcontent0), ([[subtitle1]] subcontent1), ([[subtitle2]] subcontent2), ...]
        paragraphs = [subsections[0]]
        for i in range(2, len(subsections), 2):
            paragraphs.append(f"[[{subsections[i-1].rstrip()}]] " + subsections[i])
        
        paragraphs_docs = []
        for paragraph in paragraphs:
            paragraphs_docs.append(Document(page_content=paragraph,
                                            metadata={
                                                self.source_id_key: parent.metadata[self.source_id_key],
                                                "title": parent.metadata["title"],
                                            },
                                            ))

        text_splitter = RecursiveCharacterTextSplitter()
        children = text_splitter.split_documents(paragraphs_docs)
        
        return children
    

class Ruleparser():
    repl_patterns: Dict[str, Tuple[Pattern[str], Union[str, Callable]]] = {
        "utf1": ("\\n", ""),
        "utf2": ("\\uf000", ""),
        "utf3": ("\\x0c", ""),
        "utf4": ("\\xa0", ""),
        "utf5": ("\u3007","1"),
        "preamble1":(r"부\s*칙.*", ''),
        "revision1": (r"\d+\.\s?\d+\s?\.?\.?\s?\d*\s?\.?\s?(일부\s*개정|제\s*정|전부\s*개정|전면\s*개정|개\s*정)", ""),
        "revision2": (r"\d+년\s?\d+월\s?\d일\s*(일부\s*개정|제\s*정|전부\s*개정|전면\s*개정|개\s*정)", ""),
        "parenthesis1": (re.compile("【"), r"("),
        "parenthesis2": (re.compile("】"), r")"),
        "author1": (r"<(학사팀|원격교육센터, 학사팀|입학전형관리팀, 체육위원회|교무기획팀|학사팀, 학생지원부|학생지원부|학사팀, 대학원행정팀|교육혁신팀)>", ""),
        "author2": (r"<(교무학사팀|교육혁신팀, 입학전형관리팀|대학원 행정실|대학원행정팀|학생지원부, 대학원 행정실, 각 특수·전문대학원 행정실)>", ""),
        "author3": (r"<(인력개발팀|입학전형관리팀, 학생지원팀|글로벌서비스센터, 국제교육팀, 학생지원부|국제교육팀|학생지원부, 대외협력부)>", ""),
        "author4": (r"<(대학사업팀, 학생지원부|학생지원부, 학생복지부|사회공헌지원부, 학생지원부|글로벌리더십센터, 학생지원부|학생지원팀, 대외협력팀)>", ""),
        "author5": (r"<(학생지원팀|정경대학행정실|글로벌서비스센터|학생지원부, 경영대학행정실, 기금기획부|학생지원팀, 문과대학행정실, 이과대학행정실)>", ""),
        "author6": (r"<(사회공헌지원부|행정전문대학원 행정실|정책대학원 행정실|국제교류팀, 대외협력팀|학술정보서비스팀|학생상담센터|장애학생지원센터)>", ""),
        "author7": (r"<(안암학사 행정팀|호연학사 관리운영부|인권·성평등센터|현장실습지원센터|교양교육원|체육위원회,학생지원부|크림슨창업지원단)>", ""),
        "author8": (r"<(교양교육원행정실|학술정보기획팀|교육매체지원부|문과대학 행정실|물리학과행정실, 학생지원팀)>", ""),
        "author9": (r"<(화공생명공학과행정실|생명공학부, 학생지원부|생명과학대학 행정실|경영대학행정실|국제학부|정경대학 행정학과 행정실, 학생지원팀)>", ""),
        "author10": (r"<(공과대학행정실|기계공학부행정실|경영대학 행정실|자유전공학부 행정실|식품공학과 행정실|정경대학행정실|가정교육과행정실)>", ""),
        "author11": (r"<(화공생명공학과행정실|기업산학연협력센터|정경대학 행정실|이과대학 행정실|공과대학 행정실|의과대학 학사지원부|사범대학 행정실)>", ""),
        "author12": (r"<(간호대학 행정실|보건과학대학 행정실|정보대학 행정실|디자인조형학부 행정실|국제대학 행정실|미디어학부 행정실|심리학부 행정실)>", ""),
        "author13": (r"<(문과대학행정실|정보대학행정실|이과대학행정실|생명과학대학행정실|스마트모빌리티학부행정실|대외협력부, 학생지원부|체육위원회, 학생지원부)>", ""),
        "author14": (r"2019. 09. 01.<KU개척마을운영지원팀>", ""),
        "space1": (r'제\s*(\d+)\s*조',  r'제\1조'),
        "space2": (r'제\s*(\d+)\s*장',  r'제\1장'),
        "space3": (r'제\s*(\d+)\s*절',  r'제\1절'),
        "space4": (r'제\s*(\d+)\s*관',  r'제\1관'),
        "space5": (r"\s+", " "),
        "revision3": (r"<(개\s?정|본조\s?신설|신\s?설|삭\s?제)?[\s\d.,]+>", ""),
        "space6": (re.compile("\.(?![ ])"), '. '),
        "space7": (r'(\S)(\d{1}\.)', r'\1 \2'), # "1.(학칙)" -> "1. (학칙)" 으로 공백 추가
        "utf6": (r"[“|”]", '"'),
        "utf7": (r"[‘|’]", "'"),
        "space8": (r"\s+", " "),
        "utfnum1": (r"１", "1"),
        "utfnum2": (r"２", "2"),
        "utfnum3": (r"３", "3"),
        "utfnum4": (r"４", "4"),
        "utfnum5": (r"５", "5"),
        "utfnum6": (r"６", "6"),
        "utfnum7": (r"７", "7"),
        "utfnum8": (r"８", "8"),
    }
        
    def __init__(self, config: dict) -> None:
        self.config = config

    def parse(
        self, items: List[Document]) -> List[str]:
        
        rule_docs: List[Document] = [self.preprocess(item) for item in items]
        
        prefixed_rule_docs = []
        for rule_item in rule_docs:
            articles = self.parse_RuleToArticle(rule_item=rule_item)
            prefixed_articles = self.add_Prefix(rule_name=rule_item.metadata["rule_name"], articles=articles)
            prefixed_rule_docs += prefixed_articles
        
        return prefixed_rule_docs

    def preprocess(
        self, rule_item: Document) -> Document:

        file_name = rule_item.metadata["file_name"]
        rule_number, rule_name = map(lambda x: x.rstrip(), file_name[:-5].split('(', maxsplit=1))
        rule_name2 = rule_name.replace("(", "\\(").replace(")", "\\)")
        rule_metadata = {"rule_name": rule_name}      
        
        # RE Substitute: Whitespace, Revision, Unicode, etc.
        rule_content = rule_item.page_content
        for old, new in Ruleparser.repl_patterns.values():
            rule_content = re.sub(old, new, rule_content)
        
        # Bad Case: Bad Page number for "3-4-24(이석준장학금 지급 내규).pdf"
        if rule_content[0].isdigit(): rule_content = rule_content[1:]
        
        # Delete Page Number: "(숫자가 아닌 문자)- # -"
        rule_content = re.sub(r"(?<!\d)-\s*\d+\s*-", "", rule_content)
        
        # Delete Header: 1. "고려대학교 규정 \((문서 이름)\)[#-#-#]" 2. "고려대학교 \((문서 이름)\)"
        rule_content = re.sub(re.compile(f"고려대학교\s*규정{rule_name2}\s?[\[|\(]{rule_number}[\]|\)]\d?\s?"), "", rule_content)
        rule_content = re.sub(re.compile(f"고려대학교\s*(규정)?{rule_name2}\d?\s?"), "", rule_content)

        return Document(page_content=rule_content, metadata=rule_metadata)
        
    def parse_RuleToArticle(
        self, rule_item: Document) -> List[str]:
        
        rule_content = rule_item.page_content
        rule_name = rule_item.metadata["rule_name"]
        
        # Step 1: 상위 목차로 분할
        rule_content_split = re.split(re.compile("(제\d{1}[관|장|절])"), rule_content)
        # Validation(NoneType)
        rule_content_split = [text for text in rule_content_split if type(text)==str]
        # Bad Cases: 문서 제목으로 시작하지 않는 경우  
        if rule_content_split[0].startswith("제1"):
            rule_content_split[0] = rule_name + rule_content_split[0]
		              
        # rule_content_split: List[str] = [(chapter1), (content1), (chapter2), (content2), ...]
        chapters = []
        for idx, toptable in enumerate(rule_content_split):
            if (idx%2 == 0) and (idx != 0):
                chapters[-1] += " " + toptable.strip(" "); continue
            chapters.append(toptable.strip(" "))
        # chpaters: List[str] = [(chapter1 content1), (chapter2 content2), ...]
        
        # Step 2: 실제 조항 단위로 분할
        articles = []; article_cnt = 0
        for chapter in chapters:
            chapter_split = re.split(r"(제\s?\d+\s?조\s?[\(|<].*?[\)|>])", chapter)
            for idx, article in enumerate(chapter_split):
                if article_cnt == 0: 
                    articles.append(article); article_cnt += 1; continue
                elif idx == 0:
                    articles.append(article); continue
                
                if article.startswith(f"제{article_cnt}조"):
                    # The below line ensures consistent spacing in the all articles
                    article_title = f"제{article_cnt}조" + article.strip(f"제{article_cnt}조").strip(" ")
                    articles.append(article_title); article_cnt += 1
                elif len(articles) == 1:
                    articles.append(article)
                else:
                    articles[-1] += " " + article.strip(" ")
    
        return articles
    
    def add_Prefix(
        self, rule_name: str, articles: List[str]) -> List[str]:

        prfx_stack = [(-1, rule_name)]
        prfx_pattern = [r"^제\d+장", r"^제\d+절", r"^제\d+관", r"^제\d+조"]
        prefixed_articles = []
        
        for article in articles:
            for (prfx_level, prfx) in enumerate(prfx_pattern):
                if re.match(pattern=prfx, string=article):
                    if prfx_level == 3:
                        prefix = ", ".join([prfx[1] for prfx in prfx_stack]) + ", "
                        prefixed_articles.append(prefix + article)
                        
                    elif prfx_stack[-1][0] < prfx_level:
                        prfx_stack.append((prfx_level, article.rstrip()))
                        
                    elif prfx_stack[-1][0] >= prfx_level:
                        while prfx_stack and prfx_stack[-1][0] >= prfx_level:
                            prfx_stack.pop()
                        prfx_stack.append((prfx_level, article.rstrip()))
        
        return prefixed_articles


class Calenderparser():
    repl_patterns: Dict[str, Tuple[Pattern[str], Union[str, Callable]]] = {
        "line1": (r"\n\n\n\n\n", " "),
        "line2": (r"\n\n\n", " "),
        "utf1": ("∼", "~"),
        "date1": (r"(\d+~\d+)\n([월화수목금토일]~[월화수목금토일])", r"\n\1(\2)"),
        "date2": (r"(\d+)\n([월화수목금토일])", r"\n\1(\2)"),
        "year1": (r"2024\n", r"\n2024\n"),
        "year2": (r"2025\n", r"\n2025\n"),
        "month1": (r" (\d{1,2})\n", r"\n\1"),
        "line3": (r"\n\n", r"\n"),
    }

    def __init__(self, config: dict) -> None:
        self.config = config
    
    def parse(
        self, items: List[Document]) -> List[str]:

        calender_docs: List[Document] = [self.preprocess(item) for item in items]   

        prefixed_calender_docs = []

        for calender_item in calender_docs:
            prefixed_calender_docs += self.add_Prefix(calender_item)

        return prefixed_calender_docs
    
    def preprocess(
        self, calender_item: Document) -> Document:

        calender_content = calender_item.page_content
        calender_metadata = calender_item.metadata

        for old, new in Calenderparser.repl_patterns.values():
            calender_content = re.sub(old, new, calender_content)

        return Document(page_content=calender_content, metadata=calender_metadata)

    def add_Prefix(
        self, calender_item: Document) -> List[str]:

        calender_content = calender_item.page_content

        split_content = re.split("\n", calender_content)
        split_content = split_content[5:]

        prefixed_content = []

        year, month, date, activity = "", "", "", ""

        for content in split_content:
            if content.isdigit():
                if len(content) == 4:
                    year = content
                else:
                    month = content
            elif re.match(r"\d+~\d+\([월화수목금토일]~[월화수목금토일]\)|\d{1,2}\([월화수목금토일]\)", content):
                date = content
            else:
                activity = content

                prefixed_content.append(f"{activity}: {year}년 {month}월 {date}일")
            
        return prefixed_content
