from sqlalchemy.orm import Session
from models.db_models import User

def get_or_create_test_user(db: Session) -> User:
    """
    开发阶段：获取或创建测试用户（user_id=1）
    """
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(username="test_user", password_hash="dev_mode")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """根据 ID 获取用户"""
    return db.query(User).filter(User.id == user_id).first()