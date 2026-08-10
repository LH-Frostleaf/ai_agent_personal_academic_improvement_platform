from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from config.upload_config import ALLOWED_EXTENSIONS
from config.database_config import get_db
from models.db_models import User, Mistake, StudyRecord
from models.schemas import MistakeRecord, CourseStudyInfo, UserAcademicProfile
from services.ocr_service import save_uploaded_file, extract_text_from_image
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import asyncio

router = APIRouter()

# 临时存储（后续换成数据库）
user_profile = UserAcademicProfile()

# ==================== 辅助函数：获取当前用户 ====================
def get_or_create_test_user(db: Session) -> User:
    """
    开发阶段：固定使用 user_id=1 的测试用户
    如果不存在则自动创建
    """
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, username="test_user", password_hash="dev_mode")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


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
        total_count = db.query(Mistake).filter(
            Mistake.user_id == current_user.id
        ).count()

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


@router.put("/profile/update")
async def update_study_profile(
        courses: List[CourseStudyInfo]  # 前端传课程列表
):
    """
    学习情况：更新各科成绩和学习时长
    """
    try:
        for course in courses:
            # 更新成绩
            if course.score is not None:
                # 校验成绩范围
                if course.score < 0 or course.score > 100:
                    raise HTTPException(400, f"{course.course_name} 成绩必须在 0-100 之间")
                user_profile.course_scores[course.course_name] = course.score

            # 累加学习时长
            if course.study_duration is not None:
                if course.study_duration < 0:
                    raise HTTPException(400, f"{course.course_name} 学习时长不能为负数")
                user_profile.study_duration[course.course_name] += course.study_duration

        return {
            "code": 200,
            "message": "✅ 学习情况更新成功",
            "data": {
                "course_scores": user_profile.course_scores,
                "study_duration": user_profile.study_duration
            }
        }

    except Exception as e:
        raise HTTPException(500, f"更新失败: {str(e)}")


@router.get("/profile")
async def get_user_profile():
    """
    获取用户当前学业画像（用于前端数据看板）
    """
    return {
        "code": 200,
        "data": {
            "mistakes": [m.model_dump() for m in user_profile.mistakes],
            "course_scores": user_profile.course_scores,
            "study_duration": user_profile.study_duration,
            "summary": user_profile.summary,
            "total_mistakes": len(user_profile.mistakes)
        }
    }