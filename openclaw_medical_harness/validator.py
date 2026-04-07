"""
Result Validator — Harness结果验证器。

医疗AI输出验证维度：
1. 格式验证：输出结构是否完整
2. 一致性验证：诊断与症状是否匹配
3. 安全验证：是否包含危险建议
4. 置信度验证：置信度是否在合理范围
5. 领域验证：输出是否符合医疗领域标准

验证层级：
  1. Structural — 输出具有必需字段和正确类型
  2. Consistency — 内部逻辑不自相矛盾
  3. Domain — 输出符合医疗领域标准
  4. Safety — 无危险建议（未经适当警告）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    """验证发现的严重程度。"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationFinding:
    """单个验证发现。"""
    severity: ValidationSeverity = ValidationSeverity.INFO
    field: str = ""
    message: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    """验证结果。

    Attributes:
        passed: 验证是否通过（无错误或严重问题）。
        confidence: 质量分数，0.0（最差）到 1.0（最好）。
        issues: 问题列表（兼容旧API）。
        warnings: 警告列表。
        findings: 详细验证发现列表。
        message: 摘要消息。
        retry_count: 重试次数。
        metadata: 额外验证元数据。
    """
    passed: bool = True
    confidence: float = 1.0
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    findings: list[ValidationFinding] = field(default_factory=list)
    message: str = "Validation passed"
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


# 高风险关键词 — 需要额外验证
HIGH_RISK_KEYWORDS: list[str] = [
    "恶性", "癌症", "肿瘤", "malignant", "cancer", "tumor",
    "急性", "危重", "紧急", "acute", "critical", "emergency",
    "心肌梗死", "脑卒中", "肺栓塞", "myocardial infarction",
]

# 禁止的绝对性表述
ABSOLUTE_TERMS: list[str] = [
    "肯定", "一定", "100%", "绝对", "毫无疑问",
    "definitely", "certainly", "100% sure", "absolutely",
]

# 已知危险医疗模式
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"no need for (further )?testing", "跳过检测的建议需要审核"),
    (r"definitely (not )?cancer", "没有活检的绝对癌症声明是危险的"),
    (r"stop all medications", "在无监督下停用所有药物是不安全的"),
    (r"guaranteed (cure|recovery)", "无法保证任何医疗结果"),
]

# 领域特定必需字段
DOMAIN_REQUIRED_FIELDS: dict[str, list[str]] = {
    "diagnosis": ["diagnosis", "confidence"],
    "drug_discovery": ["target", "candidates"],
    "health_management": ["assessment", "plan"],
}


