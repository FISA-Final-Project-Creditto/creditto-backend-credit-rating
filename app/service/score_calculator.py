# features -> 모델 -> 스케일러 적용 -> 최종 신용점수 산출

import numpy as np
from app.model.load_model import load_credit_model, load_scaler

MODEL_FEATURE_ORDER = [
    "income_avg_6m",
    "income_volatility_6m",
    "spending_avg_6m",
    "saving_rate_6m",
    "min_balance_3m",
    "liquidity_months_3m",
    "remittance_to_income_ratio",
    "remittance_failure_rate_6m",
    "dti_loan_ratio",
    "loan_overdue_score",
    "recent_overdue_flag",
    "card_utilization_3m",
    "card_cash_advance_ratio",
    "card_risky_month_count",
    "risk_event_count"
]

def calculate_final_score(features: dict) -> int:

    # 1) feature 순서 validation
    input_vector = []

    for key in MODEL_FEATURE_ORDER:
        value = features.get(key, 0.0) # 값 없으면 기본값 0
        input_vector.append(float(value))
    
    input_array = np.array([input_vector])

    # 2) 모델 & 스케일러 로드
    model = load_credit_model()
    scaler = load_scaler()

    # 3) 스케일링
    scaled = scaler.transform(input_array)

    # 4) 예측
    raw_score = model.predic(scaled)[0]

    # 5) 점수 반올림
    score = int(round(raw_score))

    # 6) 최소/최대 범위 클램프
    score = max(500, min(990, score))

    return score