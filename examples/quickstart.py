"""Quick Start — 5 lines to run a diagnostic Harness.

This example demonstrates the simplest way to use OpenClaw-Medical-Harness:
just create a DiagnosticHarness and execute it with patient symptoms.

Usage:
    python examples/quickstart.py
"""

from harness.diagnosis import DiagnosticHarness


def main() -> None:
    """Run a quick diagnostic Harness demo."""

    # 1. Create a diagnostic Harness
    harness = DiagnosticHarness(name="quick-start-dx")

    # 2. Execute with patient symptoms
    result = harness.execute({
        "symptoms": ["chest pain", "shortness of breath"],
        "age": 55,
        "sex": "male",
    })

    # 3. Print the results
    print(f"Status: {result.status}")
    print(f"Execution time: {result.metrics.execution_time_ms:.1f}ms")
    print(f"Harness: {result.harness_name}")
    print(f"Validation score: {result.metrics.validation_score:.2f}")


if __name__ == "__main__":
    main()
