EXTRACT_PROMPT_TEMPLATE = """
你是一个知识点提取助手。给定一道错题的 OCR 文本，以及检索到的候选知识点列表，选出最匹配的 1~3 个知识点，并给出置信度（0~1）。

候选知识点列表（格式：kp_id: 名称）：
{retrieved}

错题内容：
{ocr_text}

请输出 JSON 数组，每个元素包含 "kp_id" 和 "confidence"。只输出 JSON，不要包含其他内容。
示例输出：[{{"kp_id": "kp_001", "confidence": 0.95}}, {{"kp_id": "kp_002", "confidence": 0.80}}]
"""