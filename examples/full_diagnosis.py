"""Full Diagnosis Example — comprehensive diagnostic workflow.

Demonstrates the full diagnostic Harness pipeline with:
  - Multi-agent orchestration
  - MCP tool integration
  - Recovery mechanisms
  - Result validation

Usage:
    python examples/full_diagnosis.py
"""

import logging

from harness.diagnosis import DiagnosticHarness
from harness.context import ContextConfig, CompressionStrategy
from harness.recovery import RecoveryStrategy
from agents.orchestrator import MultiAgentOrchestrator, OrchestrationMode, AgentRole
from mcp_tools.registry import MedicalToolRegistry

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_full_diagnosis() -> None:
    """Run a comprehensive diagnostic workflow."""

    # ── Step 1: Set up MCP tools ──────────────────────────────────────
    registry = MedicalToolRegistry()
    diagnosis_tools = registry.get_tools_for_harness("diagnosis")
    logger.info("Available tools for diagnosis: %s", [t.name for t in diagnosis_tools])

    # ── Step 2: Configure the diagnostic Harness ──────────────────────
    context_config = ContextConfig(
        max_tokens=8192,
        compression_strategy=CompressionStrategy.MEDICAL_PRIORITIZED,
        patient_history_depth=3,
    )

    harness = DiagnosticHarness(
        name="full-diagnosis-workflow",
        model_provider="mimo",
        tools=diagnosis_tools,
        context_config=context_config,
        recovery_strategy=RecoveryStrategy.ESCALATE,
        enable_rare_disease_screening=True,
        multidisciplinary_mode=True,
    )

    # ── Step 3: Prepare patient data ──────────────────────────────────
    patient_data = {
        "symptoms": [
            "chest pain",
            "shortness of breath",
            "diaphoresis",
            "nausea",
        ],
        "age": 62,
        "sex": "male",
        "medical_history": [
            "hypertension",
            "type 2 diabetes",
            "hyperlipidemia",
            "family history of CAD",
        ],
        "current_medications": [
            "metformin 500mg BID",
            "lisinopril 10mg daily",
            "atorvastatin 40mg daily",
        ],
        "vital_signs": {
            "bp": "158/94",
            "hr": 102,
            "rr": 22,
            "spo2": 94,
            "temp": 37.1,
        },
        "allergies": ["penicillin"],
    }

    # ── Step 4: Execute the Harness ───────────────────────────────────
    logger.info("Executing diagnostic Harness for patient: %s", patient_data)
    result = harness.execute(patient_data)

    # ── Step 5: Review results ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DIAGNOSTIC HARNESS RESULT")
    print("=" * 60)
    print(f"Status:           {result.status.value}")
    print(f"Execution time:   {result.metrics.execution_time_ms:.1f}ms")
    print(f"Tools called:     {result.metrics.tools_called}")
    print(f"Tools succeeded:  {result.metrics.tools_succeeded}")
    print(f"Validation score: {result.metrics.validation_score:.2f}")
    print(f"Recovery attempts:{result.metrics.recovery_attempts}")
    print("=" * 60)

    # ── Step 6: Multi-agent orchestration demo ────────────────────────
    print("\n" + "=" * 60)
    print("MULTI-AGENT ORCHESTRATION")
    print("=" * 60)

    orchestrator = MultiAgentOrchestrator(
        mode=OrchestrationMode.OPENCLAW,
        model="mimo",
    )

    # Add relevant agents
    orchestrator.add_agent(AgentRole.DIAGNOSTIC)
    orchestrator.add_agent(AgentRole.LITERATURE)
    orchestrator.add_agent(AgentRole.DRUG)
    orchestrator.add_agent(AgentRole.COMMUNICATION)

    # Run orchestrated analysis
    agent_results = orchestrator.run(
        objective="Comprehensive evaluation of 62yo male with chest pain, "
                 "SOB, diaphoresis — rule out ACS",
        context=patient_data,
    )

    for agent_result in agent_results:
        print(f"\n[{agent_result.agent_role.value.upper()} AGENT]")
        print(f"  Output: {str(agent_result.output)[:100]}...")
        print(f"  Confidence: {agent_result.confidence:.2f}")

    print("\n" + "=" * 60)
    print("Workflow complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_full_diagnosis()
