from pydantic import BaseModel, Json, Field
from typing import Optional, Dict, List
from datetime import datetime

# ===== perception所需学习情况模块 =====
class CourseStudyInfo(BaseModel):
    """单门课程的学习情况"""
    course_name: str
    score: Optional[float] = None  # 0-100
    study_duration: Optional[float] = None  # 小时

# ===== auth所需账号密码类 =====
class UserRegister(BaseModel):
    """用户注册请求体"""
    username: str = Field(..., min_length=2, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=30, description="密码")