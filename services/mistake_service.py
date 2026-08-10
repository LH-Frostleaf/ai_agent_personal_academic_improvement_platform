from sqlalchemy.orm import Session
from models.db_models import Mistake


def get_user_mistakes(db: Session, user_id: int, limit: int = None):
    """获取用户的所有错题（按时间倒序）"""
    query = db.query(Mistake).filter(
        Mistake.user_id == user_id
    ).order_by(Mistake.created_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def count_user_mistakes(db: Session, user_id: int) -> int:
    """统计用户错题总数"""
    return db.query(Mistake).filter(Mistake.user_id == user_id).count()