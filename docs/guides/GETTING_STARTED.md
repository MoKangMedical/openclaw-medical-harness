# Getting Started Guide

Build your first medical AI agent in 5 minutes.

## Step 1: Install

```bash
pip install openclaw-medical-harness
```

## Step 2: Create a Harness

```python
from openclaw_medical_harness import DiagnosisHarness

# Create a neurology diagnosis harness
# Auto-selects MIMO model as default provider
harness = DiagnosisHarness(specialty="neurology")
```

## Step 3: Execute

```python
result = harness.execute({
    "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
    "patient": {"age": 35, "sex": "F"}
})

print(result["diagnosis"])    # Myasthenia Gravis
print(result["confidence"])   # 0.85
print(result["differential"]) # ["Lambert-Eaton", "Botulism", "CPEO"]
print(result["next_steps"])   # ["AChR antibody", "RNS", "Ice pack test"]
```

## Step 4: Validate Results

```python
from openclaw_medical_harness import ResultValidator

validator = ResultValidator(threshold=0.7)
validation = validator.validate(result)

if validation.passed:
    print("✅ Result validated")
else:
    print(f"⚠️ Issues: {validation.findings}")
```

## Step 5: Handle Failures

```python
from openclaw_medical_harness import FailureRecovery, RecoveryStrategy

recovery = FailureRecovery(strategy=RecoveryStrategy.FALLBACK)

if not validation.passed:
    safe_result = recovery.recover(result, validation)
    print(f"Recovered with confidence: {safe_result['confidence']:.0%}")
```

## Full Example

```python
from openclaw_medical_harness import (
    DiagnosisHarness, ResultValidator, FailureRecovery, RecoveryStrategy
)

def diagnose(symptoms, age, sex):
    harness = DiagnosisHarness(specialty="neurology")
    validator = ResultValidator(threshold=0.7)
    recovery = FailureRecovery(strategy=RecoveryStrategy.FALLBACK)
    
    result = harness.execute({
        "symptoms": symptoms,
        "patient": {"age": age, "sex": sex}
    })
    
    validation = validator.validate(result)
    if not validation.passed:
        result = recovery.recover(result, validation)
    
    return result

# Use it
r = diagnose(["ptosis", "fatigable weakness"], 35, "F")
print(f"{r['diagnosis']} ({r['confidence']:.0%})")
```

## What's Next?

- [API Reference](../api/REFERENCE.md) — Full API documentation
- [Examples](../examples/CODE_EXAMPLES.md) — More practical examples
- [Benchmarks](../benchmarks/PERFORMANCE.md) — Performance data
- [Harness Theory](../harness_theory.md) — Why architecture > model
- [Architecture](../architecture.md) — System design details
