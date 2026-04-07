"""MCP Tool Registry — pre-configured medical data source tools.

Provides a centralized registry of MCP-compatible medical tools:
  - PubMed: Literature search and citation analysis
  - ChEMBL: Drug compound bioactivity data
  - OpenTargets: Target-disease association evidence
  - OMIM: Mendelian genetics and rare disease data
  - OpenFDA: Drug safety and adverse event signals

Each tool is defined with its MCP endpoint, parameters, and
Harness integration metadata.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from openclaw_medical_harness.harness.base import ToolBase

logger = logging.getLogger(__name__)


class MCPCategory(str, Enum):
    """Categories for MCP tool classification."""

    LITERATURE = "literature"
    DRUG_DATA = "drug_data"
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
    """Adapter that wraps an MCPToolDefinition as a ToolBase.

    Translates between the Harness tool interface and the MCP protocol,
    enabling seamless integration of external medical data sources.
    """

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
        """Execute the MCP tool call.

        Args:
            context: Current Harness context.
            prior_results: Results from earlier tools in the chain.

        Returns:
            Dict with the tool's response data.
        """
        self._call_count += 1

        # Rate limit check
        if self._call_count > self._definition.rate_limit_per_minute:
            logger.warning("Rate limit reached for tool %s", self.name)
            return {"error": "rate_limited", "tool": self.name}

        # Extract parameters from context
        params = self._extract_params(context, prior_results)

        logger.info(
            "MCP call: %s.%s with %d params",
            self.name,
            self._definition.mcp_method,
            len(params),
        )

        # In production, this would make the actual MCP call
        # For now, return a structured placeholder
        return {
            "tool": self.name,
            "method": self._definition.mcp_method,
            "params": params,
            "status": "placeholder",
            "message": f"MCP tool '{self.name}' — configure MCP client for live data",
        }

    def _extract_params(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract tool parameters from context and prior results.

        Args:
            context: Current Harness context.
            prior_results: Results from earlier tools.

        Returns:
            Dict of parameters for the MCP call.
        """
        input_data = context.get("input", {})
        params: dict[str, Any] = {}

        # Tool-specific parameter extraction
        if self._definition.category == MCPCategory.LITERATURE:
            params["query"] = input_data.get("search_query", "")
            params["symptoms"] = input_data.get("symptoms", [])
        elif self._definition.category == MCPCategory.DRUG_DATA:
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


# Pre-registered medical MCP tools
_MEDICAL_TOOLS: dict[str, MCPToolDefinition] = {
    "pubmed_search": MCPToolDefinition(
        name="pubmed_search",
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
    "chembl_query": MCPToolDefinition(
        name="chembl_query",
        display_name="ChEMBL Drug Data",
        description="Query ChEMBL for drug compound bioactivity, structure, and target data",
        category=MCPCategory.DRUG_DATA,
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
    "opentargets_association": MCPToolDefinition(
        name="opentargets_association",
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
    "omim_lookup": MCPToolDefinition(
        name="omim_lookup",
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
    "openfae_safety": MCPToolDefinition(
        name="openfae_safety",
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
}


class MedicalToolRegistry:
    """Registry of pre-configured medical MCP tools.

    Provides a centralized way to discover, configure, and instantiate
    medical data tools for use within Harnesses.

    Example:
        >>> registry = MedicalToolRegistry()
        >>> tools = registry.get_tools_for_harness("diagnosis")
        >>> print([t.name for t in tools])
        ['pubmed_search', 'omim_lookup', 'openfae_safety']
    """

    def __init__(self, mcp_client: Any | None = None) -> None:
        self._definitions = dict(_MEDICAL_TOOLS)
        self._mcp_client = mcp_client
        self._custom_tools: dict[str, MCPToolDefinition] = {}

    def register(
        self,
        definition: MCPToolDefinition,
        override: bool = False,
    ) -> None:
        """Register a custom MCP tool.

        Args:
            definition: The tool definition to register.
            override: If True, override existing tool with same name.

        Raises:
            ValueError: If tool already registered and override is False.
        """
        if definition.name in self._definitions and not override:
            raise ValueError(
                f"Tool '{definition.name}' already registered. Use override=True to replace."
            )
        self._custom_tools[definition.name] = definition
        self._definitions[definition.name] = definition
        logger.info("Registered MCP tool: %s", definition.name)

    def get(self, name: str) -> MCPToolAdapter | None:
        """Get a tool by name as an MCPToolAdapter.

        Args:
            name: The tool name.

        Returns:
            MCPToolAdapter instance, or None if not found.
        """
        definition = self._definitions.get(name)
        if not definition:
            return None
        return MCPToolAdapter(definition, client=self._mcp_client)

    def get_tools_for_harness(self, harness_type: str) -> list[MCPToolAdapter]:
        """Get all tools compatible with a specific Harness type.

        Args:
            harness_type: Harness type ('diagnosis', 'drug_discovery', 'health_management').

        Returns:
            List of compatible MCPToolAdapter instances.
        """
        return [
            MCPToolAdapter(defn, client=self._mcp_client)
            for defn in self._definitions.values()
            if harness_type in defn.harness_compatible
        ]

    def list_all(self) -> list[MCPToolDefinition]:
        """List all registered tool definitions.

        Returns:
            List of all MCPToolDefinition objects.
        """
        return list(self._definitions.values())

    def list_by_category(self, category: MCPCategory) -> list[MCPToolDefinition]:
        """List tools filtered by category.

        Args:
            category: The MCP category to filter by.

        Returns:
            List of matching MCPToolDefinition objects.
        """
        return [d for d in self._definitions.values() if d.category == category]
