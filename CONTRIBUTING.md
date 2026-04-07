# Contributing to OpenClaw-Medical-Harness

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/MoKangMedical/openclaw-medical-harness.git
cd openclaw-medical-harness

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Project Structure

```
openclaw-medical-harness/
├── harness/                    # Core Harness implementations
│   ├── base.py                # BaseHarness abstract class
│   ├── context.py             # ContextManager
│   ├── recovery.py            # FailureRecovery
│   ├── validator.py           # ResultValidator
│   ├── diagnosis/             # Diagnostic Harness
│   ├── drug_discovery/        # Drug Discovery Harness
│   └── health_management/     # Health Management Harness
├── agents/                     # Multi-agent orchestration
│   └── orchestrator.py        # MultiAgentOrchestrator
├── mcp_tools/                  # MCP tool registry
│   └── registry.py            # MedicalToolRegistry
├── skills/                     # OpenClaw skill definitions
├── examples/                   # Usage examples
├── docs/                       # Documentation
└── tests/                      # Test suite
```

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker
- Include reproduction steps
- Specify your Python version and OS

### Adding a New Medical Tool

1. Define the tool in `mcp_tools/registry.py`:
   ```python
   my_tool = MCPToolDefinition(
       name="my_medical_tool",
       display_name="My Medical Tool",
       description="What it does",
       category=MCPCategory.LITERATURE,  # or other category
       mcp_endpoint="https://...",
       mcp_method="method_name",
       parameters_schema={...},
   )
   ```

2. Register it in `_MEDICAL_TOOLS` dict
3. Add tests in `tests/test_mcp_tools.py`
4. Update documentation

### Adding a New Harness

1. Create a new package under `harness/`
2. Extend `BaseHarness` and implement:
   - `_build_prompt()` — domain-specific prompt formatting
   - `_domain()` — domain identifier string
3. Add domain-specific validation rules in `validator.py`
4. Create example scripts in `examples/`
5. Update `README.md` and `docs/architecture.md`

### Adding a New Skill

1. Create a YAML file in `skills/<category>/`
2. Follow the schema in `skills/clinical/diagnostic_reasoning.yaml`
3. Include input/output schemas, tool dependencies, and recovery config

## Code Style

- **Python 3.10+** with type annotations
- **Ruff** for linting (`ruff check .`)
- **MyPy** for type checking (`mypy .`)
- Docstrings: Google style with type annotations
- Line length: 100 characters

### Example

```python
def process_symptoms(
    symptoms: list[str],
    severity_threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """Process and filter symptoms by severity.

    Args:
        symptoms: Raw symptom strings from patient input.
        severity_threshold: Minimum severity score to retain (0-1).

    Returns:
        List of structured symptom dicts with severity scores.

    Raises:
        ValueError: If severity_threshold is outside [0, 1].
    """
    if not 0.0 <= severity_threshold <= 1.0:
        raise ValueError(f"Threshold must be in [0, 1], got {severity_threshold}")
    # ...
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=harness --cov=agents --cov=mcp_tools

# Run specific test file
pytest tests/test_diagnostic_harness.py
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with tests
4. Ensure all checks pass (`ruff check . && mypy . && pytest`)
5. Submit a PR with a clear description

## Harness Theory Contributions

We welcome contributions that advance Harness theory in medical AI:

- **New Harness designs** for medical domains
- **Context management** strategies for clinical data
- **Recovery mechanisms** for diagnostic uncertainty
- **Validation rules** for medical safety
- **Performance benchmarks** demonstrating Harness impact

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
