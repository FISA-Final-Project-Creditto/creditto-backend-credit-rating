# API 요청과 응답 정의 스키마

from pydantic import BaseModel

class ScoreRequest(BaseModel):
    user_id: int

class ScoreResponse(BaseModel):
    credit_score: int