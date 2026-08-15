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
    print(f"[删除] 找到记录: id={mistake.id}, course={mistake.course_name}")
    db.delete(mistake)
    db.commit()
    print("[删除] 提交成功")
    still_exists = db.query(Mistake).filter(Mistake.id == mistake_id).first() is not None
    print(f"[删除] 删除后记录仍存在: {still_exists}")
    return True

def get_mistake_by_id(db: Session, mistake_id: int) -> Mistake | None:
    """根据 ID 获取错题"""
    return db.query(Mistake).filter(Mistake.id == mistake_id).first()