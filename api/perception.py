from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.schemas import PerceptionInput
from services.ocr_service import save_uploaded_file, extract_text_from_image
from services.perception_service import clean_and_aggregate
from config.upload_config import ALLOWED_EXTENSIONS

router = APIRouter()


@router.post("/perceive")
async def perceive_user_input(
        # 接收图片文件
        screenshot: UploadFile = File(...),
        # 接收其他数据，因为Form传过来的是字符串，我们需要用Form()解析
        course_scores: str = Form(...),  # 传 JSON 字符串，如 '{"高数":78,"英语":85}'
        study_duration: str = Form(...)
):
    """
    感知模块入口
    """
    # 1. 校验文件类型
    if not screenshot.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        raise HTTPException(status_code=400, detail="只支持上传 PNG, JPG, JPEG, BMP 格式的图片")

    try:

        # 2. 组装成 Pydantic 数据模型
        raw_data = PerceptionInput(
            course_scores=course_scores,    # 函数内部利用Json自动将JSON字符串转为Python字典
            study_duration=study_duration
        )

        # 3. 【OCR处理】保存图片到本地
        saved_path = save_uploaded_file(screenshot)
        # 4. 【OCR处理】从图片中提取文字
        ocr_result = extract_text_from_image(saved_path)
        print(f"OCR识别结果: {ocr_result}")  # 在控制台打印看看效果

        # 5. 【核心】调用清洗整理服务
        cleaned_data = clean_and_aggregate(ocr_result, raw_data)

        # 6. 返回清洗后的干净数据给前端以及后续Agent
        return {
            "code": 200,
            "message": "感知模块处理成功",
            "data": cleaned_data.model_dump()   # 类对象转为字典
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"图片文件处理失败: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"OCR 服务调用失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器处理出错: {str(e)}")