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
    
    # 학습할 때와 똑같이 스케일링(MinMax) 적용 -> 결과는 numpy array
    X_scaled_array = scaler.transform(df)
    
    # [중요] 경고 메시지 제거를 위해 다시 DataFrame으로 변환 (컬럼명 복구)
    X_scaled_df = pd.DataFrame(X_scaled_array, columns=MODEL_FEATURE_ORDER)
    
    # -------------------------------
    # 3) 모델 로딩 + 예측 (Random Forest)
    # -------------------------------
    # [수정] 상수항(const) 추가 로직 삭제 (Random Forest는 불필요)
    model = load_credit_model()
    
    # 예측 실행
    pred = model.predict(X_scaled_df)

    # 결과값 추출 (배열의 첫 번째 값)
    raw_score = float(pred[0])

    # -------------------------------
    # 4) 점수 반올림 + 범위 제한 (클램프)
    # -------------------------------
    score = round(raw_score)
    
    # SQL 로직(2:6:2 분포 전략)과 동일하게 550 ~ 920 사이로 제한
    score = max(550, min(920, score))

    return score