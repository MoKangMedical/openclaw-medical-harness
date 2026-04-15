"""
Model Providers — 可插拔的LLM后端。

支持：
- MIMO (小米大模型)
- OpenAI (GPT-4等)
- Claude (Anthropic)
- 本地Ollama

核心原则：模型可替换，Harness是私有的。
"""

from .base import ModelProvider
from .mimo import MIMOProvider
from .factory import create_provider

__all__ = [
    "ModelProvider",
    "MIMOProvider",
    "create_provider",
]
