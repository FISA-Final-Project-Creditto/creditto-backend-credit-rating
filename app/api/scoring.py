# API 엔드포인트
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from app.schema.score import (
    ScoreRequest, ScoreResponse, ScoreHistoryResponse,
    CreditScorePredictRequest, CreditScorePredictResponse
)
from app.db.core_banking import get_core_banking_db
from app.db.mydata import get_mydata_db
import app.service.scoring_service as scoring_service
import app.repository.credit_repository as credit_repository
from app.common.exceptions import NotFoundException 

router = APIRouter()


# ================ 신용 점수 계산 엔드포인트 ==================
@router.post("", response_model=ScoreResponse)
def scoring_credit_score(
    request: ScoreRequest,
    core_db = Depends(get_core_banking_db),
    mydata_db = Depends(get_mydata_db)
):
    result = scoring_service.calculate_credit_score(request, core_db, mydata_db)
    return ScoreResponse(credit_score=result["credit_score"])


# ================ 최신 신용 점수 조회 엔드포인트 ==================
@router.get("/{user_id}", response_model=ScoreResponse)
def latest_credit_score(
    user_id: int,
    core_db = Depends(get_core_banking_db)
):
    score = credit_repository.get_latest_credit_score(user_id, core_db)
    return ScoreResponse(credit_score=score)


# ================ 신용 점수 히스토리 엔드포인트 ==================
@router.get("/history/{user_id}", response_model=ScoreHistoryResponse)
def credit_score_history(
    user_id: int,
    core_db = Depends(get_core_banking_db)
):
    history = credit_repository.get_credit_score_history(user_id, core_db)
    return ScoreHistoryResponse(history=history)

# ================ 신용 점수 예측 엔드포인트 ==================
@router.post("/prediction", response_model=CreditScorePredictResponse)
def predict_credit_score(
    request: CreditScorePredictRequest,
    core_db: Session = Depends(get_core_banking_db),
    mydata_db: Session = Depends(get_mydata_db)
):
    if request.user_id == 999: # For demonstration purposes
        raise NotFoundException(message=f"User with ID {request.user_id} not found.")

    result = scoring_service.process_prediction(request, core_db, mydata_db)
    return result       
