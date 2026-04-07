"""
Context Manager — Harness上下文管理器。

负责构建、压缩和传递Harness执行过程中的上下文信息。
核心原则：结构化上下文 > 原始文本，压缩 > 原样传递。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime, timezone


class CompressionStrategy(str, Enum):
    """上下文压缩策略。"""
    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"
    HIERARCHICAL = "hierarchical"
    MEDICAL_PRIORITIZED = "medical_prioritized"


@dataclass
class HarnessContext:
    """Harness执行上下文。"""
    patient_data: dict[str, Any] = field(default_factory=dict)
    clinical_history: list[dict[str, Any]] = field(default_factory=list)
    tool_outputs: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_compact(self) -> dict[str, Any]:
        """压缩上下文为模型友好的格式。"""
        return {
            "patient": self._summarize_patient(),
            "history": self._summarize_history(),
            "tools": self._summarize_tools(),
            "meta": self.metadata,
        }

    def _summarize_patient(self) -> dict[str, Any]:
        essential = {}
        for key in ["age", "sex", "symptoms", "chief_complaint", "diagnosis"]:
            if key in self.patient_data:
                essential[key] = self.patient_data[key]
        return essential

    def _summarize_history(self) -> list[str]:
        return [
            f"{h.get('date', '?')}: {h.get('event', '?')}"
            for h in self.clinical_history[-10:]
        ]

    def _summarize_tools(self) -> dict[str, Any]:
        summary = {}
        for tool_name, output in self.tool_outputs.items():
            if isinstance(output, dict) and "findings" in output:
                summary[tool_name] = output["findings"]
            elif isinstance(output, dict) and "error" not in output:
                summary[tool_name] = output
        return summary


class ContextManager:
    """Harness上下文管理器。

    职责：
      - 从原始输入数据构建结构化上下文
      - 在接近token限制时压缩上下文
      - 维护关键信息（过敏、药物交互）
      - 在Harness阶段间传递带连续性的上下文
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.max_history = self.config.get("max_history", 20)
        self.compression = self.config.get("compression", "medical_prioritized")
        self.max_tokens = self.config.get("max_tokens", 8192)
        self.include_tool_outputs = self.config.get("include_tool_outputs", True)

    def build(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """从输入数据构建结构化上下文。

        Args:
            input_data: 原始输入（症状、患者数据等）。

        Returns:
            结构化的Harness上下文。
        """
        ctx = HarnessContext()

        # 提取患者数据
        if "patient" in input_data:
            ctx.patient_data = input_data["patient"]
        if "patient_history" in input_data:
            ctx.patient_data.update(input_data["patient_history"])
        if "symptoms" in input_data:
            ctx.patient_data["symptoms"] = input_data["symptoms"]
        if "chief_complaint" in input_data:
            ctx.patient_data["chief_complaint"] = input_data["chief_complaint"]
        # 合并顶层字段到patient_data
        for key in ["age", "sex", "disease", "conditions", "lab_results", "wearable_data"]:
            if key in input_data and key not in ctx.patient_data:
                ctx.patient_data[key] = input_data[key]

        # 提取临床历史
        if "history" in input_data:
            ctx.clinical_history = input_data["history"]
        if "medical_history" in input_data:
            ctx.clinical_history.extend(
                {"event": h} if isinstance(h, str) else h
                for h in input_data["medical_history"]
            )

        # 元数据
        ctx.metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "specialty": input_data.get("specialty", "general"),
            "urgency": input_data.get("urgency", "routine"),
            "language": input_data.get("language", "zh"),
            "compression_strategy": self.compression,
        }

        return ctx.to_compact()

    def compress(self, context: dict[str, Any]) -> dict[str, Any]:
        """压缩上下文以适应token限制。"""
        estimated_tokens = self._estimate_tokens(context)
        if estimated_tokens <= self.max_tokens:
            return context

        if self.compression == CompressionStrategy.TRUNCATE.value or self.compression == "truncate":
            return self._compress_truncate(context)
        elif self.compression == CompressionStrategy.SUMMARIZE.value or self.compression == "summarize":
            return self._compress_summarize(context)
        elif self.compression == CompressionStrategy.HIERARCHICAL.value or self.compression == "hierarchical":
            return self._compress_hierarchical(context)
        else:
            return self._compress_medical_prioritized(context)

    def merge(self, base: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        """合并新上下文到基础上下文。"""
        merged = base.copy()
        for key, value in new.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = {**merged[key], **value}
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = merged[key][-self.max_history:] + value
            else:
                merged[key] = value
        return merged

    def _compress_truncate(self, context: dict[str, Any]) -> dict[str, Any]:
        compressed = dict(context)
        if "history" in compressed:
            compressed["history"] = compressed["history"][-2:]
        compressed["_compressed"] = True
        return compressed

    def _compress_summarize(self, context: dict[str, Any]) -> dict[str, Any]:
        compressed = dict(context)
        if "history" in compressed and compressed["history"]:
            compressed["history_summary"] = f"{len(compressed['history'])} prior stages"
            compressed["history"] = compressed["history"][-1:]
        compressed["_compressed"] = True
        return compressed

    def _compress_hierarchical(self, context: dict[str, Any]) -> dict[str, Any]:
        compressed = dict(context)
        for key in list(compressed.keys()):
            if isinstance(compressed[key], dict) and key not in ("patient", "meta"):
                compressed[key] = {k: type(v).__name__ for k, v in compressed[key].items()}
        compressed["_compressed"] = True
        return compressed

    def _compress_medical_prioritized(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "patient": context.get("patient", {}),
            "meta": context.get("meta", {}),
            "history": context.get("history", [])[-2:],
            "tools": context.get("tools", {}),
            "_compressed": True,
            "_strategy": "medical_prioritized",
        }

    @staticmethod
    def _estimate_tokens(context: dict[str, Any]) -> int:
        text = json.dumps(context, default=str)
        return len(text) // 4
