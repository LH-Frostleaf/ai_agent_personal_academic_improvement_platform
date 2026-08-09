# api/perception.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.schemas import MistakeRecord, UserAcademicProfile, CourseStudyInfo
from services.ocr_service import save_uploaded_file, extract_text_from_image
from datetime import datetime
from typing import List
import asyncio

router = APIRouter()

# 临时存储（后续换成数据库）
user_profile = UserAcademicProfile()


@router.post("/mistakes/upload")
async def upload_mistake(
        screenshot: UploadFile = File(...),
        course_name: str = Form(...)  # 强制选择所属课程
):
    """
    题目解析：上传错题截图 + 所属课程
    """
    # 1. 校验文件类型
    allowed_ext = ('.png', '.jpg', '.jpeg', '.bmp')
    if not screenshot.filename.lower().endswith(allowed_ext):
        raise HTTPException(400, f"只支持 {', '.join(allowed_ext)} 格式")

    saved_path = None
    try:
        # 2. 保存图片并 OCR
        loop = asyncio.get_event_loop()
        saved_path = await loop.run_in_executor(None, save_uploaded_file, screenshot)
        ocr_text = await loop.run_in_executor(None, extract_text_from_image, saved_path)

        # 3. 生成错题记录（此时还没有知识点标签，后续 RAG 处理）
        mistake = MistakeRecord(
            course_name=course_name,
            ocr_text=ocr_text,
            image_path=saved_path,
            uploaded_at=datetime.now()
        )

        # 4. 存入用户画像（临时存储，后续换数据库）
        user_profile.mistakes.append(mistake)

        # 5. 返回成功响应 + 当前错题总数
        return {
            "code": 200,
            "message": f"✅ 已收录 {course_name} 错题，当前共 {len(user_profile.mistakes)} 道",
            "data": {
                "mistake": mistake.dict(),
                "total_count": len(user_profile.mistakes)
            }
        }

    except Exception as e:
        # 异常处理（同之前）
        raise HTTPException(500, f"服务器处理出错: {str(e)}")
    finally:
        # 注意：这里不删除图片，因为后面要用于回溯
        # 或者你可以保留，定期清理
        pass


@router.put("/profile/update")
async def update_study_profile(
        courses: List[CourseStudyInfo]  # 前端传课程列表
):
    """
    学习情况：更新各科成绩和学习时长
    """
    try:
        # 更新成绩
        for course in courses:
            if course.score is not None:
                # 校验成绩范围
                if course.score < 0 or course.score > 100:
                    raise HTTPException(400, f"{course.course_name} 成绩必须在 0-100 之间")
                user_profile.course_scores[course.course_name] = course.score

            if course.study_duration is not None:
                if course.study_duration < 0:
                    raise HTTPException(400, f"{course.course_name} 学习时长不能为负数")
                user_profile.study_duration[course.course_name] = course.study_duration

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
            "mistakes": [m.dict() for m in user_profile.mistakes],
            "course_scores": user_profile.course_scores,
            "study_duration": user_profile.study_duration,
            "summary": user_profile.summary,
            "total_mistakes": len(user_profile.mistakes)
        }
    }