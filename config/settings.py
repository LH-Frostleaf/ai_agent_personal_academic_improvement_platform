import os
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()


class Settings:
    # DashScope API Key（从环境变量读取）
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")


settings = Settings()