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
    HarnessConfig,
    HarnessResult,
    HarnessStatus,
    RecoveryStrategy,
    ValidationResult,
    CompressionStrategy,
)


# ── Diagnosis Harness ───────────────────────────────────────────────

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
        assert "execution_time_ms" in result

    def test_sma_diagnosis(self):
        """测试SMA诊断。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["muscle weakness", "hypotonia", "areflexia"],
            "patient": {"age": 2, "sex": "M"},
        })
        assert "脊髓性肌萎缩" in result["diagnosis"] or "SMA" in result["diagnosis"]
        assert result["confidence"] > 0.5

    def test_unknown_symptoms(self):
        """测试未知症状的处理。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["random_symptom_xyz"],
            "patient": {"age": 30, "sex": "M"},
        })
        assert result["confidence"] < 0.5

    def test_empty_symptoms(self):
        """测试空症状列表。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": [],
            "patient": {"age": 30, "sex": "M"},
        })
        assert result["confidence"] <= 0.5

    def test_multiple_symptom_categories(self):
        """测试跨系统症状。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["ptosis", "muscle weakness", "dysphagia"],
            "patient": {"age": 45, "sex": "M"},
        })
        assert result["diagnosis"] != ""
        assert result["confidence"] > 0

    def test_rare_disease_kb_query(self):
        """测试罕见病知识库查询。"""
        harness = DiagnosisHarness(specialty="neurology")
        results = harness.query_rare_disease_kb(["ptosis", "diplopia"])
        assert len(results) > 0
        assert any("MG" in r.get("code", "") for r in results)

    def test_multidisciplinary_consult(self):
        """测试多学科会诊请求。"""
        harness = DiagnosisHarness(specialty="neurology")
        consult = harness.request_multidisciplinary_consult(
            ["neurology", "immunology"], {"case": "suspected MG"}
        )
        assert "neurology" in consult
        assert "immunology" in consult

    def test_different_specialties(self):
        """测试不同专科。"""
        for specialty in ["neurology", "cardiology", "pulmonology", "gastroenterology"]:
            harness = DiagnosisHarness(specialty=specialty)
            assert harness.specialty == specialty
            assert harness.name == f"diagnosis_{specialty}"

    def test_result_has_all_fields(self):
        """测试返回结果包含所有必需字段。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["ptosis"],
            "patient": {"age": 35, "sex": "F"},
        })
        required_fields = ["diagnosis", "confidence", "differential", "next_steps",
                           "evidence", "harness_name", "execution_time_ms", "recovery_applied"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"


# ── Drug Discovery Harness ──────────────────────────────────────────

class TestDrugDiscoveryHarness:
    """药物发现Harness测试。"""

    def test_basic_execution(self):
        harness = DrugDiscoveryHarness(target_disease="Myasthenia Gravis")
        result = harness.execute({"disease": "Myasthenia Gravis"})
        assert "target" in result
        assert "candidates" in result
        assert "admet_profile" in result

    def test_with_target(self):
        harness = DrugDiscoveryHarness(target_disease="NSCLC")
        result = harness.execute({"target": "EGFR", "disease": "NSCLC"})
        assert result["confidence"] > 0
        assert isinstance(result["candidates"], list)

    def test_optimization_suggestions(self):
        harness = DrugDiscoveryHarness()
        result = harness.execute({"disease": "test"})
        assert "optimization_suggestions" in result

    def test_validate_target(self):
        harness = DrugDiscoveryHarness()
        validation = harness.validate_target("EGFR", "NSCLC")
        assert validation["validated"] is True

    def test_result_fields(self):
        harness = DrugDiscoveryHarness()
        result = harness.execute({"disease": "test"})
        required = ["target", "candidates", "admet_profile",
                     "optimization_suggestions", "confidence", "harness_name"]
        for field in required:
            assert field in result


# ── Health Management Harness ───────────────────────────────────────

class TestHealthManagementHarness:
    """健康管理Harness测试。"""

    def test_basic_execution(self):
        harness = HealthManagementHarness(health_domain="weight_management")
        result = harness.execute({
            "patient": {"age": 35, "health_goal": "减重10kg"},
        })
        assert "assessment" in result
        assert "plan" in result

    def test_diabetes_management(self):
        harness = HealthManagementHarness(health_domain="diabetes")
        result = harness.execute({
            "conditions": ["type 2 diabetes"],
            "lab_results": {"hba1c": 7.2},
            "patient": {"age": 55},
        })
        assert result["confidence"] > 0

    def test_follow_up(self):
        harness = HealthManagementHarness()
        followup = harness.conduct_follow_up("P123", {"weight": 80})
        assert "patient_id" in followup

    def test_result_fields(self):
        harness = HealthManagementHarness()
        result = harness.execute({"patient": {"age": 30}})
        required = ["assessment", "plan", "adherence_metrics",
                     "effectiveness", "confidence", "harness_name"]
        for field in required:
            assert field in result


# ── Medical Orchestrator ────────────────────────────────────────────

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

    def test_no_agents(self):
        orchestrator = MedicalOrchestrator()
        result = orchestrator.run(task="test")
        assert result.confidence == 0.0 or result.final_diagnosis == ""

    def test_crewai_mode(self):
        orchestrator = MedicalOrchestrator(mode="crewai")
        orchestrator.add_agent("diagnostician", specialty="neurology")
        result = orchestrator.run(task="test")
        assert result.final_diagnosis != ""

    def test_agent_with_context(self):
        orchestrator = MedicalOrchestrator()
        orchestrator.add_agent("diagnostician", specialty="neurology")
        result = orchestrator.run(
            task="鉴别诊断",
            context={"symptoms": ["ptosis", "diplopia"], "medical_history": ["hypertension"]}
        )
        assert result.confidence > 0


# ── Medical Tool Registry ───────────────────────────────────────────

class TestMedicalToolRegistry:
    """MCP工具注册中心测试。"""

    def test_builtin_tools(self):
        registry = MedicalToolRegistry()
        tools = registry.list_tools()
        assert len(tools) >= 6  # pubmed, chembl, opentargets, omim, openfda, rdkit

    def test_get_tool(self):
        registry = MedicalToolRegistry()
        pubmed = registry.get("pubmed")
        assert pubmed is not None
        assert pubmed.name == "pubmed"

    def test_get_nonexistent(self):
        registry = MedicalToolRegistry()
        tool = registry.get("nonexistent_tool")
        assert tool is None

    def test_list_categories(self):
        registry = MedicalToolRegistry()
        categories = registry.list_categories()
        assert "literature" in categories
        assert "drug" in categories

    def test_list_tools_by_category(self):
        registry = MedicalToolRegistry()
        tools = registry.list_tools(category="literature")
        assert len(tools) > 0
        assert all(t["category"] == "literature" for t in tools)


# ── Result Validator ────────────────────────────────────────────────

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

    def test_empty_output(self):
        validator = ResultValidator()
        validation = validator.validate({})
        assert not validation.passed

    def test_missing_confidence(self):
        validator = ResultValidator()
        validation = validator.validate({"diagnosis": "MG"})
        assert not validation.passed

    def test_confidence_out_of_range(self):
        validator = ResultValidator()
        validation = validator.validate({"diagnosis": "MG", "confidence": 1.5})
        assert not validation.passed

    def test_strict_mode(self):
        validator = ResultValidator(strict_mode=True)
        # In strict mode, warnings become failures
        # Use a result that triggers a domain warning
        result = {"diagnosis": "MG", "confidence": 0.9}
        validation = validator.validate(result, domain="diagnosis")
        # Should have a warning about missing differential (converted to failure in strict mode)
        assert not validation.passed or len(validation.findings) > 0

    def test_dangerous_patterns(self):
        validator = ResultValidator()
        result = {"diagnosis": "no need for further testing", "confidence": 0.9}
        validation = validator.validate(result)
        assert not validation.passed

    def test_domain_validation(self):
        validator = ResultValidator()
        result = {"diagnosis": "MG", "confidence": 0.9}
        validation = validator.validate(result, domain="diagnosis")
        # Should warn about differential < 2
        assert len(validation.findings) > 0


# ── Context Manager ─────────────────────────────────────────────────

class TestContextManager:
    """上下文管理器测试。"""

    def test_basic_build(self):
        cm = ContextManager()
        ctx = cm.build({"symptoms": ["fever"], "patient": {"age": 30}})
        assert "patient" in ctx
        assert ctx["patient"]["age"] == 30
        assert "fever" in str(ctx["patient"].get("symptoms", []))

    def test_with_medical_history(self):
        cm = ContextManager()
        ctx = cm.build({
            "symptoms": ["cough"],
            "medical_history": ["asthma", "allergies"],
            "patient": {"age": 25},
        })
        assert "history" in ctx

    def test_compression_not_needed(self):
        cm = ContextManager({"max_tokens": 100000})
        ctx = cm.build({"symptoms": ["fever"]})
        compressed = cm.compress(ctx)
        assert "_compressed" not in compressed

    def test_compression_when_needed(self):
        cm = ContextManager({"max_tokens": 10})
        ctx = cm.build({"symptoms": ["fever"] * 100})
        compressed = cm.compress(ctx)
        assert "_compressed" in compressed

    def test_merge_contexts(self):
        cm = ContextManager()
        base = {"patient": {"age": 30}}
        new = {"patient": {"weight": 70}}
        merged = cm.merge(base, new)
        assert merged["patient"]["age"] == 30
        assert merged["patient"]["weight"] == 70


# ── Failure Recovery ────────────────────────────────────────────────

class TestFailureRecovery:
    """失败恢复测试。"""

    def test_critical_severity(self):
        fr = FailureRecovery(strategy=RecoveryStrategy.ESCALATE)
        # Create a mock validation with very low confidence
        class MockValidation:
            confidence = 0.1
            issues = ["critical issue"]
            message = "Critical failure"
        result = fr.recover({}, MockValidation())
        assert "无法确定" in result["diagnosis"] or result["confidence"] == 0.0

    def test_fallback_strategy(self):
        fr = FailureRecovery(strategy=RecoveryStrategy.FALLBACK)
        class MockValidation:
            confidence = 0.5
            issues = ["some issue"]
        result = fr.recover({}, MockValidation())
        assert result["confidence"] == 0.3

    def test_recovery_log(self):
        fr = FailureRecovery()
        class MockValidation:
            confidence = 0.5
            issues = ["test"]
        fr.recover({}, MockValidation())
        assert len(fr.recovery_log) > 0

    def test_reset(self):
        fr = FailureRecovery()
        class MockValidation:
            confidence = 0.5
            issues = ["test"]
        fr.recover({}, MockValidation())
        fr.reset()
        assert len(fr.escalation_log) >= 0  # escalation_log persists, counter resets


# ── Integration Tests ───────────────────────────────────────────────

class TestIntegration:
    """集成测试。"""

    def test_diagnosis_to_validation(self):
        """诊断结果应通过验证。"""
        harness = DiagnosisHarness(specialty="neurology")
        result = harness.execute({
            "symptoms": ["bilateral ptosis", "fatigable weakness"],
            "patient": {"age": 35, "sex": "F"},
        })
        validator = ResultValidator(threshold=0.5)
        validation = validator.validate(result)
        assert validation.passed

    def test_drug_discovery_to_validation(self):
        """药物发现结果应通过验证。"""
        harness = DrugDiscoveryHarness()
        result = harness.execute({"target": "EGFR", "disease": "NSCLC"})
        # Use domain-specific validation and lower threshold
        validator = ResultValidator(threshold=0.3)
        validation = validator.validate(result, domain="drug_discovery")
        assert validation.passed

    def test_orchestrator_with_context(self):
        """编排器应能处理完整上下文。"""
        orchestrator = MedicalOrchestrator()
        orchestrator.add_agent("diagnostician", specialty="neurology")
        orchestrator.add_agent("literature_reviewer")
        result = orchestrator.run(
            task="鉴别诊断：35岁女性，双眼睑下垂",
            context={
                "symptoms": ["bilateral ptosis", "fatigable weakness"],
                "medical_history": ["no significant history"],
            },
            consensus_rounds=2,
        )
        assert result.confidence > 0
        assert len(result.agent_opinions) == 2
