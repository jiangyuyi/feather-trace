"""
鸟类识别模块

提供多种识别引擎支持：
- 本地 BioCLIP 模型
- 云平台 API (HuggingFace, ModelScope, Aliyun, Baidu)
"""
from .base import AbstractBirdRecognizer, BaseRecognizer, BirdRecognizer
from .inference_local import LocalBirdRecognizer
from .protocol import (
    RecognitionPlatform,
    RecognizeRequest,
    RecognizeResponse,
    BatchRecognizeRequest,
    BatchRecognizeResponse,
    RecognitionResult,
    BatchJobStatus,
)

__all__ = [
    # 基类
    "AbstractBirdRecognizer",
    "BaseRecognizer",
    "BirdRecognizer",
    # 本地识别
    "LocalBirdRecognizer",
    # 云平台
    "cloud",
    # 协议
    "RecognitionPlatform",
    "RecognizeRequest",
    "RecognizeResponse",
    "BatchRecognizeRequest",
    "BatchRecognizeResponse",
    "RecognitionResult",
    "BatchJobStatus",
]
