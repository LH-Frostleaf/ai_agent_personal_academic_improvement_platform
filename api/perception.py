from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from config.upload_config import ALLOWED_EXTENSIONS
from config.database_config import get_db
from models.schemas import CourseStudyInfo
from models.db_models import User, Mistake, StudyRecord
from sqlalchemy.orm import Session
from typing import List
import asyncio

from services.ocr_service import save_uploaded_file, extract_text_from_image
from services.user_service import get_or_create_test_user
from services.mistake_service import get_user_mistakes, count_user_mistakes
from services.study_service import (
    get_latest_scores,
    get_total_durations,
    generate_study_summary
)

router = APIRouter()


# ==================== 1. 错题上传接口 ====================
@router.post("/mistakes/upload")
async def upload_mistake(
    screenshot: UploadFile = File(...),
    course_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    题目解析：上传错题截图 + 所属课程
    """
    # 1. 校验文件类型
    if not screenshot.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        raise HTTPException(
            status_code=400,
            detail=f"只支持 {', '.join(ALLOWED_EXTENSIONS)} 格式的图片"
        )

    saved_path = None
    try:
        # 2. 获取当前用户
        current_user = get_or_create_test_user(db)

        # 3. 保存图片并 OCR
        loop = asyncio.get_running_loop()
        saved_path = await loop.run_in_executor(None, save_uploaded_file, screenshot)
        ocr_result = await loop.run_in_executor(None, extract_text_from_image, saved_path)

        # 4. 存入数据库
        db_mistake = Mistake(
            user_id=current_user.id,
            course_name=course_name,
            ocr_text=ocr_result,       # 目前清洗逻辑已合并，直接复用
            image_path=saved_path,
        )
        db.add(db_mistake)
        db.commit()
        db.refresh(db_mistake)

        # 5. 查询当前用户总错题数
        total_count = count_user_mistakes(db, current_user.id)

        # 6. 返回成功响应
        return {
            "code": 200,
            "message": f"✅ 已收录 {course_name} 错题，当前共 {total_count} 道",
            "data": {
                "mistake": {
                    "id": db_mistake.id,
                    "course_name": db_mistake.course_name,
                    "ocr_text": db_mistake.ocr_text[:100] + "..." if len(db_mistake.ocr_text or "") > 100 else db_mistake.ocr_text,
                    "created_at": db_mistake.created_at.isoformat() if db_mistake.created_at else None,
                },
                "total_count": total_count
            }
        }

    except Exception as e:
        # 如果有异常，回滚事务
        db.rollback()
        raise HTTPException(status_code=500, detail=f"服务器处理出错: {str(e)}")
    finally:
        # 注意：图片保留用于回溯，不删除
        pass


# ==================== 2. 上传学习情况接口 ====================
@router.put("/profile/update")
async def update_study_profile(
    courses: List[CourseStudyInfo],
    db: Session = Depends(get_db)
):
    """
    学习情况：记录每次提交的成绩和新增学习时长（追加写入）
    """
    try:
        # 1. 获取当前用户
        current_user = get_or_create_test_user(db)

        # 2. 校验并批量插入
        inserted_courses = []
        for course in courses:
            # 校验成绩范围
            if course.score is not None:
                if course.score < 0 or course.score > 100:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{course.course_name} 成绩必须在 0-100 之间，当前值：{course.score}"
                    )

            # 校验学习时长不能为负
            if course.study_duration is not None and course.study_duration < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"{course.course_name} 学习时长不能为负数，当前值：{course.study_duration}"
                )

            # 创建新记录
            new_record = StudyRecord(
                user_id=current_user.id,
                course_name=course.course_name,
                score=course.score,
                study_duration=course.study_duration
            )
            db.add(new_record)
            inserted_courses.append(course.course_name)

        # 提交事务
        db.commit()

    except HTTPException:
        # 校验失败，回滚
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库写入失败: {str(e)}")

    # 3. 查询最新成绩（每个课程取最新一条记录）
    latest_scores = get_latest_scores(db, current_user.id)

    # 4. 查询累计学习时长
    total_durations = get_total_durations(db, current_user.id)

    # 5. 返回结果
    return {
        "code": 200,
        "message": f"✅ 已记录 {len(inserted_courses)} 门课程的学习情况",
        "data": {
            "latest_scores": latest_scores,
            "total_durations": total_durations,
            "inserted_courses": inserted_courses
        }
    }


# ==================== 3. 获取用户画像接口 ====================
@router.get("/profile")
async def get_user_profile(
    db: Session = Depends(get_db)
):
    """
    获取用户当前学业画像（用于前端数据看板）
    """
    # 1. 获取当前用户
    current_user = get_or_create_test_user(db)

    # 2. 查询所有错题
    mistakes = get_user_mistakes(db, current_user.id)

    # 3. 查询错题总数
    total_mistakes = count_user_mistakes(db, current_user.id)

    # 4. 查询最新成绩（每个课程取最新一条记录）
    latest_scores = get_latest_scores(db, current_user.id)

    # 5. 查询累计学习时长
    total_durations = get_total_durations(db, current_user.id)

    # 6. 生成摘要
    summary = generate_study_summary(latest_scores, total_durations, total_mistakes)

    # 7. 格式化错题列表（返回简洁版）
    mistake_list = []
    for m in mistakes:
        text_preview = m.ocr_text
        if text_preview and len(text_preview) > 50:
            text_preview = text_preview[:50] + "..."
        mistake_list.append({
            "id": m.id,
            "course_name": m.course_name,
            "ocr_text": text_preview,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {
        "code": 200,
        "data": {
            "total_mistakes": total_mistakes,
            "mistakes": mistake_list,
            "latest_scores": latest_scores,
            "total_durations": total_durations,
            "summary": summary
        }
    }