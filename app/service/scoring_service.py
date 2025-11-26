# app/service/scoring_service.py

from sqlalchemy.orm import Session
from app.schema.score import ScoreRequest
from app.model.load_model import load_credit_model, load_scaler

# ================ 신용 점수 계산 메서드 ==================
def calculate_credit_score(request: ScoreRequest,
                           core_db: Session,
                           mydata_db: Session):
    user_id = request.user_id

    # 1) Core Banking: 계좌 정보 조회
    account = core_db.execute(
        """
        SELECT salary_amount, balance
        FROM account
        WHERE user_id = :user_id
        """,
        {"user_id": user_id}
    ).fetchone()

    # 2) MyData: 금융 행동 데이터 조회
    finance = mydata_db.execute(
        """
        SELECT saving_rate, income_to_expense_ratio,
               interest_burden_score, overdue_count_12m
        FROM user_finance_behavior
        WHERE user_id = :user_id
        """,
        {"user_id": user_id}
    ).fetchone()

    # 3) 송금 성공률 조회
    remittance_stats = core_db.execute(
        """
        SELECT 
            SUM(CASE WHEN success_flag = 1 THEN 1 ELSE 0 END) AS success_count,
            COUNT(*) AS total_count
        FROM remittance
        WHERE user_id = :user_id
        """,
        {"user_id": user_id}
    ).fetchone()

    # 4) 피처 정리
    salary_amount = float(account.salary_amount) if account else 0
    balance = float(account.balance) if account else 0

    success_ratio = (
        remittance_stats.success_count / remittance_stats.total_count
        if remittance_stats and remittance_stats.total_count > 0
        else 0
    )

    saving_rate = float(finance.saving_rate) if finance else 0
    income_to_expense_ratio = float(finance.income_to_expense_ratio) if finance else 0
    interest_burden_score = float(finance.interest_burden_score) if finance else 0
    overdue_count_12m = int(finance.overdue_count_12m) if finance else 0

    # 5) 모델 + 스케일러 로드
    model = load_credit_model()
    scaler = load_scaler()

    # 6) 입력 피처
    features = [
        salary_amount,
        balance,
        success_ratio,
        saving_rate,
        income_to_expense_ratio,
        interest_burden_score,
        overdue_count_12m
    ]

    # 7) 스케일링
    scaled = scaler.transform([features])

    # 8) 예측
    raw_score = model.predict(scaled)[0]
    credit_score = int(round(raw_score))


    # 9) 최신 신용 점수 저장 [credit_score]
    core_db.execute("""
        INSERT INTO credit_score (user_id, score, created_at)
        VALUES (:user_id, :score, NOW())
        ON DUPLICATE KEY UPDATE
            score = VALUES(score),
            updated_at = NOW();
        """, {"user_id": user_id, "score": credit_score})

    # 10) 신용 점수 히스토리 저장 [credit_score_history]
    core_db.execute("""
        INSERT INTO credit_score_history (user_id, score, created_at)
        VALUES (:user_id, :score, NOW());
        """, {"user_id": user_id, "score": credit_score})

    core_db.commit()

    # 신용 점수 반환
    return {
        "credit_score": credit_score
    }


# ================ 최신 신용 점수 조회 메서드 ==================
def get_latest_credit_score(user_id: int, core_db: Session):
    
    result = core_db.execute(
        """
        SELECT score
        FROM credit_score
        WHERE user_id = :user_id
        """,
        {"user_id": user_id}
    ).fetchone()

    if result is None:
        return 0
    
    return int(result.score)


# ================ 신용 점수 히스토리 조회 메서드 ==================
def get_credit_score_history(user_id: int, core_db: Session):

    results = core_db.execute(
        """
        SELECT
            YEAR(created_at) AS year,
            MONTH(created_at) AS month,
            AVG(score) AS avg_score
        FROM credit_score_history
        WHERE user_id = :user_id
        GROUP BY YEAR(created_at), MONTH(created_at)
        ORDER BY year ASC, month ASC;
        """,
        {"user_id": user_id}
    ).fetchall()

    history_list = []
    for result in results:
        history_list.append({
            "year": int(result.year),
            "month": int(result.month),
            "avg_score": int(round(result.avg_score))
        })

    return history_list