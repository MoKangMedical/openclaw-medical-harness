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
                "evidence": result.output.get("evidence", {}),
                "harness_name": result.harness_name,
                "execution_time_ms": result.execution_time_ms,
            }
        return {
            "assessment": {},
            "plan": {},
            "adherence_metrics": {},
            "effectiveness": {},
            "confidence": result.confidence,
            "evidence": {},
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
        """健康管理推理：结合数据+模型推理。"""
        patient = context.get("patient", {})

        # 构建prompt
        prompt = self._build_health_prompt(patient, tool_results, context)

        # 调用模型
        model_result = self._call_model(prompt)

        # 模型返回了结构化结果
        if model_result.get("mode") != "fallback" and (
            "assessment" in model_result or "plan" in model_result
        ):
            return {
                "assessment": model_result.get("assessment", {}),
                "plan": model_result.get("plan", {}),
                "adherence": model_result.get("adherence", model_result.get("adherence_metrics", {})),
                "effectiveness": model_result.get("effectiveness", {}),
                "confidence": model_result.get("confidence", 0.6),
                "evidence": {"source": "model", "provider": self.model_provider},
            }

        # 回退
        age = patient.get("age", "未知")
        return {
            "assessment": {
                "overall_risk": "需进一步评估",
                "patient_age": age,
                "note": "请配置MIMO_API_KEY以获取个性化方案",
            },
            "plan": {"note": "需模型推理"},
            "adherence": {"tracking_metrics": ["待定"]},
            "effectiveness": {"evaluation_points": ["待定"]},
            "confidence": 0.3,
            "evidence": {"source": "fallback"},
        }

    def _build_health_prompt(
        self,
        patient: dict[str, Any],
        tool_results: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """构建健康管理推理prompt。"""
        age = patient.get("age", "未知")
        goal = patient.get("health_goal", "未指定")
        conditions = patient.get("conditions", [])
        lab = patient.get("lab_results", {})
        wearable = patient.get("wearable_data", {})

        prompt = f"""你是一位{self.health_domain}方向的健康管理专家。请根据以下信息制定个性化健康管理方案。

## 用户信息
- 年龄: {age}
- 健康目标: {goal}
"""
        if conditions:
            cond_str = ", ".join(conditions) if isinstance(conditions, list) else str(conditions)
            prompt += f"- 现有疾病/状况: {cond_str}\n"
        if lab:
            prompt += f"- 实验室结果: {lab}\n"
        if wearable:
            prompt += f"- 可穿戴数据: {wearable}\n"

        # 注入工具结果
        if tool_results:
            prompt += "\n## 文献参考\n"
            for tool_name, output in tool_results.items():
                if isinstance(output, dict) and "error" not in output:
                    articles = output.get("articles", [])
                    for a in articles[:3]:
                        prompt += f"- {a.get('title', '')}\n"

        prompt += """
## 输出要求
请以严格的JSON格式返回：
{"assessment": {"overall_risk": "low/moderate/high", "key_findings": ["发现1", "发现2"]}, "plan": {"diet": "", "exercise": "", "medication": "", "mental_health": ""}, "adherence": {"tracking_metrics": ["指标1"], "check_interval_days": 7}, "effectiveness": {"evaluation_points": ["时间点1"], "success_criteria": ""}, "confidence": 0.7}

要求：
- 方案要个性化，不要泛泛而谈
- 饮食方案要具体（如每日热量、宏量素比例）
- 运动方案要可执行（频率、强度、时长）
- 依从性指标要可量化
"""
        return prompt

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
