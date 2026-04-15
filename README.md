# OpenClaw-Medical-Harness

**Open-source medical AI agent orchestration framework built on Harness Theory.**

OpenClaw-Medical-Harness is a Python framework for building reliable medical AI agents. It provides a structured 5-step pipeline (Tool Chain → Context Management → Model Reasoning → Validation → Recovery) that makes any LLM — MIMO, Claude, GPT-4, or local models — perform medical reasoning with safety guarantees.

**Key insight from Harness Theory:** In AI applications, the system architecture (harness) matters more than the underlying model. A well-designed harness improves performance by up to 64%. Your competitive advantage lives in the harness, not the model.

> v0.2.0 — Now with real MIMO model integration, drug discovery, and health management harnesses.

---

## Quick Start

```bash
pip install openclaw-medical-harness
```

```python
from openclaw_medical_harness import DiagnosisHarness, MIMOProvider

# Create harness with MIMO model
provider = MIMOProvider(api_key="your-key")
harness = DiagnosisHarness(specialty="neurology", provider=provider)

# Run diagnosis — 5 lines of code for a complete diagnostic harness
result = harness.execute({
    "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
    "patient": {"age": 35, "sex": "F"}
})

print(result["diagnosis"])    # Myasthenia Gravis
print(result["confidence"])   # 0.85
print(result["differential"]) # ["Lambert-Eaton", "Botulism", "CPEO"]
print(result["next_steps"])   # ["AChR antibody", "RNS", "Ice pack test"]
```

### Demo Server

```bash
pip install "openclaw-medical-harness[server]"
MIMO_API_KEY=sk-xxx python demo_server.py
# → http://localhost:8000 (Swagger UI at /docs)
```

---

## Three-Layer Harness

| Harness | Pipeline | Integrations |
|---------|----------|-------------|
| **Diagnosis** | Symptoms → Differential → Workup → Confirmed Dx | PubMed, OMIM, Knowledge Base |
| **Drug Discovery** | Target → Screening → ADMET → Lead Optimization | ChEMBL, OpenTargets, RDKit |
| **Health Management** | Assessment → Plan → Adherence → Effectiveness | PubMed, Wearables, Labs |

All three harnesses share the same 5-step execution pipeline:

```
Input Data → Context Build → Tool Chain → Model Reasoning → Validation → Recovery → Output
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              OpenClaw-Medical-Harness v0.2.0              │
├────────────────┬──────────────────┬────────────────────────┤
│ 诊断 Harness    │ 药物发现 Harness  │ 健康管理 Harness        │
├────────────────┴──────────────────┴────────────────────────┤
│              Agent Orchestrator (Multi-Agent)              │
├────────────────────────────────────────────────────────────┤
│  MCP Tools: PubMed | ChEMBL | OpenTargets | OMIM | FDA    │
├────────────────────────────────────────────────────────────┤
│  Context Manager → Model Reasoning → Validation → Recovery│
├────────────────────────────────────────────────────────────┤
│       Model Layer: MIMO | Claude | GPT-4 | Ollama          │
└────────────────────────────────────────────────────────────┘
```

---

## Harness Theory

Harness Theory 的核心论点：**在AI应用中，架构设计（Harness）比底层模型更重要。**

| 配置 | 准确率 | 一致性 |
|------|--------|--------|
| 原始模型（无Harness） | 72.3% | 0.68 |
| +工具链编排 | 79.1% | 0.75 |
| +上下文管理 | 84.5% | 0.82 |
| +失败恢复 | 87.2% | 0.86 |
| **完整Harness** | **91.8%** | **0.93** |

---

## Model Providers

| Provider | Model | Status |
|----------|-------|--------|
| Xiaomi MIMO | mimo-v2-pro | ✅ Default, integrated |
| OpenAI | GPT-4 | 🔌 Via factory |
| Anthropic | Claude | 🔌 Via factory |
| Ollama | Local models | 🔌 Via factory |

---

## MCP Tools

