# OpenClaw Medical Harness — 工作流示例

本文档展示典型医疗 AI Agent 编排工作流，涵盖诊断、药物发现和健康管理场景。

---

## 工作流一：多 Agent 协作诊断

### 场景

35岁女性，双眼睑下垂6个月，下午加重，伴四肢乏力。

### 编排流程

```
┌─────────────────────────────────────────────────────────┐
│                    患者输入                               │
│   症状: 双眼睑下垂, 肌无力, 午后加重                       │
│   病史: 无特殊                                           │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│  Step 1: 分诊 Agent       │
│  - 评估紧急程度            │
│  - 分诊级别: 3 (urgent)    │
│  - 建议: 非立即危及生命，    │
│    但需尽快明确诊断         │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  Step 2: 并行执行（3个Agent同时工作）                       │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │ 诊断推理 Agent  │  │ 文献综述 Agent  │  │ 药物学 Agent│ │
│  │                │  │                │  │            │ │
│  │ 鉴别诊断:      │  │ 检索相关文献:   │  │ 排查药物    │ │
│  │ 1. 重症肌无力   │  │ - PMID:12345   │  │ 诱发因素:   │ │
│  │ 2. Lambert-   │  │   病例系列      │  │ - 无相关    │ │
│  │    Eaton      │  │ - PMID:67890   │  │   用药史     │ │
│  │ 3. 甲亢性肌病  │  │   系统综述      │  │            │ │
│  │                │  │                │  │            │ │
│  │ 置信度: 0.75   │  │ 置信度: 0.70   │  │ 置信度: 0.8 │ │
│  └───────┬────────┘  └───────┬────────┘  └─────┬──────┘ │
│          └───────────────────┼─────────────────┘        │
└──────────────────────────────┬───────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│  Step 3: 共识构建（3轮协商）                               │
│                                                          │
│  Round 1: 各Agent查看他人结果，调整置信度                    │
│  Round 2: 收敛 — 所有Agent置信度差 < 0.1                   │
│  Round 3: 确认共识                                        │
│                                                          │
│  共识结论: 重症肌无力（MG）可能性最高                        │
│  综合置信度: 0.78                                         │
│  建议: AChR抗体检测 + 胸腺CT                               │
└──────────────────────────────┬───────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│  Step 4: 患者沟通 Agent                                   │
│                                                          │
│  通俗解释: "您的症状提示一种叫'重症肌无力'的自身免疫性疾病，  │
│  身体的免疫系统错误地攻击了控制肌肉的信号传导。好消息是，     │
│  这种疾病有成熟的治疗方案。我们需要做一些检查来确认诊断。"   │
│                                                          │
│  下一步:                                                  │
│  1. 抽血检查 AChR 抗体                                    │
│  2. 胸部 CT 排查胸腺异常                                   │
│  3. 神经内科复诊                                          │
└──────────────────────────────────────────────────────────┘
```

### Python 代码

```python
from openclaw_medical_harness.agents import MultiAgentOrchestrator, OrchestrationMode, AgentRole

# 创建编排器
orchestrator = MultiAgentOrchestrator(mode=OrchestrationMode.OPENCLAW)

# 添加 Agent
orchestrator.add_agent(AgentRole.DIAGNOSTIC, specialty="neurology")
orchestrator.add_agent(AgentRole.LITERATURE)
orchestrator.add_agent(AgentRole.DRUG)
orchestrator.add_agent(AgentRole.COMMUNICATION)

# 执行编排
result = orchestrator.run(
    objective="35岁女性，双眼睑下垂6个月，下午加重，伴四肢乏力",
    context={
        "symptoms": ["bilateral ptosis", "fatigable weakness", "afternoon worsening"],
        "medical_history": [],
        "vital_signs": {"bp": "120/80", "hr": 78, "temp": 36.8},
    },
    consensus_rounds=3,
)

# 查看结果
print(f"诊断结论: {result.final_diagnosis}")
print(f"综合置信度: {result.confidence:.2f}")
print(f"共识轮次: {result.consensus_rounds}")
print(f"是否需要人工审核: {result.escalation_needed}")

for name, agent_result in result.agent_results.items():
    print(f"\n[{name}] ({agent_result.agent_role.value})")
    print(f"  置信度: {agent_result.confidence:.2f}")
    print(f"  分析: {agent_result.output.get('analysis', 'N/A')}")
```

