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

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class OrchestratorMode(Enum):
    """编排模式。"""
    OPENCLAW = "openclaw"   # OpenClaw原生
    CREWAI = "crewai"       # CrewAI兼容


@dataclass
class AgentDefinition:
    """Agent定义。"""
    name: str
    role: str
    specialty: str = ""
    tools: list[str] = field(default_factory=list)
    backstory: str = ""


@dataclass
class ConsensusResult:
    """多Agent共识结果。"""
    final_diagnosis: str
    confidence: float
    agent_opinions: dict[str, Any] = field(default_factory=dict)
    consensus_rounds: int = 0
    disagreements: list[str] = field(default_factory=list)


class MedicalOrchestrator:
    """
    医疗多Agent编排器。

    编排多个专业Agent协作完成复杂医疗推理任务。
    支持共识达成机制：多轮讨论 → 分歧解决 → 最终结论。
    """

    def __init__(self, mode: str | OrchestratorMode = "openclaw"):
        if isinstance(mode, str):
            mode = OrchestratorMode(mode)
        self.mode = mode
        self.agents: dict[str, AgentDefinition] = {}

    def add_agent(
        self,
        name: str,
        role: str = "",
        specialty: str = "",
        tools: list[str] | None = None,
        backstory: str = "",
    ) -> None:
        """添加Agent到编排器。"""
        self.agents[name] = AgentDefinition(
            name=name,
            role=role or name,
            specialty=specialty,
            tools=tools or [],
            backstory=backstory,
        )

    def run(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        consensus_rounds: int = 3,
    ) -> ConsensusResult:
        """
        执行多Agent协作推理。

        Args:
            task: 推理任务描述。
            context: 任务上下文。
            consensus_rounds: 共识达成轮数。

        Returns:
            共识结果。
        """
        context = context or {}
        start_time = time.time()

        # Phase 1: 各Agent独立推理
        agent_opinions = {}
        for name, agent in self.agents.items():
            opinion = self._agent_reason(agent, task, context)
            agent_opinions[name] = opinion

        # Phase 2: 共识达成
        final_result = self._reach_consensus(
            agent_opinions, consensus_rounds
        )

        elapsed = (time.time() - start_time) * 1000

        return ConsensusResult(
            final_diagnosis=final_result.get("diagnosis", ""),
            confidence=final_result.get("confidence", 0.0),
            agent_opinions=agent_opinions,
            consensus_rounds=consensus_rounds,
            disagreements=final_result.get("disagreements", []),
        )

    def _agent_reason(
        self,
        agent: AgentDefinition,
        task: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """单个Agent推理。实际实现通过模型适配器调用。"""
        return {
            "agent": agent.name,
            "role": agent.role,
            "opinion": f"[{agent.role}] 基于专业判断的分析",
            "confidence": 0.7,
            "evidence": [],
        }

    def _reach_consensus(
        self,
        opinions: dict[str, Any],
        rounds: int,
    ) -> dict[str, Any]:
        """
        共识达成机制。

        简化实现：取最高置信度的意见作为最终结论。
        完整实现：多轮讨论 → 分歧标注 → 投票/加权。
        """
        if not opinions:
            return {"diagnosis": "无法确定", "confidence": 0.0}

        # 按置信度排序
        sorted_opinions = sorted(
            opinions.values(),
            key=lambda x: x.get("confidence", 0),
            reverse=True,
        )

        top = sorted_opinions[0]
        disagreements = [
            f"{op['agent']}: {op['opinion']}"
            for op in sorted_opinions[1:]
            if op.get("confidence", 0) > 0.5
        ]

        return {
            "diagnosis": top.get("opinion", ""),
            "confidence": top.get("confidence", 0.0),
            "disagreements": disagreements,
        }
