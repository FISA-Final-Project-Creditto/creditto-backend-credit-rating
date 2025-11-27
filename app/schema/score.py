# API 요청과 응답 정의 스키마

from pydantic import BaseModel

# 요청: user_id
class ScoreRequest(BaseModel):
    user_id: int

# 최신 점수 조회: 신용 점수
class ScoreResponse(BaseModel):
    credit_score: int

# 히스토리 조회: 월별 평균 점수
class ScoreHistoryItem(BaseModel):
    year: int
    month: int
    avg_score: int

class ScoreHistoryResponse(BaseModel):
    history: list[ScoreHistoryItem]  # 최대 7개월치