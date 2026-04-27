# OpenClaw Medical Harness

医疗AI Agent编排框架 — 5步Harness将任意AI升级为医疗专家

## 一句话定义

Medical Harness 不卖AI模型，卖AI模型的医疗能力。任何大模型 + 5步Harness = 医疗级AI助手。

## 5步Harness

1. 症状解析: 自然语言→结构化SOAP
2. 知识检索: OMIM/HPO/PubMed实时检索
3. 鉴别诊断: 多候选诊断排序
4. 循证推荐: 基于指南的治疗建议
5. 安全校验: 防幻觉+合规检查

## 快速开始

    git clone https://github.com/MoKangMedical/openclaw-medical-harness.git
    cd openclaw-medical-harness
    pip install -r requirements.txt
    python src/harness.py --input "头痛三天，伴恶心呕吐"

MIT License