---

## 工作流二：药物重定位分析

### 场景

探索已批准药物用于新适应症的可能性（如：二甲双胍用于抗衰老）。

### 流程

```python
from openclaw_medical_harness.drug_discovery import DrugHarness
from openclaw_medical_harness.mcp_tools import MedicalToolRegistry

# 初始化
registry = MedicalToolRegistry()
harness = DrugHarness()

# Step 1: 获取药物信息
chembl = registry.get("chembl")
drug_info = chembl.execute(
    context={"input": {"pref_name": "metformin"}},
    prior_results={},
)

# Step 2: 查询靶点-疾病关联
opentargets = registry.get("opentargets")
target_disease = opentargets.execute(
    context={"input": {"target_id": "ENSG00000132849", "disease_id": "EFO_0001467"}},
    prior_results={"drug_info": drug_info},
)

# Step 3: 检索文献支持
pubmed = registry.get("pubmed")
literature = pubmed.execute(
    context={"input": {"search_query": "metformin anti-aging longevity clinical trial"}},
    prior_results={"drug_info": drug_info, "target_disease": target_disease},
)

# Step 4: 安全性评估
openfda = registry.get("openfda")
safety = openfda.execute(
    context={"input": {"drug_name": "metformin", "serious_only": True}},
    prior_results={},
)

# 输出报告
print("=== 药物重定位分析报告 ===")
print(f"药物: 二甲双胍 (Metformin)")
print(f"目标适应症: 抗衰老/长寿")
print(f"文献支持: {len(literature.get('results', []))} 篇相关文献")
print(f"安全性信号: {safety.get('adverse_events', [])}")
```

---

## 工作流三：健康管理计划

### 场景

为2型糖尿病患者生成个性化健康管理计划。

### 流程

```python
from openclaw_medical_harness.health_management import HealthHarness
from openclaw_medical_harness.agents import MultiAgentOrchestrator, AgentRole

orchestrator = MultiAgentOrchestrator()

# 添加相关 Agent
orchestrator.add_agent(AgentRole.DIAGNOSTIC, specialty="endocrinology")
orchestrator.add_agent(AgentRole.DRUG)
orchestrator.add_agent(AgentRole.COMMUNICATION)

result = orchestrator.run(
    objective="为55岁2型糖尿病男性患者制定个性化健康管理计划",
    context={
        "diagnosis": "2型糖尿病",
        "lab_results": {
            "hba1c": 8.2,
            "fasting_glucose": 9.5,
            "bmi": 28.5,
            "egfr": 75,
        },
        "current_medications": ["二甲双胍 500mg bid"],
        "patient_preferences": ["偏好口服药", "不愿注射"],
        "lifestyle": {
            "exercise": "久坐",
            "diet": "高碳水",
            "smoking": False,
            "alcohol": "偶尔",
        },
    },
    consensus_rounds=2,
)

print("=== 个性化健康管理计划 ===")
print(f"诊断: {result.final_diagnosis}")
print(f"置信度: {result.confidence:.2f}")

# 患者沟通 Agent 的输出
comm_result = result.agent_results.get("communication_agent_4")
if comm_result:
    print(f"\n给患者的建议:")
    print(comm_result.output.get("explanation", ""))
    print(f"\n下一步:")
    for step in comm_result.output.get("next_steps", []):
        print(f"  - {step}")
```

---

## 工作流四：临床试验匹配

### 场景

为患者匹配合适的临床试验。

