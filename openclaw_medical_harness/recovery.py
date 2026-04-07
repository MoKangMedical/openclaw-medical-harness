"""
Failure Recovery — Harness失败恢复机制。

医疗AI中的失败恢复策略：
1. ESCALATE: 不确定时升级到更高级别的推理（如多学科会诊）
2. RETRY: 换模型/换prompt重试
3. FALLBACK: 降级到规则引擎
4. DEGRADE_GRACEFULLY: 优雅降级，返回部分结果

在医疗AI中，失败不是选项。恢复模块实现多层升级策略：
重试 → 降级 → 人工升级。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RecoveryStrategy(str, Enum):
    """恢复策略枚举。"""
    ESCALATE = "escalate"
    RETRY = "retry"
    FALLBACK = "fallback"
    DEGRADE_GRACEFULLY = "degrade_gracefully"
    ABORT = "abort"


class EscalationLevel(str, Enum):
    """升级严重程度。"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RecoveryResult:
    """恢复尝试的结果。

    Attributes:
        recovered: 恢复是否成功。
        strategy_used: 使用的恢复策略。
        validation: 恢复后的验证结果。
        message: 人类可读的恢复摘要。
        requires_human: 是否需要人工专家审核。
    """
    recovered: bool = False
    strategy_used: RecoveryStrategy = RecoveryStrategy.RETRY
    validation: Any = None
    message: str = ""
    requires_human: bool = False


@dataclass
class EscalationEvent:
    """升级事件记录（审计轨迹）。"""
    level: EscalationLevel = EscalationLevel.MEDIUM
    source: str = ""
    reason: str = ""
    context_snapshot: dict[str, Any] | None = None
    resolution: str = "pending"


class FailureRecovery:
    """
    Harness失败恢复器。

    医疗场景下的失败恢复原则：
    - 宁可说"不确定"，不可给错误诊断
    - 不确定时自动升级到更严谨的推理路径
    - 所有恢复操作必须有审计日志
    - 优雅降级优于静默失败

    Attributes:
        strategy: 默认恢复策略。
        max_retries: 升级前的最大重试次数。
        escalation_threshold: 人工升级前的失败次数。
    """

    def __init__(
        self,
        strategy: RecoveryStrategy | str = RecoveryStrategy.ESCALATE,
        max_retries: int = 2,
        escalation_threshold: int = 3,
    ) -> None:
        if isinstance(strategy, str):
            strategy = RecoveryStrategy(strategy)
        self.strategy = strategy
        self.max_retries = max_retries
        self.escalation_threshold = escalation_threshold
        self._escalation_log: list[EscalationEvent] = []
        self._recovery_log: list[dict[str, Any]] = []
        self._failure_count: int = 0

    def recover(
        self,
        context: dict[str, Any],
        validation: Any,
        reason_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """执行失败恢复。

        Args:
            context: 当前Harness上下文。
            validation: 验证结果（包含失败原因）。
            reason_fn: 推理函数，用于重试（可选）。

        Returns:
            恢复后的推理结果（dict）。
        """
        self._failure_count += 1
        severity = self._assess_severity(validation)

        # 记录审计日志
        self._recovery_log.append({
            "strategy": self.strategy.value,
            "severity": severity.value,
            "issues": getattr(validation, "issues", []),
            "confidence": getattr(validation, "confidence", 0.0),
            "context_keys": list(context.keys()),
        })

        event = EscalationEvent(
            level=severity,
            source="validation",
            reason=getattr(validation, "message", str(getattr(validation, "issues", ["Validation failed"]))),
            context_snapshot=self._safe_context_snapshot(context),
        )

        # CRITICAL → 需要人工
        if severity == EscalationLevel.CRITICAL:
            event.resolution = "escalated_to_human"
            self._escalation_log.append(event)
            return {
                "diagnosis": "无法确定 — 需要人工专家审核",
                "confidence": 0.0,
                "method": "escalate_to_human",
                "issues": getattr(validation, "issues", []),
                "recommendation": "请提供更多信息或联系专科医生",
            }

        # HIGH → 优雅降级
        if severity == EscalationLevel.HIGH:
            event.resolution = "degraded_gracefully"
            self._escalation_log.append(event)
            return self._degrade_gracefully(context, validation)

        # MEDIUM + 可重试
        if severity == EscalationLevel.MEDIUM and self._failure_count <= self.max_retries:
            if reason_fn is not None:
                event.resolution = "retry_attempted"
                self._escalation_log.append(event)
                enhanced_context = {
                    **context,
                    "_recovery": {
                        "original_issues": getattr(validation, "issues", []),
                        "constraint": "请给出鉴别诊断列表，并标注每个诊断的置信度。如果不确定，明确说明。",
                        "attempt": self._failure_count,
                    },
                }
                return reason_fn(enhanced_context, {})

        # 降级到规则引擎
        event.resolution = "accepted_with_warnings"
        self._escalation_log.append(event)
        return self._fallback(context, validation)

    def _assess_severity(self, validation: Any) -> EscalationLevel:
        """评估失败严重程度。"""
        score = getattr(validation, "confidence", 0.5)
        if score < 0.2:
            return EscalationLevel.CRITICAL
        if score < 0.4:
            return EscalationLevel.HIGH
        if score < 0.6:
            return EscalationLevel.MEDIUM
        return EscalationLevel.LOW

    def _degrade_gracefully(self, context: dict[str, Any], validation: Any) -> dict[str, Any]:
        """优雅降级：返回部分结果并标记不确定性。"""
        return {
            "diagnosis": "需要进一步检查（部分结果）",
            "confidence": 0.3,
            "method": "degraded_gracefully",
            "issues": getattr(validation, "issues", []),
            "recommendation": "建议进一步检查或人工会诊",
            "degraded": True,
            "uncertainty": "high",
        }

    def _fallback(self, context: dict[str, Any], validation: Any) -> dict[str, Any]:
        """降级策略：回退到规则引擎。"""
        return {
            "diagnosis": "需要进一步检查",
            "confidence": 0.3,
            "method": "rule_based_fallback",
            "issues": getattr(validation, "issues", []),
            "recommendation": "建议人工会诊",
        }

    def _abort(self, context: dict[str, Any], validation: Any) -> dict[str, Any]:
        """安全中止：明确告知无法完成推理。"""
        return {
            "diagnosis": "无法确定",
            "confidence": 0.0,
            "method": "abort",
            "issues": getattr(validation, "issues", []),
            "recommendation": "请提供更多信息或联系专科医生",
        }

    @staticmethod
    def _safe_context_snapshot(context: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage": context.get("meta", {}).get("specialty", "unknown"),
            "input_keys": list(context.get("patient", {}).keys()),
            "has_history": bool(context.get("history")),
        }

    @property
    def escalation_log(self) -> list[EscalationEvent]:
        return list(self._escalation_log)

    @property
    def recovery_log(self) -> list[dict[str, Any]]:
        return list(self._recovery_log)

    def reset(self) -> None:
        """重置恢复状态。"""
        self._failure_count = 0
