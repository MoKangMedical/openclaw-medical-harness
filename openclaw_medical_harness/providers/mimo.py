"""
MIMO Provider — 小米大模型API适配器。

支持小米MIMO模型系列。
API格式兼容OpenAI Chat Completions。
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import httpx

from .base import ModelProvider, GenerationResult

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_BASE_URL = "https://api.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2-pro"


class MIMOProvider(ModelProvider):
    """小米MIMO模型提供者。

    通过HTTP API调用MIMO模型。
    支持OpenAI兼容的Chat Completions格式。

    Example:
        >>> provider = MIMOProvider(api_key="your-key")
        >>> result = provider.generate("你好，请介绍一下自己")
        >>> print(result.text)

        >>> # 使用JSON模式
        >>> data = provider.generate_json(
        ...     "返回一个JSON，包含3个罕见病名称",
        ...     system="你是一个医学专家"
        ... )
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        timeout: float = 60.0,
    ) -> None:
        """初始化MIMO提供者。

        Args:
            api_key: API密钥（也可以通过MIMO_API_KEY环境变量设置）。
            base_url: API基础URL（也可以通过MIMO_BASE_URL设置）。
            model: 模型名称（也可以通过MIMO_MODEL设置）。
            timeout: 请求超时时间（秒）。
        """
        self._api_key = api_key or os.getenv("MIMO_API_KEY", "")
        self._base_url = (base_url or os.getenv("MIMO_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self._model_name = model or os.getenv("MIMO_MODEL", DEFAULT_MODEL)
        self._timeout = timeout

        if not self._api_key:
            logger.warning(
                "MIMO API key not set. "
                "Set MIMO_API_KEY env var or pass api_key= parameter."
            )

        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    @property
    def name(self) -> str:
        return "mimo"

    @property
    def model(self) -> str:
        return self._model_name

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> GenerationResult:
        """调用MIMO API生成文本。

        Args:
            prompt: 用户消息。
            system: 系统提示。
            temperature: 温度（0-1）。
            max_tokens: 最大token数（含推理token，默认4096）。
            **kwargs: 额外参数（top_p, stop等）。

        Returns:
            GenerationResult。
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        try:
            response = self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            # MIMO模型将思考过程放在reasoning_content字段
            content = message.get("content", "")
            reasoning = message.get("reasoning_content", "")

            # 如果content为空但有reasoning，用reasoning
            if not content and reasoning:
                content = reasoning

            return GenerationResult(
                text=content,
                model=data.get("model", self._model_name),
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", ""),
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            logger.error("MIMO API HTTP error: %s %s", e.response.status_code, e.response.text)
            return GenerationResult(
                text=f"[MIMO API Error: {e.response.status_code}]",
                model=self._model_name,
                finish_reason="error",
            )
        except httpx.RequestError as e:
            logger.error("MIMO API request error: %s", str(e))
            return GenerationResult(
                text=f"[MIMO API Connection Error: {e}]",
                model=self._model_name,
                finish_reason="error",
            )
        except Exception as e:
            logger.error("MIMO API unexpected error: %s", str(e))
            return GenerationResult(
                text=f"[MIMO API Error: {e}]",
                model=self._model_name,
                finish_reason="error",
            )

    def close(self) -> None:
        """关闭HTTP客户端。"""
        self._client.close()

    def __del__(self) -> None:
        self.close()
