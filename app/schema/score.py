# API 요청과 응답 정의 스키마

from pydantic import BaseModel

# 요청: user_id
class ScoreRequest(BaseModel):
    user_id: int

# 최신 점수 조회: 신용 점수
class ScoreResponse(BaseModel):
    credit_score: int

# 히스토리 조회: 월별 평균 점수 -> 리스트 형태로 반환
class ScoreHistoryItem(BaseModel):
    year: int
    month: int
    avg_score: int

class ScoreHistoryResponse(BaseModel):
    history: list[ScoreHistoryItem]  # 최대 7개월치


# ===============================================
# 신용 점수 예측

# 요청: 유저 ID, 월 정기 송금액
class CreditScorePredictRequest(BaseModel):
    user_id: int
    monthly_amount: float # 정기 송금 등록할 월 금액

# 예측 점수 정보
class PredictedScore(BaseModel):
    score: int # 예측 점수
    delta: int # 상승폭

# 응답: 예측 응답 전체
class CreditScorePredictResponse(BaseModel):
    user_id: int
    monthly_remit_amount: float
    current_score: int

    after_6m: PredictedScore
    after_12m: PredictedScore
    after_18m: PredictedScore