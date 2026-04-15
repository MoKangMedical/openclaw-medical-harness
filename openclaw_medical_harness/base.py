"""
Base Harness — 所有医疗Harness的抽象基类。

Harness = 工具链 + 信息格式 + 上下文管理 + 失败恢复 + 结果验证

核心理念：
- 模型可替换，Harness是私有的
- 优秀的Harness设计使性能提升64%
- 护城河来自Harness设计，而非模型本身
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class HarnessStatus(str, Enum):
    """Harness执行状态。"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    RECOVERED = "recovered"


@dataclass
class HarnessMetrics:
    """Harness执行指标。"""
    execution_time_ms: float = 0.0
    tools_called: int = 0
    tools_succeeded: int = 0
    context_tokens_used: int = 0
    recovery_attempts: int = 0
    validation_score: float = 0.0


@dataclass
class HarnessResult:
    """Harness执行结果。

    Attributes:
        output: Harness的验证输出数据。
        harness_name: 产生此结果的Harness名称。
        status: 整体执行状态。
        metrics: 性能和可靠性指标。
        metadata: 额外的上下文元数据。
    """
    output: Any = None
    harness_name: str = ""
    status: HarnessStatus = HarnessStatus.SUCCESS
    confidence: float = 0.0
    metrics: HarnessMetrics = field(default_factory=HarnessMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    recovery_applied: bool = False
    tool_chain_results: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status in (HarnessStatus.SUCCESS, HarnessStatus.RECOVERED)


@dataclass
class HarnessConfig:
    """Harness配置。

    Attributes:
        name: Harness实例的唯一名称。
        model_provider: LLM后端（默认: mimo）。
        tools: 要执行的工具名称列表。
        recovery_strategy: 失败时的恢复策略。
        validation_threshold: 结果验证阈值。
        max_retries: 最大重试次数。
        timeout_seconds: 执行超时时间。
    """
    name: str
    model_provider: str = "mimo"
    tools: list[str] = field(default_factory=list)
    context_config: dict[str, Any] = field(default_factory=dict)
    recovery_strategy: str = "escalate"
    validation_threshold: float = 0.7
    max_retries: int = 3
    timeout_seconds: float = 30.0


@dataclass
class ToolExecutionRecord:
    """工具执行记录，用于检查点和回滚。

    Attributes:
        tool_name: 工具名称。
        timestamp: 执行时间戳。
        result: 工具执行结果。
        rolled_back: 是否已回滚。
        rollback_fn: 回滚回调函数。
    """
    tool_name: str = ""
    timestamp: float = 0.0
    result: dict[str, Any] = field(default_factory=dict)
    rolled_back: bool = False
    rollback_fn: Optional[Callable[[dict[str, Any]], None]] = None


class ToolBase(ABC):
    """Harness中可使用的工具的抽象基类。

    工具是Harness中原子操作单元。每个工具接收当前上下文和
    先前已执行工具的结果，支持顺序依赖链。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具的唯一标识符。"""
        ...

    @property
    def description(self) -> str:
        """工具功能的人类可读描述。"""
        return ""

    @abstractmethod
    def execute(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """使用给定上下文和先前结果执行工具。

        Args:
            context: 当前Harness上下文（由ContextManager构建）。
            prior_results: 链中先前执行工具的结果。

        Returns:
            包含此工具输出数据的字典。
        """
        ...


class CheckpointError(Exception):
    """预执行检查点失败时引发（参数错误、缺少必需字段等）。"""

    def __init__(self, message: str, checkpoint_name: str = "", details: dict[str, Any] | None = None):
        self.checkpoint_name = checkpoint_name
        self.details = details or {}
        super().__init__(f"Checkpoint '{checkpoint_name}' failed: {message}")


class ToolExecutionError(Exception):
    """工具执行期间失败时引发。"""

    def __init__(self, tool_name: str, message: str, recoverable: bool = True):
        self.tool_name = tool_name
        self.recoverable = recoverable
        super().__init__(f"Tool '{tool_name}' failed: {message}")


@dataclass
class DryRunPlan:
    """Harness执行预览（dry-run模式）。"""

    harness_name: str = ""
    domain: str = ""
    input_summary: dict[str, Any] = field(default_factory=dict)
    tool_chain_preview: list[dict[str, Any]] = field(default_factory=list)
    context_preview: dict[str, Any] = field(default_factory=dict)
    checkpoint_results: list[dict[str, Any]] = field(default_factory=list)
    estimated_tools: int = 0


class ModelProviderBase(ABC):
    """模型提供者的抽象基类（可插拔后端）。

    模型是Harness中最可替换的组件。
    此接口允许在Mimo、GPT-4、Claude或任何其他LLM提供者之间切换，
    而不更改Harness逻辑。
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """从模型生成响应。

        Args:
            prompt: 格式化的提示字符串。
            **kwargs: 提供者特定的参数。

        Returns:
            模型的文本响应。
        """
        ...

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """生成并解析JSON。"""
        import json
        text = self.generate(prompt, **kwargs)
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"raw_text": text}


class BaseHarness(ABC):
    """
    Harness基类：所有医疗Harness的抽象层。

    Harness = 工具链 + 信息格式 + 上下文管理 + 失败恢复 + 结果验证

    一个Harness封装：
      1. 工具链 — 要调用的有序工具序列
      2. 信息格式 — 上下文如何结构化和压缩
      3. 上下文管理 — 构建、压缩和传递上下文
      4. 失败恢复 — 失败时自动升级
      5. 结果验证 — 领域特定的输出验证
      6. 决策检查点 — 执行前参数确认、工具结果确认
      7. 回滚机制 — 工具链失败时逆序回滚副作用
      8. Dry-run预览 — 不执行工具，预览执行计划

    核心洞察：模型是可替换的，Harness是私有的。
    投资Harness设计比模型升级回报更高。
    """

    def __init__(
        self,
        config: Optional[HarnessConfig] = None,
        name: str = "base",
        model_provider: str = "mimo",
        tools: list[str] | None = None,
        checkpoint_fn: Optional[Callable[[str, dict[str, Any]], bool]] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = HarnessConfig(
                name=name,
                model_provider=model_provider,
                tools=tools or [],
            )
        self.config = config
        self.name = config.name
        self.model_provider = config.model_provider
        self.checkpoint_fn = checkpoint_fn

        from .context import ContextManager
        from .recovery import FailureRecovery
        from .validator import ResultValidator

        self.context = ContextManager(config.context_config)
        self.recovery = FailureRecovery(config.recovery_strategy)
        self.validator = ResultValidator(config.validation_threshold)
        self._tool_registry: dict[str, Any] = {}
        self._tool_executions: list[ToolExecutionRecord] = []

        # 模型提供者：支持传入实例或自动创建
        self._model_provider_instance = None
        provider_arg = kwargs.get("provider")
        if provider_arg is not None:
            if hasattr(provider_arg, "generate"):
                # 已是ModelProvider实例
                self._model_provider_instance = provider_arg
            elif isinstance(provider_arg, str):
                from .providers import create_provider
                self._model_provider_instance = create_provider(provider_arg)
        elif self.model_provider == "mimo":
            # 默认尝试创建MIMO provider（从环境变量读key）
            import os
            if os.getenv("MIMO_API_KEY"):
                from .providers import MIMOProvider
                self._model_provider_instance = MIMOProvider()

    def register_tool(self, name: str, tool: Any) -> None:
        """注册工具到Harness。"""
        self._tool_registry[name] = tool

    # ── 决策检查点 1: 预执行参数验证 ─────────────────────────────────

    def validate_input(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """预执行检查点：验证输入参数。

        子类可覆盖以添加领域特定检查。默认检查：
          - input_data 必须是非空字典
          - 值不能为 None

        Returns:
            检查结果列表，每项含 name, passed, message, details
        """
        results: list[dict[str, Any]] = []

        # 检查 1: 类型必须为 dict
        results.append({
            "name": "input_type",
            "passed": isinstance(input_data, dict),
            "message": "输入必须为字典类型",
            "details": {"type": type(input_data).__name__},
        })

        # 检查 2: 非空
        results.append({
            "name": "input_non_empty",
            "passed": bool(input_data),
            "message": "输入数据不能为空",
            "details": {"keys": list(input_data.keys()) if isinstance(input_data, dict) else []},
        })

        # 检查 3: 无 None 值
        none_keys = [k for k, v in input_data.items() if v is None] if isinstance(input_data, dict) else []
        results.append({
            "name": "no_none_values",
            "passed": len(none_keys) == 0,
            "message": f"以下键的值为None: {none_keys}" if none_keys else "无None值",
            "details": {"none_keys": none_keys},
        })

        return results

    def _run_input_checkpoints(self, input_data: dict[str, Any]) -> None:
        """执行预执行检查点，失败则抛出 CheckpointError。"""
        results = self.validate_input(input_data)
        failed = [r for r in results if not r["passed"]]
        if failed:
            first = failed[0]
            raise CheckpointError(
                message=first["message"],
                checkpoint_name=first["name"],
                details=first.get("details", {}),
            )

    # ── 决策检查点 2: Dry-run 预览 ───────────────────────────────────

    def dry_run(self, input_data: dict[str, Any]) -> DryRunPlan:
        """预览Harness将执行的操作（不实际执行工具）。

        用于参数确认和调试。

        Args:
            input_data: 原始输入数据。

        Returns:
            DryRunPlan 包含执行预览信息。
        """
        # 先做参数验证
        checkpoint_results = self.validate_input(input_data)

        # 构建上下文预览（不产生副作用）
        ctx = self.context.build(input_data)
        ctx_preview = {
            "stage": ctx.get("stage"),
            "input_keys": list(ctx.get("input", {}).keys()),
            "has_critical_items": bool(ctx.get("critical_items")),
            "history_depth": len(ctx.get("history", [])),
        }

        # 工具链预览
        tool_preview = []
        for tool_name in self.config.tools:
            tool = self._tool_registry.get(tool_name)
            tool_preview.append({
                "order": len(tool_preview) + 1,
                "name": tool_name,
                "registered": tool is not None,
                "has_rollback": hasattr(tool, "rollback") if tool else False,
            })

        return DryRunPlan(
            harness_name=self.name,
            domain=self._domain(),
            input_summary={k: type(v).__name__ for k, v in input_data.items()},
            tool_chain_preview=tool_preview,
            context_preview=ctx_preview,
            checkpoint_results=checkpoint_results,
            estimated_tools=len(self.config.tools),
        )

    # ── 主执行流程 ───────────────────────────────────────────────────

    def execute(self, input_data: dict[str, Any], *, dry_run: bool = False) -> HarnessResult:
        """执行Harness流水线（含三重决策检查点）。

        Pipeline stages:
          0. 检查点 — 输入参数验证（gate，失败则拒绝执行）
          1. 上下文构建 — 将输入结构化为Harness上下文
          2. 检查点 — 上下文确认
          3. 工具链调用 — 按顺序执行工具并传递依赖
          4. 检查点 — 工具结果确认（失败则回滚）
          5. 模型推理 — 从工具结果生成洞察
          6. 结果验证 — 验证输出满足领域标准
          7. 失败恢复 — 必要时进行升级处理

        Args:
            input_data: 原始输入字典（症状、患者数据等）。
            dry_run: 若为True，返回执行预览而不实际运行工具。

        Returns:
            包含验证输出和执行指标的HarnessResult。
            dry_run模式下，output包含DryRunPlan。
        """
        # Stage 0: 输入参数检查点
        self._run_input_checkpoints(input_data)

        # Dry-run: 仅返回预览
        if dry_run:
            plan = self.dry_run(input_data)
            logger.info("[DRY-RUN] Harness '%s' preview: %d tools, domain=%s",
                        self.name, plan.estimated_tools, self._domain())
            return HarnessResult(
                output=plan,
                harness_name=self.name,
                status=HarnessStatus.SUCCESS,
                metadata={"mode": "dry_run", "domain": self._domain()},
            )

        start_time = time.time()
        self._tool_executions = []

        # 决策检查点: 执行前日志预览
        logger.info("[EXEC] Harness '%s' starting | domain=%s | tools=%s | checkpoints=3",
                    self.name, self._domain(), self.config.tools)

        # Stage 1: 上下文构建
        ctx = self.context.build(input_data)

        # Stage 2: 检查点 — 上下文确认
        if not self._run_checkpoint("context_built", ctx):
            logger.warning("[CHECKPOINT] context_rejected for harness '%s'", self.name)
            return self._rejected_result("context_rejected")
        logger.info("[CHECKPOINT] context_confirmed | keys=%s",
                    list(ctx.keys())[:8])

        # Stage 3: 工具链调用（含回滚）
        tool_results = self._chain_tools(ctx)

        # Stage 4: 检查点 — 工具结果确认
        if not self._run_checkpoint("tools_executed", {"tool_results": tool_results, **ctx}):
            logger.warning("[CHECKPOINT] tools_rejected for harness '%s' — rolling back", self.name)
            self._rollback_tools()
            return self._rejected_result("tools_rejected")
        logger.info("[CHECKPOINT] tools_confirmed | results=%d | errors=%d",
                    len(tool_results), sum(1 for v in tool_results.values() if isinstance(v, dict) and v.get("error")))

        # Stage 5: 模型推理（Harness包装后的）
        reasoning = self._reason(ctx, tool_results)

        # Stage 6: 结果验证
        validation = self.validator.validate(reasoning, context=ctx)

        # Stage 7: 失败恢复
        recovery_applied = False
        if not validation.passed:
            reasoning = self.recovery.recover(ctx, validation, self._reason)
            recovery_applied = True
            validation = self.validator.validate(reasoning, context=ctx)

        elapsed = (time.time() - start_time) * 1000

        return HarnessResult(
            output=reasoning,
            harness_name=self.name,
            confidence=validation.confidence if validation else 0.0,
            metrics=self._compute_metrics(ctx, tool_results, elapsed),
            metadata={"domain": self._domain(), "model": self.model_provider},
            execution_time_ms=elapsed,
            recovery_applied=recovery_applied,
            tool_chain_results=tool_results,
            status=HarnessStatus.SUCCESS if (validation and validation.passed) else HarnessStatus.FAILED,
        )

    def _run_checkpoint(self, stage: str, data: dict[str, Any]) -> bool:
        """执行检查点回调。

        Args:
            stage: 当前阶段名称 (context_built / tools_executed)。
            data: 当前阶段的数据。

        Returns:
            True 表示继续执行，False 表示中止。
        """
        if self.checkpoint_fn is None:
            return True
        try:
            return self.checkpoint_fn(stage, data)
        except Exception as e:
            logger.error("Checkpoint error at stage '%s': %s", stage, e)
            return False

    def _rejected_result(self, reason: str) -> HarnessResult:
        """生成被检查点拒绝的结果。"""
        return HarnessResult(
            output={"error": f"Execution rejected at checkpoint: {reason}"},
            harness_name=self.name,
            status=HarnessStatus.FAILED,
            confidence=0.0,
            metadata={"rejection_reason": reason},
        )

    def _chain_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        """工具链有序调用：每个工具的输出作为后续工具的输入。

        每个工具执行后记录到 _tool_executions，支持后续回滚。
        当工具执行失败时，自动触发已执行工具的回滚（逆序）。
        工具可通过 rollback() 方法注册回滚回调。
        """
        results: dict[str, Any] = {}
        for tool_name in self.config.tools:
            tool = self._tool_registry.get(tool_name)
            if tool is None:
                results[tool_name] = {"error": f"Tool '{tool_name}' not registered"}
                self._rollback_tools()
                return results
            try:
                result = tool.execute(context, prior_results=results)
                results[tool_name] = result
                self._record_execution(tool_name, tool, result)
                # 检查工具返回是否包含错误
                if isinstance(result, dict) and result.get("error"):
                    logger.warning("Tool '%s' returned error: %s", tool_name, result["error"])
                    self._rollback_tools()
                    return results
            except ToolExecutionError as exc:
                results[tool_name] = {"error": str(exc), "tool": tool_name, "recoverable": exc.recoverable}
                if not exc.recoverable:
                    logger.warning("Tool '%s' failed non-recoverably, rolling back", tool_name)
                    self._rollback_tools()
                    return results
            except Exception as e:
                results[tool_name] = {"error": str(e), "tool": tool_name}
                logger.warning("Tool '%s' failed unexpectedly, rolling back", tool_name)
                self._rollback_tools()
                return results
        return results

    def _record_execution(
        self, tool_name: str, tool: Any, result: dict[str, Any]
    ) -> None:
        """记录工具执行结果，便于检查点审计和回滚。"""
        rollback_fn = getattr(tool, "rollback", None)
        self._tool_executions.append(ToolExecutionRecord(
            tool_name=tool_name,
            timestamp=time.time(),
            result=result,
            rollback_fn=rollback_fn if callable(rollback_fn) else None,
        ))

    def _rollback_tools(self) -> None:
        """按逆序回滚已执行的工具（如工具提供了 rollback 回调）。"""
        for record in reversed(self._tool_executions):
            if record.rolled_back:
                continue
            if record.rollback_fn is not None:
                try:
                    record.rollback_fn(record.result)
                    record.rolled_back = True
                    logger.info("Rolled back tool '%s'", record.tool_name)
                except Exception as e:
                    logger.error("Rollback failed for tool '%s': %s", record.tool_name, e)
            record.rolled_back = True

    @property
    def tool_executions(self) -> list[ToolExecutionRecord]:
        """工具执行历史记录（只读）。"""
        return list(self._tool_executions)

    def _reason(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> dict[str, Any]:
        """模型推理（可插拔模型）。子类可覆盖以定制推理逻辑。"""
        prompt = self._build_prompt(context, tool_results)
        return self._call_model(prompt)

    def _call_model(self, prompt: str) -> dict[str, Any]:
        """调用模型进行推理。支持MIMO/Ollama/Claude等。"""
        # 尝试使用真实的模型提供者
        provider = getattr(self, "_model_provider_instance", None)
        if provider is not None:
            try:
                result = provider.generate(
                    prompt,
                    system="你是一位专业的医疗AI助手。请以JSON格式返回结构化诊断结果。",
                    temperature=0.3,
                    max_tokens=2048,
                )
                parsed = result.as_dict()
                if isinstance(parsed, dict) and "raw_text" not in parsed:
                    return parsed
                # 如果无法解析JSON，包装成dict
                return {"analysis": result.text, "provider": provider.name, "confidence": 0.6}
            except Exception as e:
                logger.warning("Model call failed, falling back to rule-based: %s", str(e))

        # 回退：返回结构化提示（用于无API Key的开发/测试）
        return {"reasoning": prompt, "provider": self.model_provider, "mode": "fallback"}

    def _compute_metrics(
        self,
        context: dict[str, Any] | None = None,
        tool_results: dict[str, Any] | None = None,
        elapsed_ms: float = 0.0,
    ) -> HarnessMetrics:
        """计算执行指标。"""
        return HarnessMetrics(
            execution_time_ms=elapsed_ms,
            tools_called=len(tool_results or {}),
            tools_succeeded=sum(1 for v in (tool_results or {}).values() if "error" not in v),
        )

    @abstractmethod
    def _build_prompt(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        """构建推理Prompt。子类必须实现。"""
        ...

    @abstractmethod
    def _domain(self) -> str:
        """返回此Harness的领域标识符。子类必须实现。"""
        ...

    def _log_step(self, step: str, data: Any) -> None:
        """记录执行步骤（可配置日志级别）。"""
        pass
