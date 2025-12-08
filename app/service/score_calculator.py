import numpy as np
import pandas as pd
from app.model.load_model import load_credit_model, load_scaler

# ML 모델이 학습된 실제 Feature 순서 (18개)
# 주의: card_risky_month_count는 학습 데이터에 없으므로 포함하지 않습니다.
MODEL_FEATURE_ORDER = [
    "income_avg_6m",
    "income_volatility_6m",
    "spending_avg_6m",
    "saving_rate_6m",
    "min_balance_3m",
    "liquidity_months_3m",
    "remittance_count_6m",
    "remittance_amount_avg_6m",
    "remittance_amount_std_6m",
    "remittance_income_ratio",
    "remittance_failure_rate_6m",
    "remittance_cycle_stability",
    "dti_loan_ratio",
    "loan_overdue_score",
    "recent_overdue_flag",
    "card_utilization_3m",
    "card_cash_advance_ratio",
    "risk_event_count"
]

def calculate_final_score(features: dict) -> int:
    """
    추출된 금융 특성(features)을 사용하여 ML 모델 기반의 신용 점수를 예측합니다.
    """
    # -------------------------------
    # 1) Feature 순서에 맞춰 벡터 생성
    # -------------------------------
    # 딕셔너리에서 값을 꺼내 순서대로 나열합니다. (값이 없으면 0.0 처리)
    row = {col: float(features.get(col, 0.0)) for col in MODEL_FEATURE_ORDER}
    df = pd.DataFrame([row])

    # -------------------------------
    # 2) scaler 로딩 + 스케일링
    # -------------------------------
    scaler = load_scaler()
    
    # 스케일링 적용
    X_scaled_array = scaler.transform(df)
    X_scaled_df = pd.DataFrame(X_scaled_array, columns=MODEL_FEATURE_ORDER)
    
    # 모델 로딩 + 예측
    model = load_credit_model()
    
    # 예측 실행
    pred = model.predict(X_scaled_df)

    # 결과값 추출
    raw_score = float(pred[0])

    # 점수 반올림 + 범위 제한
    score = round(raw_score)
    
    score = max(550, min(950, score))
    return score