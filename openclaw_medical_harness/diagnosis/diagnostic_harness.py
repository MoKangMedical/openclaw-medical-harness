"""
Diagnostic Harness — 诊断Harness实现。

Harness流程：
症状输入 → 分层鉴别 → 检查策略 → 确诊路径
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ..base import BaseHarness, HarnessConfig, HarnessResult
from ..recovery import RecoveryStrategy

logger = logging.getLogger(__name__)


# 罕见病知识库（精简版，完整版通过MCP加载）
RARE_DISEASE_KB: dict[str, dict[str, Any]] = {
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
    "PKU": {
        "name": "苯丙酮尿症 / Phenylketonuria",
        "key_symptoms": ["intellectual disability", "musty odor", "seizures", "eczema"],
        "diagnostic_tests": ["phenylalanine level", "PAH gene test", "BH4 loading test"],
        "differential": ["BH4 deficiency", "tyrosinemia", "maple syrup urine disease"],
    },
}


@dataclass
class DifferentialDiagnosis:
    """鉴别诊断中的单个条目。"""
    condition: str = ""
    probability: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    icd10_code: str = ""


@dataclass
class DiagnosticResult:
    """诊断Harness的结构化输出。"""
    primary_diagnosis: str = "Undetermined"
    confidence: float = 0.0
    differential_list: list[DifferentialDiagnosis] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    urgency_level: str = "routine"
    specialist_referral: str = ""
    reasoning_chain: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


_RED_FLAG_PATTERNS: dict[str, str] = {
    "chest pain": "Possible cardiac event — consider ACS workup",
    "sudden severe headache": "Possible subarachnoid hemorrhage",
    "shortness of breath at rest": "Respiratory emergency evaluation needed",
    "loss of consciousness": "Neurological emergency",
    "vision loss": "Ophthalmological or neurological emergency",
    "severe abdominal pain": "Surgical abdomen — rule out acute conditions",
}


class DiagnosisHarness(BaseHarness):
    """
    诊断Harness。

    将诊断推理过程结构化为Harness流程：
    1. 症状解析 → 结构化症状列表
    2. 分层鉴别 → 候选诊断排序
    3. 检查策略 → 最优检查路径
    4. 确诊路径 → 诊断结论 + 下一步

    Example:
        >>> harness = DiagnosisHarness(specialty="neurology")
        >>> result = harness.execute({
        ...     "symptoms": ["bilateral ptosis", "fatigable weakness"],
        ...     "patient": {"age": 35, "sex": "F"},
        ... })
    """

    def __init__(
        self,
        model_provider: str = "mimo",
        specialty: str = "neurology",
        knowledge_base: dict[str, Any] | None = None,
        name: str = "",
        config: Optional[HarnessConfig] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = HarnessConfig(
                name=name or f"diagnosis_{specialty}",
                model_provider=model_provider,
                tools=["pubmed", "omim", "opentargets"],
                recovery_strategy=RecoveryStrategy.ESCALATE.value,
                validation_threshold=0.7,
            )
        super().__init__(config=config, **kwargs)
        self.specialty = specialty
        self.kb = knowledge_base or RARE_DISEASE_KB

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行诊断Harness流程。

        Args:
            input_data: 包含symptoms、patient等字段的输入。

        Returns:
            诊断结果，包含diagnosis、confidence、next_steps等。
        """
        # 预处理：结构化症状
        symptoms = input_data.get("symptoms", [])
        if symptoms:
            input_data.setdefault("patient", {})
            input_data["patient"]["symptoms"] = symptoms

        # 调用父类的五步流水线
        result = super().execute(input_data)

        # 如果推理结果是dict，直接返回
        if isinstance(result.output, dict):
            return {
                "diagnosis": result.output.get("diagnosis", "无法确定"),
                "confidence": result.output.get("confidence", result.confidence),
                "differential": result.output.get("differential", []),
                "next_steps": result.output.get("next_steps", []),
                "evidence": result.output.get("evidence", {}),
                "harness_name": result.harness_name,
                "execution_time_ms": result.execution_time_ms,
                "recovery_applied": result.recovery_applied,
            }
        return {
            "diagnosis": str(result.output),
            "confidence": result.confidence,
            "differential": [],
            "next_steps": [],
            "evidence": {},
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
{chr(10).join(f'- {s}' for s in symptoms) if symptoms else '- 未提供'}

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
        """诊断推理：结合知识库 + 模型推理 + 工具结果。"""
        patient = context.get("patient", {})
        symptoms = [s.lower() for s in patient.get("symptoms", [])]

        # Step 1: 知识库匹配（提供先验上下文）
        kb_candidates: list[dict[str, Any]] = []
        for disease_code, disease_info in self.kb.items():
            match_score = sum(
                1 for key_symptom in disease_info["key_symptoms"]
                if any(key_symptom.lower() in s for s in symptoms)
            )
            if match_score > 0:
                kb_candidates.append({
                    "code": disease_code,
                    "name": disease_info["name"],
                    "score": match_score / len(disease_info["key_symptoms"]),
                    "differential": disease_info["differential"],
                    "tests": disease_info["diagnostic_tests"],
                })
        kb_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Step 2: 构建推理prompt
        prompt = self._build_model_prompt(patient, symptoms, kb_candidates, tool_results, context)

        # Step 3: 调用模型
        model_result = self._call_model(prompt)

        # Step 4: 合并知识库和模型结果
        if model_result.get("mode") == "fallback" or "diagnosis" not in model_result:
            # 模型未返回结构化结果，使用知识库结果
            if kb_candidates:
                top = kb_candidates[0]
                return {
                    "diagnosis": top["name"],
                    "confidence": min(top["score"] + 0.2, 0.95),
                    "differential": [c["name"] for c in kb_candidates[1:4]],
                    "next_steps": top["tests"],
                    "evidence": {"source": "knowledge_base", "candidates": len(kb_candidates)},
                }
            else:
                return {
                    "diagnosis": model_result.get("analysis", "需要进一步评估"),
                    "confidence": model_result.get("confidence", 0.3),
                    "differential": ["详细病史采集", "体格检查", "实验室检查"],
                    "next_steps": ["详细病史采集", "体格检查", "实验室检查"],
                    "evidence": {"source": "model_fallback"},
                }

        # 模型返回了结构化结果，使用模型结果
        result = {
            "diagnosis": model_result.get("diagnosis", "无法确定"),
            "confidence": model_result.get("confidence", 0.5),
            "differential": model_result.get("differential", model_result.get("differentials", [])),
            "next_steps": model_result.get("next_steps", model_result.get("tests", [])),
            "reasoning": model_result.get("reasoning", model_result.get("analysis", "")),
            "evidence": {
                "source": "model",
                "provider": self.model_provider,
                "kb_candidates": len(kb_candidates),
                "tool_results": tool_results,
            },
        }

        # 如果知识库有匹配，补充知识库的下一步检查
        if kb_candidates and not result["next_steps"]:
            result["next_steps"] = kb_candidates[0]["tests"]

        return result

    def _build_model_prompt(
        self,
        patient: dict[str, Any],
        symptoms: list[str],
        kb_candidates: list[dict[str, Any]],
        tool_results: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """构建完整的模型推理prompt。"""
        age = patient.get('age', '未知')
        sex = patient.get('sex', '未知')

        prompt = f"""你是一位{self.specialty}专科医生。请根据以下信息进行鉴别诊断。

## 患者信息
- 年龄: {age}
- 性别: {sex}
- 主诉: {patient.get('chief_complaint', '未提供')}

## 症状列表
"""
        for s in symptoms:
            prompt += f"- {s}\n"

        # 注入知识库先验
        if kb_candidates:
            prompt += "\n## 知识库匹配结果（供参考）\n"
            for c in kb_candidates[:3]:
                prompt += f"- {c['name']} (匹配度: {c['score']:.0%})\n"
                prompt += f"  鉴别: {', '.join(c['differential'])}\n"

        # 注入工具结果
        if tool_results:
            prompt += "\n## 工具检索结果\n"
            for tool_name, output in tool_results.items():
                if isinstance(output, dict) and "error" not in output:
                    articles = output.get("articles", [])
                    if articles:
                        prompt += f"\n### {tool_name} 文献\n"
                        for a in articles[:3]:
                            prompt += f"- {a.get('title', '')} ({a.get('journal', '')})\n"
                    associations = output.get("associations", [])
                    if associations:
                        prompt += f"\n### {tool_name} 靶点关联\n"
                        for a in associations[:3]:
                            prompt += f"- {a.get('disease_name', '')} (score: {a.get('score', 0):.2f})\n"

        # 恢复约束
        recovery_info = context.get("_recovery", {})
        if recovery_info:
            prompt += f"\n## 注意\n上次分析有问题：{recovery_info.get('original_issues', [])}\n"
            prompt += "请给出更准确的鉴别诊断列表，并标注每个诊断的置信度。\n"

        prompt += """
## 输出要求
请以严格的JSON格式返回，格式如下（不要输出其他内容）：
{"diagnosis": "最可能的诊断名称", "confidence": 0.85, "differential": ["鉴别诊断1", "鉴别诊断2", "鉴别诊断3"], "next_steps": ["检查1", "检查2", "检查3"], "reasoning": "诊断推理过程"}

注意：
- confidence 范围 0-1
- 如果不确定，明确说明并给出较低的置信度
- 不要使用"肯定"、"100%"等绝对性表述
- differential 至少列出3个鉴别诊断
"""
        return prompt

    def _domain(self) -> str:
        return "diagnosis"

    def request_multidisciplinary_consult(
        self, specialists: list[str], context: dict[str, Any]
    ) -> dict[str, Any]:
        """请求多学科会诊。"""
        return {s: {"status": "pending", "specialist_type": s} for s in specialists}

    def query_rare_disease_kb(
        self, symptoms: list[str], genetic_markers: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """查询罕见病知识库。"""
        results = []
        symptoms_lower = [s.lower() for s in symptoms]
        for code, info in self.kb.items():
            score = sum(
                1 for ks in info["key_symptoms"]
                if any(ks.lower() in s for s in symptoms_lower)
            )
            if score > 0:
                results.append({"code": code, "name": info["name"], "match_score": score})
        return sorted(results, key=lambda x: x["match_score"], reverse=True)
