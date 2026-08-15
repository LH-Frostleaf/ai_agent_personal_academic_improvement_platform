import os
import json
from typing import AsyncGenerator, Optional
import dashscope
from dashscope import Generation

from config.settings import settings


dashscope.api_key = settings.DASHSCOPE_API_KEY


async def stream_explain_mistake(
    course_name: str,
    ocr_text: str,
) -> AsyncGenerator[str, None]:
    """
    流式解析错题，逐字返回结果。
    """
    # 1. 构造 Prompt
    system_prompt = """
        你是一位经验丰富的学科辅导老师。你的任务是针对学生提供的题目，进行深入、清晰的讲解。

        请按以下结构进行解析，使用友好的语气，帮助学生真正理解：
        1.  **正确思路**：给出详细的、分步骤的正确解题思路。
        2.  **知识点总结**：提炼出本题的关键知识点.
        3.  **提供建议**: 针对性适当提供一些学习建议。

        请确保讲解内容准确、有启发性。
    """
    user_prompt = f"""
        请帮我解析以下错题：
        所属课程：{course_name}
        题目内容（OCR识别结果）：{ocr_text}
    """

    # 2. 调用 DashScope 的处理纯文本的流式 API
    responses = Generation.call(
        model="qwen3.8-max",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        result_format='message',
        stream=True,  # 关键：开启流式输出
        incremental_output=True # 推荐开启，每次只返回新增的部分
    )

    # 3. 逐块（chunk）返回结果
    for response in responses:
        if response.status_code == 200:
            # 从流式响应中提取文本
            chunk = response.output.choices[0].message.content
            if chunk:
                yield chunk
        else:
            # 处理错误
            error_msg = f"大模型API调用失败: {response.message}"
            yield f"[ERROR] {error_msg}"
            break