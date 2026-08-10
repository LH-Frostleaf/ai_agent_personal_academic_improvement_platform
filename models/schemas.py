from pydantic import BaseModel, Json
from typing import Optional, Dict, List
from datetime import datetime

# ===== perception所需学习情况模块 =====
class CourseStudyInfo(BaseModel):
    """单门课程的学习情况"""
    course_name: str
    score: Optional[float] = None  # 0-100
    study_duration: Optional[float] = None  # 小时