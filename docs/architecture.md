# Architecture

## Overview

OpenClaw-Medical-Harness is built on **Harness Theory** — the principle that
environment design (tools, context, validation, recovery) matters more than
model selection for domain-specific AI performance.

## Harness Theory — The Core Insight

```
Traditional AI thinking:
  Better Model → Better Results

Harness Theory:
  Better Environment → Better Results (even with the same model)

Key finding: Well-designed Harness architecture yields up to 64%
performance improvement — with the SAME underlying model.
```

### Why Does This Work?

LLMs are general-purpose reasoners. Their output quality depends heavily on:
1. **What information they receive** (context quality)
2. **How information is structured** (information format)
3. **What tools they can access** (tool chain)
4. **How failures are handled** (recovery)
5. **How outputs are checked** (validation)

A Harness optimizes all five dimensions, while the model remains swappable.

## The Seven-Layer Ecosystem

```
┌─────────────────────────────────────────────┐
│  Layer 7: Business Value                     │
│  Patient outcomes, clinical decisions        │
├─────────────────────────────────────────────┤
│  Layer 6: Harness Design ← WE ARE HERE      │
│  Tool chains, context, recovery, validation  │
├─────────────────────────────────────────────┤
│  Layer 5: Agent Framework                    │
│  OpenClaw, CrewAI, AutoGen, LangGraph       │
├─────────────────────────────────────────────┤
│  Layer 4: Tool Integration                   │
│  MCP tools, APIs, databases                  │
├─────────────────────────────────────────────┤
│  Layer 3: Context Management                 │
│  Token optimization, compression, memory     │
├─────────────────────────────────────────────┤
│  Layer 2: Reasoning Optimization             │
│  Prompt engineering, chain-of-thought        │
├─────────────────────────────────────────────┤
│  Layer 1: Model Layer                        │
│  Mimo, GPT-4, Claude, Llama, etc.           │
└─────────────────────────────────────────────┘
```

Most frameworks focus on Layers 1-3. We focus on Layer 6 (Harness Design),
which orchestrates all lower layers for maximum domain-specific performance.

## Three-Layer Medical Harness Architecture

### Layer 1: Diagnostic Harness

```
Symptoms Input ─→ Triage & Red Flags ─→ Differential Diagnosis
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                              Primary Dx   Alt Dx₁   Alt Dxₙ
                                    │
                                    ▼
                         Workup Strategy ─→ Specialist Referral
                                    │
                                    ▼
                           Confirmed Diagnosis
```

**Pipeline stages:**
1. **Symptom Intake** — Structure raw symptoms with metadata
2. **Red Flag Screening** — Identify emergency indicators
3. **Differential Generation** — Produce ranked differential list
4. **Evidence Gathering** — Query PubMed, OMIM for supporting evidence
5. **Workup Planning** — Recommend diagnostic tests
6. **Diagnosis Narrowing** — Refine based on available evidence

**Key features:**
- Multi-disciplinary consultation routing
- Rare disease knowledge base integration
- Escalation protocols for uncertain cases
- Step-wise reasoning chain with evidence tracking

### Layer 2: Drug Discovery Harness

```
Disease Target ─→ Target Validation (OpenTargets)
                        │
                        ▼
              Virtual Screening (ChEMBL)
                        │
                        ▼
              ADMET Prediction ─→ Filter candidates
                        │
                        ▼
              Lead Optimization ─→ Iterative improvement
                        │
                        ▼
              Drug Candidate Profile
```

**Pipeline stages:**
1. **Target Validation** — Verify target-disease association via OpenTargets
2. **Virtual Screening** — Screen compound libraries via ChEMBL
3. **ADMET Prediction** — Predict absorption, distribution, metabolism, excretion, toxicity
4. **Lead Optimization** — Iterative structural improvement
5. **Candidate Profiling** — Complete drug-like property assessment

**Key features:**
- ChEMBL/OpenTargets data source integration
- Molecular generation agent interface
- Lipinski Rule of Five validation
- Novelty scoring for compound prioritization

### Layer 3: Health Management Harness