class ResultValidator:
    """
    Harness结果验证器。

    医疗级验证标准：
    - 输出必须包含诊断和置信度
    - 置信度低于阈值时标记为不通过
    - 高风险诊断必须有鉴别诊断列表
    - 禁止输出绝对确定性表述（"肯定"、"100%"等）
    - 危险模式检测

    Attributes:
        threshold: 置信度阈值。
        strict_mode: 如果为True，警告也导致验证失败。
    """

    def __init__(
        self,
        threshold: float = 0.7,
        strict_mode: bool = False,
        domain_rules: dict[str, Any] | None = None,
    ) -> None:
        self.threshold = threshold
        self.strict_mode = strict_mode
        self.domain_rules = domain_rules or {}

    def validate(
        self,
        result: Any,
        context: dict[str, Any] | None = None,
        domain: str = "general",
    ) -> ValidationResult:
        """执行多维度验证。

        Args:
            result: Harness推理结果。
            context: 执行上下文（可选）。
            domain: 医疗领域（用于领域特定规则）。

        Returns:
            验证结果。
        """
        # 规范化输出为dict
        result_dict = self._normalize_output(result)

        issues: list[str] = []
        warnings: list[str] = []
        findings: list[ValidationFinding] = []

        # 1. 格式验证
        format_issues = self._validate_format(result_dict, domain)
        issues.extend(format_issues)

        # 2. 置信度验证
        confidence = result_dict.get("confidence", 0.0)
        if isinstance(confidence, (int, float)) and confidence < self.threshold:
            msg = f"置信度 {confidence:.2f} 低于阈值 {self.threshold}"
            issues.append(msg)
            findings.append(ValidationFinding(
                severity=ValidationSeverity.ERROR,
                field="confidence",
                message=msg,
            ))

        # 3. 置信度范围验证
        if isinstance(confidence, (int, float)) and not 0.0 <= confidence <= 1.0:
            msg = f"置信度 {confidence} 超出有效范围 [0, 1]"
            issues.append(msg)
            findings.append(ValidationFinding(
                severity=ValidationSeverity.ERROR,
                field="confidence",
                message=msg,
            ))

        # 4. 安全验证
        safety_issues = self._validate_safety(result_dict)
        issues.extend(safety_issues)

        # 5. 一致性验证
        if context:
            consistency_warnings = self._validate_consistency(result_dict, context)
            warnings.extend(consistency_warnings)

        # 6. 高风险诊断验证
        risk_warnings = self._validate_high_risk(result_dict)
        warnings.extend(risk_warnings)

        # 7. 领域验证
        domain_findings = self._validate_domain(result_dict, domain)
        findings.extend(domain_findings)

        passed = len(issues) == 0
        if self.strict_mode and warnings:
            passed = False

        score = self._calculate_score(findings, issues)

        if passed:
            message = f"Validation passed (score: {score:.2f})"
        else:
            error_count = len(issues)
            message = f"Validation failed — {error_count} issue(s)"

        return ValidationResult(
            passed=passed,
            confidence=confidence if isinstance(confidence, (int, float)) else 0.0,
            issues=issues,
            warnings=warnings,
            findings=findings,
            message=message,
            metadata={"domain": domain, "strict_mode": self.strict_mode},
        )

    def _normalize_output(self, output: Any) -> dict[str, Any]:
        """规范化输出为字典。"""
        if isinstance(output, dict):
            return output
        if isinstance(output, str):
            return {"raw_output": output}
        if hasattr(output, "__dict__"):
            return {k: v for k, v in output.__dict__.items() if not k.startswith("_")}
        if hasattr(output, "output"):
            return self._normalize_output(output.output)
        return {"raw_output": str(output)}

    def _validate_format(self, result: dict[str, Any], domain: str) -> list[str]:
        """验证输出格式完整性。"""
        issues = []
        if not result:
            issues.append("输出为空")
            return issues

        # 必须有诊断字段
        if "diagnosis" not in result and "output" not in result and "raw_output" not in result:
            issues.append("输出缺少 'diagnosis' 或 'output' 字段")

        # 必须有置信度
        if "confidence" not in result:
            issues.append("输出缺少 'confidence' 字段")
        elif not isinstance(result.get("confidence"), (int, float)):
            issues.append("'confidence' 必须是数值类型")

        # 领域特定必需字段
        required = DOMAIN_REQUIRED_FIELDS.get(domain, [])
        for field_name in required:
            if field_name not in result:
                issues.append(f"缺少领域必需字段: {field_name}")

        return issues

    def _validate_safety(self, result: dict[str, Any]) -> list[str]:
        """安全验证：检查禁止的绝对性表述和危险模式。"""
        issues = []
        text = str(result)

        # 检查绝对性表述
        for term in ABSOLUTE_TERMS:
            if term in text:
                issues.append(f"包含禁止的绝对性表述: '{term}'")

        # 检查危险模式
        for pattern, message in DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"检测到危险模式: {message}")

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
        if age is not None and isinstance(age, (int, float)) and age < 18:
            adult_diseases = ["冠心病", "帕金森", "coronary", "parkinson"]
            if any(d in str(diagnosis).lower() for d in adult_diseases):
                warnings.append(f"诊断 '{diagnosis}' 在 {age} 岁患者中不常见")

        return warnings

    def _validate_high_risk(self, result: dict[str, Any]) -> list[str]:
        """高风险诊断验证。"""
        warnings = []
        text = str(result).lower()

        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in text:
                if "differential" not in text and "鉴别" not in text:
                    warnings.append(f"高风险诊断 '{keyword}' 缺少鉴别诊断列表")
                break

        return warnings

    def _validate_domain(
        self,
        output: dict[str, Any],
        domain: str,
    ) -> list[ValidationFinding]:
        """领域特定验证。"""
        findings = []
        if domain == "diagnosis":
            differential = output.get("differential", output.get("differential_list", []))
            if isinstance(differential, list) and len(differential) < 2:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.WARNING,
                    field="differential",
                    message="鉴别诊断列表少于2个替代方案",
                ))
        return findings

    def _calculate_score(
        self,
        findings: list[ValidationFinding],
        issues: list[str],
    ) -> float:
        """计算质量分数。"""
        if not findings and not issues:
            return 1.0
        penalties = {
            ValidationSeverity.INFO: 0.0,
            ValidationSeverity.WARNING: 0.1,
            ValidationSeverity.ERROR: 0.25,
            ValidationSeverity.CRITICAL: 0.5,
        }
        total = sum(penalties.get(f.severity, 0.0) for f in findings)
        total += len(issues) * 0.15  # 旧式issues也扣分
        return max(0.0, 1.0 - total)
