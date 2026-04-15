"""
Test MIMO API — 测试MIMO模型集成。

运行方式：
    export MIMO_API_KEY="sk-your-key"
    python examples/test_mimo.py
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openclaw_medical_harness.providers import MIMOProvider


def test_mimo_basic():
    """测试基本的MIMO API调用。"""
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        print("❌ MIMO_API_KEY 未设置")
        return False

    print(f"🔑 API Key: {api_key[:10]}...{api_key[-6:]}")

    provider = MIMOProvider(api_key=api_key)

    print("📡 测试基本调用...")
    result = provider.generate("你好，请用一句话介绍自己")
    print(f"   模型：{result.model}")
    print(f"   响应：{result.text[:100]}")
    print(f"   Tokens：{result.tokens_used}")
    print(f"   状态：{result.finish_reason}")

    if result.finish_reason == "error":
        print(f"❌ API调用失败: {result.text}")
        return False

    print("✅ 基本调用成功\n")
    return True


def test_mimo_medical():
    """测试医疗推理。"""
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        return False

    provider = MIMOProvider(api_key=api_key)

    print("🏥 测试医疗推理...")
    result = provider.generate(
        "患者：35岁女性，主诉：双眼睑下垂6个月，下午加重，伴有复视和易疲劳性肌无力。\n"
        "请给出最可能的诊断和3个鉴别诊断，用JSON格式返回。格式：{\"diagnosis\": \"\", \"differential\": [], \"confidence\": 0.0}",
        system="你是一位神经内科专科医生，请进行鉴别诊断。",
    )
    print(f"   响应：{result.text[:200]}")
    print(f"   Tokens：{result.tokens_used}")

    if result.finish_reason == "error":
        print(f"❌ API调用失败: {result.text}")
        return False

    print("✅ 医疗推理成功\n")
    return True


def test_harness_integration():
    """测试Harness完整集成。"""
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        return False

    from openclaw_medical_harness import DiagnosisHarness, MIMOProvider

    print("🔗 测试Harness + MIMO集成...")
    provider = MIMOProvider(api_key=api_key)
    harness = DiagnosisHarness(specialty="neurology", provider=provider)

    result = harness.execute({
        "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
        "patient": {"age": 35, "sex": "F"},
    })

    print(f"   诊断：{result['diagnosis']}")
    print(f"   置信度：{result['confidence']:.2f}")
    print(f"   下一步：{', '.join(result['next_steps'])}")
    print("✅ Harness集成成功\n")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw-Medical-Harness — MIMO API 测试")
    print("=" * 60 + "\n")

    ok1 = test_mimo_basic()
    ok2 = test_mimo_medical() if ok1 else False
    ok3 = test_harness_integration() if ok1 else False

    print("=" * 60)
    if ok1 and ok2 and ok3:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试未通过，请检查配置")
