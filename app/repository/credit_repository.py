from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


# ================ 최신 신용 점수 저장 메서드 ==================
def save_latest_credit_score(db: Session, user_id: int, credit_score: int):

    db.execute(
        text("""
        INSERT INTO credit_score (user_id, score, created_at, updated_at)
        VALUES (:user_id, :score, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            score = VALUES(score),
            updated_at = NOW();
        """),
        {"user_id": user_id, "score": credit_score}
    )
    db.commit()


# ================ 신용 점수 기록 저장 메서드 ==================
# 신용점수 기록 저장 - user_id, created_date 복합 키 저장
def save_credit_score_history(db: Session, user_id: int, credit_score: int):
    db.execute(
        text("""
        INSERT INTO credit_score_history (user_id, score, created_at)
        VALUES (:user_id, :score, NOW())
        ON DUPLICATE KEY UPDATE
            score = VALUES(score);
        """),
        {"user_id": user_id, "score": credit_score}
    )
    db.commit()

# ================ 최신 신용 점수 조회 메서드 ==================
def get_latest_credit_score(user_id: int, core_db: Session):
    
    result = core_db.execute(
        text("""
        SELECT score
        FROM credit_score
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchone()

    if result is None:
        return 0
    
    return int(result.score)


# ================ 신용 점수 기록 조회 메서드 (월별 평균) ==================
def get_credit_score_history(user_id: int, core_db: Session):

    results = core_db.execute(
        text("""
        SELECT
            YEAR(created_at) AS year,
            MONTH(created_at) AS month,
            AVG(score) AS avg_score
        FROM credit_score_history
        WHERE user_id = :user_id
        GROUP BY YEAR(created_at), MONTH(created_at)
        ORDER BY year ASC, month ASC;
        """),
        {"user_id": user_id}
    ).fetchall()

    history_list = []

    for row in results:
        history_list.append({
            "year": int(row.year),
            "month": int(row.month),
            "avg_score": int(round(row.avg_score))
        })

    return history_list