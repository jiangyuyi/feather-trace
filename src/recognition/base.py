"""
识别器抽象基类

定义所有识别器（本地、云平台）必须实现的接口，
支持同步和异步两种调用方式。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from typing_extensions import Protocol
from .protocol import RecognizeRequest, RecognizeResponse, RecognitionResult


class BaseRecognizer(Protocol):
    """识别器协议（接口）"""

    @property
    def platform(self) -> str:
        """返回平台标识符"""
        ...

    @property
    def is_available(self) -> bool:
        """检查识别器是否可用"""
        ...

    async def recognize(self, request: RecognizeRequest) -> RecognizeResponse:
        """
        识别单张图片

        Args:
            request: 识别请求

        Returns:
            识别响应
        """
        ...

    async def recognize_batch(
        self,
        requests: List[RecognizeRequest],
        max_concurrent: int = 5
    ) -> List[RecognizeResponse]:
        """
        批量识别多张图片

        Args:
            requests: 识别请求列表
            max_concurrent: 最大并发数

        Returns:
            识别响应列表
        """
        ...


class AbstractBirdRecognizer(ABC):
    """鸟类识别器抽象基类"""

    @property
    @abstractmethod
    def platform(self) -> str:
        """返回平台标识符"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """检查识别器是否可用（API Key、模型等）"""
        pass

    @abstractmethod
    async def recognize(self, request: RecognizeRequest) -> RecognizeResponse:
        """
        识别单张图片

        Args:
            request: 识别请求

        Returns:
            RecognizeResponse: 识别响应
        """
        pass

    async def recognize_batch(
        self,
        requests: List[RecognizeRequest],
        max_concurrent: int = 5
    ) -> List[RecognizeResponse]:
        """
        批量识别（默认使用顺序处理，子类可重写为并发）

        Args:
            requests: 识别请求列表
            max_concurrent: 最大并发数

        Returns:
            List[RecognizeResponse]: 识别响应列表
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(request: RecognizeRequest) -> RecognizeResponse:
            async with semaphore:
                return await self.recognize(request)

        tasks = [process_with_limit(req) for req in requests]
        return await asyncio.gather(*tasks)

    def _parse_response(
        self,
        raw_results: List[Dict[str, Any]],
        platform: str,
        image_path: str,
        processing_time_ms: int
    ) -> RecognizeResponse:
        """
        解析平台原始响应为统一格式

        Args:
            raw_results: 平台原始结果
            platform: 平台标识
            image_path: 图片路径
            processing_time_ms: 处理时间

        Returns:
            统一的识别响应
        """
        results = []
        for item in raw_results:
            results.append(RecognitionResult(
                label=item.get("label", ""),
                scientific_name=item.get("scientific_name"),
                chinese_name=item.get("chinese_name"),
                confidence=item.get("confidence", 0.0),
                source_label=item.get("source_label")
            ))

        return RecognizeResponse(
            success=True,
            image_path=image_path,
            results=results,
            platform=platform,
            processing_time_ms=processing_time_ms
        )

    def _create_error_response(
        self,
        request: RecognizeRequest,
        error: str
    ) -> RecognizeResponse:
        """创建错误响应"""
        return RecognizeResponse(
            success=False,
            image_path=request.image_path,
            image_url=request.image_url,
            results=[],
            platform=request.platform.value,
            processing_time_ms=0,
            error=error
        )


# 兼容旧版接口
BirdRecognizer = AbstractBirdRecognizer
