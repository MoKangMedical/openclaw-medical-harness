"""Multi-Agent Orchestrator — independent orchestrator module.

This module provides the multi-agent orchestration layer that sits above
individual Harnesses. It coordinates multiple specialized agents through
consensus-based decision making.

Two orchestration modes:
  - OpenClaw native: Uses OpenClaw's Skill system for agent routing
  - CrewAI compatible: Maps to CrewAI Agent/Crew/Task API

Agent roles:
  - Diagnostic Agent: Clinical reasoning, differential diagnosis
  - Literature Agent: Evidence retrieval and synthesis
  - Drug Agent: Pharmacology, interactions, dosing
  - Communication Agent: Patient-facing explanations
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class OrchestrationMode(str, Enum):
    """Orchestration mode selection.

    OPENCLAW: Native OpenClaw Skill-based routing.
    CREWAI:   CrewAI Agent/Crew/Task compatible mode.
    """

    OPENCLAW = "openclaw"
    CREWAI = "crewai"


class AgentRole(str, Enum):
    """Pre-defined medical agent roles.

    Each role maps to a specific type of medical reasoning expertise
    and has access to a curated set of MCP tools.
    """

    DIAGNOSTIC = "diagnostic"
    LITERATURE = "literature"
    DRUG = "drug"
    COMMUNICATION = "communication"


@dataclass
class AgentDefinition:
    """Definition of a medical agent.

    Attributes:
        name: Unique agent identifier.
        role: The agent's role in the orchestration.
        specialty: Optional medical specialty (e.g., 'neurology', 'cardiology').
        backstory: Background context for the agent's persona.
        tools: List of MCP tool names this agent can use.
        model_override: Optional model override for this specific agent.
        temperature: Model temperature for this agent (lower = more deterministic).
    """

    name: str = ""
    role: AgentRole = AgentRole.DIAGNOSTIC
    specialty: str = ""
    backstory: str = ""
    tools: list[str] = field(default_factory=list)
    model_override: str = ""
    temperature: float = 0.3


@dataclass
class AgentTask:
    """A task assigned to an agent.

    Attributes:
        objective: What the agent should accomplish.
        context: Shared context data for the task.
        priority: Task priority (higher = more important).
        timeout_seconds: Maximum execution time.
        depends_on: List of agent names whose results are needed first.
    """

    objective: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    timeout_seconds: float = 120.0
    depends_on: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result produced by an agent.

    Attributes:
        agent_name: Name of the agent that produced this result.
        agent_role: Role of the agent.
        output: The agent's output data.
        confidence: Confidence in the output (0.0 - 1.0).
        evidence: Supporting evidence or citations.
        execution_time_ms: Time taken to produce the result.
        warnings: Any warnings or caveats.
    """

    agent_name: str = ""
    agent_role: AgentRole = AgentRole.DIAGNOSTIC
    output: Any = None
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ConsensusResult:
    """Result of multi-agent consensus.

    Attributes:
        final_diagnosis: The consensus diagnosis or conclusion.
        confidence: Aggregate confidence across all agents.
        agent_results: Individual results from each agent.
        consensus_rounds: Number of rounds used to reach consensus.
        disagreements: List of unresolved disagreements.
        evidence_summary: Aggregated evidence from all agents.
        escalation_needed: Whether human expert review is recommended.
    """

    final_diagnosis: str = ""
    confidence: float = 0.0
    agent_results: dict[str, AgentResult] = field(default_factory=dict)
    consensus_rounds: int = 0
    disagreements: list[str] = field(default_factory=list)
    evidence_summary: list[str] = field(default_factory=list)
    escalation_needed: bool = False


# ── Agent Templates ──────────────────────────────────────────────────

_AGENT_TEMPLATES: dict[AgentRole, dict[str, Any]] = {
    AgentRole.DIAGNOSTIC: {
        "backstory": (
            "You are an experienced clinical diagnostician with expertise in "
            "differential diagnosis. You approach cases systematically, considering "
            "common conditions first, then rare diseases when evidence warrants."
        ),
        "tools": ["pubmed_search", "omim_lookup"],
        "temperature": 0.2,
    },
    AgentRole.LITERATURE: {
        "backstory": (
            "You are a medical research librarian specializing in evidence synthesis. "
            "You excel at finding, evaluating, and summarizing clinical evidence "
            "from peer-reviewed literature."
        ),
        "tools": ["pubmed_search"],
        "temperature": 0.1,
    },
    AgentRole.DRUG: {
        "backstory": (
            "You are a clinical pharmacologist with deep knowledge of drug mechanisms, "
            "interactions, dosing, and adverse effects. You prioritize patient safety."
        ),
        "tools": ["chembl_query", "openfae_safety"],
        "temperature": 0.2,
    },
    AgentRole.COMMUNICATION: {
        "backstory": (
            "You are a patient communication specialist who translates complex "
            "medical information into clear, empathetic, and actionable language "
            "that patients can understand and act upon."
        ),
        "tools": [],
        "temperature": 0.5,
    },
}


