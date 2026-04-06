"""
OpenClaw-Medical-Harness
========================

Medical AI Agent Orchestration Framework for OpenClaw — Built on Harness Theory.

核心理念：Harness（环境设计）比模型本身更重要。
模型可以被替换，Harness是私有的。

三层Harness：
- DiagnosisHarness: 症状→鉴别→确诊
- DrugDiscoveryHarness: 靶点→筛选→先导优化
- HealthManagementHarness: 评估→方案→随访
"""

__version__ = "0.1.0"
__author__ = "MoKangMedical"

from .base import BaseHarness
from .context import ContextManager
from .recovery import FailureRecovery
from .validator import ResultValidator, ValidationResult

# Harness implementations
from .diagnosis import DiagnosisHarness
from .drug_discovery import DrugDiscoveryHarness
from .health_management import HealthManagementHarness

# Agent orchestration
from .agents import MedicalOrchestrator

# MCP tools
from .mcp_tools import MedicalToolRegistry

__all__ = [
    "BaseHarness",
    "ContextManager",
    "FailureRecovery",
    "ResultValidator",
    "ValidationResult",
    "DiagnosisHarness",
    "DrugDiscoveryHarness",
    "HealthManagementHarness",
    "MedicalOrchestrator",
    "MedicalToolRegistry",
]
