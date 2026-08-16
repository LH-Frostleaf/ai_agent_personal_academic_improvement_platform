from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database_config import get_db
from dependencies.auth_deps import get_current_user
from models.db_models import User, DiagnosisReport
from services.diagnosis_service import generate_diagnosis
import json

router = APIRouter(prefix="/api/v1/diagnosis", tags=["诊断"])

@router.post("/generate")
async def create_diagnosis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成新的诊断报告"""
    try:
        result = generate_diagnosis(db, current_user.id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"code": 200, "message": "诊断报告生成成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断生成失败: {str(e)}")

@router.get("/latest")
async def get_latest_diagnosis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最近一份诊断报告"""
    report = db.query(DiagnosisReport).filter(
        DiagnosisReport.user_id == current_user.id
    ).order_by(DiagnosisReport.generated_at.desc()).first()
    if not report:
        return {"code": 404, "message": "暂无诊断报告", "data": None}
    return {
        "code": 200,
        "data": {
            "report_id": report.id,
            "summary": report.report_summary,
            "weak_points": json.loads(report.weak_points),
            "generated_at": report.generated_at.isoformat()
        }
    }