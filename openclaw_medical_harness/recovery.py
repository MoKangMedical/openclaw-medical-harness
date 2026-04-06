"""
Failure Recovery — Harness失败恢复机制。

医疗AI中的失败恢复策略：
1. ESCALATE: 不确定时升级到更高级别的推理（如多学科会诊）
2. RETRY: 换模型/换prompt重试
3. FALLBACK: 降级到规则引擎
4. ABORT: 安全中止，返回"需要人工介入"
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional

from .validator import ValidationResult


class RecoveryStrategy(Enum):
    """恢复策略枚举。"""
    ESCALATE = "escalate"   # 升级推理
    RETRY = "retry"         # 重试
    FALLBACK = "fallback"   # 降级
    ABORT = "abort"         # 安全中止


class FailureRecovery:
    """
    Harness失败恢复器。

    医疗场景下的失败恢复原则：
    - 宁可说"不确定"，不可给错误诊断
    - 不确定时自动升级到更严谨的推理路径
    - 所有恢复操作必须有审计日志
    """

    def __init__(self, strategy: RecoveryStrategy = RecoveryStrategy.ESCALATE):
        self.strategy = strategy
        self._recovery_log: list[dict[str, Any]] = []

    def recover(
        self,
        context: dict[str, Any],
        validation: ValidationResult,
        reason_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any]:
        """
        执行失败恢复。

        Args:
            context: 当前上下文。
            validation: 验证结果（包含失败原因）。
            reason_fn: 推理函数，用于重试。

        Returns:
            恢复后的推理结果。
        """
        self._log_recovery_start(context, validation)

        if self.strategy == RecoveryStrategy.ESCALATE:
            return self._escalate(context, validation, reason_fn)
        elif self.strategy == RecoveryStrategy.RETRY:
            return self._retry(context, validation, reason_fn)
        elif self.strategy == RecoveryStrategy.FALLBACK:
            return self._fallback(context, validation)
        else:
            return self._abort(context, validation)

    def _escalate(
        self,
        context: dict[str, Any],
        validation: ValidationResult,
        reason_fn: Callable,
    ) -> dict[str, Any]:
        """
        升级策略：添加更多约束后重试。

        医疗场景：
        - 添加"请给出鉴别诊断列表"约束
        - 添加"如果不确定，请明确说明"约束
        - 添加更多工具输出作为参考
        """
        enhanced_context = {
            **context,
            "_recovery": {
                "original_issues": validation.issues,
                "constraint": "请给出鉴别诊断列表，并标注每个诊断的置信度。如果不确定，明确说明。",
                "escalation_level": "differential_diagnosis",
            },
        }
        return reason_fn(enhanced_context, {})

    def _retry(
        self,
        context: dict[str, Any],
        validation: ValidationResult,
        reason_fn: Callable,
    ) -> dict[str, Any]:
        """重试策略：使用相同输入但不同参数重试。"""
        retry_context = {
            **context,
            "_retry": {"attempt": validation.retry_count + 1},
        }
        return reason_fn(retry_context, {})

    def _fallback(
        self,
        context: dict[str, Any],
        validation: ValidationResult,
    ) -> dict[str, Any]:
        """
        降级策略：回退到规则引擎。

        医疗场景：使用临床指南的决策树规则。
        """
        return {
            "diagnosis": "需要进一步检查",
            "confidence": 0.3,
            "method": "rule_based_fallback",
            "issues": validation.issues,
            "recommendation": "建议人工会诊",
        }

    def _abort(
        self,
        context: dict[str, Any],
        validation: ValidationResult,
    ) -> dict[str, Any]:
        """安全中止：明确告知无法完成推理。"""
        return {
            "diagnosis": "无法确定",
            "confidence": 0.0,
            "method": "abort",
            "issues": validation.issues,
            "recommendation": "请提供更多信息或联系专科医生",
        }

    def _log_recovery_start(
        self,
        context: dict[str, Any],
        validation: ValidationResult,
    ) -> None:
        """记录恢复操作的审计日志。"""
        self._recovery_log.append({
            "strategy": self.strategy.value,
            "issues": validation.issues,
            "confidence": validation.confidence,
            "context_keys": list(context.keys()),
        })

    @property
    def recovery_log(self) -> list[dict[str, Any]]:
        return self._recovery_log.copy()
