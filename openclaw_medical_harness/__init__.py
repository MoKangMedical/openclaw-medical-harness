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

__version__ = "0.2.0"
__author__ = "MoKangMedical"

from .base import (
    BaseHarness,
    HarnessConfig,
    HarnessResult,
    HarnessStatus,
    HarnessMetrics,
    ToolBase,
    ToolExecutionError,
    ModelProviderBase,
    CheckpointError,
    DryRunPlan,
)

from .context import ContextManager, HarnessContext, CompressionStrategy

from .recovery import FailureRecovery, RecoveryStrategy, RecoveryResult

from .validator import ResultValidator, ValidationResult, ValidationSeverity

# Harness implementations
from .diagnosis import DiagnosisHarness, DiagnosticResult, DifferentialDiagnosis
from .drug_discovery import DrugDiscoveryHarness, DrugDiscoveryResult, CompoundProfile
from .health_management import HealthManagementHarness, HealthPlan, HealthAssessment

# Agent orchestration
from .agents import (
    MultiAgentOrchestrator,
    MedicalOrchestrator,
    OrchestrationMode,
    AgentRole,
    ConsensusResult,
)

# MCP tools
from .mcp_tools import MedicalToolRegistry, MCPToolAdapter, MCPCategory

# Model providers
from .providers import ModelProvider, MIMOProvider, create_provider

__all__ = [
    # Base
    "BaseHarness",
    "HarnessConfig",
    "HarnessResult",
    "HarnessStatus",
    "HarnessMetrics",
    "ToolBase",
    "ToolExecutionError",
    "ModelProviderBase",
    "CheckpointError",
    "DryRunPlan",
    # Context
    "ContextManager",
    "HarnessContext",
    "CompressionStrategy",
    # Recovery
    "FailureRecovery",
    "RecoveryStrategy",
    "RecoveryResult",
    # Validator
    "ResultValidator",
    "ValidationResult",
    "ValidationSeverity",
    # Diagnosis
    "DiagnosisHarness",
    "DiagnosticResult",
    "DifferentialDiagnosis",
    # Drug Discovery
    "DrugDiscoveryHarness",
    "DrugDiscoveryResult",
    "CompoundProfile",
    # Health Management
    "HealthManagementHarness",
    "HealthPlan",
    "HealthAssessment",
    # Agents
    "MultiAgentOrchestrator",
    "MedicalOrchestrator",
    "OrchestrationMode",
    "AgentRole",
    "ConsensusResult",
    # MCP Tools
    "MedicalToolRegistry",
    "MCPToolAdapter",
    "MCPCategory",
    # Providers
    "ModelProvider",
    "MIMOProvider",
    "create_provider",
]
