from models.schemas import UserAcademicProfile


def prepare_diagnosis_data(profile: UserAcademicProfile) -> dict:
    """
    从用户画像中提取诊断所需的数据（供 Agent 调用）
    """
    # 1. 按课程归类错题
    mistakes_by_course = {}
    for m in profile.mistakes:
        if m.course_name not in mistakes_by_course:
            mistakes_by_course[m.course_name] = []
        mistakes_by_course[m.course_name].append(m.ocr_text)

    # 2. 组装诊断数据
    return {
        "course_scores": profile.course_scores,
        "study_duration": profile.study_duration,
        "mistakes_by_course": mistakes_by_course,
        "total_mistakes": len(profile.mistakes),
        "summary": profile.summary
    }