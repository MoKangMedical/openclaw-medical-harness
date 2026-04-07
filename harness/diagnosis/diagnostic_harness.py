"""Diagnostic Harness — symptom-to-diagnosis orchestration.

Implements the full diagnostic reasoning pipeline:
  Symptoms → Triage → Differential Diagnosis → Workup Strategy → Confirmed Diagnosis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from harness.base import BaseHarness, ToolBase, HarnessResult

logger = logging.getLogger(__name__)


@dataclass
class DifferentialDiagnosis:
    """A single entry in the differential diagnosis list."""

    condition: str = ""
    probability: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    icd10_code: str = ""


@dataclass
class DiagnosticResult:
    """Structured output from the Diagnostic Harness."""

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


class DiagnosticHarness(BaseHarness):
    """Medical diagnostic reasoning Harness.

    Orchestrates the full diagnostic workflow:
      1. Symptom intake and structuring
      2. Triage and urgency assessment
      3. Differential diagnosis generation
      4. Workup strategy formulation
      5. Evidence-based narrowing

    Example:
        >>> harness = DiagnosticHarness(name="cardiac-dx")
        >>> result = harness.execute({
        ...     "symptoms": ["chest pain", "shortness of breath"],
        ...     "age": 55, "sex": "male",
        ...     "medical_history": ["hypertension", "diabetes"],
        ... })
    """

    def __init__(
        self,
        name: str = "diagnostic-harness",
        model_provider: str = "mimo",
        tools: list[ToolBase] | None = None,
        enable_rare_disease_screening: bool = False,
        multidisciplinary_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, model_provider=model_provider, tools=tools, **kwargs)
        self.enable_rare_disease_screening = enable_rare_disease_screening
        self.multidisciplinary_mode = multidisciplinary_mode

    def execute(self, input_data: dict[str, Any]) -> HarnessResult:
        """Execute the diagnostic Harness pipeline."""
        symptoms = input_data.get("symptoms", [])
        input_data["symptoms_structured"] = self._structure_symptoms(symptoms) if symptoms else []
        input_data["red_flags"] = self._screen_red_flags(symptoms)
        return super().execute(input_data)

    def _build_prompt(self, context: dict[str, Any], tool_results: dict[str, Any]) -> str:
        input_data = context.get("input", {})
        symptoms = input_data.get("symptoms_structured", input_data.get("symptoms", []))
        red_flags = input_data.get("red_flags", [])

        parts = [
            "You are a clinical diagnostic reasoning assistant.",
            "## Patient Presentation",
            f"- Symptoms: {', '.join(s if isinstance(s, str) else s.get('name','') for s in symptoms) if symptoms else 'Not specified'}",
            f"- Age: {input_data.get('age', 'Not specified')}",
            f"- Sex: {input_data.get('sex', 'Not specified')}",
            f"- History: {', '.join(input_data.get('medical_history', [])) or 'None'}",
        ]
        if red_flags:
            parts.extend(["", "## ⚠️ Red Flags", *[f"- {f}" for f in red_flags]])
        if tool_results:
            parts.extend(["", "## Evidence"])
            for name, result in tool_results.items():
                parts.append(f"### {name}: {str(result)[:300]}")
        parts.extend(["", "## Required Output",
            "1. Primary diagnosis with confidence", "2. Differential list (≥3 alternatives)",
            "3. Recommended tests", "4. Urgency level", "5. Specialist referral", "6. Reasoning chain"])
        return "\n".join(parts)

    def _domain(self) -> str:
        return "diagnosis"

    def _structure_symptoms(self, symptoms: list[str]) -> list[dict[str, Any]]:
        return [{"name": s.lower().strip(), "category": self._categorize_symptom(s)} for s in symptoms]

    def _screen_red_flags(self, symptoms: list[str]) -> list[str]:
        combined = " ".join(s.lower() for s in symptoms)
        return [w for p, w in _RED_FLAG_PATTERNS.items() if p in combined]

    @staticmethod
    def _categorize_symptom(symptom: str) -> str:
        categories = {
            "cardiac": ["chest pain", "palpitations", "edema", "syncope"],
            "respiratory": ["cough", "shortness of breath", "wheezing"],
            "neurological": ["headache", "dizziness", "numbness", "weakness"],
            "gastrointestinal": ["nausea", "vomiting", "diarrhea", "abdominal pain"],
            "constitutional": ["fever", "fatigue", "weight loss", "night sweats"],
        }
        sl = symptom.lower()
        for cat, kws in categories.items():
            if any(kw in sl for kw in kws):
                return cat
        return "general"

    def request_multidisciplinary_consult(
        self, specialists: list[str], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Request multi-disciplinary consultation."""
        return {s: {"status": "pending", "specialist_type": s} for s in specialists}

    def query_rare_disease_kb(
        self, symptoms: list[str], genetic_markers: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Query rare disease knowledge base (OMIM/Orphanet)."""
        if not self.enable_rare_disease_screening:
            return []
        return []
