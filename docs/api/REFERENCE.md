# API Reference

Complete API documentation for OpenClaw Medical Harness v0.2.0.

## Installation

```bash
pip install openclaw-medical-harness          # Core
pip install "openclaw-medical-harness[server]" # + FastAPI demo server
pip install "openclaw-medical-harness[crewai]" # + CrewAI integration
pip install "openclaw-medical-harness[all]"    # Everything
```

---

## Core Classes

### DiagnosisHarness

Diagnostic reasoning harness for clinical decision support.

```python
from openclaw_medical_harness import DiagnosisHarness

harness = DiagnosisHarness(specialty="neurology")

result = harness.execute({
    "symptoms": ["bilateral ptosis", "fatigable weakness"],
    "patient": {"age": 35, "sex": "F"},
    "medical_history": ["hypothyroidism"],
    "lab_results": {"AChR_antibody": "positive"}
})
```

**Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `specialty` | str | `"general"` | neurology, cardiology, pulmonology, gastroenterology, general |
| `provider` | ModelProvider | None | Model provider (auto-selects MIMO) |
| `config` | dict | None | Override defaults |

**Returns:**
```python
{
    "diagnosis": "Myasthenia Gravis",        # str: Primary diagnosis
    "confidence": 0.85,                       # float: 0.0-1.0
    "differential": ["LEMS", "CPEO"],         # list: Alternative diagnoses
    "next_steps": ["AChR antibody", "RNS"],   # list: Recommended workup
    "evidence": ["Classic MG pattern"],       # list: Supporting evidence
    "harness_name": "diagnosis_neurology",    # str
    "execution_time_ms": 1234,                # int
    "recovery_applied": False                 # bool
}
```

**Methods:**
- `execute(input_data)` — Run full diagnostic pipeline
- `query_rare_disease_kb(symptoms)` — Search rare disease knowledge base
- `request_multidisciplinary_consult(specialties, context)` — Request MDT consultation
- `get_status()` — Get harness health status

---

### DrugDiscoveryHarness

Drug discovery pipeline: target validation → screening → ADMET → optimization.

```python
from openclaw_medical_harness import DrugDiscoveryHarness

harness = DrugDiscoveryHarness(target_disease="Myasthenia Gravis")

result = harness.execute({
    "target": "AChE",
    "disease": "Myasthenia Gravis",
    "constraints": {"max_mw": 500, "min_logp": -1}
})
```

**Returns:**
```python
{
    "target": "AChE",
    "candidates": [                           # list: Drug candidates
        {"name": "Pyridostigmine", "ic50": 0.5, "source": "ChEMBL"},
    ],
    "admet_profile": {                        # dict: ADMET scores (0-1)
        "absorption": 0.85,
        "distribution": 0.72,
        "metabolism": 0.68,
        "excretion": 0.91,
        "toxicity": 0.15
    },
    "optimization_suggestions": ["Improve oral bioavailability"],
    "confidence": 0.78,
    "harness_name": "drug_discovery",
    "execution_time_ms": 2345,
    "recovery_applied": False
}
```

**Methods:**
- `execute(input_data)` — Run drug discovery pipeline
- `validate_target(target, disease)` — Validate a specific target

---

### HealthManagementHarness

Health management, adherence tracking, and outcome assessment.

```python
from openclaw_medical_harness import HealthManagementHarness

harness = HealthManagementHarness(health_domain="diabetes")

result = harness.execute({
    "conditions": ["type 2 diabetes"],
    "lab_results": {"hba1c": 7.2, "fasting_glucose": 145},
    "patient": {"age": 55, "weight": 82, "height": 175},
    "medications": ["metformin 1000mg bid"]
})
```

**Domains:** `diabetes`, `weight_management`, `cardiovascular`, `general`

**Methods:**
- `execute(input_data)` — Run health assessment
- `conduct_follow_up(patient_id, metrics)` — Schedule follow-up

---

### MedicalOrchestrator

Multi-agent orchestration with consensus.

```python
from openclaw_medical_harness import MedicalOrchestrator

orchestrator = MedicalOrchestrator(mode="openclaw")
orchestrator.add_agent("diagnostician", specialty="neurology")
orchestrator.add_agent("literature_reviewer")
orchestrator.add_agent("pharmacologist")
orchestrator.add_agent("ethics_reviewer")

result = orchestrator.run(
    task="鉴别诊断：35岁女性，双眼睑下垂",
    context={"symptoms": ["ptosis", "fatigable weakness"]},
    consensus_rounds=2
)
```

**Modes:** `openclaw` (native), `crewai` (via CrewAI)

---

## MCP Tools

### MedicalToolRegistry

```python
from openclaw_medical_harness import MedicalToolRegistry

registry = MedicalToolRegistry()
tools = registry.list_tools()           # All tools
pubmed = registry.get("pubmed")         # Specific tool
drug_tools = registry.list_tools(category="drug")  # By category
```

**Built-in Tools:**

| Tool | Category | Description | Auth Required |
|------|----------|-------------|---------------|
| `pubmed` | literature | PubMed article search & retrieval | No |
| `chembl` | drug | ChEMBL compound database (2.4M+) | No |
| `opentargets` | drug | OpenTargets target-disease evidence | No |
| `omim` | genetics | Online Mendelian Inheritance in Man | API Key |
| `openfda` | drug | FDA drug safety & adverse events | No |
| `rdkit` | drug | Molecular descriptors & analysis | No |

---

## Validation

### ResultValidator

```python
from openclaw_medical_harness import ResultValidator

validator = ResultValidator(threshold=0.7, strict_mode=False)
validation = validator.validate(result, domain="diagnosis")
```

**Validation Rules:**

| Rule | Level | Trigger |
|------|-------|---------|
| Required fields | ERROR | Missing diagnosis/confidence |
| Confidence range | ERROR | Not in 0.0-1.0 |
| Absolute terms | ERROR | "definitely", "100%", "cure" |
| Dangerous patterns | ERROR | "no need for testing", "ignore symptoms" |
| Confidence mismatch | WARN | High confidence + uncertain language |
| Domain rules | WARN | Diagnosis needs differential ≥ 2 |

---

## Recovery

### FailureRecovery

```python
from openclaw_medical_harness import FailureRecovery, RecoveryStrategy

recovery = FailureRecovery(strategy=RecoveryStrategy.FALLBACK)
recovered = recovery.recover(failed_result, validation)
```

**Strategies:**
- `ESCALATE` — Flag for human review
- `FALLBACK` — Return safe default with low confidence
- `RETRY` — Re-run with adjusted parameters

---

## Context Management

### ContextManager

```python
from openclaw_medical_harness import ContextManager

cm = ContextManager({"max_tokens": 8000})
ctx = cm.build(input_data)
compressed = cm.compress(ctx)    # When exceeding max_tokens
merged = cm.merge(base, extra)
```

---

## Configuration

### HarnessConfig

```python
from openclaw_medical_harness import HarnessConfig, CompressionStrategy

config = HarnessConfig(
    name="my_harness",
    max_context_tokens=8000,
    validation_threshold=0.7,
    recovery_strategy="fallback",
    compression=CompressionStrategy.SUMMARIZE,
    tool_timeout=30,
    model_temperature=0.3
)
```

---

## Result Types

```python
from openclaw_medical_harness import HarnessResult, HarnessStatus

HarnessStatus.SUCCESS    # Pipeline completed
HarnessStatus.RECOVERED  # Recovery was applied
HarnessStatus.FAILED     # Irrecoverable failure
```
