from pydantic import BaseModel, Json
from typing import Optional, Dict

# 1. 定义前端传来的数据格式 (Form/JSON)
class PerceptionInput(BaseModel):
    # 用户上传的成绩，比如 {"高等数学": 78, "数据结构": 85}
    course_scores: Optional[Json[Dict[str, float]]] = None
    # 学习时长（单位：小时），比如 {"高等数学": 2.5, "数据结构": 1.0}
    study_duration: Optional[Json[Dict[str, float]]] = None
    # 注意：图片不在这里，图片将通过 FastAPI 的 UploadFile 单独传

# 2. 定义感知模块输出的干净数据 (给后续Agent用)
class CleanedPerceptionData(BaseModel):
    # 图片OCR提取出的文字（已经清理掉乱码）
    ocr_cleaned_text: str
    # 课程成绩（确保范围在0-100）
    course_scores: Dict[str, float]
    # 学习时长（确保为正数）
    study_duration: Dict[str, float]
    # 额外加一个汇总字段，方便Agent理解
    summary: str