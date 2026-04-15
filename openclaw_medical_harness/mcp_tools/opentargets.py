"""
OpenTargets MCP Tool — 靶点-疾病关联查询。

使用 OpenTargets Platform GraphQL API，免费，无需API Key。
文档：https://platform.opentargets.org/api
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..base import ToolBase

logger = logging.getLogger(__name__)

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"


class OpenTargetsTool(ToolBase):
    """OpenTargets靶点-疾病关联查询工具。

    支持：
    - 按基因搜索靶点
    - 查询靶点-疾病关联证据
    - 获取已知药物信息

    Example:
        >>> tool = OpenTargetsTool()
        >>> result = tool.execute({"target": "EGFR", "disease": "NSCLC"}, {})
        >>> print(result["associations"])
    """

    @property
    def name(self) -> str:
        return "opentargets"

    @property
    def description(self) -> str:
        return "Query OpenTargets for target-disease associations"

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def execute(
        self,
        context: dict[str, Any],
        prior_results: dict[str, Any],
    ) -> dict[str, Any]:
        """查询靶点-疾病关联。"""
        target = context.get("target", "")
        disease = context.get("disease", "")

        # 从patient中提取
        if not target:
            target = context.get("patient", {}).get("target", "")
        if not disease:
            disease = context.get("patient", {}).get("disease", "")

        if not target:
            return {"associations": [], "error": "No target specified", "tool": "opentargets"}

        try:
            # 搜索靶点
            search_query = """
            query SearchTarget($queryString: String!) {
                search(queryString: $queryString, entityNames: ["target"], page: {index: 0, size: 3}) {
                    hits {
                        id
                        name
                        description
                        entity
                    }
                }
            }
            """

            search_resp = self._client.post(
                OPENTARGETS_API,
                json={"query": search_query, "variables": {"queryString": target}},
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()

            hits = search_data.get("data", {}).get("search", {}).get("hits", [])
            if not hits:
                return {"associations": [], "target": target, "tool": "opentargets"}

            target_id = hits[0]["id"]
            target_name = hits[0]["name"]

            # 查询靶点详情和关联疾病
            detail_query = """
            query TargetAssociations($ensemblId: String!) {
                target(ensemblId: $ensemblId) {
                    id
                    approvedSymbol
                    approvedName
                    associatedDiseases(page: {index: 0, size: 5}) {
                        count
                        rows {
                            disease {
                                id
                                name
                            }
                            score
                        }
                    }
                    knownDrugs(page: {index: 0, size: 5}) {
                        count
                        rows {
                            drug {
                                id
                                name
                                mechanismOfAction
                            }
                            phase
                        }
                    }
                }
            }
            """

            detail_resp = self._client.post(
                OPENTARGETS_API,
                json={"query": detail_query, "variables": {"ensemblId": target_id}},
            )
            detail_resp.raise_for_status()
            detail_data = detail_resp.json()

            target_info = detail_data.get("data", {}).get("target", {})

            associations = []
            for row in target_info.get("associatedDiseases", {}).get("rows", []):
                disease_info = row.get("disease", {})
                associations.append({
                    "disease_id": disease_info.get("id", ""),
                    "disease_name": disease_info.get("name", ""),
                    "score": row.get("score", 0),
                })

            drugs = []
            for row in target_info.get("knownDrugs", {}).get("rows", []):
                drug_info = row.get("drug", {})
                drugs.append({
                    "drug_id": drug_info.get("id", ""),
                    "drug_name": drug_info.get("name", ""),
                    "mechanism": drug_info.get("mechanismOfAction", ""),
                    "phase": row.get("phase", 0),
                })

            return {
                "target_id": target_id,
                "target_symbol": target_info.get("approvedSymbol", target_name),
                "target_name": target_info.get("approvedName", ""),
                "associations": associations,
                "known_drugs": drugs,
                "total_associations": target_info.get("associatedDiseases", {}).get("count", 0),
                "tool": "opentargets",
            }

        except Exception as e:
            logger.error("OpenTargets query failed: %s", str(e))
            return {"associations": [], "target": target, "error": str(e), "tool": "opentargets"}

    def close(self) -> None:
        self._client.close()
