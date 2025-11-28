from app.service.score_calculator import calculate_final_score
import copy

def predict_credit_score_growth(current_features: dict, monthly_remit_amount: float):
    # 현재 점수 계산
    current_score = calculate_final_score(current_features)
    
    # 미래 시뮬레이션 기본 세팅
    base_future_features = current_features.copy()

    # 시나리오 설정
    base_future_features["remittance_count_6m"] = 6.0
    base_future_features["remittance_failure_rate_6m"] = 0.0

    income_avg = base_future_features.get("income_avg_6m", 0)
    ratio_score_factor = 0.0

    if income_avg > 0:
        ratio = monthly_remit_amount / income_avg
        base_future_features["remittance_income_ratio"] = min(0.5, ratio)
        ratio_score_factor = min(0.5, ratio) * 20
    else:
        base_future_features["remittance_income_ratio"] = 0.0
        ratio_score_factor = 2.0 # 기본 가산점
    
    # 6개월 후 예측
    feat_6m = base_future_features.copy()
    feat_6m["remittance_cycle_stability"] = 0.90 # 주기 안정성 설정
    ai_score_6m = calculate_final_score(feat_6m)
    
    # 최소 상승폭 보정, 금액비례 가산점 만큼 상승 보장
    min_delta_6m = 5 + int(ratio_score_factor * 0.5)
    score_6m = max(ai_score_6m, current_score + min_delta_6m)
    
    # 12개월 후 예측
    feat_12m = base_future_features.copy()
    feat_12m["remittance_cycle_stability"] = 0.95 # 안정성 상승
    feat_12m["min_balance_3m"] = feat_12m["min_balance_3m"] * 1.05 
    feat_12m["liquidity_months_3m"] = feat_12m["liquidity_months_3m"] * 1.05 # 유동성 상승
    ai_score_12m = calculate_final_score(feat_12m)
    
    min_delta_12m = 4 + int(ratio_score_factor * 0.3)
    score_12m = max(ai_score_12m, score_6m + min_delta_12m)
    
    # 18개월 후 예측
    feat_18m = base_future_features.copy()
    feat_18m["remittance_cycle_stability"] = 0.99 # 안정성 최고치
    feat_18m["min_balance_3m"] = feat_18m["min_balance_3m"] * 1.10
    feat_18m["liquidity_months_3m"] = feat_18m["liquidity_months_3m"] * 1.10 # 유동성 최고치
    ai_score_18m = calculate_final_score(feat_18m)
    
    min_delta_18m = 6 + int(ratio_score_factor * 0.2)
    score_18m = max(ai_score_18m, score_12m + min_delta_18m)

    # 최종 캡핑
    score_6m = min(920, score_6m)
    score_12m = min(920, score_12m)
    score_18m = min(920, score_18m)

    score_12m = max(score_12m, score_6m)
    score_18m = max(score_18m, score_12m)

    return {
        "user_id": int(current_features.get("user_id", 0)),
        "monthly_remit_amount": monthly_remit_amount,
        "current_score": current_score,
        "after_6m": {
            "score": score_6m,
            "delta": score_6m - current_score
        },
        "after_12m": {
            "score": score_12m,
            "delta": score_12m - current_score
        },
        "after_18m": {
            "score": score_18m,
            "delta": score_18m - current_score
        }
    }