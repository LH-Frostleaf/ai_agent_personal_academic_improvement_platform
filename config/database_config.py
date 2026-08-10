from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# 1. 定位到项目根目录，创建 instance 文件夹存放数据库文件
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(DB_DIR, exist_ok=True)  # 确保文件夹存在

# 2. 数据库文件路径
DB_PATH = os.path.join(DB_DIR, "edu_agent.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 3. 创建引擎（connect_args 是 SQLite 多线程必须的参数）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 4. 创建会话工厂（用于操作数据库）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. 基类（所有 ORM 模型都继承它）
Base = declarative_base()

# 6. 依赖注入函数（用于 FastAPI 接口获取会话）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()