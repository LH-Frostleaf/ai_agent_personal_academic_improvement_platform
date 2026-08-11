from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.db_models import User
from services.auth_service import hash_password, verify_password


def get_user_by_username(db: Session, username: str) -> User | None:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """根据用户 ID 获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, password: str) -> User:
    """注册新用户"""
    # 检查用户名是否已存在
    existing_user = get_user_by_username(db, username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被占用"
        )

    # 创建新用户
    hashed_pwd = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """验证用户登录"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user