class MultiAgentOrchestrator:
    """Multi-agent orchestrator for medical reasoning.

    Coordinates multiple specialized agents to collaboratively solve complex
    medical tasks. Supports consensus-based decision making with configurable
    rounds of deliberation.

    The orchestrator manages:
      1. Agent registration and configuration
      2. Task assignment with dependency resolution
      3. Parallel agent execution (conceptually)
      4. Consensus building across agent outputs
      5. Escalation when agents disagree

    Example:
        >>> orchestrator = MultiAgentOrchestrator(mode=OrchestrationMode.OPENCLAW)
        >>> orchestrator.add_agent(AgentRole.DIAGNOSTIC, specialty="neurology")
        >>> orchestrator.add_agent(AgentRole.LITERATURE)
        >>> orchestrator.add_agent(AgentRole.DRUG)
        >>> result = orchestrator.run(
        ...     objective="35岁女性，双眼睑下垂6个月，下午加重",
        ...     context={"symptoms": ["bilateral ptosis", "fatigable weakness"]},
        ...     consensus_rounds=3,
        ... )
    """

    def __init__(
        self,
        mode: OrchestrationMode | str = OrchestrationMode.OPENCLAW,
        model: str = "mimo",
        max_agents: int = 10,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            mode: Orchestration mode (OpenClaw or CrewAI).
            model: Default model for all agents.
            max_agents: Maximum number of agents allowed.
        """
        if isinstance(mode, str):
            mode = OrchestrationMode(mode)
        self.mode = mode
        self.model = model
        self.max_agents = max_agents
        self._agents: dict[str, AgentDefinition] = {}
        self._execution_log: list[dict[str, Any]] = []

    def add_agent(
        self,
        role: AgentRole,
        name: str = "",
        specialty: str = "",
        tools: list[str] | None = None,
        backstory: str = "",
        temperature: float | None = None,
    ) -> str:
        """Add an agent to the orchestration.

        Args:
            role: The agent's role (diagnostic, literature, drug, communication).
            name: Optional custom name. Auto-generated if empty.
            specialty: Medical specialty (e.g., 'neurology').
            tools: Override default tools for this role.
            backstory: Override default backstory.
            temperature: Override default temperature.

        Returns:
            The agent's name (useful when auto-generated).

        Raises:
            ValueError: If max_agents limit reached.
        """
        if len(self._agents) >= self.max_agents:
            raise ValueError(f"Maximum agent limit ({self.max_agents}) reached")

        template = _AGENT_TEMPLATES.get(role, {})

        agent_name = name or f"{role.value}_agent_{len(self._agents) + 1}"
        agent = AgentDefinition(
            name=agent_name,
            role=role,
            specialty=specialty,
            backstory=backstory or template.get("backstory", ""),
            tools=tools or template.get("tools", []),
            temperature=temperature if temperature is not None else template.get("temperature", 0.3),
        )

        self._agents[agent_name] = agent
        logger.info("Added agent: %s (role=%s, specialty=%s)", agent_name, role.value, specialty)
        return agent_name

    def remove_agent(self, name: str) -> bool:
        """Remove an agent by name.

        Args:
            name: The agent name to remove.

        Returns:
            True if agent was found and removed, False otherwise.
        """
        if name in self._agents:
            del self._agents[name]
            logger.info("Removed agent: %s", name)
            return True
        return False

    def run(
        self,
        objective: str,
        context: dict[str, Any] | None = None,
        consensus_rounds: int = 3,
        timeout_seconds: float = 300.0,
    ) -> ConsensusResult:
        """Execute multi-agent orchestration.

        Pipeline:
          1. Phase 1 — Each agent independently reasons about the objective
          2. Phase 2 — Agents review each other's outputs (consensus rounds)
          3. Phase 3 — Aggregate into final consensus result

        Args:
            objective: The medical task to accomplish.
            context: Shared context data (patient info, symptoms, etc.).
            consensus_rounds: Number of deliberation rounds for consensus.
            timeout_seconds: Maximum total execution time.

        Returns:
            ConsensusResult with the aggregated multi-agent output.
        """
        context = context or {}
        start_time = time.monotonic()

        if not self._agents:
            logger.warning("No agents registered — returning empty result")
            return ConsensusResult(
                final_diagnosis="No agents configured",
                confidence=0.0,
                escalation_needed=True,
            )

        # ── Phase 1: Independent reasoning ───────────────────────────
        agent_results: dict[str, AgentResult] = {}
        for name, agent in self._agents.items():
            result = self._execute_agent(agent, objective, context)
            agent_results[name] = result

        # ── Phase 2: Consensus building ──────────────────────────────
        for round_num in range(consensus_rounds):
            logger.info("Consensus round %d/%d", round_num + 1, consensus_rounds)

            # In each round, agents can see others' outputs and revise
            revised_results: dict[str, AgentResult] = {}
            for name, agent in self._agents.items():
                other_outputs = {
                    n: r for n, r in agent_results.items() if n != name
                }
                revised = self._revise_opinion(agent, objective, context, other_outputs)
                revised_results[name] = revised

            agent_results = revised_results

            # Check for convergence
            if self._check_convergence(agent_results):
                logger.info("Consensus reached at round %d", round_num + 1)
                break

        # ── Phase 3: Aggregate results ───────────────────────────────
        consensus = self._aggregate_results(
            agent_results, consensus_rounds
        )

        elapsed_ms = (time.monotonic() - start_time) * 1000
        self._execution_log.append({
            "objective": objective,
            "agents_count": len(self._agents),
            "consensus_rounds": consensus_rounds,
            "elapsed_ms": elapsed_ms,
            "final_confidence": consensus.confidence,
        })

        return consensus

    def _execute_agent(
        self,
        agent: AgentDefinition,
        objective: str,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute a single agent's reasoning.

        In production, this calls the model provider. Here we produce
        structured placeholder output based on the agent's role.

        Args:
            agent: The agent definition.
            objective: The task objective.
            context: Shared context data.

        Returns:
            AgentResult with the agent's output.
        """
        start = time.monotonic()

        # Build role-specific prompt
        prompt = self._build_agent_prompt(agent, objective, context)

        # Execute reasoning (placeholder — real implementation calls model)
        output = self._agent_reasoning(agent, prompt, context)

        elapsed_ms = (time.monotonic() - start) * 1000

        return AgentResult(
            agent_name=agent.name,
            agent_role=agent.role,
            output=output,
            confidence=output.get("confidence", 0.5),
            evidence=output.get("evidence", []),
            execution_time_ms=elapsed_ms,
        )

    def _build_agent_prompt(
        self,
        agent: AgentDefinition,
        objective: str,
        context: dict[str, Any],
    ) -> str:
        """Build a role-specific prompt for an agent.

        Args:
            agent: The agent definition.
            objective: The task objective.
            context: Shared context data.

        Returns:
            Formatted prompt string.
        """
        parts = [agent.backstory, "", f"## Objective\n{objective}"]

        if agent.specialty:
            parts.append(f"\nSpecialty: {agent.specialty}")

        if context.get("symptoms"):
            parts.append(f"\n## Symptoms\n{', '.join(context['symptoms'])}")

        if context.get("medical_history"):
            parts.append(f"\n## History\n{', '.join(context['medical_history'])}")

        parts.append("\n## Your Analysis")
        return "\n".join(parts)

    def _agent_reasoning(
        self,
        agent: AgentDefinition,
        prompt: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce agent-specific reasoning output.

        In production, this invokes the model provider with the agent's
        role-specific prompt and tools. Here we provide structured output
        based on the agent role.

        Args:
            agent: The agent definition.
            prompt: The constructed prompt.
            context: Shared context data.

        Returns:
            Dict with the agent's analysis output.
        """
        symptoms = context.get("symptoms", [])

        if agent.role == AgentRole.DIAGNOSTIC:
            return {
                "analysis": f"Differential diagnosis for: {', '.join(symptoms) or 'presenting complaint'}",
                "confidence": 0.75,
                "differentials": ["Primary consideration", "Alternative 1", "Alternative 2"],
                "evidence": ["Clinical presentation consistent", "Epidemiological support"],
                "recommendation": "Further workup recommended",
            }
        elif agent.role == AgentRole.LITERATURE:
            return {
                "analysis": f"Literature review for: {', '.join(symptoms) or 'presenting complaint'}",
                "confidence": 0.7,
                "evidence": ["PMID:12345 — relevant case series", "PMID:67890 — systematic review"],
                "recommendation": "Evidence supports further investigation",
            }
        elif agent.role == AgentRole.DRUG:
            return {
                "analysis": "Pharmacological considerations",
                "confidence": 0.7,
                "drug_interactions": [],
                "evidence": ["No contraindications identified"],
                "recommendation": "Standard dosing applicable",
            }
        elif agent.role == AgentRole.COMMUNICATION:
            return {
                "analysis": "Patient-friendly explanation",
                "confidence": 0.8,
                "explanation": "Your symptoms suggest several possible causes that we should investigate.",
                "next_steps": "We recommend some tests to narrow down the diagnosis.",
            }
        else:
            return {
                "analysis": "General analysis",
                "confidence": 0.5,
                "evidence": [],
            }

    def _revise_opinion(
        self,
        agent: AgentDefinition,
        objective: str,
        context: dict[str, Any],
        other_outputs: dict[str, AgentResult],
    ) -> AgentResult:
        """Allow an agent to revise its opinion based on others' outputs.

        In a full implementation, the agent receives others' outputs as
        additional context and may adjust its confidence or conclusions.

        Args:
            agent: The agent revising its opinion.
            objective: The task objective.
            context: Shared context.
            other_outputs: Other agents' current outputs.

        Returns:
            Revised AgentResult.
        """
        # For now, return the same result with slight confidence adjustment
        # based on agreement with others
        original = self._execute_agent(agent, objective, context)

        # Boost confidence if majority agrees
        if other_outputs:
            avg_other_confidence = sum(
                r.confidence for r in other_outputs.values()
            ) / len(other_outputs)

            if abs(original.confidence - avg_other_confidence) < 0.15:
                # Close agreement — boost confidence
                original.confidence = min(original.confidence + 0.05, 0.98)

        return original

    def _check_convergence(self, results: dict[str, AgentResult]) -> bool:
        """Check if agents have converged to consensus.

        Convergence is defined as all agents having confidence within
        a narrow band (< 0.1 spread).

        Args:
            results: Current agent results.

        Returns:
            True if convergence achieved.
        """
        if len(results) < 2:
            return True

        confidences = [r.confidence for r in results.values()]
        spread = max(confidences) - min(confidences)
        return spread < 0.1

    def _aggregate_results(
        self,
        results: dict[str, AgentResult],
        rounds: int,
    ) -> ConsensusResult:
        """Aggregate agent results into a consensus result.

        Uses weighted voting based on agent confidence and role expertise.

        Args:
            results: All agent results.
            rounds: Number of consensus rounds completed.

        Returns:
            ConsensusResult with aggregated output.
        """
        if not results:
            return ConsensusResult(
                final_diagnosis="No agent outputs available",
                confidence=0.0,
                escalation_needed=True,
            )

        # Sort by confidence
        sorted_results = sorted(
            results.values(), key=lambda r: r.confidence, reverse=True
        )

        top_result = sorted_results[0]

        # Build consensus diagnosis from top agent
        diagnosis = ""
        if isinstance(top_result.output, dict):
            diagnosis = top_result.output.get(
                "analysis", top_result.output.get("diagnosis", str(top_result.output))
            )
        else:
            diagnosis = str(top_result.output)

        # Collect disagreements
        disagreements = []
        for result in sorted_results[1:]:
            if result.confidence > 0.5 and result.agent_role != AgentRole.COMMUNICATION:
                if isinstance(result.output, dict):
                    agent_view = result.output.get("analysis", "")
                else:
                    agent_view = str(result.output)
                disagreements.append(f"[{result.agent_name}]: {agent_view}")

        # Aggregate evidence
        evidence = []
        for result in results.values():
            evidence.extend(result.evidence)

        # Determine if escalation needed
        avg_confidence = sum(r.confidence for r in results.values()) / len(results)
        escalation_needed = avg_confidence < 0.5 or len(disagreements) > len(results) // 2

        return ConsensusResult(
            final_diagnosis=diagnosis,
            confidence=avg_confidence,
            agent_results=results,
            consensus_rounds=rounds,
            disagreements=disagreements,
            evidence_summary=evidence,
            escalation_needed=escalation_needed,
        )

    @property
    def agent_count(self) -> int:
        """Number of registered agents."""
        return len(self._agents)

    @property
    def agents(self) -> dict[str, AgentDefinition]:
        """Copy of registered agents."""
        return dict(self._agents)

    @property
    def execution_log(self) -> list[dict[str, Any]]:
        """Execution history."""
        return list(self._execution_log)

    def clear(self) -> None:
        """Remove all agents and clear execution log."""
        self._agents.clear()
        self._execution_log.clear()
