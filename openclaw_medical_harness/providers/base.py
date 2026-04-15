"""
Base Model Provider — 模型提供者的抽象基类。
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """模型生成结果。

    Attributes:
        text: 生成的文本。
        model: 使用的模型名称。
        tokens_used: 使用的token数。
        finish_reason: 结束原因。
        raw_response: 原始API响应。
    """
    text: str = ""
    model: str = ""
    tokens_used: int = 0
    finish_reason: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """尝试将文本解析为dict。"""
        try:
            return json.loads(self.text)
        except (json.JSONDecodeError, TypeError):
            return {"raw_text": self.text}


class ModelProvider(ABC):
    """模型提供者抽象基类。

    所有模型后端必须实现此接口。
    Harness通过此接口调用模型，不关心底层是哪个提供商。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称。"""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """当前使用的模型名称。"""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> GenerationResult:
        """生成文本。

        Args:
            prompt: 用户提示。
            system: 系统提示（可选）。
            temperature: 采样温度（0-1）。
            max_tokens: 最大生成token数。
            **kwargs: 提供商特定参数。

        Returns:
            GenerationResult。
        """
        ...

    def generate_json(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """生成并解析JSON输出。

        Args:
            prompt: 提示（应要求模型输出JSON）。
            system: 系统提示。
            temperature: 温度。
            max_tokens: 最大token数。

        Returns:
            解析后的字典。
        """
        result = self.generate(
            prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return result.as_dict()
