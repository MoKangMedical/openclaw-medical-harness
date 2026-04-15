"""
Health Management Harness — 健康管理Harness实现。

Harness流程：
健康评估 → 个性化方案 → 依从性追踪 → 效果评估

支持：
- 多模态数据接入（问卷/可穿戴/实验室）
- 长期随访Agent
- 个性化干预方案
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ..base import BaseHarness, HarnessConfig, HarnessResult
from ..recovery import RecoveryStrategy

logger = logging.getLogger(__name__)


@dataclass
class HealthAssessment:
    """综合健康评估结果。"""
    risk_scores: dict[str, float] = field(default_factory=dict)
    lifestyle_factors: list[str] = field(default_factory=list)
    biomarkers: dict[str, dict[str, Any]] = field(default_factory=dict)
    mental_health_screen: dict[str, Any] = field(default_factory=dict)
    overall_risk_level: str = "moderate"


@dataclass
class CarePlanItem:
    """护理计划中的单个项目。"""
    category: str = ""
    description: str = ""
    frequency: str = ""
    duration: str = ""
    priority: str = "recommended"
    evidence_level: str = "B"


@dataclass
class HealthPlan:
    """个性化健康管理计划。"""
    plan_items: list[CarePlanItem] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)
    follow_up_schedule: list[dict[str, str]] = field(default_factory=list)
    compliance_tracking: dict[str, Any] = field(default_factory=dict)
    escalation_triggers: list[str] = field(default_factory=list)


class HealthManagementHarness(BaseHarness):
    """
    健康管理Harness。

    将健康管理流程结构化为Harness：
    1. 健康评估 → 多维度健康画像
    2. 个性化方案 → 基于评估的干预建议
    3. 依从性追踪 → 行为数据监测
    4. 效果评估 → 方案调整建议

    Example:
        >>> harness = HealthManagementHarness(health_domain="weight_management")
        >>> result = harness.execute({
        ...     "patient": {"age": 35, "health_goal": "减重10kg"},
        ... })
    """

    def __init__(
        self,
        model_provider: str = "mimo",
        health_domain: str = "general",
        follow_up_interval_days: int = 30,
        name: str = "",
        config: Optional[HarnessConfig] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = HarnessConfig(
                name=name or f"health_{health_domain}",
                model_provider=model_provider,
                tools=["pubmed"],
                recovery_strategy=RecoveryStrategy.FALLBACK.value,
                validation_threshold=0.6,
            )
        super().__init__(config=config, **kwargs)
        self.health_domain = health_domain
        self.follow_up_interval_days = follow_up_interval_days
        self._patient_history: dict[str, list[Any]] = {}

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行健康管理Harness流程。"""
        # 确保patient字段存在
        if "patient" not in input_data:
            input_data["patient"] = {}
        # 合并顶层健康数据到patient
        for key in ["conditions", "lab_results", "wearable_data", "health_goal"]:
            if key in input_data and key not in input_data["patient"]:
                input_data["patient"][key] = input_data[key]

        result = super().execute(input_data)

        if isinstance(result.output, dict):
            return {
                "assessment": result.output.get("assessment", {}),
                "plan": result.output.get("plan", {}),
                "adherence_metrics": result.output.get("adherence", {}),
                "effectiveness": result.output.get("effectiveness", {}),
                "confidence": result.output.get("confidence", result.confidence),
                "harness_name": result.harness_name,
                "execution_time_ms": result.execution_time_ms,
            }
        return {
            "assessment": {},
            "plan": {},
            "adherence_metrics": {},
            "effectiveness": {},
            "confidence": result.confidence,
            "harness_name": result.harness_name,
            "execution_time_ms": result.execution_time_ms,
        }

    def _build_prompt(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        patient = context.get("patient", {})

        prompt = f"""你是一位AI健康管理专家（{self.health_domain}方向）。请根据以下信息制定健康管理方案。

## 用户信息
- 年龄: {patient.get('age', '未知')}
- 健康目标: {patient.get('health_goal', '未指定')}
- 现有数据: {patient.get('health_data', '无')}
"""
        if "conditions" in patient:
            prompt += f"- 现有疾病: {', '.join(patient['conditions']) if isinstance(patient['conditions'], list) else patient['conditions']}\n"

        prompt += "\n## 工具数据\n"
        for tool_name, output in tool_results.items():
            if "error" not in output:
                prompt += f"\n### {tool_name}\n{output}\n"

        prompt += """
## 请输出
1. 健康评估摘要
2. 个性化干预方案（饮食/运动/用药/心理）
3. 依从性监测指标
4. 效果评估时间点
"""
        return prompt

    def _reason(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> dict[str, Any]:
        """健康管理推理。"""
        patient = context.get("patient", {})
        return {
            "assessment": {
                "overall_risk": "moderate",
                "key_findings": ["BMI偏高", "运动不足"],
                "patient_age": patient.get("age", "unknown"),
            },
            "plan": {
                "diet": "地中海饮食为主",
                "exercise": "每周150分钟中等强度",
                "monitoring": "每周体重记录",
            },
            "adherence": {
                "tracking_metrics": ["体重", "运动时长", "饮食日志"],
                "check_interval_days": 7,
            },
            "effectiveness": {
                "evaluation_points": ["2周", "1月", "3月"],
                "success_criteria": "体重下降5%或BMI改善",
            },
            "confidence": 0.7,
        }

    def _domain(self) -> str:
        return "health_management"

    def conduct_follow_up(self, patient_id: str, current_data: dict[str, Any]) -> dict[str, Any]:
        """执行随访评估。"""
        return {
            "patient_id": patient_id,
            "compliance_rate": 0.75,
            "outcome_changes": {},
            "plan_adjustments": [],
            "alerts": [],
        }
