from pydantic import BaseModel, Json
from typing import Optional, Dict, List
from datetime import datetime


# ===== 1. 题目解析模块 =====
class MistakeRecord(BaseModel):
    """单条错题记录"""
    user_id: str # 用户id
    course_name: str  # 所属课程（强制）
    ocr_text: str  # OCR 识别的文字
    image_path: str  # 图片存储路径（用于追溯）
    uploaded_at: datetime = datetime.now()  # 上传时间
    # 后续可扩展：
    # knowledge_points: List[str]         # 提取的知识点标签（RAG后填充）
    # difficulty: str                     # 难度等级（可选）

# ===== 2. 学习情况模块 =====
class CourseStudyInfo(BaseModel):
    """单门课程的学习情况"""
    user_id: str  # 用户id
    course_name: str
    score: Optional[float] = None  # 0-100
    study_duration: Optional[float] = None  # 小时

# ===== 3. 用户学业画像（汇总） =====
class UserAcademicProfile(BaseModel):
    """用户的完整学业画像（用于后续诊断）"""
    user_id: str  # 后续加用户系统
    mistakes: List[MistakeRecord] = []  # 所有错题记录
    course_scores: Dict[str, float] = {}  # {"高数": 78, "英语": 85}
    study_duration: Dict[str, float] = {}  # {"高数": 2.5, "英语": 1.0}

    @property
    def summary(self) -> str:
        """生成摘要（供 Agent 快速理解）"""
        parts = []
        if self.course_scores:
            avg = sum(self.course_scores.values()) / len(self.course_scores)
            parts.append(f"各科平均成绩 {avg:.1f} 分")
        if self.study_duration:
            total = sum(self.study_duration.values())
            parts.append(f"总学习时长 {total:.1f} 小时")
        if self.mistakes:
            parts.append(f"已收录 {len(self.mistakes)} 道错题")
        return "；".join(parts) if parts else "暂无学业数据"