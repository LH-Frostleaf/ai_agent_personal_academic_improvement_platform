from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from models.db_models import Mistake, DiagnosisReport
from services.llm_service import generate_diagnosis_summary
from services.study_service import get_latest_scores, get_total_durations
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

def get_recent_mistake_kps(db: Session, user_id: int, days: int = 30) -> Dict[str, Dict]:
    """统计最近N天错题关联的知识点频次，返回 {kp_id: {"count": count, "subject": subject, "name": name}}"""
    cutoff = datetime.now() - timedelta(days=days)
    results = db.query(
        Mistake.knowledge_points,
        Mistake.course_name
    ).filter(
        Mistake.user_id == user_id,
        Mistake.created_at >= cutoff,
        Mistake.knowledge_points.isnot(None)
    ).all()

    kp_stats = {}
    for row in results:
        kps = row.knowledge_points
        if not kps:
            continue
        subject = row.course_name
        for kp in kps:
            kp_id = kp.get('kp_id')
            if not kp_id:
                continue
            if kp_id not in kp_stats:
                kp_stats[kp_id] = {
                    "count": 0,
                    "subject": subject,
                    "name": kp.get('name', ''),
                }
            kp_stats[kp_id]["count"] += 1
    return kp_stats

def get_latest_scores(db: Session, user_id: int) -> Dict[str, float]:
    """获取各科最新成绩"""
    return get_latest_scores(db, user_id)

def get_total_durations(db: Session, user_id: int) -> Dict[str, float]:
    """获取各科累计学习时长"""
    return get_total_durations(db, user_id)

def calculate_priorities(kp_stats: Dict, scores: Dict, durations: Dict) -> List[Dict]:
    """计算每个知识点的优先级分数"""
    if not kp_stats:
        return []

    max_count = max(v["count"] for v in kp_stats.values()) if kp_stats else 1
    total_duration = sum(durations.values()) if durations else 1

    prioritized = []
    for kp_id, stat in kp_stats.items():
        subject = stat["subject"]
        freq = stat["count"] / max_count  # 归一化频次
        score = scores.get(subject)  # 可能为 None
        duration = durations.get(subject, 0)

        # 动态调整权重
        has_score = score is not None
        has_duration = duration > 0

        if has_score and has_duration:
            # 正常情况
            score_factor = (100 - score) / 100 if score else 0
            duration_factor = 1 - (duration / total_duration) if total_duration > 0 else 0
            priority = freq * 0.5 + score_factor * 0.3 + duration_factor * 0.2
        elif has_score and not has_duration:
            # 只有成绩，时长缺失
            score_factor = (100 - score) / 100 if score else 0
            priority = freq * 0.6 + score_factor * 0.4
        elif not has_score and has_duration:
            # 只有时长，成绩缺失
            duration_factor = 1 - (duration / total_duration) if total_duration > 0 else 0
            priority = freq * 0.65 + duration_factor * 0.35
        else:
            # 两者都缺失
            priority = freq

        # 生成原因说明
        reason_parts = []
        if stat["count"] > 1:
            reason_parts.append(f"错题出现 {stat['count']} 次")
        if score is not None and score < 80:
            reason_parts.append(f"成绩 {score:.0f} 分")
        if duration > 0 and duration < 10:
            reason_parts.append(f"学习时长不足 ({duration:.1f}h)")

        reason = "、".join(reason_parts) if reason_parts else "建议重点复习"

        prioritized.append({
            "kp_id": kp_id,
            "name": stat["name"],
            "subject": subject,
            "priority": round(priority, 3),
            "count": stat["count"],
            "score": score,
            "duration": duration,
            "reason": reason
        })

    # 按优先级降序排序
    prioritized.sort(key=lambda x: x["priority"], reverse=True)
    return prioritized[:7]  # 取前7个

def generate_diagnosis(db: Session, user_id: int) -> Dict[str, Any]:
    """生成完整诊断报告"""
    # 1. 获取数据
    kp_stats = get_recent_mistake_kps(db, user_id, days=30)
    scores = get_latest_scores(db, user_id)
    durations = get_total_durations(db, user_id)

    if not kp_stats:
        return {"error": "没有足够的错题数据，请先上传错题并提取知识点"}

    # 2. 计算优先级
    weak_points = calculate_priorities(kp_stats, scores, durations)

    # 3. 生成摘要
    summary = generate_diagnosis_summary(weak_points, scores, durations)

    # 4. 存储报告
    report = DiagnosisReport(
        user_id=user_id,
        report_summary=summary,
        weak_points=json.dumps(weak_points, ensure_ascii=False)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "summary": summary,
        "weak_points": weak_points,
        "generated_at": report.generated_at.isoformat()
    }