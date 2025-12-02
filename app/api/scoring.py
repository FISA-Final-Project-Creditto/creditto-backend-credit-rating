# API 엔드포인트
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from app.schema.score import (
    ScoreRequest, ScoreResponse, ScoreHistoryResponse, CreditReportResponse,
    CreditScorePredictRequest, CreditScorePredictResponse
)
from app.db.core_banking import (
    get_core_banking_read_db,
    get_core_banking_write_db,
)
from app.db.mydata import get_mydata_read_db
import app.service.scoring_service as scoring_service
import app.repository.credit_repository as credit_repository

router = APIRouter()


# ================ 신용 점수 계산 엔드포인트 ==================
@router.post("", response_model=ScoreResponse)
def scoring_credit_score(
    request: ScoreRequest,
    core_read_db = Depends(get_core_banking_read_db),
    core_write_db = Depends(get_core_banking_write_db),
    mydata_db = Depends(get_mydata_read_db)
):
    result = scoring_service.calculate_credit_score(
        request, core_read_db, core_write_db, mydata_db
    )
    return ScoreResponse(credit_score=result["credit_score"])


# ================ 최신 신용 점수 조회 엔드포인트 ==================
@router.get("/{user_id}", response_model=ScoreResponse)
def latest_credit_score(
    user_id: int,
    core_db = Depends(get_core_banking_read_db)
):
    score = credit_repository.get_latest_credit_score(user_id, core_db)
    return ScoreResponse(credit_score=score)


# ================ 신용 점수 히스토리 엔드포인트 ==================
@router.get("/history/{user_id}", response_model=ScoreHistoryResponse)
def credit_score_history(
    user_id: int,
    core_db = Depends(get_core_banking_read_db)
):
    history = credit_repository.get_credit_score_history(user_id, core_db)
    return ScoreHistoryResponse(history=history)


# ================ 신용 보고서 엔드포인트 ==================
@router.get("/report/{user_id}", response_model=CreditReportResponse)
def credit_report(
    user_id: int,
    core_db: Session = Depends(get_core_banking_db),
    mydata_db: Session = Depends(get_mydata_db)
):
    report_data = scoring_service.get_credit_report_data(user_id, core_db, mydata_db)
    return CreditReportResponse(
        credit_score=report_data["credit_score"],
        features=report_data["features"]
    )

# ================ 신용 점수 예측 엔드포인트 ==================
@router.post("/prediction", response_model=CreditScorePredictResponse)
def predict_credit_score(
    request: CreditScorePredictRequest,
    core_db: Session = Depends(get_core_banking_read_db),
    mydata_db: Session = Depends(get_mydata_read_db)
):
    result = scoring_service.process_prediction(request, core_db, mydata_db)
    return result
