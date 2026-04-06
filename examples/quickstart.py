"""
Quick Start — 5行代码启动诊断Harness。
"""

from openclaw_medical_harness import DiagnosisHarness

# 创建诊断Harness（神经内科方向）
harness = DiagnosisHarness(model_provider="mimo", specialty="neurology")

# 执行诊断
result = harness.execute({
    "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
    "patient_history": {"age": 35, "sex": "F"},
})

# 查看结果
print(f"诊断: {result['diagnosis']}")
print(f"置信度: {result['confidence']:.2f}")
print(f"下一步: {result['next_steps']}")