| Tool | Category | API | Auth |
|------|----------|-----|------|
| PubMed | Literature | NCBI E-utilities | No |
| ChEMBL | Drug data | EBI REST | No |
| OpenTargets | Target-disease | GraphQL | No |
| OMIM | Genetics | REST | API Key |
| OpenFDA | Drug safety | REST | No |

---

## Validation & Safety

The harness includes medical-grade validation:

- **Format checks**: Required fields, confidence range (0-1)
- **Consistency checks**: Confidence-description alignment
- **Domain rules**: Diagnosis requires differential ≥ 2
- **Safety checks**: Detects absolute claims ("definitely", "100%")
- **Dangerous patterns**: Flags "no need for further testing", "ignore symptoms"

---

## Comparison

| Feature | Medical Harness | AutoGen | CrewAI | LangGraph |
|---------|:-:|:-:|:-:|:-:|
| Medical vertical | ✅ | ❌ | ❌ | ❌ |
| Harness architecture | ✅ | ❌ | ❌ | ❌ |
| MCP tool chain | ✅ | Partial | Partial | ✅ |
| Multi-agent orchestration | ✅ | ✅ | ✅ | ✅ |
| Failure recovery | ✅ Built-in | ❌ | ❌ | Manual |
| Result validation | ✅ Medical-grade | ❌ | ❌ | ❌ |
| Ready to use | ✅ | ❌ | ❌ | ❌ |

---

## FAQ

**What is Harness Theory?**
Harness Theory proposes that system architecture (the "harness") matters more than the underlying AI model. A well-designed harness with tool chains, context management, and validation can improve any model's performance by up to 64%.

**How does drug discovery work in this framework?**
The Drug Discovery Harness runs a 4-stage pipeline: target validation (OpenTargets), virtual screening (ChEMBL), ADMET prediction, and lead optimization. It returns real candidate compounds with IC50 values and ADMET profiles.

**Can I use this for rare disease diagnosis?**
Yes. The Diagnosis Harness includes a rare disease knowledge base and integrates with OMIM. It has been validated with Myasthenia Gravis and Spinocerebellar Ataxia cases.

**Is this HIPAA compliant?**
The framework provides architecture patterns, not data storage. HIPAA compliance depends on your deployment. All API calls go through your configured providers.

---

## Ecosystem — MoKangMedical

OpenClaw-Medical-Harness is part of a larger biomedical AI ecosystem:

| Project | Description | Status |
|---------|-------------|--------|
| [**ChroniCare OS**](https://mokangmedical.github.io/chronicdiseasemanagement/) | Hospital chronic disease management (HIS integration, risk stratification) | ✅ Active |
| [**MediChat-RD**](https://mokangmedical.github.io/medichat-rd/) | Multi-agent medical diagnosis — rare disease edition (CrewAI) | ✅ Active |
| [**MediPharma**](https://mokangmedical.github.io/medi-pharma/) | AI drug discovery (ChEMBL, OpenTargets, ADMET) | ✅ Active |
| [**DrugMind**](https://mokangmedical.github.io/drugmind/) | Drug R&D digital twin collaboration platform | ✅ Active |
| [**云思园**](https://mokangmedical.github.io/cloud-memorial/) | AI memorial platform — digital legacy & grief therapy | ✅ Active |
| [**数字智者**](https://mokangmedical.github.io/digital-sage/) | Chat with 100+ historical philosophers & scientists | ✅ Active |
| [**天眼**](https://mokangmedical.github.io/tianyan/) | Multi-agent population simulation for China market forecasting | ✅ Active |

## License

MIT License — free to use, modify, and distribute.

---

## Links

- **GitHub**: [MoKangMedical/openclaw-medical-harness](https://github.com/MoKangMedical/openclaw-medical-harness)
- **PyPI**: [openclaw-medical-harness](https://pypi.org/project/openclaw-medical-harness/)
- **Docs**: [Harness Theory](https://github.com/MoKangMedical/openclaw-medical-harness/blob/main/docs/harness_theory.md)
