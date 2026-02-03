"""
识别 API 路由

提供批量识别、单张识别、任务管理等 REST API 端点。
"""
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Security, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import logging

from src.recognition.protocol import (
    RecognizeRequest,
    RecognizeResponse,
    BatchRecognizeRequest,
    BatchRecognizeResponse,
    BatchResultResponse,
    ListPlatformsResponse,
    PlatformInfo,
    HealthResponse,
    BatchJobStatus,
)
from src.recognition.batch import BatchRecognitionService
from src.recognition.cloud.factory import RecognizerFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recognition", tags=["recognition"])

# 全局批量识别服务实例
batch_service: Optional[BatchRecognitionService] = None

# API Key 认证头
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_batch_service() -> BatchRecognitionService:
    """获取批量识别服务实例"""
    global batch_service
    if batch_service is None:
        batch_service = BatchRecognitionService()
    return batch_service


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """验证 API Key（可选认证）"""
    # 如果没有提供 API Key，允许匿名访问（可在配置中改为必须）
    if api_key is None:
        return True

    # TODO: 从数据库验证 API Key
    # 这里简化处理，实际应该验证 Key 是否有效
    return True


# --- 单张识别 ---

@router.post("/recognize", response_model=RecognizeResponse)
async def recognize(
    request: RecognizeRequest,
    _auth: bool = Depends(verify_api_key)
) -> RecognizeResponse:
    """
    识别单张图片

    - **image_path**: 本地文件路径
    - **image_url**: 图片 URL
    - **image_base64**: Base64 编码的图片数据
    - **platform**: 识别平台 (local, huggingface, modelscope, aliyun, baidu)
    - **top_k**: 返回前 K 个结果 (默认 5)
    """
    try:
        recognizer = RecognizerFactory.create(request.platform.value)
        return await recognizer.recognize(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Recognition error: {e}")
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")


# --- 批量识别 ---

@router.post("/batch", response_model=BatchRecognizeResponse)
async def create_batch(
    request: BatchRecognizeRequest,
    background_tasks: BackgroundTasks,
    _auth: bool = Depends(verify_api_key)
) -> BatchRecognizeResponse:
    """
    创建批量识别任务

    - **images**: 图片识别请求列表
    - **webhook_url**: 完成后回调地址（可选）
    - **notify_email**: 完成后通知邮箱（可选）

    返回任务 ID，可通过 `/api/recognition/batch/{batch_id}` 查询进度和结果。
    """
    service = get_batch_service()

    # 验证请求
    if not request.images:
        raise HTTPException(status_code=400, detail="No images provided")

    if len(request.images) > 1000:
        raise HTTPException(status_code=400, detail="Max 1000 images per batch")

    # 创建任务
    response = service.create_batch(request)

    # 在后台开始处理
    background_tasks.add_task(
        service.start_batch,
        response.batch_id
    )

    return response


@router.post("/batch/{batch_id}/start")
async def start_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
    _auth: bool = Depends(verify_api_key)
) -> dict:
    """
    开始处理批量任务

    如果创建任务时没有立即开始处理，可以调用此接口开始。
    """
    service = get_batch_service()
    success = await service.start_batch(batch_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start batch {batch_id}. Check if it exists and is not already processing."
        )

    return {"status": "started", "batch_id": batch_id}


@router.get("/batch/{batch_id}", response_model=BatchRecognizeResponse)
async def get_batch_status(
    batch_id: str,
    _auth: bool = Depends(verify_api_key)
) -> BatchRecognizeResponse:
    """查询批量任务状态和进度"""
    service = get_batch_service()
    status = service.get_status(batch_id)

    if status is None:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    return status


@router.get("/batch/{batch_id}/result", response_model=BatchResultResponse)
async def get_batch_result(
    batch_id: str,
    _auth: bool = Depends(verify_api_key)
) -> BatchResultResponse:
    """获取批量任务完整结果"""
    service = get_batch_service()
    result = service.get_result(batch_id)

    if result is None:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    return result


@router.delete("/batch/{batch_id}")
async def cancel_batch(
    batch_id: str,
    _auth: bool = Depends(verify_api_key)
) -> dict:
    """取消批量任务"""
    service = get_batch_service()
    success = service.cancel_job(batch_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    return {"status": "cancelled", "batch_id": batch_id}


@router.get("/batch", response_model=list)
async def list_batches(
    status: Optional[BatchJobStatus] = None,
    limit: int = 20,
    _auth: bool = Depends(verify_api_key)
) -> list:
    """列出批量任务"""
    service = get_batch_service()
    return service.list_jobs(status=status, limit=limit)


# --- 平台信息 ---

@router.get("/platforms", response_model=ListPlatformsResponse)
async def list_platforms(
    _auth: bool = Depends(verify_api_key)
) -> ListPlatformsResponse:
    """
    列出所有可用的识别平台

    返回各平台的配置要求和能力说明。
    """
    platforms = [
        PlatformInfo(
            id="local",
            name="本地 BioCLIP",
            description="使用本地部署的 BioCLIP 模型进行识别",
            requires_api_key=False,
            is_cloud=False
        ),
        PlatformInfo(
            id="huggingface",
            name="HuggingFace",
            description="通过 HuggingFace Inference API 调用云端模型",
            requires_api_key=True,
            is_cloud=True,
            max_image_size_mb=10
        ),
        PlatformInfo(
            id="modelscope",
            name="魔搭社区",
            description="通过魔搭社区 API-Inference 调用云端模型",
            requires_api_key=True,
            is_cloud=True
        ),
        PlatformInfo(
            id="dongniao",
            name="懂鸟",
            description="国内专业鸟类识别 API 服务",
            requires_api_key=True,
            is_cloud=True,
            supported_formats=["jpg", "jpeg", "png", "webp"],
            max_image_size_mb=10
        ),
        PlatformInfo(
            id="aliyun",
            name="阿里云视觉智能",
            description="阿里云图像标签识别服务",
            requires_api_key=True,
            is_cloud=True
        ),
        PlatformInfo(
            id="baidu",
            name="百度智能云",
            description="百度云图像识别服务",
            requires_api_key=True,
            is_cloud=True
        ),
    ]

    return ListPlatformsResponse(
        platforms=platforms,
        default_platform="local"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查"""
    import torch

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        platform="feathertrace",
        gpu_available=torch.cuda.is_available(),
        gpu_device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        models_loaded=["bioclip"]
    )
