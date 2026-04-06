"""Tests for OpenClaw-Medical-Harness."""

import pytest
from openclaw_medical_harness import (
    BaseHarness,
    DiagnosisHarness,
    DrugDiscoveryHarness,
    HealthManagementHarness,
    MedicalOrchestrator,
    MedicalToolRegistry,
    ContextManager,
    ResultValidator,
    FailureRecovery,
)


class TestDiagnosisHarness:
    """诊断Harness测试。"""

    def test_mg_diagnosis(self):
        """测试MG诊断。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["bilateral ptosis", "fatigable weakness", "diplopia"],
            "patient": {"age": 35, "sex": "F"},
        })
        assert result["diagnosis"] != ""
        assert result["confidence"] > 0
        assert len(result["next_steps"]) > 0

    def test_unknown_symptoms(self):
        """测试未知症状的处理。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["random_symptom_xyz"],
            "patient": {"age": 30, "sex": "M"},
        })
        assert result["confidence"] < 0.5


class TestDrugDiscoveryHarness:
    """药物发现Harness测试。"""

    def test_basic_execution(self):
        harness = DrugDiscoveryHarness(target_disease="Myasthenia Gravis")
        result = harness.execute({
            "disease": "Myasthenia Gravis",
        })
        assert "target" in result
        assert "candidates" in result


class TestHealthManagementHarness:
    """健康管理Harness测试。"""

    def test_basic_execution(self):
        harness = HealthManagementHarness(health_domain="weight_management")
        result = harness.execute({
            "patient": {"age": 35, "health_goal": "减重10kg"},
        })
        assert "assessment" in result
        assert "plan" in result


class TestMedicalOrchestrator:
    """多Agent编排器测试。"""

    def test_single_agent(self):
        orchestrator = MedicalOrchestrator(mode="openclaw")
        orchestrator.add_agent("diagnostician", specialty="neurology")
        result = orchestrator.run(task="疑似MG的鉴别诊断")
        assert result.final_diagnosis != ""

    def test_multi_agent_consensus(self):
        orchestrator = MedicalOrchestrator(mode="openclaw")
        orchestrator.add_agent("diagnostician", specialty="neurology")
        orchestrator.add_agent("literature_reviewer")
        orchestrator.add_agent("pharmacologist")
        result = orchestrator.run(task="MG诊断", consensus_rounds=2)
        assert result.confidence > 0
        assert result.consensus_rounds == 2


class TestMedicalToolRegistry:
    """MCP工具注册中心测试。"""

    def test_builtin_tools(self):
        registry = MedicalToolRegistry()
        tools = registry.list_tools()
        assert len(tools) >= 6  # pubmed, chembl, opentargets, omim, openfda, rdkit

    def test_list_categories(self):
        registry = MedicalToolRegistry()
        categories = registry.list_categories()
        assert "literature" in categories
        assert "drug" in categories


class TestResultValidator:
    """结果验证器测试。"""

    def test_valid_result(self):
        validator = ResultValidator(threshold=0.7)
        result = {"diagnosis": "MG", "confidence": 0.85}
        validation = validator.validate(result)
        assert validation.passed

    def test_low_confidence(self):
        validator = ResultValidator(threshold=0.7)
        result = {"diagnosis": "不确定", "confidence": 0.3}
        validation = validator.validate(result)
        assert not validation.passed

    def test_absolute_term_detection(self):
        validator = ResultValidator()
        result = {"diagnosis": "肯定是MG", "confidence": 0.95}
        validation = validator.validate(result)
        assert not validation.passed
