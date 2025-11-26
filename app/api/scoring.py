# API 엔드포인트
from fastapi import APIRouter, Depends

from app.schema.score import ScoreRequest, ScoreResponse
from app.db.core_banking import get_core_banking_db
from app.db.mydata import get_mydata_db
import app.service.scoring_service as scoring_service

router = APIRouter()


# ================ 신용 점수 계산 엔드포인트 ==================
@router.post("/api/credit-score", response_model=ScoreResponse)
def scoring_credit_score(
    request: ScoreRequest,
    core_db = Depends(get_core_banking_db),
    mydata_db = Depends(get_mydata_db)
):
    result = scoring_service.calculate_credit_score(request, core_db, mydata_db)
    return ScoreResponse(credit_score=result["credit_score"])


# ================ 최신 신용 점수 조회 엔드포인트 ==================
@router.get("/api/credit-score/{user_id}", response_model=ScoreResponse)
def latest_credit_score(
    user_id: int,
    core_db = Depends(get_core_banking_db)
):
    score = scoring_service.get_latest_credit_score(user_id, core_db)
    return ScoreResponse(credit_score=score)


# ================ 신용 점수 히스토리 엔드포인트 ==================
@router.get("/api/credit-score/history/{user_id}")
def credit_score_history(
    user_id: int,
    core_db = Depends(get_core_banking_db)
):
    history = scoring_service.get_credit_score_history(user_id, core_db)
    return history
