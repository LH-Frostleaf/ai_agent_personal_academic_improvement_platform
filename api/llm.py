from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models.schemas import MistakeAnalysisRequest
from services.llm_service import stream_explain_mistake
from services.mistake_service import get_mistake_by_id
from dependencies.auth_deps import get_current_user
from models.db_models import User, Mistake
from config.database_config import get_db
from services.analysis_service import analyze_mistake

router = APIRouter(prefix="/api/v1/llm", tags=["大模型"])

@router.post("/mistake/explain")
async def explain_mistake(
    request: MistakeAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    流式返回错题解析
    """
    # 1. 获取错题数据
    mistake = get_mistake_by_id(db, request.mistake_id)
    if not mistake or mistake.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="错题不存在或无权限")

    # 3. 返回流式响应
    return StreamingResponse(
        stream_explain_mistake(
            course_name=mistake.course_name,
            ocr_text=mistake.ocr_text,
        ),
        media_type="text/event-stream"
    )


@router.post("/knowledge/extract")
async def extract_knowledge(
        request: MistakeAnalysisRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """提取错题的知识点（RAG + LLM）"""
    # 验证归属
    mistake = db.query(Mistake).filter(
        Mistake.id == request.mistake_id,
        Mistake.user_id == current_user.id
    ).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在或无权限")

    try:
        result = await analyze_mistake(request.mistake_id, db)
        return {"code": 200, "message": "知识点提取成功", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")