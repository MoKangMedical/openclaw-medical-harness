"""
Provider Factory — 创建模型提供者的工厂函数。
"""

from __future__ import annotations

import logging
from typing import Any

from .base import ModelProvider
from .mimo import MIMOProvider

logger = logging.getLogger(__name__)

# 提供商注册表
_PROVIDER_REGISTRY: dict[str, type[ModelProvider]] = {
    "mimo": MIMOProvider,
}


def create_provider(
    provider_name: str = "mimo",
    **kwargs: Any,
) -> ModelProvider:
    """创建模型提供者实例。

    Args:
        provider_name: 提供商名称（mimo/openai/claude/ollama）。
        **kwargs: 传递给提供商构造函数的参数。

    Returns:
        ModelProvider实例。

    Raises:
        ValueError: 未知的提供商名称。
    """
    provider_cls = _PROVIDER_REGISTRY.get(provider_name.lower())
    if provider_cls is None:
        available = ", ".join(_PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {available}"
        )

    logger.info("Creating model provider: %s", provider_name)
    return provider_cls(**kwargs)


def register_provider(name: str, provider_cls: type[ModelProvider]) -> None:
    """注册自定义提供商。

    Args:
        name: 提供商名称。
        provider_cls: 提供商类。
    """
    _PROVIDER_REGISTRY[name.lower()] = provider_cls
