import os
import json
from typing import AsyncGenerator, Optional
from openai import OpenAI
from config.settings import settings
from rag.prompts.knowledge_extract import EXTRACT_PROMPT_TEMPLATE
from services.rag_service import retriever

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

async def extract_knowledge_points(ocr_text: str, course_name: str = None):
    """
    从 OCR 文本中提取知识点
    """
    # 1. RAG 检索候选
    candidates = retriever.retrieve(ocr_text, top_k=5, subject=course_name)
    if not candidates:
        return []

    # 2. 构建 prompt
    retrieved_text = "\n".join([
        f"kp_id: {c['kp_id']}, name: {c['name']}" for c in candidates
    ])
    prompt = EXTRACT_PROMPT_TEMPLATE.format(retrieved=retrieved_text, ocr_text=ocr_text)

    # 3. 调用 LLM
    try:
        response = client.chat.completions.create(
            model="qwen3.8-max",
            messages=[
                {"role": "system", "content": "你是一个知识点提取助手，只输出 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        if isinstance(result, list):    # 判断变量 result 是不是一个列表（list）类型
            # 过滤确保 kp_id 在候选列表中
            valid_ids = {c['kp_id'] for c in candidates}
            filtered = [item for item in result if item.get('kp_id') in valid_ids]
            # 补充 name
            name_map = {c['kp_id']: c['name'] for c in candidates}
            for item in filtered:
                item['name'] = name_map.get(item['kp_id'], '')
            return filtered
        else:
            return []
    except Exception as e:
        print(f"LLM 提取知识点失败: {e}")
        return []