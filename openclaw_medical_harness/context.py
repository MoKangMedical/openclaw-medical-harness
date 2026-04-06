"""
Context Manager — Harness上下文管理器。

负责构建、压缩和传递Harness执行过程中的上下文信息。
核心原则：结构化上下文 > 原始文本，压缩 > 原样传递。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


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
        """摘要患者数据，去除冗余字段。"""
        essential = {}
        for key in ["age", "sex", "symptoms", "chief_complaint", "diagnosis"]:
            if key in self.patient_data:
                essential[key] = self.patient_data[key]
        return essential

    def _summarize_history(self) -> list[str]:
        """摘要临床历史为关键事件列表。"""
        return [
            f"{h.get('date', '?')}: {h.get('event', '?')}"
            for h in self.clinical_history[-10:]  # 最近10条
        ]

    def _summarize_tools(self) -> dict[str, Any]:
        """摘要工具输出，保留关键发现。"""
        summary = {}
        for tool_name, output in self.tool_outputs.items():
            if isinstance(output, dict) and "findings" in output:
                summary[tool_name] = output["findings"]
            elif isinstance(output, dict) and "error" not in output:
                summary[tool_name] = output
        return summary


class ContextManager:
    """Harness上下文管理器。"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.max_history = self.config.get("max_history", 20)
        self.compression = self.config.get("compression", "summary")
        self.include_tool_outputs = self.config.get("include_tool_outputs", True)

    def build(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        从输入数据构建结构化上下文。

        Args:
            input_data: 原始输入，可能包含症状、患者信息、历史等。

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
            "specialty": input_data.get("specialty", "general"),
            "urgency": input_data.get("urgency", "routine"),
            "language": input_data.get("language", "zh"),
        }

        return ctx.to_compact()

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
