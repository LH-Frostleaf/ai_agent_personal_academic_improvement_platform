import os
import dashscope
from dashscope import MultiModalConversation
from config.settings import settings  # 导入统一配置
from datetime import datetime
from config.upload_config import UPLOAD_DIR  # 假设你有此配置
import re   # Python 内置的正则表达式模块

# 设置 API Key（全局只需设置一次）
dashscope.api_key = settings.DASHSCOPE_API_KEY


def save_uploaded_file(upload_file) -> str:
    """
    保存前端上传的图片到本地 storage/uploads 文件夹
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(upload_file.filename)[-1]
    safe_filename = f"screenshot_{timestamp}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())

    return file_path


def extract_text_from_image(image_path: str) -> str:
    """
    使用阿里云百炼 qwen3.5-ocr 模型提取图片文字
    """
    # 检查图片是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件未找到: {image_path}")

    # 调用 DashScope 的多模态对话接口
    try:
        response = MultiModalConversation.call(
            model="qwen3.5-ocr",  # 模型名称
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": image_path},  # 本地图片路径
                        {"text": "请提取图片中的所有文字内容。"}  # 指令
                    ]
                }
            ],
            temperature=0.1,  # OCR 任务建议低温度
        )

        # 解析返回结果
        # 根据 API 文档，返回结构为 response.output.choices[0].message.content[0]["text"]
        result_text = response.output.choices[0].message.content[0]["text"]
        return result_text

    except Exception as e:
        # 抛出更具体的错误，上层会捕获并返回 500
        raise RuntimeError(f"DashScope OCR 调用失败: {str(e)}")


def clean_ocr_text(raw_text: str) -> str:
    """
    清洗 OCR 出来的文字
    """

    # 1. 压缩多个空白字符
    cleaned = re.sub(r'\s+', ' ', raw_text)
    # 2. 移除不可见控制字符
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
    # 3. 去除首尾空格
    cleaned = cleaned.strip()
    return cleaned