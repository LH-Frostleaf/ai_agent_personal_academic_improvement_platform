from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import perception

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

# 注册路由
app.include_router(perception.router, prefix="/api/v1", tags=["感知模块"])

@app.get("/")
def root():
    return {"message": "感知模块已启动，请访问 /docs 查看API文档"}

444