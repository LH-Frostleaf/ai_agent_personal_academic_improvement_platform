from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database_config import get_db
from dependencies.auth_deps import get_current_user
from models.db_models import User, KnowledgePoint
from services.resource_service import (
    get_all_subjects,
    get_knowledge_points_by_subject,
    get_resources_by_kp_id,
    get_resources_by_kp_ids,
    get_knowledge_point_by_kp_id
)

router = APIRouter(prefix="/api/v1/resources", tags=["资源推荐"])

@router.get("/subjects")
async def list_subjects(
    db: Session = Depends(get_db),
):
    """获取所有学科"""
    subjects = get_all_subjects(db)
    return {
        "code": 200,
        "data": [{"id": s.id, "name": s.name, "icon": s.icon} for s in subjects]
    }

@router.get("/knowledge-points")
async def list_knowledge_points(
    subject_id: int = Query(..., description="学科ID"),
    db: Session = Depends(get_db),
):
    """获取某学科下的知识点列表"""
    kps = get_knowledge_points_by_subject(db, subject_id)
    return {
        "code": 200,
        "data": [{"id": kp.id, "kp_id": kp.kp_id, "name": kp.name} for kp in kps]
    }

@router.get("/resources")
async def list_resources(
    kp_id: str = Query(..., description="知识点ID"),
    db: Session = Depends(get_db),
):
    """获取某知识点的资源列表"""
    resources = get_resources_by_kp_id(db, kp_id)
    return {
        "code": 200,
        "data": {
            "kp_id": kp_id,
            "resources": [
                {
                    "id": r.id,
                    "title": r.title,
                    "type": r.type,
                    "url": r.url,
                    "description": r.description,
                    "difficulty": r.difficulty,
                    "source": r.source
                } for r in resources
            ]
        }
    }

@router.get("/batch-resources")
async def batch_list_resources(
    kp_ids: str = Query(..., description="知识点ID列表，用逗号分隔"),
    db: Session = Depends(get_db),
):
    """批量获取多个知识点的资源（用于诊断报告跳转）"""
    ids = [kp_id.strip() for kp_id in kp_ids.split(',') if kp_id.strip()]
    resources_by_kp = get_resources_by_kp_ids(db, ids)
    return {
        "code": 200,
        "data": resources_by_kp
    }

@router.get("/search")
async def search_knowledge_points(
    keyword: str = Query(..., description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """搜索知识点（用于快速定位）"""
    # 简化搜索：按名称模糊匹配
    kps = db.query(KnowledgePoint).filter(
        or_(
            KnowledgePoint.name.contains(keyword),
            KnowledgePoint.kp_id.contains(keyword)
        )
    ).limit(10).all()
    return {
        "code": 200,
        "data": [
            {
                "id": kp.id,
                "kp_id": kp.kp_id,
                "name": kp.name,
                "subject": kp.subject.name if kp.subject else None
            } for kp in kps
        ]
    }