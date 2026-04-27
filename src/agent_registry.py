"""
Agent Registry — Agent注册表
Agent类型管理、能力匹配、负载均衡
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time


class AgentType(Enum):
    """Agent 类型"""
    DIAGNOSTIC = "diagnostic"
    RESEARCH = "research"
    FOLLOWUP = "followup"
    EDUCATION = "education"
    MANAGEMENT = "management"
    GENERAL = "general"


@dataclass
class AgentCapability:
    """Agent 能力"""
    name: str
    description: str
    confidence: float


@dataclass
class AgentInfo:
    """Agent 信息"""
    agent_id: str
    agent_type: AgentType
    name: str
    capabilities: List[AgentCapability]
    status: str = "idle"
    load: float = 0.0
    last_active: float = 0.0


class AgentRegistry:
    """Agent 注册表"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.type_index: Dict[AgentType, List[str]] = {
            t: [] for t in AgentType
        }
    
    def register(self, agent: AgentInfo):
        """注册 Agent"""
        self.agents[agent.agent_id] = agent
        self.type_index[agent.agent_type].append(agent.agent_id)
    
    def unregister(self, agent_id: str):
        """注销 Agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self.type_index[agent.agent_type].remove(agent_id)
            del self.agents[agent_id]
    
    def find_by_type(self, agent_type: AgentType) -> List[AgentInfo]:
        """按类型查找 Agent"""
        return [
            self.agents[aid] 
            for aid in self.type_index.get(agent_type, [])
            if aid in self.agents
        ]
    
    def find_by_capability(self, capability: str) -> List[AgentInfo]:
        """按能力查找 Agent"""
        return [
            agent for agent in self.agents.values()
            if any(cap.name == capability for cap in agent.capabilities)
        ]
    
    def find_best_match(self, task_type: str, required_capabilities: List[str]) -> Optional[AgentInfo]:
        """找到最佳匹配的 Agent"""
        candidates = []
        
        for agent in self.agents.values():
            if agent.status != "idle":
                continue
            
            # 计算匹配分数
            score = 0.0
            for cap in agent.capabilities:
                if cap.name in required_capabilities:
                    score += cap.confidence
            
            if score > 0:
                candidates.append((agent, score))
        
        if not candidates:
            return None
        
        # 返回得分最高的
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def get_load_balanced(self, agent_type: AgentType) -> Optional[AgentInfo]:
        """负载均衡选择 Agent"""
        agents = self.find_by_type(agent_type)
        idle_agents = [a for a in agents if a.status == "idle"]
        
        if not idle_agents:
            return None
        
        # 选择负载最低的
        return min(idle_agents, key=lambda a: a.load)
    
    def update_status(self, agent_id: str, status: str, load: float = None):
        """更新 Agent 状态"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].last_active = time.time()
            if load is not None:
                self.agents[agent_id].load = load
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.agents)
        idle = sum(1 for a in self.agents.values() if a.status == "idle")
        busy = sum(1 for a in self.agents.values() if a.status == "busy")
        
        return {
            "total_agents": total,
            "idle": idle,
            "busy": busy,
            "by_type": {
                t.value: len(ids) 
                for t, ids in self.type_index.items()
            }
        }
