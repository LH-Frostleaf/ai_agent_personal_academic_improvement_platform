import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from config.database_config import get_db
from config.upload_config import ALLOWED_EXTENSIONS
from models.schemas import CourseStudyInfo

# 导入所有 Service
from services.user_service import get_or_create_test_user
from services.mistake_service import create_mistake, get_user_mistakes, count_user_mistakes
from services.study_service import (
    add_study_record,
    get_latest_scores,
    get_total_durations,
    generate_study_summary
)
from services.ocr_service import save_uploaded_file, extract_text_from_image

router = APIRouter()


@router.post("/mistakes/upload")
async def upload_mistake(
    screenshot: UploadFile = File(...),
    course_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # 校验文件类型...
    if not screenshot.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        raise HTTPException(400, f"只支持 {', '.join(ALLOWED_EXTENSIONS)} 格式")

    try:
        current_user = get_or_create_test_user(db)
        loop = asyncio.get_running_loop()
        saved_path = await loop.run_in_executor(None, save_uploaded_file, screenshot)
        ocr_result = await loop.run_in_executor(None, extract_text_from_image, saved_path)

        # ✅ 调用 Service 层，路由层再也不写 SQL
        mistake = create_mistake(
            db=db,
            user_id=current_user.id,
            course_name=course_name,
            ocr_text=ocr_result,
            cleaned_text=ocr_result,
            image_path=saved_path
        )

        total_count = count_user_mistakes(db, current_user.id)

        return {
            "code": 200,
            "message": f"✅ 已收录 {course_name} 错题，当前共 {total_count} 道",
            "data": {
                "mistake": {"id": mistake.id, "course_name": mistake.course_name},
                "total_count": total_count
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"服务器处理出错: {str(e)}")


@router.put("/profile/update")
async def update_study_profile(
    courses: List[CourseStudyInfo],
    db: Session = Depends(get_db)
):
    try:
        current_user = get_or_create_test_user(db)

        inserted_courses = []
        for course in courses:
            if course.score is not None and (course.score < 0 or course.score > 100):
                raise HTTPException(400, f"{course.course_name} 成绩必须在 0-100 之间")
            if course.study_duration is not None and course.study_duration < 0:
                raise HTTPException(400, f"{course.course_name} 学习时长不能为负数")

            # ✅ 调用 Service 层
            add_study_record(
                db=db,
                user_id=current_user.id,
                course_name=course.course_name,
                score=course.score,
                duration_increment=course.study_duration
            )
            inserted_courses.append(course.course_name)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"更新失败: {str(e)}")

    # ✅ 聚合查询也交给 Service
    latest_scores = get_latest_scores(db, current_user.id)
    total_durations = get_total_durations(db, current_user.id)

    return {
        "code": 200,
        "message": f"✅ 已记录 {len(inserted_courses)} 门课程的学习情况",
        "data": {
            "latest_scores": latest_scores,
            "total_durations": total_durations,
        }
    }


@router.get("/profile")
async def get_user_profile(
    db: Session = Depends(get_db)
):
    current_user = get_or_create_test_user(db)

    mistakes = get_user_mistakes(db, current_user.id)
    latest_scores = get_latest_scores(db, current_user.id)
    total_durations = get_total_durations(db, current_user.id)
    total_mistakes = count_user_mistakes(db, current_user.id)

    # ✅ 生成摘要也用 Service
    summary = generate_study_summary(latest_scores, total_durations, total_mistakes)

    return {
        "code": 200,
        "data": {
            "mistakes": [
                {
                    "id": m.id,
                    "course_name": m.course_name,
                    "cleaned_text": (m.cleaned_text[:50] + "...") if m.cleaned_text and len(m.cleaned_text) > 50 else m.cleaned_text,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in mistakes
            ],
            "latest_scores": latest_scores,
            "total_durations": total_durations,
            "summary": summary,
            "total_mistakes": total_mistakes
        }
    }