# ASKu AI API

## Dev Environment Setting
프로젝트를 진행하기 위해 다음과 같은 Setup이 필요합니다.
1. Docker Setup
2. Environment Setup
3. VectorDB Setup
4. Django Setup

### 1. Docker Setup 
Local Redis-stack Docker Container 환경을 필요로 합니다.
Local Docker Setup과 관련된 절차는 [Notion: Docker Setting](https://www.notion.so/034179/Docker-Setting-9a9b108fa0944d5c9553bfdc0974e035)을 확인해주세요.

### 2. Environment Setup 
#### 2.1 Directory Setting
[Notion: Data Files](https://www.notion.so/034179/ASKu-AI-API-992c992ed43249a6afd91852dfad7d7c)에 접속하여 data, schema, systemprompt.txt .env 파일들을 다운받은 후 아래와 같이 디렉토리를 구성해주세요.

```Plain text
. 
├─ chatbot
├─ config
├─ data
│  ├─rule (생략)
│  │   ├─제10편 내규
│  │   ├─제2편 학칙 및 학위수여규정
│  │   ├─제3편 학사관리-교무행정
│  │   ├─제3편 학사관리-학생행정
│  │   └─제5편 부속기관
│  ├─schema 
│  │   ├─data_schema.yaml
│  │   ├─eval_schema.yaml
│  │   └─manaage_schema.yaml 
│  ├─docstore(*script 코드를 실행하면 자동적으로 이 위치에 생성됨)
│  └─RecordManager(*script 코드를 실행하면 자동적으로 이 위치에 생성됨)
├─ script
│  └─utils 
├─ .env 
├─ .gitignore 
├─ manage.py
├─ Pipfile
├─ Pipfile.lock 
└─ systemprompt.txt
```

##### Dotenv Setting
Dotenv 파일은 아래의 항목들로 구성되어 있습니다. 
```
SECRET_KEY=your-secret-key
IS_DEVELOP=True
DJANGO_SETTINGS_MODULE=config.settings pylint --load-plugins pylint_django

# DOCKERIZE SETTINGS
PORT=0000
USE_DOCKER=True

# MYSQL SETTINGS
MYSQL_NAME=mysql-name
MYSQL_USER=mysql-user
MYSQL_PASSWORD=mysql-password
MYSQL_HOST=mysql-host-address
MYSQL_PORT=3306

# REDIS SETTINGS
REDIS_URL=redis://localhost:6379
REDIS_REQUIREPASS=redis-requirepass

# OPENAI SETTINGS
OPENAI_API_KEY=your-openai-api-key

# INDEX
WIKI_INDEX=WIKI_INDEX
RULE_INDEX=RULE_INDEX

# PATH
PICKLE_PATH=PICKLE_PATH

# LANGFUSE SETTINGS
LANGFUSE_SECRET_KEY=LANGFUSE_SECRET_KEY
LANGFUSE_PUBLIC_KEY=LANGFUSE_PUBLIC_KEY
LANGFUSE_HOST=https://cloud.langfuse.com

# Schema
DATA_SCHEMA_PATH="./data/schema/data_schema.yaml"
MANAGE_SCHEMA_PATH="./data/schema/manage_schema.yaml"
```

#### 2.2 Environment Setting
개발 환경을 구성하기 위하여 파이썬 가상 환경을 생성합니다. \
가상환경은 pipenv를 사용하여 설정합니다.
권장 Python 버전은 3.10.11입니다. 해당 파이썬 버전이 없다면 설치 후 진행해주세요.

```shell
# install & 가상환경 만들기
> pipenv install

# 가상환경 실행
> pipenv shell
```

아래의 명령어들은 개발을 하며 알아두면 좋은 명령어입니다.
```shell

# 추가 패키지 설치하기
> pipenv install 패키지명
  `pip freeze > requirements.txt`과 같이 라이브러리 설치 후 명령어를 실행하지 않아도, pipenv는 자동으로 의존성 관리 파일을 업데이트합니다.

# 패키지 라이브러리 버전 확인
> pip show 패키지

# 단일 명령어를 가상환경 내부 python으로 돌리기
> pipenv run 명령어_블라블라

# 의존성 그래프 출력
> pipenv graph

# 가상환경 삭제
> pipenv --rm

# 가상환경 비활성화
> deactivate
```


### 3. VectorDB Setup
script 디렉토리에는 RAG Vectorstore를 구성하는 데 필요한 데이터의 적재, 로드 및 저장과 관련된 코드들이 위치합니다. \
모든 코드는 가상환경을 활성화 한 후 실행해주세요.

#### 3.1 VectorDB Setting
다음 명령어를 실행해주세요.
```shell
# 학칙 script 실행
> python script/manage_rule.py -SETUP True

# Wiki script 실행
> python script/manage_wiki.py -SETUP True

```
script를 실행하는데 약간의 시간이 소요됩니다.

학칙 script는 실행 후 출력이 없습니다. 
Wiki script는 실행 후 다음과 같이 출력됩니다. \
{'num_added': 395, 'num_updated': 0, 'num_skipped': 0, 'num_deleted': 0}


##### VectorDB Setup 부가 설명
```shell
# script 실행
> python script/{script_name}.py

```

몇몇 스크립트는 Optional Argument 파라미터를 입력받습니다. (Optional이기 때문에 입력하지 않아도 작동합니다.) \
스크립트 실행 명령 뒤에 "-h" 키워드를 추가하여 Optional Argument에 대한 설명을 확인할 수 있습니다.
```shell
# 도움말 보기 예시
> python script/manage_rule.py -h

: '
usage: manage_rule.py [-h] [-SETUP SETUP]

ASKu-AI: SETUP Vectorstore FROM Rule data.

optional arguments:
  -h, --help    show this help message and exit
  -SETUP SETUP  If True, then creates an index in Vectorstore
'
```

#### 3.2 VectorDB Index Inspection
Redis Vectorstore Indexing과 관련된 코드를 작업한 후에는 반드시 Index가 제대로 생성되었는 지 확인해주세요. \
Redis가 설치된 Docker Container의 터미널, 또는 그 터미널과 통합된 Linux Terminal에 접속해주세요.

**manage_wiki** 스크립트를 실행할 때에는 반드시 data 디렉토리 내의 RecordManager를 삭제해주시기 바라며, \
**manage_wikiUpdate** 스크립트를 실행할 때에는 .env 파일 내에 이전 InMemorySotre_path를 업데이트 해주세요.
```bash
# Redis cilent 접속
redis-cli

# 존재하는 Redis Index 확인
127.0.0.1:6379> ft._list

# 생성한 Index의 Record 개수 및 hash_indexing_failures 의 값이 0인지 확인
127.0.0.1:6379> ft.info ($your_index_name)

# 비정상적으로 생성된 Redis Index는 삭제
127.0.0.1:6379> ft.dropindex ($your_index_name) DD
```


### 4. Django Setup

```장고_서버_실행
# 마이그레이션
> python manage.py migrate

# 장고 서버 실행
> python manage.py runserver

```

### 문서화 확인하는 방법

- [127.0.0.1:8000/swagger](127.0.0.1:8000/swagger) 또는 [127.0.0.1:8000/redoc](127.0.0.1:8000/redoc) 접속하기

