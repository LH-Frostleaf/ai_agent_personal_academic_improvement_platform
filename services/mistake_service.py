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

def delete_mistake(db: Session, mistake_id: int, user_id: int) -> bool:
    """
    删除指定的错题记录，同时验证所有权
    返回 True 表示删除成功，False 表示记录不存在或无权限
    """
    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.user_id == user_id
    ).first()
    if not mistake:
        return False
    db.delete(mistake)
    db.commit()
    return True