# creditto-backend-credit-rating

<br>

신용 점수를 계산하는 FastAPI 기반 백엔드 서버입니다.  
Core Banking DB + MyData DB 조회 -> ML 모델 기반 점수 산출 -> DB 저장까지 수행합니다.

<br>

## 1. Python 가상환경(venv) 생성 & 활성화,
### - Windows (Git Bash)

`python -m venv venv`

`source venv/Scripts/activate`

### - Windows (PowerShell)

`python -m venv venv`

`venv\Scripts\Activate`

### - Mac / Linux
`python3 -m venv venv`

`source venv/bin/activate`

(venv) 표시가 프롬프트 앞에 보이면 성공

<br>

## 2. 프로젝트 필수 패키지 설치

FastAPI, SQLAlchemy, MySQL 드라이버, Pydantic Settings, ML 관련 패키지 설치:

`pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pandas numpy scikit-learn pydantic-settings`

<br>

## 3. 환경설정(.env) 파일 생성

```
MODEL_PATH=credit_model.pkl
SCALER_PATH=scaler.pkl

# DB URL
CORE_BANKING_DB_URL=~
MYDATA_DB_URL=~

```

<br>

## 4. 서버 실행
`uvicorn app.main:app --reload`

특정 포트를 사용하고 싶다면: ex) 9090
`uvicorn app.main:app --host 0.0.0.0 --port 9090 --reload`

<br>

