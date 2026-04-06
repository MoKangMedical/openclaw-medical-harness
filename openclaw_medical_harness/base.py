"""
Base Harness — 所有医疗Harness的抽象基类。

Harness = 工具链 + 信息格式 + 上下文管理 + 失败恢复 + 结果验证
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from .context import ContextManager
from .recovery import FailureRecovery, RecoveryStrategy
from .validator import ResultValidator, ValidationResult


@dataclass
class HarnessResult:
    """Harness执行结果。"""
    output: Any
    harness_name: str
    confidence: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)
    validation: Optional[ValidationResult] = None
    recovery_applied: bool = False
    execution_time_ms: float = 0.0
    tool_chain_results: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.validation is not None and self.validation.passed


@dataclass
class HarnessConfig:
    """Harness配置。"""
    name: str
    model_provider: str = "mimo"
    tools: list[str] = field(default_factory=list)
    context_config: dict[str, Any] = field(default_factory=dict)
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.ESCALATE
    validation_threshold: float = 0.7
    max_retries: int = 3
    timeout_seconds: float = 30.0


class BaseHarness(ABC):
    """
    Harness基类：所有医疗Harness的抽象层。

    Harness = 工具链 + 信息格式 + 上下文管理 + 失败恢复 + 结果验证

    核心理念：
    - 模型可替换，Harness是私有的
    - 优秀的Harness设计使性能提升64%
    - 护城河来自Harness设计，而非模型本身
    """

    def __init__(
        self,
        config: Optional[HarnessConfig] = None,
        name: str = "base",
        model_provider: str = "mimo",
        tools: list[str] | None = None,
    ):
        if config is None:
            config = HarnessConfig(
                name=name,
                model_provider=model_provider,
                tools=tools or [],
            )
        self.config = config
        self.name = config.name
        self.model_provider = config.model_provider
        self.context = ContextManager(config.context_config)
        self.recovery = FailureRecovery(config.recovery_strategy)
        self.validator = ResultValidator(config.validation_threshold)
        self._tool_registry: dict[str, Any] = {}

    def register_tool(self, name: str, tool: Any) -> None:
        """注册工具到Harness。"""
        self._tool_registry[name] = tool

    def execute(self, input_data: dict[str, Any]) -> HarnessResult:
        """
        执行Harness流程。

        五步流水线：
        1. 上下文构建
        2. 工具链调用
        3. 模型推理
        4. 结果验证
        5. 失败恢复（如需要）
        """
        start_time = time.time()

        # Step 1: 上下文构建
        ctx = self.context.build(input_data)
        self._log_step("context_built", ctx)

        # Step 2: 工具链调用
        tool_results = self._chain_tools(ctx)
        self._log_step("tools_executed", tool_results)

        # Step 3: 模型推理（Harness包装后的）
        reasoning = self._reason(ctx, tool_results)
        self._log_step("reasoning_completed", reasoning)

        # Step 4: 结果验证
        validation = self.validator.validate(reasoning, context=ctx)
        self._log_step("validation_completed", validation)

        # Step 5: 失败恢复
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
            metrics=self._metrics(ctx, tool_results, elapsed),
            validation=validation,
            recovery_applied=recovery_applied,
            execution_time_ms=elapsed,
            tool_chain_results=tool_results,
        )

    def _chain_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        """工具链有序调用：每个工具的输出作为后续工具的输入。"""
        results = {}
        for tool_name in self.config.tools:
            tool = self._tool_registry.get(tool_name)
            if tool is None:
                results[tool_name] = {"error": f"Tool '{tool_name}' not registered"}
                continue
            try:
                results[tool_name] = tool.execute(context, previous_results=results)
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

    def _build_prompt(
        self,
        context: dict[str, Any],
        tool_results: dict[str, Any],
    ) -> str:
        """构建推理Prompt。子类应覆盖此方法。"""
        raise NotImplementedError("Subclasses must implement _build_prompt")

    def _call_model(self, prompt: str) -> dict[str, Any]:
        """调用模型进行推理。支持MIMO/Ollama/Claude等。"""
        # 实际实现通过模型适配器调用
        return {"reasoning": prompt, "provider": self.model_provider}

    @abstractmethod
    def _metrics(
        self,
        context: dict[str, Any] | None = None,
        tool_results: dict[str, Any] | None = None,
        elapsed_ms: float = 0.0,
    ) -> dict[str, Any]:
        """返回Harness执行指标。子类必须实现。"""
        ...

    def _log_step(self, step: str, data: Any) -> None:
        """记录执行步骤（可配置日志级别）。"""
        pass
