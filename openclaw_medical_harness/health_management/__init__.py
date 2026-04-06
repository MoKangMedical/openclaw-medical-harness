"""
Health Management Harness — 健康管理Harness。

Harness流程：
健康评估 → 个性化方案 → 依从性追踪 → 效果评估

支持：
- 多模态数据接入（问卷/可穿戴/实验室）
- 长期随访Agent
- 个性化干预方案
"""

from __future__ import annotations

from typing import Any, Optional

from .base import BaseHarness, HarnessConfig
from .recovery import RecoveryStrategy


class HealthManagementHarness(BaseHarness):
    """
    健康管理Harness。

    将健康管理流程结构化为Harness：
    1. 健康评估 → 多维度健康画像
    2. 个性化方案 → 基于评估的干预建议
    3. 依从性追踪 → 行为数据监测
    4. 效果评估 → 方案调整建议
    """

    def __init__(
        self,
        model_provider: str = "mimo",
        health_domain: str = "general",
        config: Optional[HarnessConfig] = None,
    ):
        if config is None:
            config = HarnessConfig(
                name=f"health_{health_domain}",
                model_provider=model_provider,
                tools=["pubmed"],
                recovery_strategy=RecoveryStrategy.FALLBACK,
                validation_threshold=0.6,
            )
        super().__init__(config=config)
        self.health_domain = health_domain

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行健康管理Harness流程。"""
        result = super().execute(input_data)

        return {
            "assessment": result.output.get("assessment", {}),
            "plan": result.output.get("plan", {}),
            "adherence_metrics": result.output.get("adherence", {}),
            "effectiveness": result.output.get("effectiveness", {}),
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

## 工具数据
"""
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
        return {
            "assessment": {
                "overall_risk": "moderate",
                "key_findings": ["BMI偏高", "运动不足"],
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

    def _metrics(
        self,
        context: dict[str, Any] | None = None,
        tool_results: dict[str, Any] | None = None,
        elapsed_ms: float = 0.0,
    ) -> dict[str, Any]:
        return {
            "harness_type": "health_management",
            "domain": self.health_domain,
            "tools_used": list((tool_results or {}).keys()),
            "elapsed_ms": elapsed_ms,
        }
