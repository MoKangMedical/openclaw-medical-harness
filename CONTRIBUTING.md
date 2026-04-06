# Contributing to OpenClaw-Medical-Harness

## 开发环境

```bash
git clone https://github.com/MoKangMedical/openclaw-medical-harness.git
cd openclaw-medical-harness
pip install -e ".[dev]"
```

## 运行测试

```bash
pytest
```

## 代码规范

```bash
ruff check .
ruff format .
mypy openclaw_medical_harness/
```

## 提交规范

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试

## 架构原则

1. **Harness优先**：所有功能都应通过Harness模式实现
2. **模型无关**：不绑定特定模型，支持MIMO/Claude/GPT/Ollama
3. **医疗安全**：验证器必须拦截不安全输出
4. **可审计**：所有推理步骤必须可追溯

## 添加新Harness

1. 继承 `BaseHarness`
2. 实现 `_build_prompt` 和 `_reason`
3. 实现 `_metrics`
4. 添加测试和文档
