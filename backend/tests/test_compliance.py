"""
DocSetu AI - Compliance Integration Tests
Tests for compliance rules listing and compliance check execution.
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestComplianceRules:
    """Tests for GET /api/compliance/rules."""

    async def test_get_compliance_rules(self, test_client: AsyncClient, test_user: dict):
        """Test listing all compliance rules."""
        with patch("routers.compliance.ComplianceEngine") as mock_engine_class:
            mock_engine = mock_engine_class.return_value
            mock_engine.get_rules.return_value = [
                {
                    "rule_id": "GST-001",
                    "rule_name": "GST Number Validation",
                    "category": "gst",
                    "description": "Validates GST number format",
                    "severity": "high",
                    "regulation": "GST Act 2017",
                },
                {
                    "rule_id": "DPDP-001",
                    "rule_name": "Personal Data Detection",
                    "category": "dpdp",
                    "description": "Detects personal data under DPDP Act",
                    "severity": "critical",
                    "regulation": "DPDP Act 2023",
                },
            ]
            mock_engine.get_categories.return_value = ["gst", "dpdp", "sebi", "rbi", "mca"]

            response = await test_client.get(
                "/api/compliance/rules",
                headers=test_user["headers"],
            )

        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "total" in data
        assert "categories" in data
        assert data["total"] == 2
        assert len(data["rules"]) == 2
        assert data["categories"] == ["gst", "dpdp", "sebi", "rbi", "mca"]

        # Verify rule structure
        rule = data["rules"][0]
        assert "rule_id" in rule
        assert "rule_name" in rule
        assert "category" in rule
        assert "description" in rule
        assert "severity" in rule
        assert "regulation" in rule

    async def test_get_compliance_rules_without_auth_fails(self, test_client: AsyncClient):
        """Test that compliance rules endpoint requires authentication."""
        response = await test_client.get("/api/compliance/rules")
        assert response.status_code == 401


class TestComplianceCheck:
    """Tests for POST /api/compliance/check/{doc_id}."""

    async def test_run_compliance_check_on_document(
        self, test_client: AsyncClient, test_user: dict, test_document: dict
    ):
        """Test running a compliance check on an uploaded document."""
        doc_id = test_document["id"]

        mock_compliance_result = {
            "overall_status": "partial",
            "overall_score": 72.5,
            "rules_checked": [
                {"rule_id": "GST-001", "rule_name": "GST Number Validation", "status": "pass"},
                {"rule_id": "DPDP-001", "rule_name": "Personal Data Detection", "status": "violation"},
            ],
            "violations": [
                {
                    "rule_id": "DPDP-001",
                    "rule_name": "Personal Data Detection",
                    "severity": "critical",
                    "detail": "PAN number found without encryption",
                    "recommendation": "Encrypt or redact personal identifiers",
                    "affected_text": "PAN AAPFU0939F",
                }
            ],
            "recommendations": [
                "Encrypt sensitive personal identifiers",
                "Add data processing consent notice",
            ],
            "gst_compliance": {"status": "compliant", "score": 95.0},
            "dpdp_compliance": {"status": "non_compliant", "score": 50.0},
            "sebi_compliance": None,
            "rbi_compliance": None,
            "mca_compliance": None,
            "checked_by": "rule_engine",
        }

        with patch("routers.compliance.ComplianceEngine") as mock_engine_class:
            mock_engine = mock_engine_class.return_value
            mock_engine.check_compliance = AsyncMock(return_value=mock_compliance_result)

            response = await test_client.post(
                f"/api/compliance/check/{doc_id}",
                headers=test_user["headers"],
            )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["overall_status"] == "partial"
        assert data["overall_score"] == 72.5
        assert "rules_checked" in data
        assert "violations" in data
        assert "recommendations" in data
        assert len(data["violations"]) == 1
        assert data["violations"][0]["rule_id"] == "DPDP-001"
        assert data["violations"][0]["severity"] == "critical"
        assert "id" in data
        assert "created_at" in data

    async def test_compliance_check_nonexistent_document_returns_404(
        self, test_client: AsyncClient, test_user: dict
    ):
        """Test that compliance check on non-existent document returns 404."""
        response = await test_client.post(
            "/api/compliance/check/nonexistent-doc-id",
            headers=test_user["headers"],
        )

        assert response.status_code == 404

    async def test_compliance_check_without_auth_fails(
        self, test_client: AsyncClient, test_document: dict
    ):
        """Test that compliance check requires authentication."""
        response = await test_client.post(
            f"/api/compliance/check/{test_document['id']}"
        )

        assert response.status_code == 401

    async def test_compliance_check_with_specific_regulations(
        self, test_client: AsyncClient, test_user: dict, test_document: dict
    ):
        """Test compliance check with specific regulation filters."""
        doc_id = test_document["id"]

        mock_compliance_result = {
            "overall_status": "compliant",
            "overall_score": 95.0,
            "rules_checked": [
                {"rule_id": "GST-001", "rule_name": "GST Number Validation", "status": "pass"},
            ],
            "violations": [],
            "recommendations": [],
            "gst_compliance": {"status": "compliant", "score": 95.0},
            "dpdp_compliance": None,
            "sebi_compliance": None,
            "rbi_compliance": None,
            "mca_compliance": None,
            "checked_by": "rule_engine",
        }

        with patch("routers.compliance.ComplianceEngine") as mock_engine_class:
            mock_engine = mock_engine_class.return_value
            mock_engine.check_compliance = AsyncMock(return_value=mock_compliance_result)

            response = await test_client.post(
                f"/api/compliance/check/{doc_id}",
                json={"regulations": ["gst"], "strict_mode": False},
                headers=test_user["headers"],
            )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "compliant"
        assert data["overall_score"] == 95.0
        assert len(data["violations"]) == 0
