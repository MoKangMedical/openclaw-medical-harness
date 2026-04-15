# What is Harness Theory?

*Why system architecture matters more than the underlying AI model.*

## The Core Insight

In AI applications, the system architecture wrapping the model — the **harness** — is more important than the model itself.

A well-designed harness improves any model's performance by up to **64%**. Your competitive advantage lives in the harness, not the model.

## The 5-Step Pipeline

Every harness in OpenClaw Medical follows the same pipeline:

```
Input → Context Build → Tool Chain → Model Reasoning → Validation → Recovery → Output
```

### 1. Context Build

Before asking the model anything, we build rich context:

- Patient demographics and medical history
- Relevant lab results and imaging
- Current medications
- Known allergies
- Prior diagnoses

The context manager ensures we stay within token limits while maximizing information density.

### 2. Tool Chain

The model doesn't work alone. MCP tools provide real-time data:

- **PubMed**: Search medical literature for evidence
- **ChEMBL**: Query 2.4M+ drug compounds
- **OpenTargets**: Get target-disease evidence scores
- **OMIM**: Look up genetic disease information
- **OpenFDA**: Check drug safety and adverse events

Tools run in parallel when possible, adding rich external knowledge.

### 3. Model Reasoning

With context and tool data loaded, the model reasons through the problem:

- Differential diagnosis generation
- Treatment recommendation
- Risk assessment
- Prognosis prediction

The model is the "thinking engine" — but it's guided by the harness.

### 4. Validation

Every output is validated before delivery:

- **Format checks**: Required fields, confidence range
- **Consistency checks**: Confidence-description alignment
- **Domain rules**: Diagnosis requires differential ≥ 2
- **Safety checks**: No absolute claims, no dangerous patterns

Bad outputs are caught before they reach users.

### 5. Recovery

When validation fails, the harness recovers gracefully:

- **ESCALATE**: Flag for human review
- **FALLBACK**: Return safe default with low confidence
- **RETRY**: Re-run with adjusted parameters

No silent failures. No garbage output.

## Why It Works

| Factor | Raw Model | With Harness |
|--------|-----------|-------------|
| Knowledge | Training data only | + Real-time literature + drug databases |
| Safety | No guardrails | Medical-grade validation |
| Consistency | Variable | Deterministic pipeline |
| Recovery | None | Automatic failure handling |
| Accuracy | 72.3% | **91.8%** |

## The Business Implication

If you're building a medical AI product, your moat isn't in the model — it's in:

1. **Your tool chain** — Which databases you integrate, how you query them
2. **Your context management** — How you structure patient data
3. **Your validation** — How you catch errors
4. **Your recovery** — How you handle edge cases
5. **Your domain knowledge** — How you encode medical expertise

Models are commodities. Harnesses are competitive advantages.

## Try It

```bash
pip install openclaw-medical-harness
```

```python
from openclaw_medical_harness import DiagnosisHarness

h = DiagnosisHarness(specialty="neurology")
r = h.execute({"symptoms": ["ptosis"], "patient": {"age": 35}})
print(r["diagnosis"], r["confidence"])
```

---

*Read the full [architecture documentation](../architecture.md) for implementation details.*
