"""
Medical Orchestrator — 多Agent编排器。

支持两种模式：
- OpenClaw原生模式：通过Skill系统编排
- CrewAI兼容模式：通过CrewAI框架编排

Agent角色：
- 诊断Agent：执行鉴别诊断推理
- 文献Agent：检索和评估文献证据
- 药物Agent：药物信息和交互分析
- 沟通Agent：患者友好的结果解读
"""

from .orchestrator import (
    MultiAgentOrchestrator,
    OrchestrationMode,
    AgentRole,
    AgentDefinition,
    AgentTask,
    AgentResult,
    ConsensusResult,
)

# Backward compatibility alias
MedicalOrchestrator = MultiAgentOrchestrator

__all__ = [
    "MultiAgentOrchestrator",
    "MedicalOrchestrator",
    "OrchestrationMode",
    "AgentRole",
    "AgentDefinition",
    "AgentTask",
    "AgentResult",
    "ConsensusResult",
]
