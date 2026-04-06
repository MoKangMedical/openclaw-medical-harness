"""
Diagnosis Harness — 诊断Harness。

Harness流程：
症状输入 → 分层鉴别 → 检查策略 → 确诊路径

支持：
- 罕见病专项诊断（MG/SMA/DMD/ALS/PKU等）
- 多学科会诊编排
- 临床指南约束
"""

from __future__ import annotations

from typing import Any, Optional

from .base import BaseHarness, HarnessConfig
from .recovery import RecoveryStrategy


# 罕见病知识库（精简版，完整版通过MCP加载）
RARE_DISEASE_KB = {
    "MG": {
        "name": "重症肌无力 / Myasthenia Gravis",
        "key_symptoms": ["ptosis", "diplopia", "fatigable weakness", "bilateral ptosis"],
        "diagnostic_tests": ["AChR antibody", "MuSK antibody", "EMG", "CT chest (thymoma)"],
        "differential": ["Lambert-Eaton", "botulism", "CPEO", "thyroid eye disease"],
    },
    "SMA": {
        "name": "脊髓性肌萎缩症 / Spinal Muscular Atrophy",
        "key_symptoms": ["muscle weakness", "hypotonia", "areflexia", "fasciculations"],
        "diagnostic_tests": ["SMN1 gene test", "SMN2 copy number", "EMG/NCS", "CK"],
        "differential": ["DMD", "ALS", "Pompe disease", "CIDP"],
    },
    "DMD": {
        "name": "杜氏肌营养不良 / Duchenne Muscular Dystrophy",
        "key_symptoms": ["progressive weakness", "calf pseudohypertrophy", "Gowers sign"],
        "diagnostic_tests": ["DMD gene test", "CK level", "muscle biopsy", "EMG"],
        "differential": ["Becker MD", "SMA", "LGMD", "inflammatory myopathy"],
    },
    "ALS": {
        "name": "肌萎缩侧索硬化 / Amyotrophic Lateral Sclerosis",
        "key_symptoms": ["UMN + LMN signs", "progressive weakness", "dysarthria", "dysphagia"],
        "diagnostic_tests": ["EMG/NCS", "MRI brain/spine", "CK", "genetic testing"],
        "differential": ["Kennedy disease", "MMN", "SMA", "cervical myelopathy"],
    },
}


class DiagnosisHarness(BaseHarness):
    """
    诊断Harness。

    将诊断推理过程结构化为Harness流程：
    1. 症状解析 → 结构化症状列表
    2. 分层鉴别 → 候选诊断排序
    3. 检查策略 → 最优检查路径
    4. 确诊路径 → 诊断结论 + 下一步
    """

    def __init__(
        self,
        model_provider: str = "mimo",
        specialty: str = "neurology",
        knowledge_base: dict[str, Any] | None = None,
        config: Optional[HarnessConfig] = None,
    ):
        if config is None:
            config = HarnessConfig(
                name=f"diagnosis_{specialty}",
                model_provider=model_provider,
                tools=["pubmed", "omim", "opentargets"],
                recovery_strategy=RecoveryStrategy.ESCALATE,
                validation_threshold=0.7,
            )
        super().__init__(config=config)
        self.specialty = specialty
        self.kb = knowledge_base or RARE_DISEASE_KB

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        执行诊断Harness流程。

        Args:
            input_data: 包含symptoms、patient_history等字段的输入。

        Returns:
            诊断结果，包含diagnosis、confidence、next_steps等。
        """
        # 调用父类的五步流水线
        result = super().execute(input_data)

        # 转换为诊断特化格式
        return {
            "diagnosis": result.output.get("diagnosis", "无法确定"),
            "confidence": result.confidence,
            "differential": result.output.get("differential", []),
            "next_steps": result.output.get("next_steps", []),
            "evidence": result.output.get("evidence", {}),
            "harness_name": result.harness_name,
            "execution_time_ms": result.execution_time_ms,
            "recovery_applied": result.recovery_applied,
        }

    def _build_prompt(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        """构建诊断推理Prompt。"""
        patient = context.get("patient", {})
        symptoms = patient.get("symptoms", [])

        prompt = f"""你是一位{self.specialty}专科医生。请根据以下信息进行鉴别诊断。

## 患者信息
- 年龄: {patient.get('age', '未知')}
- 性别: {patient.get('sex', '未知')}
- 主诉: {patient.get('chief_complaint', '未提供')}

## 症状列表
{chr(10).join(f'- {s}' for s in symptoms)}

## 工具检索结果
"""
        for tool_name, output in tool_results.items():
            if "error" not in output:
                prompt += f"\n### {tool_name}\n{output}\n"

        prompt += """
## 请按以下格式输出
1. 最可能的诊断（含置信度）
2. 鉴别诊断列表（至少3个，按可能性排序）
3. 建议的下一步检查
4. 诊断依据

注意：如果不确定，请明确说明。不要使用"肯定"、"100%"等绝对性表述。
"""
        return prompt

    def _reason(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> dict[str, Any]:
        """诊断推理：结合知识库和工具结果。"""
        patient = context.get("patient", {})
        symptoms = [s.lower() for s in patient.get("symptoms", [])]

        # 知识库匹配
        candidates = []
        for disease_code, disease_info in self.kb.items():
            match_score = sum(
                1 for key_symptom in disease_info["key_symptoms"]
                if any(key_symptom.lower() in s for s in symptoms)
            )
            if match_score > 0:
                candidates.append({
                    "code": disease_code,
                    "name": disease_info["name"],
                    "score": match_score / len(disease_info["key_symptoms"]),
                    "differential": disease_info["differential"],
                    "tests": disease_info["diagnostic_tests"],
                })

        # 按匹配度排序
        candidates.sort(key=lambda x: x["score"], reverse=True)

        if candidates:
            top = candidates[0]
            return {
                "diagnosis": top["name"],
                "confidence": min(top["score"] + 0.2, 0.95),
                "differential": [c["name"] for c in candidates[1:4]],
                "next_steps": top["tests"],
                "evidence": {
                    "knowledge_base_match": True,
                    "candidates": len(candidates),
                    "tool_results": tool_results,
                },
            }
        else:
            return {
                "diagnosis": "需要进一步评估",
                "confidence": 0.3,
                "differential": [],
                "next_steps": ["详细病史采集", "体格检查", "实验室检查"],
                "evidence": {"knowledge_base_match": False},
            }

    def _metrics(
        self,
        context: dict[str, Any] | None = None,
        tool_results: dict[str, Any] | None = None,
        elapsed_ms: float = 0.0,
    ) -> dict[str, Any]:
        return {
            "harness_type": "diagnosis",
            "specialty": self.specialty,
            "tools_used": list((tool_results or {}).keys()),
            "elapsed_ms": elapsed_ms,
        }
