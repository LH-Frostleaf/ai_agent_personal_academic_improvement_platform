from sqlalchemy.orm import Session
from models.db_models import Mistake
from services.ocr_service import extract_text_from_image
from services.llm_service import extract_knowledge_points

async def analyze_mistake(mistake_id: int, db: Session):
    """
    解析错题：确保 OCR 存在，提取知识点，更新数据库
    """
    mistake = db.query(Mistake).filter(Mistake.id == mistake_id).first()
    if not mistake:
        raise ValueError("错题不存在")

    # 1. 确保有 OCR 文本
    ocr_text = mistake.ocr_text
    if not ocr_text and mistake.image_path:
        ocr_text = extract_text_from_image(mistake.image_path)
        mistake.ocr_text = ocr_text
        db.commit()

    if not ocr_text:
        return {
            "mistake_id": mistake.id,
            "ocr_text": "",
            "knowledge_points": [],
            "error": "无法提取 OCR 文本"
        }

    # 2. 提取知识点
    knowledge_points = await extract_knowledge_points(ocr_text, mistake.course_name)

    # 3. 更新数据库
    mistake.knowledge_points = knowledge_points
    db.commit()
    db.refresh(mistake)

    return {
        "mistake_id": mistake.id,
        "ocr_text": ocr_text,
        "knowledge_points": knowledge_points
    }