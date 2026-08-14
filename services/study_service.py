from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.db_models import StudyRecord
from typing import Dict, List, Optional


def get_latest_scores(db: Session, user_id: int) -> Dict[str, float]:
    """获取用户各科最新成绩（每个课程取最新一条记录）"""
    # 子查询
    subquery = db.query(
        StudyRecord.course_name,
        func.max(StudyRecord.id).label('latest_id')
    ).filter(
        StudyRecord.user_id == user_id
    ).group_by(
        StudyRecord.course_name
    ).subquery()

    # 主查询
    latest_records = db.query(StudyRecord).join(
        subquery,
        StudyRecord.id == subquery.c.latest_id
    ).all()

    # 转换成字典
    latest_scores = {r.course_name: r.score for r in latest_records}
    return latest_scores

def get_total_durations(db: Session, user_id: int) -> Dict[str, float]:
    """获取用户各科累计学习时长（SUM 聚合）"""
    duration_summary = db.query(
        StudyRecord.course_name,
        func.sum(StudyRecord.study_duration).label('total_duration')
    ).filter(
        StudyRecord.user_id == user_id
    ).group_by(
        StudyRecord.course_name
    ).all()

    total_durations = {row.course_name: row.total_duration for row in duration_summary}
    return total_durations


def get_daily_durations(db: Session, user_id: int, date: datetime) -> Dict[str, float]:
    """
    获取用户某日的各科学习时长（按北京时间）
    """
    # 转换到北京时间
    beijing_tz = ZoneInfo("Asia/Shanghai")
    date_beijing = date.astimezone(beijing_tz)
    start = date_beijing.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    # 转 UTC 用于查询
    start_utc = start.astimezone(ZoneInfo("UTC"))
    end_utc = end.astimezone(ZoneInfo("UTC"))

    results = db.query(
        StudyRecord.course_name,
        func.sum(StudyRecord.study_duration).label('daily_duration')
    ).filter(
        StudyRecord.user_id == user_id,
        StudyRecord.created_at >= start_utc,
        StudyRecord.created_at < end_utc
    ).group_by(StudyRecord.course_name).all()

    return {row.course_name: row.daily_duration or 0 for row in results}


def get_weekly_durations(
        db: Session,
        user_id: int,
        week_offset: int = 0
) -> Dict[str, float]:
    """
    获取用户某周的各科学习时长（按北京时间）
    week_offset: 0=本周, -1=上周, -2=上上周...
    """
    beijing_tz = ZoneInfo("Asia/Shanghai")
    now_beijing = datetime.now(beijing_tz)

    # 计算该周的周一 00:00
    # days_since_monday = now_beijing.weekday()  # 周一=0
    # monday = (now_beijing - datetime.timedelta(days=days_since_monday)
    #           - timedelta(weeks=abs(week_offset) if week_offset < 0 else 0))
    # if week_offset < 0:
    #     monday = monday - timedelta(weeks=abs(week_offset))
    # elif week_offset > 0:
    #     monday = monday + timedelta(weeks=week_offset)

    monday = ((now_beijing - timedelta(days=now_beijing.weekday()))
              + timedelta(weeks=week_offset))

    start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)

    start_utc = start.astimezone(ZoneInfo("UTC"))
    end_utc = end.astimezone(ZoneInfo("UTC"))

    results = db.query(
        StudyRecord.course_name,
        func.sum(StudyRecord.study_duration).label('weekly_duration')
    ).filter(
        StudyRecord.user_id == user_id,
        StudyRecord.created_at >= start_utc,
        StudyRecord.created_at < end_utc
    ).group_by(StudyRecord.course_name).all()

    return {row.course_name: row.weekly_duration or 0 for row in results}


def get_weekly_range(week_offset: int = 0) -> tuple:
    """
    获取某周的日期范围（北京时间），用于显示
    """
    beijing_tz = ZoneInfo("Asia/Shanghai")
    now_beijing = datetime.now(beijing_tz)

    # days_since_monday = now_beijing.weekday()
    # monday = (now_beijing - timedelta(days=days_since_monday)
    #           - timedelta(weeks=abs(week_offset) if week_offset < 0 else 0))
    # if week_offset < 0:
    #     monday = monday - timedelta(weeks=abs(week_offset))
    # elif week_offset > 0:
    #     monday = monday + timedelta(weeks=week_offset)

    monday = ((now_beijing - timedelta(days=now_beijing.weekday()))
              + timedelta(weeks=week_offset))

    start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

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

    summary = "；".join(parts) if parts else "暂无学业数据"

    return summary