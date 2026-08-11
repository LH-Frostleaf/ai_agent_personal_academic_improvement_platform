from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.database_config import get_db
from services.user_service import create_user, authenticate_user, get_user_by_id
from services.auth_service import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["认证"])

# OAuth2 密码流, 让 Swagger UI 知道去哪里获取 Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register")
async def register(
        username: str,
        password: str,
        db: Session = Depends(get_db)
):
    """
    用户注册
    """
    try:
        user = create_user(db, username, password)
        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "created_at": user.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),   # 把前端登录时发来的表单数据（username 和 password）整理成 Python 对象
        db: Session = Depends(get_db)
):
    """
    用户登录（返回 JWT Token）
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成 JWT
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }
    }
    # return {
    #     "access_token": access_token,
    #     "token_type": "bearer"
    # }


@router.get("/me")
async def get_current_user_info(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """
    获取当前登录用户信息（用于前端验证 Token 有效性）
    """
    payload = decode_access_token(token)
    user_id = int(payload.get("sub"))
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat()
        }
    }