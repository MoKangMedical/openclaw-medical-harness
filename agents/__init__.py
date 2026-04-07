"""Agents package — multi-agent orchestration for medical reasoning.

Re-exports the orchestrator module's public API.
"""

from agents.orchestrator import (
    MultiAgentOrchestrator,
    OrchestrationMode,
    AgentRole,
    AgentDefinition,
    AgentTask,
    AgentResult,
    ConsensusResult,
)

__all__ = [
    "MultiAgentOrchestrator",
    "OrchestrationMode",
    "AgentRole",
    "AgentDefinition",
    "AgentTask",
    "AgentResult",
    "ConsensusResult",
]
