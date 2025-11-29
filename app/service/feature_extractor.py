from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import math

def to_date(dt):
    if dt is None: return None
    if isinstance(dt, date): return dt
    if isinstance(dt, datetime): return dt.date()
    try:
        if isinstance(dt, str): return date.fromisoformat(dt)
    except: pass
    try:
        return datetime.fromisoformat(str(dt)).date()
    except: return None

def safe_float(v):
    try: return float(v)
    except: return 0.0

def safe_int(v):
    try: return int(v)
    except: return 0


#  Feature 추출 함수 (순수 데이터 가공)
# ------------------------------------------
def extract_features(transaction_rows, card_rows, loan_rows, remit_rows):

    today = date.today()
    start_6m_date = today - relativedelta(months=6) 
    start_6m = datetime.combine(start_6m_date, datetime.min.time()) 
    start_3m_date = today - relativedelta(months=3)
    start_3m = datetime.combine(start_3m_date, datetime.min.time()) 

    features = {}

    # 1) 소득 / 지출
    # ------------------------------------------
    salary_amounts = []
    spend_amounts = []
    for row in transaction_rows:
        tx_dt = row.tx_datetime
        if tx_dt is None: continue
        if tx_dt >= start_6m and row.direction == "IN" and row.category == "SALARY":
            salary_amounts.append(safe_float(row.amount))
        if tx_dt >= start_6m and row.direction == "OUT" \
                and row.category in ("LIVING", "RENT", "ENTERTAIN", "ETC", "REMIT_OUT"):
            spend_amounts.append(safe_float(row.amount))

    income_avg_6m = sum(salary_amounts) / len(salary_amounts) if salary_amounts else 0.0 
    features["income_avg_6m"] = income_avg_6m

    if len(salary_amounts) >= 2:
        mean_val = sum(salary_amounts) / len(salary_amounts)
        var = sum((x - mean_val) ** 2 for x in salary_amounts) / len(salary_amounts)
        features["income_volatility_6m"] = math.sqrt(var)
    else:
        features["income_volatility_6m"] = 0.0

    spending_avg_6m = sum(spend_amounts) / len(spend_amounts) if spend_amounts else 0.0
    features["spending_avg_6m"] = spending_avg_6m

    if income_avg_6m > 0:
        saving_rate = (income_avg_6m - spending_avg_6m) / income_avg_6m
        saving_rate = max(-1, min(1, saving_rate))
    else:
        saving_rate = 0.0
    
    features["saving_rate_6m"] = saving_rate

    # 2) 유동성
    # ------------------------------------------
    balance_list = []
    spend_3m_total = 0.0
    for row in transaction_rows:
        tx_dt = row.tx_datetime
        if tx_dt is None: continue
        if tx_dt >= start_3m:
            if row.balance_after is not None:
                balance_list.append(safe_float(row.balance_after))
            if row.direction == "OUT" and row.category in ("LIVING", "RENT", "ENTERTAIN", "ETC", "REMIT_OUT"):
                spend_3m_total += safe_float(row.amount)

    min_balance_3m = min(balance_list) if balance_list else 0.0
    features["min_balance_3m"] = min_balance_3m

    spend_3m_monthly = (spend_3m_total / 3) if spend_3m_total > 0 else 0
    if spend_3m_monthly > 0:
        liquidity_months = min(12, min_balance_3m / spend_3m_monthly)
    else:
        liquidity_months = 12
    features["liquidity_months_3m"] = liquidity_months

    # 3) 해외 송금
    # ------------------------------------------
    remit_amounts = []
    remit_cnt = 0
    remit_fail = 0
    remit_total_amount = 0.0
    for row in remit_rows:
        r_date = to_date(row.created_at) 
        if r_date is None: continue
        r_dt_for_comparison = datetime.combine(r_date, datetime.min.time())
        if r_dt_for_comparison >= start_6m: 
            amount = safe_float(row.send_amount)
            remit_cnt += 1
            remit_total_amount += amount
            remit_amounts.append(amount)
            if str(row.remittance_status).upper() == "FAILED":
                remit_fail += 1

    features["remittance_count_6m"] = remit_cnt
    
    if remit_amounts:
        avg_send = sum(remit_amounts) / len(remit_amounts)
        m = avg_send
        var = sum((x - m) ** 2 for x in remit_amounts) / len(remit_amounts)
        std = math.sqrt(var)
    else:
        avg_send = 0.0
        std = 0.0
        
    features["remittance_amount_avg_6m"] = avg_send
    features["remittance_amount_std_6m"] = std

    salary_6m_total = sum(salary_amounts)
    if salary_6m_total > 0:
        remit_income_ratio = remit_total_amount / salary_6m_total
    else:
        remit_income_ratio = 0.0
    features["remittance_income_ratio"] = remit_income_ratio

    if remit_cnt > 0:
        features["remittance_failure_rate_6m"] = remit_fail / remit_cnt
    else:
        features["remittance_failure_rate_6m"] = 0.0

    if avg_send > 0 and remit_cnt >= 2:
        st = 1 - (std / avg_send)
        features["remittance_cycle_stability"] = max(0.0, st)
    else:
        features["remittance_cycle_stability"] = 0.0

    # 4) 대출 / 연체
    # ------------------------------------------
    loan_principal_total = 0.0
    overdue_cnt_total = 0
    overdue_amt_total = 0.0
    max_overdue_days = 0
    last_overdue_date = None

    for row in loan_rows:
        loan_principal_total += safe_float(row.loan_principal)
        overdue_cnt_total += safe_int(row.overdue_count_12m)
        overdue_amt_total += safe_float(row.overdue_amount)
        max_overdue_days = max(max_overdue_days, safe_int(row.max_overdue_days))
        if row.last_overdue_dt:
            od = to_date(row.last_overdue_dt)
            if last_overdue_date is None or (od and od > last_overdue_date):
                last_overdue_date = od

    annual_income = income_avg_6m * 12
    if annual_income > 0:
        dti = loan_principal_total / annual_income
    else:
        dti = 0.0
    features["dti_loan_ratio"] = dti

    score_cnt = (overdue_cnt_total / 5.0) * 0.3
    score_days = (max_overdue_days / 90.0) * 0.4
    score_amt = (overdue_amt_total / loan_principal_total) * 0.3 if loan_principal_total > 0 else 0.0
    raw_score = score_cnt + score_days + score_amt

    # 0~1로 클램프
    loan_overdue_score = max(0, min(1, raw_score))

    features["loan_overdue_score"] = loan_overdue_score

    if last_overdue_date and last_overdue_date >= start_6m.date():
        features["recent_overdue_flag"] = 1
    else:
        features["recent_overdue_flag"] = 0

    # 5) 카드 위험도
    # ------------------------------------------
    max_utilization_ratio = 0.0
    ca_total = 0.0
    card_total = 0.0
    for row in card_rows:
        credit_limit = safe_float(row.credit_limit)
        outstanding_amt = safe_float(row.outstanding_amt)
        if credit_limit > 0:
            util_ratio = outstanding_amt / credit_limit
            max_utilization_ratio = max(max_utilization_ratio, util_ratio)
        
        tx_dt = row.tx_datetime 
        if tx_dt and tx_dt >= start_3m:
            amt = safe_float(row.tx_amount)
            card_total += amt
            if row.tx_category == "CASH_ADVANCE":
                ca_total += amt

    features["card_utilization_3m"] = max_utilization_ratio
    if card_total > 0:
        features["card_cash_advance_ratio"] = ca_total / card_total
    else:
        features["card_cash_advance_ratio"] = 0.0

    # 6) 리스크
    # ------------------------------------------
    risk_cnt = 0
    if overdue_cnt_total > 0: risk_cnt += 1
    if remit_fail > 0: risk_cnt += 1
    if features["card_cash_advance_ratio"] > 0.3: risk_cnt += 1
    if features["card_utilization_3m"] > 0.9: risk_cnt += 1
    features["risk_event_count"] = risk_cnt

    return features