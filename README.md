# ASKu AI API

## Dev Environment Setting

### 프로젝트 폴더 바로 아래에 .env 파일을 만들고 아래 내용을 넣어주세요.
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
```

### 라이브러리 설정하기 
#### pipenv
```shell
# install & 가상환경 만들기
> pipenv install

# 가상환경 실행
> pipenv shell 

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

```

### Tip! venv exit하는법
```shell
> deactivate
```
 

## 문서화 확인하는 방법
- [127.0.0.1:8000/swagger](127.0.0.1:8000/swagger) 또는 [127.0.0.1:8000/redoc](127.0.0.1:8000/redoc) 접속하기 