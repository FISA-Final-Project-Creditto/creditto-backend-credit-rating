from datetime import datetime
from sqlalchemy.orm import Session


# 최신 신용점수 저장
def save_latest_credit_score(db: Session, user_id: int, credit_score: int):

    db.execute(
        """
        INSERT INTO credit_score (user_id, score, created_at)
        VALUES (:user_id, :score, NOW())
        ON DUPLICATE KEY UPDATE
            score = VALUES(score),
            updated_at = NOW();
        """,
        {"user_id": user_id, "score": credit_score}
    )
    db.commit()


# 신용점수 기록 저장 - user_id, created_date 복합 키 저장
def save_credit_score_history(db: Session, user_id: int, credit_score: int):
    db.execute(
        """
        INSERT INTO credit_score_history (user_id, score, created_at)
        VALUES (:user_id, :score, NOW())
        ON DUPLICATE KEY UPDATE
            score = VALUES(score);
        """,
        {"user_id": user_id, "score": credit_score}
    )
    db.commit()

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