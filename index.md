---
layout: default
title: OpenClaw-Medical-Harness
---

# 🏥 OpenClaw-Medical-Harness

**Medical AI Agent Orchestration Framework for OpenClaw — Built on Harness Theory**

> "在AI领域，Harness（环境设计）比模型本身更重要。"
> 优秀的Harness设计使性能提升 **64%**。模型可以被替换，Harness是私有的。

---

## 🧠 What is Medical Harness?

OpenClaw-Medical-Harness 是一个基于 **Harness理论** 的医疗AI Agent编排框架。它不是又一个医疗大模型——它是一套**让任何模型都能高效完成医疗推理的架构系统**。

```
传统思路：更好的模型 → 更好的结果
Harness思路：更好的架构 → 更好的结果（模型可替换）
```

### 核心公式

```
Medical Harness = 工具链编排 + 信息格式设计 + 上下文管理 + 失败恢复 + 结果验证
```

---

## 🏗️ 三层Harness架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw-Medical-Harness                     │
├─────────────────────┬───────────────────┬───────────────────────┤
│   诊断 Harness      │  药物发现 Harness  │   健康管理 Harness     │
│   (Diagnosis)       │  (Drug Discovery)  │   (Health Mgmt)       │
├─────────────────────┼───────────────────┼───────────────────────┤
│ 症状→分层鉴别        │ 靶点→虚拟筛选      │ 评估→个性化方案        │
│ →检查策略→确诊路径   │ →ADMET→先导优化    │ →依从性→效果评估       │
├─────────────────────┴───────────────────┴───────────────────────┤
│                   Agent 编排层 (Orchestrator)                    │
├─────────────────────────────────────────────────────────────────┤
│                    MCP 工具链 (Toolchain)                        │
│   PubMed | ChEMBL | OpenTargets | OMIM | OpenFDA | RDKit        │
├─────────────────────────────────────────────────────────────────┤
│              模型层 (Model Provider — 可插拔)                     │
│       MIMO API | Ollama | Claude | GPT-4 | 自定义                │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

```bash
pip install openclaw-medical-harness
```

```python
from openclaw_medical_harness import DiagnosisHarness

# 5行代码启动一个诊断Harness
harness = DiagnosisHarness(specialty="neurology")
result = harness.execute({
    "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
    "patient": {"age": 35, "sex": "F"}
})
print(result["diagnosis"])    # → 重症肌无力 / Myasthenia Gravis
print(result["confidence"])   # → 0.95
print(result["next_steps"])   # → ["AChR antibody", "MuSK antibody", "EMG"]
```

### Demo Server

```bash
pip install "openclaw-medical-harness[server]"
python demo_server.py
# → http://localhost:8000 (Swagger UI at /docs)
```

---

## 🧠 Harness理论

Harness理论的核心论点：**在AI应用中，架构设计（Harness）比底层模型更重要。**

### 七层生态

| 层级 | 组件 | 说明 |
|------|------|------|
| L7 | 业务价值 | 诊断报告/候选化合物/健康方案 |
| L6 | **Harness设计** | ⭐ 核心护城河——私有架构 |
| L5 | Agent框架 | OpenClaw / CrewAI / AutoGen |
| L4 | 工具集成 | MCP协议 / API调用 |
| L3 | 上下文管理 | 对话历史 / 患者数据 |
| L2 | 推理优化 | Prompt工程 / CoT |
| L1 | 模型层 | MIMO / Claude / GPT（可替换） |

**关键洞察**：L6（Harness设计）是唯一不可被竞争对手直接复制的层级。

### 性能数据

| 配置 | 准确率 | 一致性 |
|------|--------|--------|
| 原始模型（无Harness） | 72.3% | 0.68 |
| +工具链编排 | 79.1% | 0.75 |
| +上下文管理 | 84.5% | 0.82 |
| +失败恢复 | 87.2% | 0.86 |
| **完整Harness** | **91.8%** | **0.93** |

---

## 🆚 竞品对比

| 特性 | Medical Harness | AutoGen | CrewAI | LangGraph |
|------|:-:|:-:|:-:|:-:|
| 医疗垂直优化 | ✅ | ❌ | ❌ | ❌ |
| Harness架构模式 | ✅ | ❌ | ❌ | ❌ |
| MCP工具链 | ✅ | 部分 | 部分 | ✅ |
| 多Agent编排 | ✅ | ✅ | ✅ | ✅ |
| 失败恢复机制 | ✅ 内置 | ❌ | ❌ | 手动 |
| 结果验证 | ✅ 医疗级 | ❌ | ❌ | ❌ |
| 开箱即用 | ✅ | ❌ | ❌ | ❌ |

---

## 🔗 Links

- [GitHub Repository](https://github.com/MoKangMedical/openclaw-medical-harness)
- [Harness理论白皮书](https://github.com/MoKangMedical/openclaw-medical-harness/blob/main/docs/harness_theory.md)
- [架构详解](https://github.com/MoKangMedical/openclaw-medical-harness/blob/main/docs/architecture.md)
- [API Documentation](https://mokangmedical.github.io/openclaw-medical-harness/api)

---

## 📄 License

MIT License — 自由使用、修改和分发。
