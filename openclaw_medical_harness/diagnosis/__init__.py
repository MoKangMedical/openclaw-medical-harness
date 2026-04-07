"""
Diagnosis Harness — 诊断Harness。

Harness流程：
症状输入 → 分层鉴别 → 检查策略 → 确诊路径

支持：
- 罕见病专项诊断（MG/SMA/DMD/ALS/PKU等）
- 多学科会诊编排
- 临床指南约束
"""

from .diagnostic_harness import (
    DiagnosisHarness,
    DiagnosticResult,
    DifferentialDiagnosis,
)

__all__ = ["DiagnosisHarness", "DiagnosticResult", "DifferentialDiagnosis"]
