"""
Result Validator — Harness结果验证器。

医疗AI输出验证维度：
1. 格式验证：输出结构是否完整
2. 一致性验证：诊断与症状是否匹配
3. 安全验证：是否包含危险建议
4. 置信度验证：置信度是否在合理范围
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """验证结果。"""
    passed: bool = True
    confidence: float = 1.0
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    retry_count: int = 0


class ResultValidator:
    """
    Harness结果验证器。

    医疗级验证标准：
    - 输出必须包含诊断和置信度
    - 置信度低于阈值时标记为不通过
    - 高风险诊断必须有鉴别诊断列表
    - 禁止输出绝对确定性表述（"肯定"、"100%"等）
    """

    # 高风险关键词 — 需要额外验证
    HIGH_RISK_KEYWORDS = [
        "恶性", "癌症", "肿瘤", "malignant", "cancer", "tumor",
        "急性", "危重", "紧急", "acute", "critical", "emergency",
        "心肌梗死", "脑卒中", "肺栓塞", "myocardial infarction",
    ]

    # 禁止的绝对性表述
    ABSOLUTE_TERMS = [
        "肯定", "一定", "100%", "绝对", "毫无疑问",
        "definitely", "certainly", "100% sure", "absolutely",
    ]

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def validate(
        self,
        result: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        执行多维度验证。

        Args:
            result: Harness推理结果。
            context: 执行上下文（可选）。

        Returns:
            验证结果。
        """
        issues = []
        warnings = []

        # 1. 格式验证
        format_issues = self._validate_format(result)
        issues.extend(format_issues)

        # 2. 置信度验证
        confidence = result.get("confidence", 0.0)
        if confidence < self.threshold:
            issues.append(f"置信度 {confidence:.2f} 低于阈值 {self.threshold}")

        # 3. 安全验证
        safety_issues = self._validate_safety(result)
        issues.extend(safety_issues)

        # 4. 一致性验证
        if context:
            consistency_warnings = self._validate_consistency(result, context)
            warnings.extend(consistency_warnings)

        # 5. 高风险诊断验证
        risk_warnings = self._validate_high_risk(result)
        warnings.extend(risk_warnings)

        passed = len(issues) == 0

        return ValidationResult(
            passed=passed,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
        )

    def _validate_format(self, result: dict[str, Any]) -> list[str]:
        """验证输出格式完整性。"""
        issues = []

        # 必须有诊断字段
        if "diagnosis" not in result and "output" not in result:
            issues.append("输出缺少 'diagnosis' 或 'output' 字段")

        # 必须有置信度
        if "confidence" not in result:
            issues.append("输出缺少 'confidence' 字段")
        elif not isinstance(result.get("confidence"), (int, float)):
            issues.append("'confidence' 必须是数值类型")

        return issues

    def _validate_safety(self, result: dict[str, Any]) -> list[str]:
        """安全验证：检查禁止的绝对性表述。"""
        issues = []
        text = str(result)

        for term in self.ABSOLUTE_TERMS:
            if term in text:
                issues.append(f"包含禁止的绝对性表述: '{term}'")

        return issues

    def _validate_consistency(
        self,
        result: dict[str, Any],
        context: dict[str, Any],
    ) -> list[str]:
        """一致性验证：诊断与患者数据是否匹配。"""
        warnings = []

        patient = context.get("patient", {})
        diagnosis = result.get("diagnosis", "")

        # 年龄-疾病一致性检查
        age = patient.get("age")
        if age is not None and age < 18:
            adult_diseases = ["冠心病", "帕金森", "coronary", "parkinson"]
            if any(d in str(diagnosis).lower() for d in adult_diseases):
                warnings.append(f"诊断 '{diagnosis}' 在 {age} 岁患者中不常见")

        return warnings

    def _validate_high_risk(self, result: dict[str, Any]) -> list[str]:
        """高风险诊断验证。"""
        warnings = []
        text = str(result).lower()

        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in text:
                if "differential" not in text and "鉴别" not in text:
                    warnings.append(
                        f"高风险诊断 '{keyword}' 缺少鉴别诊断列表"
                    )
                break

        return warnings
