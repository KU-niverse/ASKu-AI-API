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
```

### 라이브러리 설정하기
```shell
# 만약 안되면 아래를 넣어보시길
> Set-ExecutionPolicy Unrestricted -Scope Process
# 가상환경 만들기
> python -m venv venv
# 가상환경 활성화
## Windows
> .\venv\Scripts\activate
## Mac
> source venv/bin/activate
## 라이브러리 설치하기
> pip install -r requirements.txt
## django 실행하기
> python manage.py migrate
> python manage.py runserver
```

### Tip! venv exit하는법
```shell
> deactivate
```

### Third party 설치하는 법

```shell
# 가상환경 활성화 후에!
# 설치
> pip intall blahblah
# 다른 작업자가 이를 알 수 있게, requirements.txt에 반영하기
> pip freeze > requirements.txt
```

## 문서화 확인하는 방법
- [127.0.0.1:8000/swagger](127.0.0.1:8000/swagger) 또는 [127.0.0.1:8000/redoc](127.0.0.1:8000/redoc) 접속하기 