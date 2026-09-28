🚀 后端 FastAPI 服务（AI 学业诊断平台）


1️⃣ 搭建 Python 环境（PyCharm）

- 用 PyCharm 打开项目，**File → Settings → Project → Python Interpreter**，点击齿轮添加新的虚拟环境（Virtualenv）。
- 选择 Python 3.10+ 作为基础解释器，等待创建完成。

> 如果不会用 PyCharm 配环境，也可以直接在终端用 `python -m venv venv` 创建虚拟环境。


2️⃣ 安装依赖

打开项目根目录下的 `requirements.txt`：

- 如果里面有被注释掉的包（行首有 `#`），**先取消注释**（删掉 `#`）。
- 然后在终端执行以下命令安装所有依赖：

pip install -r requirements.txt
如果下载太慢，可以换国内镜像：
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


3️⃣ 配置大模型 API Key
在系统环境变量中设置 DASHSCOPE_API_KEY：

Windows：系统属性 → 高级 → 环境变量 → 新建，变量名 DASHSCOPE_API_KEY，值为你的阿里云百炼 API Key。

Mac / Linux：在 ~/.bashrc 或 ~/.zshrc 中添加：

export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxx"
然后执行 source ~/.bashrc 使其生效。

如果不想配系统环境变量，也可以在项目根目录新建 .env 文件，写入 DASHSCOPE_API_KEY=sk-xxxx 即可。


4️⃣ 修改模型名称（可选）
如果代码中默认的模型（如 qwen3.8-max）在您的账户下不可用，可以到 services/ 目录下找到调用大模型的文件（如 ocr_service.py、llm_service.py），找到类似下面这行：

python
model="qwen3.8-max"
改成你账户支持的模型，例如 qwen-max、qwen-plus 或 qwen-turbo。


5️⃣ 启动后端服务
在项目根目录执行：

uvicorn main:app --reload
看到类似 Uvicorn running on http://127.0.0.1:8000 的输出，就说明启动成功了。

然后打开浏览器访问 http://127.0.0.1:8000/docs 即可看到自动生成的接口文档。
