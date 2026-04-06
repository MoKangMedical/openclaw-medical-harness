"""
Medical Tool Registry — MCP工具注册中心。

预注册的医疗MCP工具：
- PubMed：文献检索
- ChEMBL：药物活性数据
- OpenTargets：靶点-疾病关联
- OMIM：遗传病数据库
- OpenFDA：药物安全
- RDKit：分子计算
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class MCPTool:
    """MCP工具定义。"""
    name: str
    description: str
    endpoint: str = ""
    category: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    execute_fn: Optional[Callable] = None

    def execute(self, context: dict[str, Any], **kwargs) -> dict[str, Any]:
        """执行工具调用。"""
        if self.execute_fn:
            return self.execute_fn(context, **kwargs)
        return {"tool": self.name, "status": "not_implemented"}


# 预注册的医疗工具
BUILTIN_TOOLS: dict[str, MCPTool] = {
    "pubmed": MCPTool(
        name="pubmed",
        description="PubMed文献检索 — 搜索生物医学文献",
        endpoint="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        category="literature",
        parameters={"query": "string", "max_results": "int", "sort": "string"},
    ),
    "chembl": MCPTool(
        name="chembl",
        description="ChEMBL药物数据 — 化合物活性、靶点、适应症",
        endpoint="https://www.ebi.ac.uk/chembl/api/data/",
        category="drug",
        parameters={"query_type": "string", "identifier": "string"},
    ),
    "opentargets": MCPTool(
        name="opentargets",
        description="OpenTargets靶点关联 — 基因-疾病-药物关联网络",
        endpoint="https://api.platform.opentargets.org/api/v4/graphql",
        category="target",
        parameters={"gene": "string", "disease": "string"},
    ),
    "omim": MCPTool(
        name="omim",
        description="OMIM遗传病数据库 — 人类孟德尔遗传病信息",
        endpoint="https://api.omim.org/api/",
        category="genetics",
        parameters={"search": "string", "mim_number": "string"},
    ),
    "openfda": MCPTool(
        name="openfda",
        description="OpenFDA药物安全 — 不良事件、药物标签、召回信息",
        endpoint="https://api.fda.gov/",
        category="safety",
        parameters={"search": "string", "limit": "int"},
    ),
    "rdkit": MCPTool(
        name="rdkit",
        description="RDKit分子计算 — 分子描述符、相似性、子结构搜索",
        category="cheminformatics",
        parameters={"smiles": "string", "operation": "string"},
    ),
}


class MedicalToolRegistry:
    """
    医疗MCP工具注册中心。

    管理和调度所有医疗相关的MCP工具。
    支持自定义工具注册和工具链编排。
    """

    def __init__(self):
        self._tools: dict[str, MCPTool] = {}
        # 自动注册内置工具
        for name, tool in BUILTIN_TOOLS.items():
            self._tools[name] = tool

    def register(self, name: str, tool: MCPTool | Any) -> None:
        """注册工具。"""
        if isinstance(tool, MCPTool):
            self._tools[name] = tool
        elif hasattr(tool, "execute"):
            self._tools[name] = MCPTool(
                name=name,
                description=getattr(tool, "description", ""),
                execute_fn=tool.execute,
            )
        else:
            raise ValueError(f"Tool must be MCPTool or have execute method")

    def get(self, name: str) -> Optional[MCPTool]:
        """获取工具。"""
        return self._tools.get(name)

    def list_tools(self, category: str = "") -> list[dict[str, str]]:
        """列出所有工具。"""
        tools = []
        for name, tool in self._tools.items():
            if category and tool.category != category:
                continue
            tools.append({
                "name": name,
                "description": tool.description,
                "category": tool.category,
            })
        return tools

    def list_categories(self) -> list[str]:
        """列出所有工具分类。"""
        return list(set(t.category for t in self._tools.values()))
