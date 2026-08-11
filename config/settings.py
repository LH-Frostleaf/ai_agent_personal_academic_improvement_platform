import os
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()


class Settings:
    # DashScope API Key（从环境变量读取）
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # JWT 配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")   # 密钥，JWT 令牌的“签名私章”
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")    # JWT 的签名算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))    # 令牌有效期为24小时


settings = Settings()