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
    使用阿里云百炼 qwen3.5-ocr 模型提取图片文字，并自动清洗
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件未找到: {image_path}")

    file_size = os.path.getsize(image_path)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    if file_size > MAX_IMAGE_SIZE:
        raise ValueError(f"图片大小 {file_size / 1024 / 1024:.1f}MB 超过限制 20MB")

    try:
        response = MultiModalConversation.call(
            model="qwen3.5-ocr",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": image_path},
                        {"text": "请提取图片中的所有文字内容。"}
                    ]
                }
            ],
            temperature=0.1,
        )

        # 防御性取值
        if not response or not hasattr(response, 'output'):
            raise RuntimeError("阿里云 OCR 返回数据格式异常（缺少 output 字段）")
        if not response.output or not response.output.choices:
            raise RuntimeError("阿里云 OCR 返回数据格式异常（缺少 choices 字段）")

        result_text = response.output.choices[0].message.content[0]["text"]

        # 如果结果为空，提前返回友好提示
        if not result_text or not result_text.strip():
            return "[未检测到任何文字，请检查图片是否清晰或是否包含文字]"

        # 数据清洗
        # 1. 压缩多个空白字符（空格、换行、制表符等）为单个空格
        cleaned = re.sub(r'\s+', ' ', result_text)
        # 2. 移除不可见控制字符
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        # 3. 去除首尾空格
        cleaned = cleaned.strip()

        return cleaned

    except Exception as e:
        raise RuntimeError(f"DashScope OCR 调用失败: {str(e)}")