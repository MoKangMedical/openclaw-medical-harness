"""
Harness Core Engine — 5步Pipeline
接收 → 解析 → 路由 → 执行 → 输出
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time


class PipelineStage(Enum):
    """Pipeline 阶段"""
    RECEIVE = "receive"
    PARSE = "parse"
    ROUTE = "route"
    EXECUTE = "execute"
    OUTPUT = "output"


@dataclass
class HarnessRequest:
    """Harness 请求"""
    request_id: str
    request_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float


@dataclass
class HarnessResponse:
    """Harness 响应"""
    request_id: str
    status: str
    result: Dict[str, Any]
    execution_time: float
    pipeline_trace: List[Dict]


class HarnessCore:
    """Harness 核心引擎"""
    
    def __init__(self):
        self.agents = {}
        self.tools = {}
        self.pipeline_stages = [
            PipelineStage.RECEIVE,
            PipelineStage.PARSE,
            PipelineStage.ROUTE,
            PipelineStage.EXECUTE,
            PipelineStage.OUTPUT
        ]
    
    def process(self, request: HarnessRequest) -> HarnessResponse:
        """处理请求的主流程"""
        start_time = time.time()
        trace = []
        
        # Stage 1: 接收
        trace.append({"stage": "receive", "timestamp": time.time()})
        
        # Stage 2: 解析
        parsed = self._parse_request(request)
        trace.append({"stage": "parse", "timestamp": time.time(), "result": parsed})
        
        # Stage 3: 路由
        target = self._route_request(parsed)
        trace.append({"stage": "route", "timestamp": time.time(), "target": target})
        
        # Stage 4: 执行
        result = self._execute(target, parsed)
        trace.append({"stage": "execute", "timestamp": time.time(), "result": result})
        
        # Stage 5: 输出
        output = self._format_output(result)
        trace.append({"stage": "output", "timestamp": time.time()})
        
        return HarnessResponse(
            request_id=request.request_id,
            status="success",
            result=output,
            execution_time=time.time() - start_time,
            pipeline_trace=trace
        )
    
    def _parse_request(self, request: HarnessRequest) -> Dict:
        """解析请求"""
        return {
            "type": request.request_type,
            "content": request.payload,
            "metadata": request.metadata
        }
    
    def _route_request(self, parsed: Dict) -> str:
        """路由请求到合适的Agent"""
        request_type = parsed.get("type", "general")
        
        routing_map = {
            "diagnosis": "diagnostic_agent",
            "research": "research_agent",
            "follow_up": "followup_agent",
            "education": "education_agent",
            "management": "management_agent"
        }
        
        return routing_map.get(request_type, "general_agent")
    
    def _execute(self, target: str, parsed: Dict) -> Dict:
        """执行任务"""
        if target in self.agents:
            return self.agents[target].execute(parsed)
        return {"status": "no_agent", "message": f"Agent {target} not found"}
    
    def _format_output(self, result: Dict) -> Dict:
        """格式化输出"""
        return {
            "data": result,
            "formatted": True,
            "timestamp": time.time()
        }
    
    def register_agent(self, name: str, agent: Any):
        """注册Agent"""
        self.agents[name] = agent
    
    def register_tool(self, name: str, tool: Any):
        """注册工具"""
        self.tools[name] = tool
