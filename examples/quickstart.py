"""
Quick Start — OpenClaw-Medical-Harness 快速入门。

运行方式：
    export MIMO_API_KEY="sk-your-key"
    python examples/quickstart.py
"""

import os
from openclaw_medical_harness import DiagnosisHarness


def main():
    # 确保API Key已设置
    if not os.getenv("MIMO_API_KEY"):
        print("⚠️  请先设置 MIMO_API_KEY 环境变量")
        print("   export MIMO_API_KEY='sk-your-key'")
        return

    # 创建诊断Harness（自动使用MIMO模型）
    harness = DiagnosisHarness(specialty="neurology")

    # 执行诊断
    print("🏥 诊断Harness — 罕见病鉴别诊断\n")
    result = harness.execute({
        "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
        "patient": {"age": 35, "sex": "F"},
    })

    print(f"📋 诊断结果：{result['diagnosis']}")
    print(f"📊 置信度：{result['confidence']:.2f}")
    print(f"🔬 下一步检查：{', '.join(result['next_steps'])}")
    print(f"⏱️  执行时间：{result['execution_time_ms']:.0f}ms")


if __name__ == "__main__":
    main()
