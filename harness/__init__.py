"""OpenClaw Medical Harness — Medical AI Agent Orchestration Framework.

Built on Harness Theory: environment design matters more than model selection.
Well-designed Harness architecture yields up to 64% performance improvement.

Components:
    - BaseHarness: Abstract Harness layer for all medical Harnesses
    - DiagnosticHarness: Symptom → Differential → Confirmed diagnosis
    - DrugDiscoveryHarness: Target → Screening → Lead optimization
    - HealthManagementHarness: Assessment → Plan → Follow-up
    - MultiAgentOrchestrator: Dual-mode agent orchestration
    - MedicalToolRegistry: MCP-based medical data source registry
"""

__version__ = "0.1.0"
__author__ = "MoKangMedical"
__license__ = "MIT"

from harness.base import BaseHarness, HarnessResult
from harness.context import ContextManager
from harness.recovery import FailureRecovery
from harness.validator import ResultValidator
from harness.diagnosis.diagnostic_harness import DiagnosticHarness
from harness.drug_discovery.drug_harness import DrugDiscoveryHarness
from harness.health_management.health_harness import HealthManagementHarness
from agents.orchestrator import MultiAgentOrchestrator
from mcp_tools.registry import MedicalToolRegistry

__all__ = [
    "BaseHarness",
    "HarnessResult",
    "ContextManager",
    "FailureRecovery",
    "ResultValidator",
    "DiagnosticHarness",
    "DrugDiscoveryHarness",
    "HealthManagementHarness",
    "MultiAgentOrchestrator",
    "MedicalToolRegistry",
]