### 流程

```python
from openclaw_medical_harness.mcp_tools import MedicalToolRegistry

registry = MedicalToolRegistry()

# 查询临床试验
trials_tool = registry.get("clinical_trials_gov")
trials = trials_tool.execute(
    context={
        "input": {
            "condition": "non-small cell lung cancer",
            "intervention": "pembrolizumab",
            "status": "recruiting",
        }
    },
    prior_results={},
)

print("=== 匹配的临床试验 ===")
for trial in trials.get("studies", []):
    print(f"NCT号: {trial.get('nct_id')}")
    print(f"标题: {trial.get('title')}")
    print(f"状态: {trial.get('status')}")
    print(f"入排标准: {trial.get('eligibility')}")
    print("---")
```

---

## 工作流五：MCP 工具链式调用

### 场景

从症状出发，自动串联多个 MCP 工具完成端到端分析。

### 流程图

```
症状输入
    │
    ▼
┌─────────┐     ┌──────────┐     ┌──────────┐
│  ICD-10  │────▶│  PubMed  │────▶│OpenTargets│
│  编码查询 │     │  文献检索 │     │ 靶点关联  │
└─────────┘     └──────────┘     └──────────┘
    │                                   │
    ▼                                   ▼
┌─────────┐                       ┌──────────┐
│  OMIM   │                       │  ChEMBL  │
│  遗传病  │                       │  药物数据 │
└─────────┘                       └──────────┘
                                       │
                                       ▼
                                  ┌──────────┐
                                  │  OpenFDA │
                                  │  安全评估 │
                                  └──────────┘
```

### 代码

```python
from openclaw_medical_harness.mcp_tools import MedicalToolRegistry

registry = MedicalToolRegistry()

# 链式调用
results = {}

# 1. 症状 → 疾病编码
icd10 = registry.get("icd10_api")
results["icd10"] = icd10.execute(
    context={"input": {"query": "bilateral ptosis fatigable weakness"}},
    prior_results=results,
)

# 2. 疾病 → 文献
pubmed = registry.get("pubmed")
results["pubmed"] = pubmed.execute(
    context={"input": {"search_query": "myasthenia gravis diagnosis guidelines"}},
    prior_results=results,
)

# 3. 文献 → 靶点
opentargets = registry.get("opentargets")
results["opentargets"] = opentargets.execute(
    context={"input": {"target_id": "ENSG00000197043", "disease_id": "EFO_0000782"}},
    prior_results=results,
)

# 4. 靶点 → 治疗药物
chembl = registry.get("chembl")
results["chembl"] = chembl.execute(
    context={"input": {"target_chembl_id": "CHEMBL2074"}},
    prior_results=results,
)

# 5. 药物 → 安全性
openfda = registry.get("openfda")
results["openfda"] = openfda.execute(
    context={"input": {"drug_name": "pyridostigmine", "serious_only": True}},
    prior_results=results,
)

print("=== 端到端分析完成 ===")
print(f"共调用 {len(results)} 个 MCP 工具")
for tool_name, result in results.items():
    print(f"  [{tool_name}] 状态: {result.get('status', 'unknown')}")
```

---

## 最佳实践

1. **始终使用共识机制** — 关键诊断决策不应依赖单一 Agent
2. **设置置信度阈值** — 低于 0.5 的结果应触发人工审核
3. **记录所有 MCP 调用** — 便于审计和调试
4. **尊重速率限制** — MCP 工具有调用频率限制，使用批量查询
5. **敏感数据脱敏** — 患者信息在传入 Agent 前应进行脱敏处理
6. **渐进式部署** — 先在非关键场景验证，再逐步应用于临床辅助

---

## 相关文档

- [架构设计](../docs/architecture.md)
- [Harness 理论](../docs/harness_theory.md)
- [MCP 工具参考](../AWESOME_MEDICAL_MCP.md)
- [API 文档](../docs/api/reference.html)
