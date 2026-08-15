import os
from typing import AsyncGenerator, Optional
from openai import OpenAI
from config.settings import settings

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

async def stream_explain_mistake(
    course_name: str,
    ocr_text: str,
) -> AsyncGenerator[str, None]:
    """
    流式解析错题，逐字返回结果。
    """
    system_prompt = """
        你是一位经验丰富的学科辅导老师。你的任务是针对学生提供的错题，进行深入、清晰的讲解。

        请按以下结构进行解析，使用友好的语气，帮助学生真正理解：
        1.  **正确思路**：给出详细的、分步骤的正确解题思路。
        2.  **知识点总结**：提炼出本题的关键知识点，
        3.  **学习思路**: 针对性提供一些合理的学习建议。

        请确保讲解内容准确、有启发性。
        """

    user_prompt = f"""
        请帮我解析以下错题：
        所属课程：{course_name}
        题目内容（OCR识别结果）：{ocr_text}
    """

    try:
        # 调用 OpenAI 兼容接口，开启流式
        response = client.chat.completions.create(
            model="qwen3.8-max",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True,
            stream_options={"include_usage": False},  # 可选
        )

        # 逐块返回内容
        for chunk in response:
            # 检查是否有内容
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        # 捕获异常并返回错误信息
        error_msg = f"大模型API调用失败: {str(e)}"
        yield f"[ERROR] {error_msg}"