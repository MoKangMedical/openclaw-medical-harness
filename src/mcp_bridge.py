"""
MCP Bridge — Model Context Protocol 桥接模块
工具注册、调用、结果解析
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import time


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict
    handler: Optional[Callable] = None


@dataclass
class MCPCallResult:
    """MCP 调用结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class MCPBridge:
    """MCP 桥接器"""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.call_history: List[MCPCallResult] = []
    
    def register_tool(self, tool: MCPTool):
        """注册 MCP 工具"""
        self.tools[tool.name] = tool
    
    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    def call_tool(self, tool_name: str, arguments: Dict) -> MCPCallResult:
        """调用 MCP 工具"""
        start_time = time.time()
        
        if tool_name not in self.tools:
            return MCPCallResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool {tool_name} not found",
                execution_time=time.time() - start_time
            )
        
        tool = self.tools[tool_name]
        
        try:
            if tool.handler:
                result = tool.handler(**arguments)
            else:
                result = {"message": f"Tool {tool_name} executed (mock)"}
            
            call_result = MCPCallResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            call_result = MCPCallResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
        
        self.call_history.append(call_result)
        return call_result
    
    def get_call_history(self, limit: int = 100) -> List[MCPCallResult]:
        """获取调用历史"""
        return self.call_history[-limit:]


# 预定义的医疗 MCP 工具
MEDICAL_TOOLS = [
    MCPTool(
        name="pubmed_search",
        description="搜索 PubMed 医学文献",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}}
    ),
    MCPTool(
        name="drug_interaction_check",
        description="检查药物相互作用",
        input_schema={"type": "object", "properties": {"drugs": {"type": "array"}}}
    ),
    MCPTool(
        name="clinical_guideline",
        description="获取临床指南",
        input_schema={"type": "object", "properties": {"disease": {"type": "string"}}}
    ),
    MCPTool(
        name="lab_reference",
        description="查询检验参考值",
        input_schema={"type": "object", "properties": {"test_name": {"type": "string"}}}
    ),
    MCPTool(
        name="icd10_lookup",
        description="ICD-10 编码查询",
        input_schema={"type": "object", "properties": {"code_or_name": {"type": "string"}}}
    )
]
