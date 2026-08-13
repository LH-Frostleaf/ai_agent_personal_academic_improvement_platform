from typing import List

# 预设课程列表（集中管理）
DEFAULT_COURSES: List[str] = [
    "高等数学",
    "大学英语",
    "数据结构",
    "算法",
    "线性代数",
    "概率论与数理统计",
    "操作系统",
    "计算机网络",
    "数据库原理",
    "软件工程",
]

def get_course_list() -> List[str]:
    """获取课程列表（方便后续扩展，比如从数据库读取）"""
    # 目前返回固定列表，未来可以改为从数据库查询
    return DEFAULT_COURSES