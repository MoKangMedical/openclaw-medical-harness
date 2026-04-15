"""MCP Tool Registry — pre-configured medical data source tools.

Provides a centralized registry of MCP-compatible medical tools:
  - PubMed: Literature search and citation analysis
  - ChEMBL: Drug compound bioactivity data
  - OpenTargets: Target-disease association evidence
  - OMIM: Mendelian genetics and rare disease data
  - OpenFDA: Drug safety and adverse event signals
  - RDKit: Cheminformatics calculations

Each tool is defined with its MCP endpoint, parameters, and
Harness integration metadata.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from openclaw_medical_harness.base import ToolBase

logger = logging.getLogger(__name__)


class MCPCategory(str, Enum):
    """Categories for MCP tool classification."""

    LITERATURE = "literature"
    DRUG = "drug"
    GENETICS = "genetics"
    SAFETY = "safety"
    TARGET = "target"


@dataclass
class MCPToolDefinition:
    """Definition of an MCP-compatible medical tool.

    Attributes:
        name: Unique tool identifier.
        display_name: Human-readable name.
        description: What this tool does.
        category: Tool category for filtering.
        mcp_endpoint: MCP server endpoint URL.
        mcp_method: Method to call on the MCP server.
        parameters_schema: JSON schema for tool parameters.
        harness_compatible: Which Harness types can use this tool.
        rate_limit_per_minute: API rate limit.
        requires_auth: Whether authentication is required.
    """

    name: str = ""
    display_name: str = ""
    description: str = ""
    category: MCPCategory = MCPCategory.LITERATURE
    mcp_endpoint: str = ""
    mcp_method: str = ""
    parameters_schema: dict[str, Any] = field(default_factory=dict)
    harness_compatible: list[str] = field(
        default_factory=lambda: ["diagnosis", "drug_discovery", "health_management"]
    )
    rate_limit_per_minute: int = 60
    requires_auth: bool = False


class MCPToolAdapter(ToolBase):
    """Adapter that wraps an MCPToolDefinition as a ToolBase."""

    def __init__(self, definition: MCPToolDefinition, client: Any | None = None) -> None:
        self._definition = definition
        self._client = client
        self._call_count = 0

    @property
    def name(self) -> str:
        return self._definition.name

    @property
    def description(self) -> str:
        return self._definition.description

    def execute(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the MCP tool call."""
        self._call_count += 1
        if self._call_count > self._definition.rate_limit_per_minute:
            logger.warning("Rate limit reached for tool %s", self.name)
            return {"error": "rate_limited", "tool": self.name}

        params = self._extract_params(context, prior_results)
        logger.info("MCP call: %s.%s with %d params",
                     self.name, self._definition.mcp_method, len(params))

        return {
            "tool": self.name,
            "method": self._definition.mcp_method,
            "params": params,
            "status": "placeholder",
            "message": f"MCP tool '{self.name}' — configure MCP client for live data",
        }

    def _extract_params(
        self, context: dict[str, Any], prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract tool parameters from context and prior results."""
        input_data = context.get("input", {})
        params: dict[str, Any] = {}

        if self._definition.category == MCPCategory.LITERATURE:
            params["query"] = input_data.get("search_query", "")
            params["symptoms"] = input_data.get("symptoms", [])
        elif self._definition.category == MCPCategory.DRUG:
            params["compound"] = input_data.get("compound", "")
            params["target"] = input_data.get("target", "")
        elif self._definition.category == MCPCategory.TARGET:
            params["target"] = input_data.get("target", "")
            params["disease"] = input_data.get("disease", "")
        elif self._definition.category == MCPCategory.GENETICS:
            params["gene"] = input_data.get("gene", "")
            params["phenotype"] = input_data.get("phenotype", "")
        elif self._definition.category == MCPCategory.SAFETY:
            params["drug"] = input_data.get("drug", "")

        return params


# ── Pre-registered medical MCP tools ───────────────────────────────

_MEDICAL_TOOLS: dict[str, MCPToolDefinition] = {
    "pubmed": MCPToolDefinition(
        name="pubmed",
        display_name="PubMed Literature Search",
        description="Search PubMed for biomedical literature, retrieve abstracts and citations",
        category=MCPCategory.LITERATURE,
        mcp_endpoint="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        mcp_method="esearch.fcgi",
        parameters_schema={
            "query": {"type": "string", "required": True},
            "max_results": {"type": "integer", "default": 20},
            "sort": {"type": "string", "enum": ["relevance", "date"], "default": "relevance"},
        },
        harness_compatible=["diagnosis", "drug_discovery", "health_management"],
        rate_limit_per_minute=10,
    ),
    "chembl": MCPToolDefinition(
        name="chembl",
        display_name="ChEMBL Drug Data",
        description="Query ChEMBL for drug compound bioactivity, structure, and target data",
        category=MCPCategory.DRUG,
        mcp_endpoint="https://www.ebi.ac.uk/chembl/api/data",
        mcp_method="molecule",
        parameters_schema={
            "target_chembl_id": {"type": "string"},
            "molecule_chembl_id": {"type": "string"},
            "pref_name": {"type": "string"},
        },
        harness_compatible=["drug_discovery"],
        rate_limit_per_minute=30,
    ),
    "opentargets": MCPToolDefinition(
        name="opentargets",
        display_name="OpenTargets Target-Disease Association",
        description="Query OpenTargets for target-disease association scores and evidence",
        category=MCPCategory.TARGET,
        mcp_endpoint="https://api.platform.opentargets.org/api/v4/graphql",
        mcp_method="target",
        parameters_schema={
            "target_id": {"type": "string", "required": True},
            "disease_id": {"type": "string"},
        },
        harness_compatible=["diagnosis", "drug_discovery"],
        rate_limit_per_minute=30,
    ),
    "omim": MCPToolDefinition(
        name="omim",
        display_name="OMIM Genetic Disease Lookup",
        description="Search OMIM for Mendelian disease-gene-phenotype relationships",
        category=MCPCategory.GENETICS,
        mcp_endpoint="https://api.omim.org/api",
        mcp_method="entry",
        parameters_schema={
            "mim_number": {"type": "string"},
            "gene": {"type": "string"},
            "phenotype": {"type": "string"},
        },
        harness_compatible=["diagnosis"],
        rate_limit_per_minute=10,
        requires_auth=True,
    ),
    "openfda": MCPToolDefinition(
        name="openfda",
        display_name="OpenFDA Drug Safety",
        description="Query OpenFDA for drug adverse event reports and safety signals",
        category=MCPCategory.SAFETY,
        mcp_endpoint="https://api.fda.gov",
        mcp_method="drug/event.json",
        parameters_schema={
            "drug_name": {"type": "string", "required": True},
            "date_range": {"type": "string"},
            "serious_only": {"type": "boolean", "default": True},
        },
        harness_compatible=["drug_discovery", "health_management"],
        rate_limit_per_minute=20,
    ),
    "rdkit": MCPToolDefinition(
        name="rdkit",
        display_name="RDKit Cheminformatics",
        description="Molecular structure analysis, property calculation, and similarity search",
        category=MCPCategory.DRUG,
        mcp_endpoint="https://rdkit.local/api",
        mcp_method="compute",
        parameters_schema={
            "smiles": {"type": "string", "required": True},
            "properties": {"type": "array", "default": ["mw", "logp", "tpsa"]},
        },
        harness_compatible=["drug_discovery"],
        rate_limit_per_minute=60,
    ),
}


class MedicalToolRegistry:
    """Registry of pre-configured medical MCP tools."""

    def __init__(self, mcp_client: Any | None = None) -> None:
        self._definitions = dict(_MEDICAL_TOOLS)
        self._mcp_client = mcp_client
        self._custom_tools: dict[str, MCPToolDefinition] = {}

    def register(
        self, definition: MCPToolDefinition, override: bool = False,
    ) -> None:
        """Register a custom MCP tool."""
        if definition.name in self._definitions and not override:
            raise ValueError(
                f"Tool '{definition.name}' already registered. Use override=True to replace."
            )
        self._custom_tools[definition.name] = definition
        self._definitions[definition.name] = definition
        logger.info("Registered MCP tool: %s", definition.name)

    def get(self, name: str) -> MCPToolAdapter | None:
        """Get a tool by name as an MCPToolAdapter."""
        definition = self._definitions.get(name)
        if not definition:
            return None
        return MCPToolAdapter(definition, client=self._mcp_client)

    def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """List tools as dicts, optionally filtered by category string."""
        tools = self._definitions.values()
        if category:
            tools = [d for d in tools if d.category.value == category]
        return [
            {"name": d.name, "display_name": d.display_name,
             "category": d.category.value, "description": d.description}
            for d in tools
        ]

    def list_categories(self) -> list[str]:
        """Return unique category strings."""
        return sorted({d.category.value for d in self._definitions.values()})

    def list_all(self) -> list[MCPToolDefinition]:
        """List all registered tool definitions."""
        return list(self._definitions.values())

    def list_by_category(self, category: MCPCategory) -> list[MCPToolDefinition]:
        """List tools filtered by category enum."""
        return [d for d in self._definitions.values() if d.category == category]

    def get_tools_for_harness(self, harness_type: str) -> list[MCPToolAdapter]:
        """Get all tools compatible with a specific Harness type."""
        return [
            MCPToolAdapter(defn, client=self._mcp_client)
            for defn in self._definitions.values()
            if harness_type in defn.harness_compatible
        ]
