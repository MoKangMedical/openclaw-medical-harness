"""Health Management Harness — assessment-to-follow-up orchestration.

Pipeline: Health Assessment → Personalized Plan → Compliance Tracking → Outcome Evaluation
Supports: Multi-modal data, wearable integration, longitudinal monitoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from harness.base import BaseHarness, ToolBase, HarnessResult

logger = logging.getLogger(__name__)


@dataclass
class HealthAssessment:
    """Comprehensive health assessment result."""

    risk_scores: dict[str, float] = field(default_factory=dict)
    lifestyle_factors: list[str] = field(default_factory=list)
    biomarkers: dict[str, dict[str, Any]] = field(default_factory=dict)
    mental_health_screen: dict[str, Any] = field(default_factory=dict)
    overall_risk_level: str = "moderate"


@dataclass
class CarePlanItem:
    """A single item in a care plan."""

    category: str = ""
    description: str = ""
    frequency: str = ""
    duration: str = ""
    priority: str = "recommended"
    evidence_level: str = "B"


@dataclass
class HealthPlan:
    """Personalized health management plan."""

    plan_items: list[CarePlanItem] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)
    follow_up_schedule: list[dict[str, str]] = field(default_factory=list)
    compliance_tracking: dict[str, Any] = field(default_factory=dict)
    escalation_triggers: list[str] = field(default_factory=list)


@dataclass
class FollowUpResult:
    """Result of a follow-up assessment."""

    date: str = ""
    compliance_rate: float = 0.0
    outcome_changes: dict[str, Any] = field(default_factory=dict)
    plan_adjustments: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


class HealthManagementHarness(BaseHarness):
    """Long-term health management Harness.

    Pipeline:
      1. Health assessment — multi-modal data aggregation
      2. Plan generation — personalized care plans
      3. Compliance monitoring
      4. Outcome evaluation

    Example:
        >>> harness = HealthManagementHarness(name="diabetes-mgmt")
        >>> result = harness.execute({
        ...     "patient_id": "P12345",
        ...     "conditions": ["type 2 diabetes"],
        ...     "lab_results": {"hba1c": 7.2},
        ... })
    """

    def __init__(
        self,
        name: str = "health-management-harness",
        model_provider: str = "mimo",
        tools: list[ToolBase] | None = None,
        follow_up_interval_days: int = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, model_provider=model_provider, tools=tools, **kwargs)
        self.follow_up_interval_days = follow_up_interval_days
        self._patient_history: dict[str, list[Any]] = {}

    def execute(self, input_data: dict[str, Any]) -> HarnessResult:
        patient_id = input_data.get("patient_id", "unknown")
        input_data["aggregated_data"] = self._aggregate_multimodal_data(input_data)
        if patient_id not in self._patient_history:
            self._patient_history[patient_id] = []
        self._patient_history[patient_id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_summary": {k: type(v).__name__ for k, v in input_data.items()},
        })
        return super().execute(input_data)

    def _build_prompt(self, context: dict[str, Any], tool_results: dict[str, Any]) -> str:
        input_data = context.get("input", {})
        parts = [
            "You are a health management planning assistant.",
            "## Patient Data",
            f"- ID: {input_data.get('patient_id', 'N/A')}",
            f"- Conditions: {', '.join(input_data.get('conditions', [])) or 'None'}",
        ]
        if "lab_results" in input_data:
            parts.extend(["", "## Lab Results", *[f"- {k}: {v}" for k, v in input_data["lab_results"].items()]])
        if "wearable_data" in input_data:
            parts.extend(["", "## Wearable Data", *[f"- {k}: {v}" for k, v in input_data["wearable_data"].items()]])
        parts.extend(["", "## Required Output",
            "Risk assessment, personalized care plan, measurable goals, follow-up schedule, compliance tracking."])
        return "\n".join(parts)

    def _domain(self) -> str:
        return "health_management"

    def _aggregate_multimodal_data(self, input_data: dict[str, Any]) -> dict[str, Any]:
        sources = [f for f in ["lab_results", "wearable_data", "questionnaire_responses"] if f in input_data]
        return {"sources": sources, "data_quality_score": len(sources) / 3.0}

    def conduct_follow_up(self, patient_id: str, current_data: dict[str, Any]) -> FollowUpResult:
        return FollowUpResult(date=datetime.now(timezone.utc).isoformat())
