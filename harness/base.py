"""Harness base class — the abstract layer all medical Harnesses extend.

Harness = Tool Chain + Information Format + Context Management
        + Failure Recovery + Result Validation + Checkpoint/Rollback

Core philosophy: The model is swappable; the Harness is proprietary.
A well-designed Harness outperforms a better model with a poor Harness.

v2 additions:
  - Pre-execution parameter validation (checkpoint gate)
  - Rollback mechanism on tool chain failure
  - Dry-run preview mode
"""

from __future__ import annotations

import copy
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class HarnessStatus(str, Enum):
    """Execution status of a Harness run."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    RECOVERED = "recovered"


@dataclass
class HarnessMetrics:
    """Metrics collected during Harness execution."""

    execution_time_ms: float = 0.0
    tools_called: int = 0
    tools_succeeded: int = 0
    context_tokens_used: int = 0
    recovery_attempts: int = 0
    validation_score: float = 0.0


@dataclass
class HarnessResult:
    """Structured result from a Harness execution.

    Attributes:
        output: The validated output data from the Harness.
        harness_name: Name of the Harness that produced this result.
        status: Overall execution status.
        metrics: Performance and reliability metrics.
        metadata: Additional context-specific metadata.
    """

    output: Any = None
    harness_name: str = ""
    status: HarnessStatus = HarnessStatus.SUCCESS
    metrics: HarnessMetrics = field(default_factory=HarnessMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolBase(ABC):
    """Abstract base class for tools usable within a Harness.

    Tools are the atomic units of action within a Harness. Each tool
    receives the current context and results from previously executed
    tools, enabling sequential dependency chains.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        return ""

    @abstractmethod
    def execute(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the tool with the given context and prior results.

        Args:
            context: The current Harness context (built by ContextManager).
            prior_results: Results from tools executed earlier in the chain.

        Returns:
            A dict containing this tool's output data.
        """
        ...

    def rollback(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
        own_result: dict[str, Any],
    ) -> RollbackResult:
        """Rollback this tool's side effects after a downstream failure.

        Override in subclasses that have side effects (DB writes, API calls).
        Default implementation is a no-op.

        Args:
            context: The current Harness context.
            prior_results: Results from tools executed before this one.
            own_result: This tool's own execute() result.

        Returns:
            RollbackResult indicating success/failure of rollback.
        """
        return RollbackResult(
            tool_name=self.name,
            rolled_back=True,
            message=f"No rollback needed for {self.name} (no-op)",
        )


class CheckpointError(Exception):
    """Raised when a pre-execution checkpoint fails (bad params, missing required fields)."""

    def __init__(self, message: str, checkpoint_name: str = "", details: dict[str, Any] | None = None):
        self.checkpoint_name = checkpoint_name
        self.details = details or {}
        super().__init__(f"Checkpoint '{checkpoint_name}' failed: {message}")


class ToolExecutionError(Exception):
    """Raised when a tool fails during execution."""

    def __init__(self, tool_name: str, message: str, recoverable: bool = True):
        self.tool_name = tool_name
        self.recoverable = recoverable
        super().__init__(f"Tool '{tool_name}' failed: {message}")


@dataclass
class RollbackResult:
    """Result of a rollback operation."""

    tool_name: str = ""
    rolled_back: bool = False
    message: str = ""


@dataclass
class DryRunPlan:
    """Preview of what the Harness would do in a real execution."""

    harness_name: str = ""
    domain: str = ""
    input_summary: dict[str, Any] = field(default_factory=dict)
    tool_chain_preview: list[dict[str, Any]] = field(default_factory=list)
    context_preview: dict[str, Any] = field(default_factory=dict)
    checkpoint_results: list[dict[str, Any]] = field(default_factory=list)
    estimated_tools: int = 0


class ModelProviderBase(ABC):
    """Abstract base for model providers (pluggable backends).

    The model is the most replaceable component of the Harness.
    This interface allows swapping between Mimo, GPT-4, Claude,
    or any other LLM provider without changing the Harness logic.
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the model.

        Args:
            prompt: The formatted prompt string.
            **kwargs: Provider-specific parameters.

        Returns:
            The model's text response.
        """
        ...


class BaseHarness(ABC):
    """Base class for all medical Harnesses.

    A Harness encapsulates:
      1. Tool chain — ordered sequence of tools to call
      2. Information format — how context is structured and compressed
      3. Context management — building, compressing, and passing context
      4. Failure recovery — automatic escalation on failure
      5. Result validation — domain-specific output verification
      6. Checkpoint gates — pre-execution parameter validation
      7. Rollback — reverse side effects on downstream failure
      8. Dry-run — preview execution plan without running tools

    The core insight: models are interchangeable, Harnesses are proprietary.
    Investing in Harness design yields more returns than model upgrades.

    Attributes:
        name: Unique name for this Harness instance.
        model_provider: The LLM backend (default: "mimo").
        tools: Ordered list of ToolBase instances to execute.
        context_config: Configuration for the ContextManager.
        recovery_strategy: Strategy for handling failures.
    """

    def __init__(
        self,
        name: str,
        model_provider: str | ModelProviderBase = "mimo",
        tools: list[ToolBase] | None = None,
        context_config: Any | None = None,
        recovery_strategy: Any = None,
    ) -> None:
        from harness.context import ContextManager, ContextConfig
        from harness.recovery import FailureRecovery, RecoveryStrategy

        self.name = name
        self._model_provider_str = (
            model_provider if isinstance(model_provider, str) else "custom"
        )
        self._model_provider = model_provider
        self.tools: list[ToolBase] = tools or []
        self.context = ContextManager(context_config or ContextConfig())
        self.recovery = FailureRecovery(
            strategy=recovery_strategy or RecoveryStrategy.ESCALATE
        )
        from harness.validator import ResultValidator
        self.validator = ResultValidator()

    # ── Checkpoint 1: Pre-execution parameter validation ─────────────

    def validate_input(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate input data before execution.

        Override in subclasses for domain-specific checks.
        Default checks:
          - input_data must be a non-empty dict
          - must not contain None values for required keys

        Returns:
            List of checkpoint results, each with keys:
              name, passed, message, details
        """
        results: list[dict[str, Any]] = []

        # Check 1: input is a dict
        results.append({
            "name": "input_type",
            "passed": isinstance(input_data, dict),
            "message": "Input must be a dict",
            "details": {"type": type(input_data).__name__},
        })

        # Check 2: not empty
        results.append({
            "name": "input_non_empty",
            "passed": bool(input_data),
            "message": "Input data must not be empty",
            "details": {"keys": list(input_data.keys()) if isinstance(input_data, dict) else []},
        })

        # Check 3: no None values
        none_keys = [k for k, v in input_data.items() if v is None] if isinstance(input_data, dict) else []
        results.append({
            "name": "no_none_values",
            "passed": len(none_keys) == 0,
            "message": f"Keys with None values: {none_keys}" if none_keys else "No None values",
            "details": {"none_keys": none_keys},
        })

        return results

    def _run_checkpoints(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Run all pre-execution checkpoints.

        Raises CheckpointError if any checkpoint fails.
        """
        results = self.validate_input(input_data)
        failed = [r for r in results if not r["passed"]]
        if failed:
            first = failed[0]
            raise CheckpointError(
                message=first["message"],
                checkpoint_name=first["name"],
                details=first.get("details", {}),
            )
        return results

    # ── Checkpoint 2: Dry-run preview ───────────────────────────────

    def dry_run(self, input_data: dict[str, Any]) -> DryRunPlan:
        """Preview what the Harness would do without executing tools.

        Useful for debugging and parameter confirmation.

        Args:
            input_data: Raw input dict.

        Returns:
            DryRunPlan with execution preview.
        """
        # Validate first
        checkpoint_results = self.validate_input(input_data)

        # Build context preview (without side effects)
        ctx = self.context.build(input_data)
        ctx_preview = {
            "stage": ctx.get("stage"),
            "input_keys": list(ctx.get("input", {}).keys()),
            "has_critical_items": bool(ctx.get("critical_items")),
            "history_depth": len(ctx.get("history", [])),
        }

        # Tool chain preview
        tool_preview = []
        for tool in self.tools:
            tool_preview.append({
                "order": len(tool_preview) + 1,
                "name": tool.name,
                "description": tool.description,
                "has_rollback": type(tool).rollback is not ToolBase.rollback,
            })

        return DryRunPlan(
            harness_name=self.name,
            domain=self._domain(),
            input_summary={k: type(v).__name__ for k, v in input_data.items()},
            tool_chain_preview=tool_preview,
            context_preview=ctx_preview,
            checkpoint_results=checkpoint_results,
            estimated_tools=len(self.tools),
        )

    # ── Main execution ───────────────────────────────────────────────

    def execute(
        self,
        input_data: dict[str, Any],
        *,
        dry_run: bool = False,
    ) -> HarnessResult:
        """Execute the full Harness pipeline.

        Pipeline stages:
          0. Checkpoint — validate input parameters (gate)
          1. Context build — structure input into Harness context
          2. Tool chain — execute tools in order with dependency passing
          3. Model reasoning — generate insights from tool results
          4. Validation — verify output meets domain standards
          5. Recovery — handle failures with escalation if needed

        Args:
            input_data: Raw input dict (symptoms, patient data, etc.)
            dry_run: If True, return a preview plan without executing tools.

        Returns:
            HarnessResult with validated output and execution metrics.
            In dry_run mode, output contains the DryRunPlan.
        """
        # Stage 0: Checkpoint gate
        self._run_checkpoints(input_data)

        # Dry-run: return preview only
        if dry_run:
            plan = self.dry_run(input_data)
            return HarnessResult(
                output=plan,
                harness_name=self.name,
                status=HarnessStatus.SUCCESS,
                metadata={"mode": "dry_run", "domain": self._domain()},
            )

        start_time = time.monotonic()
        metrics = HarnessMetrics()

        # Stage 1: Context construction
        ctx = self.context.build(input_data)

        # Stage 2: Tool chain execution (with rollback on failure)
        tool_results = self._chain_tools_with_rollback(ctx, metrics)

        # Stage 3: Model reasoning (Harness-wrapped)
        reasoning = self._reason(ctx, tool_results)

        # Stage 4: Result validation
        validated = self.validator.validate(reasoning, domain=self._domain())
        metrics.validation_score = validated.score

        # Stage 5: Failure recovery
        if not validated.passed:
            metrics.recovery_attempts += 1
            recovery_result = self.recovery.recover(ctx, validated, tool_results)
            if recovery_result.recovered:
                validated = recovery_result.validation
                status = HarnessStatus.RECOVERED
            else:
                status = HarnessStatus.FAILED
        else:
            status = HarnessStatus.SUCCESS

        metrics.execution_time_ms = (time.monotonic() - start_time) * 1000

        return HarnessResult(
            output=validated,
            harness_name=self.name,
            status=status,
            metrics=metrics,
            metadata={"domain": self._domain(), "model": self._model_provider_str},
        )

    def add_tool(self, tool: ToolBase) -> None:
        """Register a tool to this Harness's tool chain."""
        self.tools.append(tool)

    # ── Tool chain with rollback ─────────────────────────────────────

    def _chain_tools_with_rollback(
        self,
        context: dict[str, Any],
        metrics: HarnessMetrics,
    ) -> dict[str, Any]:
        """Execute tool chain with rollback on non-recoverable failure.

        When a tool fails non-recoverably, all previously executed tools
        that support rollback are rolled back in reverse order.
        """
        results: dict[str, Any] = {}
        executed: list[tuple[ToolBase, dict[str, Any]]] = []

        for tool in self.tools:
            metrics.tools_called += 1
            try:
                result = tool.execute(context, results)
                results[tool.name] = result
                executed.append((tool, result))
                metrics.tools_succeeded += 1
            except ToolExecutionError as exc:
                if exc.recoverable:
                    results[tool.name] = {"error": str(exc), "recoverable": True}
                    continue
                # Non-recoverable: trigger rollback
                logger.warning(
                    "Tool '%s' failed non-recoverably, initiating rollback (%d tools)",
                    exc.tool_name, len(executed),
                )
                rollback_log = self._rollback_executed(context, executed, results)
                results["_rollback_log"] = rollback_log
                raise

        return results

    def _rollback_executed(
        self,
        context: dict[str, Any],
        executed: list[tuple[ToolBase, dict[str, Any]]],
        results: dict[str, Any],
    ) -> list[RollbackResult]:
        """Rollback executed tools in reverse order."""
        rollback_log: list[RollbackResult] = []
        for tool, own_result in reversed(executed):
            prior = {k: v for k, v in results.items() if k != tool.name}
            try:
                rb = tool.rollback(context, prior, own_result)
                rollback_log.append(rb)
                logger.info("Rollback %s: %s", tool.name, rb.message)
            except Exception as exc:
                rb = RollbackResult(
                    tool_name=tool.name,
                    rolled_back=False,
                    message=f"Rollback failed: {exc}",
                )
                rollback_log.append(rb)
                logger.error("Rollback failed for %s: %s", tool.name, exc)
        return rollback_log

    # ── Legacy: kept for backward compat, now calls with-rollback version ──

    def _chain_tools(
        self,
        context: dict[str, Any],
        metrics: HarnessMetrics,
    ) -> dict[str, Any]:
        """Legacy tool chain execution (no rollback). Prefer _chain_tools_with_rollback."""
        return self._chain_tools_with_rollback(context, metrics)

    # ── Reasoning ────────────────────────────────────────────────────

    def _reason(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        """Perform model reasoning with Harness-structured prompt."""
        prompt = self._build_prompt(context, tool_results)
        if isinstance(self._model_provider, str):
            return self._default_reasoning(prompt)
        return self._model_provider.generate(prompt)

    def _default_reasoning(self, prompt: str) -> str:
        """Default reasoning stub when no real model provider is configured."""
        return f"[Harness:{self.name}] Model reasoning placeholder. Prompt length: {len(prompt)}"

    @abstractmethod
    def _build_prompt(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        """Build a domain-specific prompt from context and tool results."""
        ...

    @abstractmethod
    def _domain(self) -> str:
        """Return the domain identifier for this Harness."""
        ...



