# Examples

Practical examples for OpenClaw Medical Harness.

## 1. Quick Diagnosis

```python
from openclaw_medical_harness import DiagnosisHarness

harness = DiagnosisHarness(specialty="neurology")
result = harness.execute({
    "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
    "patient": {"age": 35, "sex": "F"}
})

print(f"Diagnosis: {result['diagnosis']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Differential: {', '.join(result['differential'])}")
print(f"Next steps: {', '.join(result['next_steps'])}")
```

## 2. Drug Discovery Pipeline

```python
from openclaw_medical_harness import DrugDiscoveryHarness

harness = DrugDiscoveryHarness(target_disease="Myasthenia Gravis")
result = harness.execute({
    "target": "AChE",
    "disease": "Myasthenia Gravis",
    "constraints": {"max_mw": 500}
})

print(f"Target: {result['target']}")
for c in result['candidates']:
    print(f"  - {c['name']}: IC50 = {c['ic50']} nM")

print(f"\nADMET Profile:")
for k, v in result['admet_profile'].items():
    print(f"  {k}: {v:.0%}")
```

## 3. Health Management

```python
from openclaw_medical_harness import HealthManagementHarness

harness = HealthManagementHarness(health_domain="diabetes")
result = harness.execute({
    "conditions": ["type 2 diabetes"],
    "lab_results": {"hba1c": 7.2, "fasting_glucose": 145},
    "patient": {"age": 55, "weight": 82},
    "medications": ["metformin 1000mg bid"]
})

print(f"Risk: {result['assessment']['risk_level']}")
print(f"Adherence: {result['adherence_metrics']}")
print(f"Effectiveness: {result['effectiveness']}")
```

## 4. Multi-Agent Consultation

```python
from openclaw_medical_harness import MedicalOrchestrator

orch = MedicalOrchestrator(mode="openclaw")
orch.add_agent("diagnostician", specialty="neurology")
orch.add_agent("literature_reviewer")
orch.add_agent("pharmacologist")
orch.add_agent("ethics_reviewer")

result = orch.run(
    task="鉴别诊断：35岁女性，双眼睑下垂3个月，疲劳后加重",
    context={
        "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
        "medical_history": ["hypothyroidism"],
        "lab_results": {"AChR_antibody": "pending"}
    },
    consensus_rounds=2
)

print(f"Consensus: {result['final_diagnosis']} ({result['confidence']:.0%})")
for opinion in result['agent_opinions']:
    agent = opinion.get('agent', 'unknown')
    print(f"  {agent}: {opinion}")
```

## 5. Validation & Recovery

```python
from openclaw_medical_harness import (
    DiagnosisHarness, ResultValidator, FailureRecovery, RecoveryStrategy
)

harness = DiagnosisHarness(specialty="neurology")
validator = ResultValidator(threshold=0.7)
recovery = FailureRecovery(strategy=RecoveryStrategy.FALLBACK)

# Execute diagnosis
result = harness.execute({
    "symptoms": ["random_symptom_xyz"],
    "patient": {"age": 30}
})

# Validate
validation = validator.validate(result)

if not validation.passed:
    print(f"Validation failed: {validation.findings}")
    result = recovery.recover(result, validation)
    print(f"Recovered with confidence: {result['confidence']:.0%}")
else:
    print(f"Diagnosis: {result['diagnosis']}")
```

## 6. Custom MCP Tool

```python
from openclaw_medical_harness import MedicalToolRegistry

registry = MedicalToolRegistry()

# Use PubMed tool
pubmed = registry.get("pubmed")
papers = pubmed.search("myasthenia gravis treatment guidelines", max_results=5)
for paper in papers:
    print(f"  {paper['title']} ({paper['year']})")
    print(f"    PMID: {paper['pmid']}")

# Use OpenTargets
opentargets = registry.get("opentargets")
evidence = opentargets.get_target_disease_evidence("ENSG00000198523", "EFO_0003767")
print(f"Evidence count: {len(evidence)}")
```

## 7. Demo Server

```python
# demo_server.py
from fastapi import FastAPI
from openclaw_medical_harness import DiagnosisHarness

app = FastAPI(title="Medical Harness API")
harness = DiagnosisHarness(specialty="neurology")

@app.post("/diagnose")
def diagnose(symptoms: list[str], age: int, sex: str):
    return harness.execute({
        "symptoms": symptoms,
        "patient": {"age": age, "sex": sex}
    })
```

```bash
pip install "openclaw-medical-harness[server]"
uvicorn demo_server:app --reload
# → http://localhost:8000/docs
```
