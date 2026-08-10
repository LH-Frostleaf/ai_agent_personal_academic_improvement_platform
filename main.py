from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import perception

# 导入数据库配置和所有模型（一定要导入，否则 SQLAlchemy 不知道要建什么表）
from config.database_config import engine
from models import db_models  # 虽然没直接用到，但必须导入才能注册表

# 创建应用实例
app = FastAPI(title="大学生学业诊断Agent后端", version="1.0")

# 配置跨域 (让Vue前端可以调用)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有，生产环境请替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建所有表（如果不存在的话）
db_models.Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(perception.router, prefix="/api/v1", tags=["感知模块"])

@app.get("/")
def root():
    return {"message": "感知模块已启动，请访问 /docs 查看API文档"}