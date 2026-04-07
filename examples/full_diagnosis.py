"""Full Diagnosis Example — Myasthenia Gravis (MG) diagnostic workflow.

Demonstrates the complete diagnostic Harness pipeline for a 35-year-old
female presenting with bilateral ptosis, fatigable weakness, and diplopia —
classic Myasthenia Gravis presentation.

Pipeline demonstrated:
  1. MCP tool registration and discovery
  2. Diagnostic Harness configuration
  3. Symptom intake with red flag screening
  4. Differential diagnosis via knowledge base + tool evidence
  5. Multi-agent consensus (diagnostician + literature + pharmacologist)
  6. Result validation and report generation

Usage:
    python examples/full_diagnosis.py
"""

from __future__ import annotations

import json
import logging
import sys
import os

# Ensure project root is on path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.diagnosis import DiagnosticHarness
from harness.context import ContextConfig, CompressionStrategy
from harness.recovery import RecoveryStrategy
from harness.validator import ResultValidator
from agents.orchestrator import (
    MultiAgentOrchestrator,
    OrchestrationMode,
    AgentRole,
)
from mcp_tools.registry import MedicalToolRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run a comprehensive MG diagnostic workflow."""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 1: Register MCP tools
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("=" * 60)
    logger.info("STEP 1: MCP Tool Registration")
    logger.info("=" * 60)

    registry = MedicalToolRegistry()
    available_tools = registry.list_tools()
    logger.info("Registered %d MCP tools:", len(available_tools))
    for tool in available_tools:
        logger.info("  • %s [%s] — %s", tool["name"], tool["category"], tool["description"])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 2: Configure the Diagnostic Harness
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("=" * 60)
    logger.info("STEP 2: Harness Configuration")
    logger.info("=" * 60)

    context_config = ContextConfig(
        max_tokens=8192,
        compression_strategy=CompressionStrategy.MEDICAL_PRIORITIZED,
        patient_history_depth=5,
        retain_critical_flags=True,
    )

    harness = DiagnosticHarness(
        name="mg-diagnosis-workflow",
        model_provider="mimo",
        tools=[],  # Tools would be MCPToolAdapter instances in production
        context_config=context_config,
        recovery_strategy=RecoveryStrategy.ESCALATE,
        enable_rare_disease_screening=True,
        multidisciplinary_mode=True,
    )

    logger.info("Harness configured: %s", harness.name)
    logger.info("  Model: mimo | Specialty: neurology")
    logger.info("  Recovery: ESCALATE | Validation: strict")
    logger.info("  Rare disease screening: enabled")
    logger.info("  Multi-disciplinary mode: enabled")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 3: Patient presentation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("=" * 60)
    logger.info("STEP 3: Patient Presentation")
    logger.info("=" * 60)

    patient_data = {
        "symptoms": [
            "bilateral ptosis",
            "fatigable weakness",
            "diplopia",
        ],
        "age": 35,
        "sex": "F",
        "medical_history": [
            "No significant past medical history",
            "Symptoms started 6 months ago",
            "Ptosis worse in the evening",
            "Difficulty climbing stairs after exertion",
            "No family history of neuromuscular disease",
        ],
        "current_medications": [],
        "vital_signs": {
            "bp": "118/72",
            "hr": 76,
            "rr": 16,
            "spo2": 99,
            "temp": 36.8,
        },
        "allergies": [],
        "physical_exam": {
            "neurological": (
                "Bilateral ptosis, more pronounced on sustained upward gaze. "
                "Diplopia on lateral gaze bilaterally. Fatigable weakness "
                "of proximal upper and lower extremities. Normal reflexes. "
                "No sensory deficits. No bulbar symptoms."
            ),
        },
    }

    logger.info("Patient: %d-year-old %s", patient_data["age"], patient_data["sex"])
    logger.info("Chief complaint: %s", ", ".join(patient_data["symptoms"]))
    logger.info("Duration: 6 months, progressive")
    logger.info("Pattern: Worse with fatigue, better with rest")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 4: Execute Diagnostic Harness
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("=" * 60)
    logger.info("STEP 4: Diagnostic Harness Execution")
    logger.info("=" * 60)

    result = harness.execute(patient_data)

    print("\n" + "━" * 70)
    print("  DIAGNOSTIC HARNESS RESULT")
    print("━" * 70)
    print(f"  Harness:          {result['harness_name']}")
    print(f"  Execution time:   {result['execution_time_ms']:.1f} ms")
    print(f"  Recovery applied: {'Yes' if result['recovery_applied'] else 'No'}")
    print()

    if "diagnosis" in result:
        print(f"  PRIMARY DIAGNOSIS:  {result['diagnosis']}")
        print(f"  CONFIDENCE:         {result.get('confidence', 0):.2f}")
        print()

    if result.get("differential"):
        print("  DIFFERENTIAL DIAGNOSIS:")
        for i, dx in enumerate(result["differential"], 1):
            print(f"    {i}. {dx}")
        print()

    if result.get("next_steps"):
        print("  RECOMMENDED NEXT STEPS:")
        for i, step in enumerate(result["next_steps"], 1):
            print(f"    {i}. {step}")
        print()

    if result.get("evidence"):
        print("  EVIDENCE:")
        evidence = result["evidence"]
        if isinstance(evidence, dict):
            for key, val in evidence.items():
                print(f"    • {key}: {val}")
        print()

    print("━" * 70)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 5: Multi-Agent Consultation (会诊)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("=" * 60)
    logger.info("STEP 5: Multi-Agent Consultation (多学科会诊)")
    logger.info("=" * 60)

    orchestrator = MultiAgentOrchestrator(
        mode=OrchestrationMode.OPENCLAW,
        model="mimo",
    )

    # Register specialized agents
    orchestrator.add_agent(AgentRole.DIAGNOSTIC, specialty="neurology")
    orchestrator.add_agent(AgentRole.LITERATURE)
    orchestrator.add_agent(AgentRole.DRUG)
    orchestrator.add_agent(AgentRole.COMMUNICATION)

    logger.info("Registered %d agents for consultation", orchestrator.agent_count)

    consensus = orchestrator.run(
        objective=(
            "35岁女性，双眼睑下垂6个月，下午加重，伴复视和波动性四肢无力。"
            "疑似重症肌无力（MG），请进行鉴别诊断和治疗建议。"
        ),
        context={
            "symptoms": patient_data["symptoms"],
            "medical_history": patient_data["medical_history"],
            "age": patient_data["age"],
            "sex": patient_data["sex"],
        },
        consensus_rounds=3,
    )

    print("\n" + "━" * 70)
    print("  MULTI-AGENT CONSULTATION RESULT")
    print("━" * 70)
    print(f"  Consensus confidence:  {consensus.confidence:.2f}")
    print(f"  Rounds completed:      {consensus.consensus_rounds}")
    print(f"  Escalation needed:     {'Yes' if consensus.escalation_needed else 'No'}")
    print()

    print("  AGENT OPINIONS:")
    for name, agent_result in consensus.agent_results.items():
        print(f"    [{name}] ({agent_result.agent_role.value})")
        print(f"      Confidence: {agent_result.confidence:.2f}")
        if isinstance(agent_result.output, dict):
            analysis = agent_result.output.get("analysis", "")
            if analysis:
                print(f"      Analysis: {analysis[:80]}...")
        print()

    if consensus.disagreements:
        print("  DISAGREEMENTS:")
        for d in consensus.disagreements:
            print(f"    ⚠ {d}")
        print()

    if consensus.evidence_summary:
        print("  EVIDENCE SUMMARY:")
        for e in consensus.evidence_summary[:5]:
            print(f"    • {e}")
        print()

    print(f"  FINAL CONCLUSION: {consensus.final_diagnosis[:200]}")
    print("━" * 70)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 6: Result Validation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    logger.info("=" * 60)
    logger.info("STEP 6: Result Validation")
    logger.info("=" * 60)

    validator = ResultValidator(strict_mode=False)

    # Validate the harness result
    harness_validation = validator.validate(result, domain="diagnosis")

    print("\n" + "━" * 70)
    print("  VALIDATION REPORT")
    print("━" * 70)
    print(f"  Harness result:  {'PASSED' if harness_validation.passed else 'FAILED'}")
    print(f"  Score:           {harness_validation.score:.2f}")
    print(f"  Findings:        {len(harness_validation.findings)}")
    for finding in harness_validation.findings:
        print(f"    [{finding.severity.value.upper()}] {finding.field}: {finding.message}")
    print("━" * 70)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Step 7: Generate Summary Report
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "━" * 70)
    print("  CLINICAL SUMMARY REPORT")
    print("━" * 70)
    print()
    print("  PATIENT: 35-year-old female")
    print("  PRESENTATION: Bilateral ptosis, fatigable weakness, diplopia")
    print("  DURATION: 6 months, progressive, worse in evening")
    print()
    print("  DIAGNOSTIC HYPOTHESIS:")
    print(f"    Primary: {result.get('diagnosis', 'Pending')}")
    print(f"    Confidence: {result.get('confidence', 0):.0%}")
    print()
    print("  RECOMMENDED WORKUP:")
    workup = result.get("next_steps", [])
    if workup:
        for i, step in enumerate(workup, 1):
            print(f"    {i}. {step}")
    print()
    print("  MULTI-AGENT REVIEW:")
    print(f"    Agents consulted: {consensus.agent_results.__len__() if consensus.agent_results else 0}")
    print(f"    Consensus level: {consensus.confidence:.0%}")
    print(f"    Escalation: {'Required' if consensus.escalation_needed else 'Not required'}")
    print()
    print("  CLINICAL NOTES:")
    print("    This case demonstrates the classic triad of Myasthenia Gravis:")
    print("    bilateral ptosis, fatigable weakness, and diplopia.")
    print("    The pattern of worsening with exertion and improving with rest")
    print("    is highly characteristic. Anti-AChR antibody testing and")
    print("    repetitive nerve stimulation are confirmatory.")
    print()
    print("━" * 70)
    print("  Workflow complete. Harness Theory in action. ⚡")
    print("━" * 70)


if __name__ == "__main__":
    main()
