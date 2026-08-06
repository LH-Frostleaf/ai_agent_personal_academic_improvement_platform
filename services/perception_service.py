from models.schemas import PerceptionInput, CleanedPerceptionData
from services.ocr_service import clean_ocr_text


def clean_and_aggregate(
        ocr_raw_text: str,
        input_data: PerceptionInput
) -> CleanedPerceptionData:
    """
    将OCR文字和前端传过来的结构化数据清洗、合并
    """

    # 1. 清洗OCR文本
    final_ocr = clean_ocr_text(ocr_raw_text)

    # 2. 清洗成绩：确保数值在 0-100 之间，超出则截断
    cleaned_scores = {}
    if input_data.course_scores:
        for course, score in input_data.course_scores.items():
            if score < 0:
                cleaned_scores[course] = 0.0
            elif score > 100:
                cleaned_scores[course] = 100.0
            else:
                cleaned_scores[course] = float(score)

    # 3. 清洗学习时长：不能为负数，负数变为0
    cleaned_duration = {}
    if input_data.study_duration:
        for course, hours in input_data.study_duration.items():
            cleaned_duration[course] = max(0.0, float(hours))

    # 4. 生成一段简短的汇总摘要，方便Agent直接“感知”当前状态
    avg_score = sum(cleaned_scores.values()) / len(cleaned_scores) if cleaned_scores else 0
    summary = f"学生当前各科平均成绩约 {avg_score:.1f} 分。"
    if cleaned_duration:
        total_time = sum(cleaned_duration.values())
        summary += f" 总学习时长 {total_time:.1f} 小时。"
    if final_ocr:
        summary += f" 最近错题涉及内容：{final_ocr[:50]}..."  # 截取前50字

    # 返回整理好的干净数据对象
    return CleanedPerceptionData(
        ocr_cleaned_text=final_ocr,
        course_scores=cleaned_scores,
        study_duration=cleaned_duration,
        summary=summary
    )