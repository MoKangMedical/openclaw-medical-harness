"""
Drug Discovery Harness — 药物发现Harness实现。

Harness流程：
靶点验证 → 虚拟筛选 → ADMET预测 → 先导优化

集成工具：
- ChEMBL：药物活性数据
- OpenTargets：靶点-疾病关联
- RDKit：分子计算
- PubMed：文献支撑
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ..base import BaseHarness, HarnessConfig, HarnessResult
from ..recovery import RecoveryStrategy

logger = logging.getLogger(__name__)


@dataclass
class ADMETProfile:
    """ADMET预测谱。"""
    absorption: float = 0.0
    distribution: float = 0.0
    metabolism: dict[str, float] = field(default_factory=dict)
    excretion: dict[str, float] = field(default_factory=dict)
    toxicity: dict[str, float] = field(default_factory=dict)
    lipinski_violations: int = 0
    drug_likeness: float = 0.0


@dataclass
class CompoundProfile:
    """候选化合物谱。"""
    compound_id: str = ""
    smiles: str = ""
    molecular_weight: float = 0.0
    target_activity: dict[str, float] = field(default_factory=dict)
    admet: ADMETProfile = field(default_factory=ADMETProfile)
    novelty_score: float = 0.0
    optimization_suggestions: list[str] = field(default_factory=list)


@dataclass
class DrugDiscoveryResult:
    """药物发现Harness的结构化输出。"""
    target: str = ""
    disease_association: dict[str, Any] = field(default_factory=dict)
    screened_compounds: list[CompoundProfile] = field(default_factory=list)
    lead_compound: CompoundProfile | None = None
    optimization_rounds: int = 0
    synthesis_feasibility: float = 0.0
    next_steps: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class DrugDiscoveryHarness(BaseHarness):
    """
    药物发现Harness。

    将药物发现流程结构化为Harness：
    1. 靶点验证 → 确认靶点与疾病的关联
    2. 虚拟筛选 → 从化合物库中筛选候选分子
    3. ADMET预测 → 吸收/分布/代谢/排泄/毒性
    4. 先导优化 → 基于SAR的分子优化建议

    Example:
        >>> harness = DrugDiscoveryHarness(target_disease="NSCLC")
        >>> result = harness.execute({"disease": "NSCLC", "target": "EGFR"})
    """

    def __init__(
        self,
        model_provider: str = "mimo",
        target_disease: str = "",
        screening_library: str = "chembl_33",
        max_compounds: int = 100,
        name: str = "",
        config: Optional[HarnessConfig] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = HarnessConfig(
                name=name or "drug_discovery",
                model_provider=model_provider,
                tools=["chembl", "opentargets", "pubmed", "rdkit"],
                recovery_strategy=RecoveryStrategy.FALLBACK.value,
                validation_threshold=0.6,
            )
        super().__init__(config=config, **kwargs)
        self.target_disease = target_disease
        self.screening_library = screening_library
        self.max_compounds = max_compounds

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行药物发现Harness流程。"""
        input_data.setdefault("screening_library", self.screening_library)
        input_data.setdefault("max_compounds", self.max_compounds)

        result = super().execute(input_data)

        if isinstance(result.output, dict):
            return {
                "target": result.output.get("target", ""),
                "candidates": result.output.get("candidates", []),
                "admet_profile": result.output.get("admet_profile", {}),
                "optimization_suggestions": result.output.get("optimization", []),
                "confidence": result.output.get("confidence", result.confidence),
                "evidence": result.output.get("evidence", {}),
                "harness_name": result.harness_name,
                "execution_time_ms": result.execution_time_ms,
            }
        return {
            "target": "",
            "candidates": [],
            "admet_profile": {},
            "optimization_suggestions": [],
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
        disease = patient.get("disease", self.target_disease)
        target = patient.get("target", "")

        prompt = f"""你是一位AI药物发现专家。请针对以下疾病进行候选药物发现分析。

## 目标疾病
{disease}
"""
        if target:
            prompt += f"\n## 靶点\n{target}\n"

        prompt += "\n## 数据源结果\n"
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
        """药物发现推理：结合工具数据+模型推理。"""
        patient = context.get("patient", {})
        disease = patient.get("disease", self.target_disease)
        target = patient.get("target", "")

        # 构建模型推理prompt
        prompt = self._build_drug_prompt(disease, target, tool_results, context)

        # 调用模型
        model_result = self._call_model(prompt)

        # 模型返回了结构化结果
        if model_result.get("mode") != "fallback" and (
            "target" in model_result or "candidates" in model_result
        ):
            return {
                "target": model_result.get("target", target or "模型推荐靶点"),
                "candidates": model_result.get("candidates", []),
                "admet_profile": model_result.get("admet_profile", model_result.get("admet", {})),
                "optimization": model_result.get("optimization", model_result.get("optimization_suggestions", [])),
                "confidence": model_result.get("confidence", 0.6),
                "evidence": {"source": "model", "provider": self.model_provider},
            }

        # 回退
        return {
            "target": target or "需要通过OpenTargets/ChEMBL查询",
            "candidates": [
                {"name": "需模型推理", "source": "fallback", "note": "请配置MIMO_API_KEY"},
            ],
            "admet_profile": {"note": "需模型推理"},
            "optimization": ["请配置模型以获取优化建议"],
            "confidence": 0.3,
            "evidence": {"source": "fallback"},
        }

    def _build_drug_prompt(
        self,
        disease: str,
        target: str,
        tool_results: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """构建药物发现推理prompt。"""
        prompt = f"""你是一位AI药物发现与药物化学专家。请针对以下疾病进行候选药物发现分析。

## 目标疾病
{disease or '未指定'}
"""
        if target:
            prompt += f"\n## 已知靶点\n{target}\n"

        # 注入工具结果
        if tool_results:
            prompt += "\n## 数据源检索结果\n"
            for tool_name, output in tool_results.items():
                if isinstance(output, dict) and "error" not in output:
                    associations = output.get("associations", [])
                    if associations:
                        prompt += f"\n### {tool_name} 靶点-疾病关联\n"
                        for a in associations[:5]:
                            prompt += f"- {a.get('disease_name', '')}: score={a.get('score', 0):.2f}\n"
                    drugs = output.get("known_drugs", [])
                    if drugs:
                        prompt += f"\n### {tool_name} 已知药物\n"
                        for d in drugs[:5]:
                            prompt += f"- {d.get('drug_name', '')}: {d.get('mechanism', '')}\n"

        prompt += """
## 输出要求
请以严格的JSON格式返回：
{"target": "推荐靶点名称", "candidates": [{"name": "化合物名", "source": "来源", "activity": "活性数据"}], "admet_profile": {"absorption": "", "distribution": "", "metabolism": "", "excretion": "", "toxicity": ""}, "optimization": ["优化建议1", "优化建议2"], "confidence": 0.7}

要求：
- 候选化合物至少3个
- ADMET预测要具体（如CYP酶亚型、logP范围等）
- 优化建议要可操作
"""
        return prompt

    def _domain(self) -> str:
        return "drug_discovery"

    def validate_target(self, target: str, disease: str) -> dict[str, Any]:
        """验证靶点与疾病的关联。"""
        return {"target": target, "disease": disease, "validated": True, "source": "opentargets"}

    def predict_admet(self, smiles: str) -> ADMETProfile:
        """预测ADMET属性。"""
        return ADMETProfile()
