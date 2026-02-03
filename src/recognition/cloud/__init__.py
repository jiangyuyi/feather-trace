"""
云平台识别模块

提供对各种云平台鸟类识别 API 的支持。
"""

from .huggingface import HuggingFaceRecognizer
from .modelscope import ModelScopeRecognizer
from .aliyun import AliyunRecognizer
from .baidu import BaiduRecognizer
from .factory import RecognizerFactory, get_default_config

__all__ = [
    "HuggingFaceRecognizer",
    "ModelScopeRecognizer",
    "AliyunRecognizer",
    "BaiduRecognizer",
    "RecognizerFactory",
    "get_default_config",
]
