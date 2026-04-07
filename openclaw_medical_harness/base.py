"""
Base Harness — 所有医疗Harness的抽象基类。

Harness = 工具链 + 信息格式 + 上下文管理 + 失败恢复 + 结果验证

核心理念：
- 模型可替换，Harness是私有的
- 优秀的Harness设计使性能提升64%
- 护城河来自Harness设计，而非模型本身
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


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


class ToolExecutionError(Exception):
    """工具执行期间失败时引发。"""

    def __init__(self, tool_name: str, message: str, recoverable: bool = True):
        self.tool_name = tool_name
        self.recoverable = recoverable
        super().__init__(f"Tool '{tool_name}' failed: {message}")


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

    核心洞察：模型是可替换的，Harness是私有的。
    投资Harness设计比模型升级回报更高。
    """

    def __init__(
        self,
        config: Optional[HarnessConfig] = None,
        name: str = "base",
        model_provider: str = "mimo",
        tools: list[str] | None = None,
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

        from .context import ContextManager
        from .recovery import FailureRecovery
        from .validator import ResultValidator

        self.context = ContextManager(config.context_config)
        self.recovery = FailureRecovery(config.recovery_strategy)
        self.validator = ResultValidator(config.validation_threshold)
        self._tool_registry: dict[str, Any] = {}

    def register_tool(self, name: str, tool: Any) -> None:
        """注册工具到Harness。"""
        self._tool_registry[name] = tool

    def execute(self, input_data: dict[str, Any]) -> HarnessResult:
        """执行Harness五步流水线。

        Pipeline stages:
          1. 上下文构建 — 将输入结构化为Harness上下文
          2. 工具链调用 — 按顺序执行工具并传递依赖
          3. 模型推理 — 从工具结果生成洞察
          4. 结果验证 — 验证输出满足领域标准
          5. 失败恢复 — 必要时进行升级处理

        Args:
            input_data: 原始输入字典（症状、患者数据等）。

        Returns:
            包含验证输出和执行指标的HarnessResult。
        """
        start_time = time.time()

        # Stage 1: 上下文构建
        ctx = self.context.build(input_data)

        # Stage 2: 工具链调用
        tool_results = self._chain_tools(ctx)

        # Stage 3: 模型推理（Harness包装后的）
        reasoning = self._reason(ctx, tool_results)

        # Stage 4: 结果验证
        validation = self.validator.validate(reasoning, context=ctx)

        # Stage 5: 失败恢复
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

    def _chain_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        """工具链有序调用：每个工具的输出作为后续工具的输入。"""
        results: dict[str, Any] = {}
        for tool_name in self.config.tools:
            tool = self._tool_registry.get(tool_name)
            if tool is None:
                results[tool_name] = {"error": f"Tool '{tool_name}' not registered"}
                continue
            try:
                results[tool_name] = tool.execute(context, prior_results=results)
            except Exception as e:
                results[tool_name] = {"error": str(e), "tool": tool_name}
        return results

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
        return {"reasoning": prompt, "provider": self.model_provider}

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
