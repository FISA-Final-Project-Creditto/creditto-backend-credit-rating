# Raw 데이터 -> Feature 데이터 변환

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def extract_features(
        transaction_rows,
        card_rows,
        loan_rows,
        remit_rows
):
    today = datetime.today().date()
    start_6m = today - relativedelta(months=6)
    start_3m = today - relativedelta(months=3)

    features = {}

    # 1) income_avg_6m - 최근 6개월 월급 평균
    # ====================================================
    salary_amounts = []

    for row in transaction_rows:
        tx_date = row.tx_datetime.date() if isinstance(row.tx_datetime, datetime) else row.tx_datetime

        if (
            tx_date >= start_6m
            and row.direction == "IN"
            and row.category == "SALARY"
        ):
            salary_amounts.append(float(row.amount))

    if salary_amounts:
        features["income_avg_6m"] = sum(salary_amounts) / len(salary_amounts)
    else:
        features["income_avg_6m"] = 0.0


    # 2) income_volatility_6m - 최근 6개월 월급 표준편차
    # ====================================================
    if salary_amounts:
        mean_val = sum(salary_amounts) / len(salary_amounts)

        variance = sum((x - mean_val) ** 2 for x in salary_amounts) / len(salary_amounts)

        features["income_volatility_6m"] = variance ** 0.5 # 표준편차
    else:
        features["income_volatility_6m"] = 0.0


    # 3) spending_avg_6m - 최근 6개월 지출 평균
    # ====================================================
    spending_categories = {"LIVING", "RENT", "ENTERTAIN", "ETC"}
    spend_amounts = []

    for row in transaction_rows:
        tx_date = (
            row.tx_datetime.date()
            if isinstance(row.tx_datetime, datetime)
            else row.tx_datetime
        )

        if (
            tx_date >= start_6m
            and row.direction == "OUT"
            and row.category in spending_categories
        ):
            spend_amounts.append(float(row.amount))
    
    if spend_amounts:
        features["spending_avg_6m"] = sum(spend_amounts) / len(spend_amounts)
    else:
        features["spending_avg_6m"] = 0.0


    # 4) saving_rate_6m - 최근 6개월 저축률
    # ====================================================
    income_avg = features.get("income_avg_6m", 0.0)
    spending_avg = features.get("spending_avg_6m", 0.0)

    if income_avg > 0:
        saving_rate = (income_avg - spending_avg) / income_avg

        saving_rate = max(-1, min(1, saving_rate))
    else:
        saving_rate = 0.0
    
    features["saving_rate_6m"] = saving_rate


    # 5) min_balance_3m - 최근 3개월 최소 잔고
    # ====================================================
    balance_values = []

    for row in transaction_rows:
        tx_date = (
            row.tx_datetime.date()
            if isinstance(row.tx_datetime, datetime)
            else row.tx_datetime
        )

        if tx_date >= start_3m:
            if row.balance_after is not None:
                balance_values.append(float(row.balance_after))
    
    if balance_values:
        features["min_balance_3m"] = min(balance_values)
    else:
        features["min_balance_3m"] = 0.0

    # 6) liquidity_months_3m - 최근 3개월 유동성 개월 수
    # ====================================================
    spend_categories = {"LIVING", "RENT", "ENTERTAIN", "ETC", "REMIT_OUT"}

    spend_3m_total = 0.0

    for row in transaction_rows:
        tx_date = (
            row.tx_datetime.date()
            if isinstance(row.tx_datetime, datetime)
            else row.tx_datetime
        )

        if (
            tx_date >= start_3m
            and row.direction == "OUT"
            and row.category in spend_categories
        ):
            spend_3m_total += float(row.amount)

    # 월 지출 금액
    spend_3m_monthly = spend_3m_total / 3

    min_balance_3m = features.get("min_balance_3m", 0.0)

    if spend_3m_monthly > 0:
        liquidity_months = min(12, min_balance_3m / spend_3m_monthly)
    else:
        liquidity_months = 12  # 지출이 없으면 최대로 안정적

    features["liquidity_months_3m"] = liquidity_months


    # 7) remittance_to_income_ratio - 최근 6개월 송금/소득 비율
    # ====================================================
    remit_6m_total = 0.0

    for row in remit_rows:
        remit_date = (
            row.remittance_date.date()
            if isinstance(row.remittance_date, datetime)
            else row.remittance_date
        )

        if remit_date >= start_6m:
            remit_6m_total += float(row.send_amount)

    # 이미 계산된 최근 6개월 월급 평균을 기반으로 총합으로 변환
    income_avg = features.get("income_avg_6m", 0.0)
    salary_6m_total = income_avg * 6  # 6개월치 총급여

    if salary_6m_total > 0:
        features["remittance_to_income_ratio"] = remit_6m_total / salary_6m_total
    else:
        features["remittance_to_income_ratio"] = 0.0


    # 8) remittance_failure_rate_6m - 최근 6개월 송금 실패율
    # ====================================================
    fail_cnt = 0
    total_cnt = 0

    for row in remit_rows:
        remit_date = (
            row.remittance_date.date()
            if isinstance(row.remittance_date, datetime)
            else row.remittance_date
        )

        if remit_date >= start_6m:
            total_cnt += 1

            # status = 'FAILED'
            if str(row.status).upper() == "FAILED":
                fail_cnt += 1

    if total_cnt > 0:
        features["remittance_failure_rate_6m"] = fail_cnt / total_cnt
    else:
        features["remittance_failure_rate_6m"] = 0.0


    # 9) dti_loan_ratio - 부채비율 (DTI)
    # ====================================================
    loan_principal_total = 0.0

    for row in loan_rows:
        if row.loan_principal is not None:
            loan_principal_total += float(row.loan_principal)

    # 연소득 income_avg_6m 기반
    income_avg = features.get("income_avg_6m", 0.0)
    annual_income = income_avg * 12

    if annual_income > 0:
        features["dti_loan_ratio"] = loan_principal_total / annual_income
    else:
        features["dti_loan_ratio"] = 0.0


    # 10) loan_overdue_score - 연체 위험 점수 (0~1)
    # ====================================================
    overdue_cnt_12m = 0
    max_overdue_days = 0
    overdue_amt_total = 0.0
    loan_principal_total = 0.0

    for row in loan_rows:
        # 총 대출원금
        if row.loan_principal is not None:
            loan_principal_total += float(row.loan_principal)

        # 12개월 연체 횟수
        if row.overdue_count_12m is not None:
            overdue_cnt_12m += int(row.overdue_count_12m)

        # 최장 연체일수
        if row.max_overdue_days is not None:
            max_overdue_days = max(max_overdue_days, int(row.max_overdue_days))

        # 연체 금액
        if row.overdue_amount is not None:
            overdue_amt_total += float(row.overdue_amount)

    # 각 요소 점수 계산
    score_cnt = (overdue_cnt_12m / 5.0) * 0.3
    score_days = (max_overdue_days / 90.0) * 0.3
    score_amt = (
        (overdue_amt_total / loan_principal_total) * 0.4
        if loan_principal_total > 0 else 0
    )

    raw_score = score_cnt + score_days + score_amt

    # 0~1로 클램프
    loan_overdue_score = max(0, min(1, raw_score))

    features["loan_overdue_score"] = loan_overdue_score


    # 11) recent_overdue_flag - 최근 6개월 연체 여부
    # ====================================================
    last_overdue_date = None

    for row in loan_rows:
        if row.last_overdue_dt:
            overdue_date = (
                row.last_overdue_dt.date()
                if isinstance(row.last_overdue_dt, datetime)
                else row.last_overdue_dt
            )

            # 가장 최근 연체 날짜 갱신 (최대값)
            if last_overdue_date is None or overdue_date > last_overdue_date:
                last_overdue_date = overdue_date

    # 최근 6개월 기준 날짜
    cutoff_6m = today - relativedelta(months=6)

    if last_overdue_date and last_overdue_date >= cutoff_6m:
        features["recent_overdue_flag"] = 1
    else:
        features["recent_overdue_flag"] = 0


    # 12) card_utilization_3m - 최근 3개월 카드 사용률
    # ====================================================
    credit_limit_max = 0.0
    outstanding_max = 0.0

    for row in card_rows:
        # credit_limit 최대값
        if row.credit_limit is not None:
            credit_limit_max = max(credit_limit_max, float(row.credit_limit))

        # outstanding_amt 최대값
        if row.outstanding_amt is not None:
            outstanding_max = max(outstanding_max, float(row.outstanding_amt))

    if credit_limit_max > 0:
        features["card_utilization_3m"] = outstanding_max / credit_limit_max
    else:
        features["card_utilization_3m"] = 0.0


    # 13) card_cash_advance_ratio - 현금서비스 비율
    # ====================================================
    card_spend_total = 0.0
    cash_advance_total = 0.0

    for row in card_rows:
        tx_date = (
            row.tx_datetime.date()
            if isinstance(row.tx_datetime, datetime)
            else row.tx_datetime
        )

        # 최근 3개월만 고려 (SQL은 안 했지만 실제로는 이게 더 정확함)
        if tx_date >= start_3m:
            # 전체 CREDIT 사용액
            if row.pay_type == "CREDIT" and row.tx_amount is not None:
                card_spend_total += float(row.tx_amount)

                # 현금서비스만 따로 더함
                if row.tx_category == "CASH_ADVANCE":
                    cash_advance_total += float(row.tx_amount)

    if card_spend_total > 0:
        features["card_cash_advance_ratio"] = cash_advance_total / card_spend_total
    else:
        features["card_cash_advance_ratio"] = 0.0
    
    features["card_cash_advance_total_3m"] = cash_advance_total


    # 14) card_risky_month_count - 위험 카드 사용 점수
    # ====================================================
    card_util = features.get("card_utilization_3m", 0.0)
    cash_adv_ratio = features.get("card_cash_advance_ratio", 0.0)

    risky_score = 0

    # 조건 1: 카드 사용률 80% 초과
    if card_util > 0.8:
        risky_score += 2

    # 조건 2: 현금서비스 비율 30% 초과
    if cash_adv_ratio > 0.3:
        risky_score += 2

    # 조건 3: 현금서비스 비율 50% 초과 (추가 점수)
    if cash_adv_ratio > 0.5:
        risky_score += 2

    features["card_risky_month_count"] = risky_score

    # 15) risk_event_count - 위험 이벤트 수
    # ====================================================
    overdue_cnt_12m = overdue_cnt_12m   # loan_overdue_score 계산될 때 이미 구함
    remit_fail_cnt = fail_cnt  # remit 실패 횟수 (rate와 별개)
    cash_advance_total = features.get("card_cash_advance_total_3m", 0)
    card_util = features.get("card_utilization_3m", 0.0)

    risk_cnt = 0

    if overdue_cnt_12m > 0:
        risk_cnt += 1

    if remit_fail_cnt > 0:
        risk_cnt += 1

    if cash_advance_total > 0:
        risk_cnt += 1

    if card_util > 0.9:
        risk_cnt += 1

    features["risk_event_count"] = risk_cnt

    return features
