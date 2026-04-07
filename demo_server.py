"""
OpenClaw-Medical-Harness Demo Server

A FastAPI-based demo server providing REST API endpoints for:
- POST /diagnose — Medical diagnosis
- POST /drug-discovery — Drug discovery
- POST /health — Health management
- GET /health-check — Server health check
- GET / — HTML introduction page

Usage:
    pip install "openclaw-medical-harness[server]"
    python demo_server.py

    # Or with uvicorn directly:
    uvicorn demo_server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import time
from typing import Any, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        "FastAPI and Pydantic are required for the demo server. "
        'Install with: pip install "openclaw-medical-harness[server]"'
    )

from openclaw_medical_harness import (
    DiagnosisHarness,
    DrugDiscoveryHarness,
    HealthManagementHarness,
    MedicalOrchestrator,
    MedicalToolRegistry,
    __version__,
)

# ── Pydantic Models ─────────────────────────────────────────────────

class PatientInfo(BaseModel):
    """Patient information."""
    age: Optional[int] = None
    sex: Optional[str] = None
    medical_history: list[str] = Field(default_factory=list)


class DiagnoseRequest(BaseModel):
    """Request body for /diagnose."""
    symptoms: list[str] = Field(..., min_length=1, description="List of symptoms")
    patient: Optional[PatientInfo] = None
    specialty: str = "neurology"
    language: str = "zh"

    model_config = {"json_schema_extra": {
        "examples": [{
            "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
            "patient": {"age": 35, "sex": "F"},
            "specialty": "neurology",
        }]
    }}


class DrugDiscoveryRequest(BaseModel):
    """Request body for /drug-discovery."""
    target: str = Field(..., description="Drug target (e.g., EGFR)")
    disease: str = Field(..., description="Target disease (e.g., NSCLC)")
    max_compounds: int = Field(default=100, ge=1, le=1000)

    model_config = {"json_schema_extra": {
        "examples": [{
            "target": "EGFR",
            "disease": "NSCLC",
        }]
    }}


class HealthRequest(BaseModel):
    """Request body for /health."""
    conditions: list[str] = Field(default_factory=list, description="Existing conditions")
    health_goal: str = Field(default="general wellness", description="Health management goal")
    lab_results: dict[str, Any] = Field(default_factory=dict)
    wearable_data: dict[str, Any] = Field(default_factory=dict)
    age: Optional[int] = None

    model_config = {"json_schema_extra": {
        "examples": [{
            "conditions": ["type 2 diabetes"],
            "health_goal": "HbA1c < 7.0%",
            "lab_results": {"hba1c": 7.2},
            "age": 55,
        }]
    }}


class HarnessResponse(BaseModel):
    """Standard Harness API response."""
    success: bool
    result: dict[str, Any]
    execution_time_ms: float
    harness_version: str = __version__


# ── App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="OpenClaw-Medical-Harness API",
    description="Medical AI Agent Orchestration Framework — Built on Harness Theory",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize harnesses
_diagnosis_harness = DiagnosisHarness(specialty="neurology")
_drug_harness = DrugDiscoveryHarness()
_health_harness = HealthManagementHarness()
_registry = MedicalToolRegistry()

# Track server start time
_start_time = time.time()


# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["General"])
async def index() -> str:
    """Return an HTML introduction page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw-Medical-Harness</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
               background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
               color: #e2e8f0; min-height: 100vh; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem;
              background: linear-gradient(90deg, #60a5fa, #a78bfa);
              -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }}
        .card {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                 border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }}
        .card h3 {{ color: #60a5fa; margin-bottom: 0.5rem; }}
        .endpoints {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        .method {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
                   font-weight: bold; font-size: 0.85rem; margin-right: 8px; }}
        .get {{ background: #065f46; color: #6ee7b7; }}
        .post {{ background: #1e40af; color: #93c5fd; }}
        a {{ color: #60a5fa; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px;
                  background: rgba(96,165,250,0.15); color: #60a5fa; font-size: 0.85rem;
                  margin-right: 8px; margin-bottom: 8px; }}
        .formula {{ background: rgba(167,139,250,0.1); border-left: 3px solid #a78bfa;
                    padding: 1rem; margin: 1rem 0; font-family: monospace; border-radius: 0 8px 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 OpenClaw-Medical-Harness</h1>
        <p class="subtitle">Medical AI Agent Orchestration Framework — Built on Harness Theory · v{__version__}</p>

        <div class="card">
            <h3>🧠 Core Philosophy</h3>
            <p>"在AI领域，Harness（环境设计）比模型本身更重要。"</p>
            <div class="formula">
                Medical Harness = Tool Chain + Info Format + Context Mgmt + Recovery + Validation
            </div>
            <p>模型可替换，Harness是私有的。优秀的Harness设计使性能提升64%。</p>
        </div>

        <div class="card">
            <h3>🔌 API Endpoints</h3>
            <div class="endpoints">
                <div>
                    <span class="method post">POST</span> <a href="/docs#/General/diagnose_diagnose_post">/diagnose</a>
                    <p style="color:#94a3b8; font-size:0.9rem; margin-top:4px;">Medical diagnosis from symptoms</p>
                </div>
                <div>
                    <span class="method post">POST</span> <a href="/docs#/General/drug_discovery_drug_discovery_post">/drug-discovery</a>
                    <p style="color:#94a3b8; font-size:0.9rem; margin-top:4px;">Drug target screening & ADMET</p>
                </div>
                <div>
                    <span class="method post">POST</span> <a href="/docs#/General/health_health_post">/health</a>
                    <p style="color:#94a3b8; font-size:0.9rem; margin-top:4px;">Personalized health management</p>
                </div>
                <div>
                    <span class="method get">GET</span> <a href="/health-check">/health-check</a>
                    <p style="color:#94a3b8; font-size:0.9rem; margin-top:4px;">Server health status</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🔗 Links</h3>
            <div>
                <span class="badge"><a href="/docs">Swagger UI</a></span>
                <span class="badge"><a href="/redoc">ReDoc</a></span>
                <span class="badge"><a href="https://github.com/MoKangMedical/openclaw-medical-harness">GitHub</a></span>
            </div>
        </div>
    </div>
</body>
</html>"""


@app.get("/health-check", tags=["General"])
async def health_check() -> dict[str, Any]:
    """Server health check endpoint."""
    uptime = time.time() - _start_time
    return {
        "status": "healthy",
        "version": __version__,
        "uptime_seconds": round(uptime, 1),
        "harnesses": {
            "diagnosis": _diagnosis_harness.name,
            "drug_discovery": _drug_harness.name,
            "health_management": _health_harness.name,
        },
        "tools_registered": len(_registry.list_all()),
    }


@app.post("/diagnose", response_model=HarnessResponse, tags=["Harness"])
async def diagnose(request: DiagnoseRequest) -> HarnessResponse:
    """Run diagnostic Harness on patient symptoms.

    Takes a list of symptoms and optional patient info, returns
    a structured diagnostic assessment with confidence scores,
    differential diagnoses, and recommended next steps.
    """
    start = time.time()

    input_data: dict[str, Any] = {
        "symptoms": request.symptoms,
        "specialty": request.specialty,
        "language": request.language,
    }
    if request.patient:
        input_data["patient"] = request.patient.model_dump(exclude_none=True)

    try:
        result = _diagnosis_harness.execute(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis harness error: {e}")

    elapsed = (time.time() - start) * 1000
    return HarnessResponse(
        success=True,
        result=result,
        execution_time_ms=round(elapsed, 2),
    )


@app.post("/drug-discovery", response_model=HarnessResponse, tags=["Harness"])
async def drug_discovery(request: DrugDiscoveryRequest) -> HarnessResponse:
    """Run drug discovery Harness.

    Takes a target and disease, returns candidate compounds with
    ADMET predictions and optimization suggestions.
    """
    start = time.time()

    input_data: dict[str, Any] = {
        "target": request.target,
        "disease": request.disease,
        "max_compounds": request.max_compounds,
    }

    try:
        result = _drug_harness.execute(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drug discovery harness error: {e}")

    elapsed = (time.time() - start) * 1000
    return HarnessResponse(
        success=True,
        result=result,
        execution_time_ms=round(elapsed, 2),
    )


@app.post("/health", response_model=HarnessResponse, tags=["Harness"])
async def health_management(request: HealthRequest) -> HarnessResponse:
    """Run health management Harness.

    Takes health conditions and goals, returns a personalized
    care plan with adherence tracking and follow-up schedule.
    """
    start = time.time()

    input_data: dict[str, Any] = {
        "conditions": request.conditions,
        "health_goal": request.health_goal,
        "lab_results": request.lab_results,
        "wearable_data": request.wearable_data,
        "patient": {"age": request.age} if request.age else {},
    }

    try:
        result = _health_harness.execute(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health harness error: {e}")

    elapsed = (time.time() - start) * 1000
    return HarnessResponse(
        success=True,
        result=result,
        execution_time_ms=round(elapsed, 2),
    )


# ── Entrypoint ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
