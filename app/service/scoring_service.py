# app/service/scoring_service.py

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.schema.score import ScoreRequest
from app.service.feature_extractor import extract_features
from app.service.score_calculator import calculate_final_score
from app.repostiory.credit_repository import (
    save_latest_credit_score,
    save_credit_score_history
)

# ================ 신용 점수 계산 메서드 ==================
def calculate_credit_score(request: ScoreRequest,
                           core_db: Session,
                           mydata_db: Session):
    user_id = request.user_id

    # 1) Core Banking DB Raw 데이터 조회
    overseas_rows = core_db.execute(
        text("""
        SELECT send_amount, status, remittance_date
        FROM overseas_remittance_raw
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchall()

    # 2) MyData DB Raw 데이터 조회
    card_rows = mydata_db.execute(
        text("""
        SELECT tx_datetime, tx_amount, pay_type, tx_category,
               credit_limit, outstanding_amt, collected_at
        FROM mydata_card_raw
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchall()

    loan_rows = mydata_db.execute(
        text("""
        SELECT loan_principal, interest_rate, status,
               overdue_count_12m, overdue_amount, max_overdue_days,
               last_overdue_dt, collected_at
        FROM mydata_loan_raw
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchall()

    transaction_rows = mydata_db.execute(
        text("""
        SELECT tx_datetime, amount, direction, category,
               balance_after, collected_at
        FROM mydata_transaction_raw
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchall()

    # 3) Feature 데이터 계산 호출
    features = extract_features(
        transaction_rows = transaction_rows,
        card_rows = card_rows,
        loan_rows = loan_rows,
        remit_rows = overseas_rows
    )

    # 4) 신용 평가 점수 계산 호출
    credit_score = calculate_final_score(
        features=features
    )

    # 5) DB 저장
    save_latest_credit_score(core_db, user_id, credit_score)
    save_credit_score_history(core_db, user_id, credit_score)

    
    # 신용 점수 반환
    return {
        "credit_score": credit_score
    }