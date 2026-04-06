"""
Drug Discovery Harness — 药物发现Harness。

Harness流程：
靶点验证 → 虚拟筛选 → ADMET预测 → 先导优化

集成工具：
- ChEMBL：药物活性数据
- OpenTargets：靶点-疾病关联
- RDKit：分子计算
- PubMed：文献支撑
"""

from __future__ import annotations

from typing import Any, Optional

from .base import BaseHarness, HarnessConfig
from .recovery import RecoveryStrategy


class DrugDiscoveryHarness(BaseHarness):
    """
    药物发现Harness。

    将药物发现流程结构化为Harness：
    1. 靶点验证 → 确认靶点与疾病的关联
    2. 虚拟筛选 → 从化合物库中筛选候选分子
    3. ADMET预测 → 吸收/分布/代谢/排泄/毒性
    4. 先导优化 → 基于SAR的分子优化建议
    """

    def __init__(
        self,
        model_provider: str = "mimo",
        target_disease: str = "",
        config: Optional[HarnessConfig] = None,
    ):
        if config is None:
            config = HarnessConfig(
                name="drug_discovery",
                model_provider=model_provider,
                tools=["chembl", "opentargets", "pubmed", "rdkit"],
                recovery_strategy=RecoveryStrategy.FALLBACK,
                validation_threshold=0.6,
            )
        super().__init__(config=config)
        self.target_disease = target_disease

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行药物发现Harness流程。"""
        result = super().execute(input_data)

        return {
            "target": result.output.get("target", ""),
            "candidates": result.output.get("candidates", []),
            "admet_profile": result.output.get("admet_profile", {}),
            "optimization_suggestions": result.output.get("optimization", []),
            "confidence": result.confidence,
            "harness_name": result.harness_name,
            "execution_time_ms": result.execution_time_ms,
        }

    def _build_prompt(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        disease = context.get("patient", {}).get("disease", self.target_disease)

        prompt = f"""你是一位AI药物发现专家。请针对以下疾病进行候选药物发现分析。

## 目标疾病
{disease}

## 数据源结果
"""
        for tool_name, output in tool_results.items():
            if "error" not in output:
                prompt += f"\n### {tool_name}\n{output}\n"

        prompt += """
## 请按以下格式输出
1. 推荐靶点（含验证依据）
2. 候选化合物列表（至少5个）
3. ADMET预测概要
4. 先导优化建议
5. 文献支撑摘要
"""
        return prompt

    def _reason(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> dict[str, Any]:
        """药物发现推理。"""
        return {
            "target": "需要通过OpenTargets/ChEMBL查询",
            "candidates": [
                {"name": "Candidate-1", "source": "ChEMBL", "activity": "IC50 < 100nM"},
                {"name": "Candidate-2", "source": "Virtual Screening", "dock_score": -8.5},
            ],
            "admet_profile": {
                "absorption": "High",
                "distribution": "Moderate",
                "metabolism": "CYP3A4 substrate",
                "excretion": "Renal",
                "toxicity": "Low risk",
            },
            "optimization": [
                "改善水溶性：引入极性基团",
                "降低CYP抑制：调整芳香环取代",
            ],
            "confidence": 0.65,
        }

    def _metrics(
        self,
        context: dict[str, Any] | None = None,
        tool_results: dict[str, Any] | None = None,
        elapsed_ms: float = 0.0,
    ) -> dict[str, Any]:
        return {
            "harness_type": "drug_discovery",
            "target_disease": self.target_disease,
            "tools_used": list((tool_results or {}).keys()),
            "elapsed_ms": elapsed_ms,
        }