```
Patient Data ─→ Multi-Modal Aggregation
   │  (labs, wearables, questionnaires)
   ▼
Health Assessment ─→ Risk Stratification
   │
   ▼
Personalized Care Plan
   │
   ├── Medications
   ├── Lifestyle modifications
   ├── Monitoring schedule
   └── Follow-up timeline
   │
   ▼
Compliance Tracking ─→ Outcome Evaluation
   │
   ▼
Plan Adjustment (continuous loop)
```

**Pipeline stages:**
1. **Data Aggregation** — Collect multi-modal health data
2. **Risk Assessment** — Stratify risk across health domains
3. **Plan Generation** — Create personalized, evidence-based care plans
4. **Compliance Monitoring** — Track adherence to care plans
5. **Outcome Evaluation** — Measure plan effectiveness
6. **Plan Adjustment** — Iterate based on outcomes

**Key features:**
- Multi-modal data intake (questionnaires, wearables, labs)
- Longitudinal follow-up agent
- Compliance and adherence scoring
- Evidence-based plan generation

## Core Infrastructure

### Context Manager

The context manager is where Harness theory becomes tangible. It determines
HOW information flows to the model, directly impacting reasoning quality.

**Compression strategies:**
- `TRUNCATE` — Simple, fast, loses information
- `SUMMARIZE` — LLM-assisted, preserves meaning
- `HIERARCHICAL` — Keeps structure, drops details
- `MEDICAL_PRIORITIZED` — Keeps clinical data, compresses metadata (default)

**Critical item retention:** Allergies, drug interactions, and clinical alerts
are NEVER compressed — they are always passed to the model.

### Failure Recovery

Medical AI cannot silently fail. The recovery system implements multi-tier
escalation:

```
Failure Detected
     │
     ▼
Assess Severity ──→ CRITICAL → Human escalation required
     │
     ▼
HIGH → Graceful degradation with uncertainty flags
     │
     ▼
MEDIUM → Retry (up to max_retries)
     │
     ▼
LOW → Accept with warnings
```

### Result Validator

Four-layer validation pipeline:

1. **Structural** — Required fields, correct types
2. **Consistency** — No internal contradictions
3. **Domain** — Medical domain-specific rules
4. **Safety** — Dangerous pattern detection

## MCP Tool Integration

Medical data sources are integrated via the Model Context Protocol:

| Tool | Source | Domain | Harness |
|------|--------|--------|---------|
| PubMed Search | NCBI E-utilities | Literature | All |
| ChEMBL Query | EMBL-EBI | Drug data | Drug Discovery |
| OpenTargets | OpenTargets Platform | Target-disease | Diagnosis, Drug Discovery |
| OMIM Lookup | Johns Hopkins | Genetics | Diagnosis |
| OpenFDA Safety | US FDA | Drug safety | Drug Discovery, Health Mgmt |

Each tool is wrapped in an `MCPToolAdapter` that translates between the
Harness tool interface and the MCP protocol.

## Multi-Agent Orchestration

Two modes, one interface:

### OpenClaw Native Mode
- Uses OpenClaw's Skill system for agent routing
- Agents are defined as OpenClaw Skills
- Context flows through OpenClaw's native management

### CrewAI Compatible Mode
- Maps to CrewAI Agent/Crew/Task API
- Familiar for CrewAI users
- Same Harness infrastructure underneath

### Agent Roles

| Role | Responsibility | Tools |
|------|---------------|-------|
| Diagnostic Agent | Clinical reasoning, differential diagnosis | PubMed, OMIM |
| Literature Agent | Evidence retrieval and synthesis | PubMed |
| Drug Agent | Pharmacology, interactions, dosing | ChEMBL, OpenFDA |
| Communication Agent | Patient-facing explanations | — |

## Comparison with Alternatives

| Dimension | OpenClaw-MH | AutoGen | CrewAI | LangGraph |
|-----------|-------------|---------|--------|-----------|
| Architecture | Harness-centric | Chat-based | Role-based | State machine |
| Medical focus | 66 skills | None | None | None |
| Data sources | 5 MCP tools | Manual | Manual | Manual |
| Failure handling | Multi-tier recovery | Manual | Basic retry | Manual |
| Validation | Domain-specific | None | None | None |
| Context strategy | Medical-aware | Token window | Simple | Graph state |
| Performance theory | Harness (+64%) | Model-dependent | Model-dependent | Model-dependent |
