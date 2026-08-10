from sqlalchemy.orm import Session
from sqlalchemy import func
from models.db_models import StudyRecord
from typing import Dict, Optional

def add_study_record(
    db: Session,
    user_id: int,
    course_name: str,
    score: Optional[float] = None,
    duration_increment: Optional[float] = None
) -> StudyRecord:
    """新增一条学习记录（追加模式）"""
    record = StudyRecord(
        user_id=user_id,
        course_name=course_name,
        score=score,
        duration_increment=duration_increment
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_latest_scores(db: Session, user_id: int) -> Dict[str, float]:
    """获取用户各科最新成绩（每个课程取最新一条记录）"""
    subquery = db.query(
        StudyRecord.course_name,
        func.max(StudyRecord.id).label('latest_id')
    ).filter(
        StudyRecord.user_id == user_id
    ).group_by(
        StudyRecord.course_name
    ).subquery()

    latest_records = db.query(StudyRecord).join(
        subquery,
        StudyRecord.id == subquery.c.latest_id
    ).all()

    return {r.course_name: r.score for r in latest_records}

def get_total_durations(db: Session, user_id: int) -> Dict[str, float]:
    """获取用户各科累计学习时长（SUM 聚合）"""
    results = db.query(
        StudyRecord.course_name,
        func.sum(StudyRecord.duration_increment).label('total_duration')
    ).filter(
        StudyRecord.user_id == user_id
    ).group_by(
        StudyRecord.course_name
    ).all()

    return {row.course_name: row.total_duration for row in results}

def generate_study_summary(
    latest_scores: Dict[str, float],
    total_durations: Dict[str, float],
    total_mistakes: int
) -> str:
    """生成学业摘要（原本在 perception_service.py 里的逻辑）"""
    parts = []
    if latest_scores:
        valid_scores = [v for v in latest_scores.values() if v is not None]
        if valid_scores:
            avg = sum(valid_scores) / len(valid_scores)
            parts.append(f"各科最新平均成绩 {avg:.1f} 分")
    if total_durations:
        total_hours = sum(total_durations.values())
        parts.append(f"累计学习时长 {total_hours:.1f} 小时")
    if total_mistakes > 0:
        parts.append(f"已收录 {total_mistakes} 道错题")

    return "；".join(parts) if parts else "暂无学业数据"