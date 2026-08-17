from sqlalchemy.orm import Session
from sqlalchemy import asc
from models.db_models import Subject, KnowledgePoint, Recommendation

def get_all_subjects(db: Session):
    """获取所有学科"""
    return db.query(Subject).order_by(asc(Subject.sort_order)).all()

def get_knowledge_points_by_subject(db: Session, subject_id: int):
    """获取某学科下的知识点"""
    return db.query(KnowledgePoint).filter(
        KnowledgePoint.subject_id == subject_id
    ).order_by(asc(KnowledgePoint.name)).all()

def get_knowledge_point_by_kp_id(db: Session, kp_id: str):
    """通过 kp_id 查找知识点"""
    return db.query(KnowledgePoint).filter(KnowledgePoint.kp_id == kp_id).first()

def get_resources_by_kp_id(db: Session, kp_id: str):
    """通过 kp_id 获取资源列表"""
    kp = get_knowledge_point_by_kp_id(db, kp_id)
    if not kp:
        return []
    return db.query(Recommendation).filter(
        Recommendation.knowledge_point_id == kp.id
    ).all()

def get_resources_by_kp_ids(db: Session, kp_ids: list):
    """批量获取多个知识点的资源（去重）"""
    if not kp_ids:
        return []
    kps = db.query(KnowledgePoint).filter(
        KnowledgePoint.kp_id.in_(kp_ids)
    ).all()
    if not kps:
        return []
    kp_id_map = {kp.id: kp for kp in kps}
    resources = db.query(Recommendation).filter(
        Recommendation.knowledge_point_id.in_([kp.id for kp in kps])
    ).all()
    # 按知识点分组
    result = {kp.kp_id: [] for kp in kps}
    for r in resources:
        kp = kp_id_map.get(r.knowledge_point_id)
        if kp:
            result[kp.kp_id].append({
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "url": r.url,
                "description": r.description,
                "difficulty": r.difficulty,
                "source": r.source
            })
    return result