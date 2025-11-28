from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schema.score import ScoreRequest, CreditScorePredictRequest
from app.service.feature_extractor import extract_features
from app.service.score_calculator import calculate_final_score
from app.service.score_predict import predict_credit_score_growth 

from app.repository.credit_repository import (
    save_latest_credit_score,
    save_credit_score_history,
    get_latest_credit_score as repo_get_latest,
    get_credit_score_history as repo_get_history
)

# =========================================================
# 신용 점수 계산 및 저장
# =========================================================
def calculate_credit_score(request: ScoreRequest, core_db: Session, mydata_db: Session):
    user_id = request.user_id

    # DB 조회
    overseas_rows = core_db.execute(text("SELECT send_amount, status, created_at FROM overseas_remittance WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
    card_rows = mydata_db.execute(text("SELECT tx_datetime, tx_amount, pay_type, tx_category, credit_limit, outstanding_amt, collected_at FROM mydata_card WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
    loan_rows = mydata_db.execute(text("SELECT loan_principal, interest_rate, status, overdue_count_12m, overdue_amount, max_overdue_days, last_overdue_dt, collected_at FROM mydata_loan WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
    transaction_rows = mydata_db.execute(text("SELECT tx_datetime, amount, direction, category, balance_after, collected_at FROM mydata_transaction WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()

    features = extract_features(transaction_rows, card_rows, loan_rows, overseas_rows)
    credit_score = calculate_final_score(features)

    save_latest_credit_score(core_db, user_id, credit_score)
    save_credit_score_history(core_db, user_id, credit_score)
    
    return {"credit_score": credit_score}


# =========================================================
# 미래 점수 예측 
# =========================================================
def process_prediction(request: CreditScorePredictRequest, core_db: Session, mydata_db: Session):
    user_id = request.user_id
    
    # 현재 유저 데이터 조회
    overseas_rows = core_db.execute(text("SELECT send_amount, remittance_status, created_at FROM overseas_remittance WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
    card_rows = mydata_db.execute(text("SELECT tx_datetime, tx_amount, pay_type, tx_category, credit_limit, outstanding_amt, collected_at FROM mydata_card WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
    loan_rows = mydata_db.execute(text("SELECT loan_principal, interest_rate, status, overdue_count_12m, overdue_amount, max_overdue_days, last_overdue_dt, collected_at FROM mydata_loan WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()
    transaction_rows = mydata_db.execute(text("SELECT tx_datetime, amount, direction, category, balance_after, collected_at FROM mydata_transaction WHERE user_id = :user_id"), {"user_id": user_id}).fetchall()

    # Feature 추출
    features = extract_features(transaction_rows, card_rows, loan_rows, overseas_rows)
    features["user_id"] = user_id 

    # 계산 로직 호출
    result = predict_credit_score_growth(features, request.monthly_amount)
    
    return result


# =========================================================
# 단순 조회 서비스
# =========================================================
def get_latest_credit_score(user_id: int, core_db: Session):
    return repo_get_latest(user_id, core_db)

def get_credit_score_history(user_id: int, core_db: Session):
    return repo_get_history(user_id, core_db)