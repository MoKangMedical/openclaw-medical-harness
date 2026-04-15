# Architecture

System design of the OpenClaw Medical Harness.

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   OpenClaw Medical Harness v0.2.0                  │
├─────────────────┬───────────────────┬───────────────────────────────┤
│  Diagnosis      │  Drug Discovery   │  Health Management            │
│  Harness        │  Harness          │  Harness                      │
├─────────────────┴───────────────────┴───────────────────────────────┤
│                   Medical Orchestrator (Multi-Agent)               │
│              OpenClaw Mode  │  CrewAI Mode                         │
├────────────────────────────────────────────────────────────────────┤
│  MCP Tools: PubMed │ ChEMBL │ OpenTargets │ OMIM │ OpenFDA │ RDKit│
├────────────────────────────────────────────────────────────────────┤
│  Context Manager → Model Reasoning → Validation → Recovery        │
├────────────────────────────────────────────────────────────────────┤
│  Providers: MIMO │ GPT-4 │ Claude │ Ollama                        │
└────────────────────────────────────────────────────────────────────┘
```

## Component Design

### Harness Layer

Each harness is a specialized pipeline:

**Diagnosis Harness**
- Input: symptoms, patient demographics, lab results, medical history
- Pipeline: symptom analysis → differential generation → workup recommendation
- Output: diagnosis, confidence, differential, next steps, evidence

**Drug Discovery Harness**
- Input: target, disease, molecular constraints
- Pipeline: target validation → compound screening → ADMET → optimization
- Output: candidates, ADMET profile, optimization suggestions

**Health Management Harness**
- Input: conditions, lab results, medications, patient goals
- Pipeline: assessment → plan generation → adherence tracking → effectiveness
- Output: assessment, plan, adherence metrics, effectiveness trends

### Orchestrator Layer

The MedicalOrchestrator coordinates multiple agents:

```
                    ┌──────────────┐
                    │  Orchestrator │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │Diagnostician│  │Literature │    │Pharmaco- │
    │Agent       │    │Reviewer   │    │logist    │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    ┌──────────┐
                    │ Consensus │
                    │ Round     │
                    └──────────┘
```

Agents share context but generate independent opinions. The orchestrator runs consensus rounds where agents can revise their positions based on peer feedback.

### Tool Layer (MCP)

Tools are accessed through the MedicalToolRegistry:

```
Registry
├── pubmed        (Literature search)
├── chembl        (Compound database)
├── opentargets   (Target-disease evidence)
├── omim          (Genetic disease info)
├── openfda       (Drug safety)
└── rdkit         (Molecular analysis)
```

Each tool implements a standard interface:
- `search(query, **kwargs)` — Search/query
- `get(id)` — Retrieve specific record
- `validate(data)` — Validate tool data

### Validation Layer

Results go through multi-level validation:

1. **Format** — Required fields, type checking, range validation
2. **Consistency** — Confidence-description alignment
3. **Domain** — Specialty-specific rules (e.g., diagnosis needs differential)
4. **Safety** — Absolute terms, dangerous patterns

### Recovery Layer

Failed validations trigger recovery strategies:

- **ESCALATE** — Log for human review, return error
- **FALLBACK** — Return safe default (low confidence)
- **RETRY** — Re-run with adjusted parameters (up to 3 times)

## Data Flow

```
User Input
    │
    ▼
┌──────────────┐
│ Context Build │ ← Patient history, labs, medications
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Tool Chain   │ ← PubMed, ChEMBL, OpenTargets (parallel)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Model        │ ← MIMO / GPT-4 / Claude
│ Reasoning    │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ Validation   │────▶│ Recovery     │ (if failed)
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────────────────────┐
│ Output                       │
│ diagnosis, confidence, etc.  │
└──────────────────────────────┘
```

## Extension Points

### Adding a New Harness

1. Inherit from `BaseHarness`
2. Implement `execute(input_data) -> dict`
3. Register in the harness factory

### Adding a New Tool

1. Implement the tool interface (`search`, `get`, `validate`)
2. Register in `MedicalToolRegistry`
3. Add category and metadata

### Adding a New Provider

1. Inherit from `ModelProvider`
2. Implement `generate(prompt, context, tools) -> str`
3. Register in the provider factory

## Security

- No PHI storage — all processing is stateless by default
- Tool calls go through configured providers
- Validation catches unsafe outputs before delivery
- Recovery prevents silent failures

## Performance

See [Benchmarks](benchmarks/PERFORMANCE.md) for detailed performance data.

Key metrics:
- Average latency: 4.5s (full harness)
- Accuracy: 91.8% (vs 72.3% raw model)
- Consistency: 0.93 (vs 0.68 raw model)
