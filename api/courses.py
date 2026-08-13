from fastapi import APIRouter
from config.courses import get_course_list

router = APIRouter(prefix="/api/v1/courses", tags=["课程"])

@router.get("/list")
async def get_courses():
    """
    获取所有预设课程列表
    """
    return {
        "code": 200,
        "message": "获取成功",
        "data": get_course_list()
    }