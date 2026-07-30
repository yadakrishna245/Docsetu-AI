"""
DocSetu AI - Indian Compliance Rules Engine
Rule-based and LLM-based compliance checking for Indian regulations.
Covers GST, DPDP Act, SEBI, RBI, and MCA requirements.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.indian_regex import extract_all_patterns, GSTIN_PATTERN, PAN_PATTERN
from services.validator import IndianDocumentValidator
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


# ==================== Compliance Rules Database ====================

COMPLIANCE_RULES: List[Dict[str, Any]] = [
    # GST Compliance Rules
    {
        "rule_id": "GST-001",
        "rule_name": "GSTIN Presence",
        "category": "gst",
        "description": "Tax invoice must contain valid GSTIN of supplier",
        "severity": "critical",
        "regulation": "CGST Act Section 31, Rule 46",
        "check_type": "rule_based",
    },
    {
        "rule_id": "GST-002",
        "rule_name": "Invoice Number Format",
        "category": "gst",
        "description": "Invoice number must be sequential, not exceeding 16 characters",
        "severity": "high",
        "regulation": "CGST Rule 46(b)",
        "check_type": "rule_based",
    },
    {
        "rule_id": "GST-003",
        "rule_name": "HSN/SAC Code",
        "category": "gst",
        "description": "HSN/SAC code must be mentioned for goods/services",
        "severity": "high",
        "regulation": "CGST Rule 46(c)",
        "check_type": "rule_based",
    },
    {
        "rule_id": "GST-004",
        "rule_name": "Tax Breakdown",
        "category": "gst",
        "description": "Invoice must show CGST, SGST/UTGST or IGST separately",
        "severity": "critical",
        "regulation": "CGST Rule 46(n)",
        "check_type": "rule_based",
    },
    {
        "rule_id": "GST-005",
        "rule_name": "Place of Supply",
        "category": "gst",
        "description": "Place of supply must be mentioned for inter-state transactions",
        "severity": "high",
        "regulation": "CGST Rule 46(e)",
        "check_type": "rule_based",
    },
    # DPDP Act Compliance Rules
    {
        "rule_id": "DPDP-001",
        "rule_name": "Consent Clause",
        "category": "dpdp",
        "description": "Document must include clear consent mechanism for data processing",
        "severity": "critical",
        "regulation": "Digital Personal Data Protection Act 2023, Section 6",
        "check_type": "llm_based",
    },
    {
        "rule_id": "DPDP-002",
        "rule_name": "Purpose Limitation",
        "category": "dpdp",
        "description": "Purpose of data collection must be clearly stated",
        "severity": "high",
        "regulation": "DPDP Act 2023, Section 5",
        "check_type": "llm_based",
    },
    {
        "rule_id": "DPDP-003",
        "rule_name": "Data Principal Rights",
        "category": "dpdp",
        "description": "Document must mention rights of data principal",
        "severity": "high",
        "regulation": "DPDP Act 2023, Section 11-14",
        "check_type": "llm_based",
    },
    {
        "rule_id": "DPDP-004",
        "rule_name": "Data Retention Period",
        "category": "dpdp",
        "description": "Data retention period must be specified",
        "severity": "medium",
        "regulation": "DPDP Act 2023, Section 8(7)",
        "check_type": "llm_based",
    },
    {
        "rule_id": "DPDP-005",
        "rule_name": "Grievance Redressal",
        "category": "dpdp",
        "description": "Contact details for grievance redressal must be provided",
        "severity": "medium",
        "regulation": "DPDP Act 2023, Section 8(10)",
        "check_type": "llm_based",
    },
    # SEBI Compliance Rules
    {
        "rule_id": "SEBI-001",
        "rule_name": "Disclosure Requirements",
        "category": "sebi",
        "description": "Material information must be disclosed as per SEBI LODR",
        "severity": "critical",
        "regulation": "SEBI LODR Regulation 30",
        "check_type": "llm_based",
    },
    {
        "rule_id": "SEBI-002",
        "rule_name": "Insider Trading Compliance",
        "category": "sebi",
        "description": "Document must not contain UPSI without proper handling",
        "severity": "critical",
        "regulation": "SEBI PIT Regulations 2015",
        "check_type": "llm_based",
    },
    {
        "rule_id": "SEBI-003",
        "rule_name": "KYC Requirements",
        "category": "sebi",
        "description": "KYC documents must contain all mandatory fields",
        "severity": "high",
        "regulation": "SEBI KYC Registration Agency Regulations",
        "check_type": "rule_based",
    },
    # RBI Compliance Rules
    {
        "rule_id": "RBI-001",
        "rule_name": "KYC/AML Compliance",
        "category": "rbi",
        "description": "Banking documents must comply with KYC/AML norms",
        "severity": "critical",
        "regulation": "RBI Master Direction on KYC 2016",
        "check_type": "llm_based",
    },
    {
        "rule_id": "RBI-002",
        "rule_name": "FEMA Compliance",
        "category": "rbi",
        "description": "Foreign exchange transactions must comply with FEMA",
        "severity": "critical",
        "regulation": "Foreign Exchange Management Act 1999",
        "check_type": "llm_based",
    },
    {
        "rule_id": "RBI-003",
        "rule_name": "Digital Lending Guidelines",
        "category": "rbi",
        "description": "Digital lending documents must disclose all fees and T&C",
        "severity": "high",
        "regulation": "RBI Digital Lending Guidelines 2022",
        "check_type": "llm_based",
    },
    # MCA Compliance Rules
    {
        "rule_id": "MCA-001",
        "rule_name": "CIN Display",
        "category": "mca",
        "description": "Company documents must display CIN",
        "severity": "medium",
        "regulation": "Companies Act 2013, Section 12(3)",
        "check_type": "rule_based",
    },
    {
        "rule_id": "MCA-002",
        "rule_name": "Registered Office Address",
        "category": "mca",
        "description": "Documents must contain registered office address",
        "severity": "medium",
        "regulation": "Companies Act 2013, Section 12(3)",
        "check_type": "rule_based",
    },
    {
        "rule_id": "MCA-003",
        "rule_name": "Director Signatures",
        "category": "mca",
        "description": "Board resolutions must have authorized director signatures",
        "severity": "high",
        "regulation": "Companies Act 2013, Section 179",
        "check_type": "llm_based",
    },
]


class ComplianceEngine:
    """Indian regulatory compliance checking engine."""

    def __init__(self):
        """Initialize compliance engine with rules and LLM service."""
        self.rules = COMPLIANCE_RULES
        self.llm_service = LLMService()
        self.validator = IndianDocumentValidator()

    def get_rules(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all compliance rules, optionally filtered by category.

        Args:
            category: Optional category filter (gst, dpdp, sebi, rbi, mca).

        Returns:
            List of compliance rule dictionaries.
        """
        if category:
            return [r for r in self.rules if r["category"] == category.lower()]
        return self.rules

    def get_categories(self) -> List[str]:
        """Get all available compliance categories."""
        return list(set(r["category"] for r in self.rules))

    async def check_compliance(
        self,
        document_text: str,
        regulations: Optional[List[str]] = None,
        strict_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Run compliance checks on a document.

        Args:
            document_text: Full text of the document.
            regulations: Optional list of regulation categories to check.
            strict_mode: If True, run all checks including expensive LLM checks.

        Returns:
            Comprehensive compliance report.
        """
        start_time = datetime.utcnow()

        # Filter rules by requested regulations
        rules_to_check = self.rules
        if regulations:
            rules_to_check = [
                r for r in self.rules if r["category"] in [reg.lower() for reg in regulations]
            ]

        # Run rule-based checks
        rule_results = []
        for rule in rules_to_check:
            if rule["check_type"] == "rule_based":
                result = self._run_rule_check(rule, document_text)
                rule_results.append(result)

        # Run LLM-based checks if in strict mode or if few rule-based checks
        llm_results = []
        if strict_mode:
            llm_rules = [r for r in rules_to_check if r["check_type"] == "llm_based"]
            if llm_rules:
                try:
                    llm_results = await self._run_llm_checks(document_text, llm_rules)
                except Exception as e:
                    logger.error(f"LLM compliance check failed: {e}")
                    for rule in llm_rules:
                        llm_results.append({
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "category": rule["category"],
                            "status": "error",
                            "severity": rule["severity"],
                            "detail": f"LLM check failed: {str(e)}",
                            "recommendation": "Manual review required",
                        })

        all_results = rule_results + llm_results

        # Calculate overall score
        overall_score = self._calculate_score(all_results)
        overall_status = self._determine_status(overall_score, all_results)

        # Categorize results
        violations = [r for r in all_results if r["status"] == "fail"]
        warnings = [r for r in all_results if r["status"] == "warning"]

        # Build category-specific reports
        report = {
            "overall_status": overall_status,
            "overall_score": overall_score,
            "rules_checked": all_results,
            "violations": violations,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(violations, warnings),
            "gst_compliance": self._get_category_report("gst", all_results),
            "dpdp_compliance": self._get_category_report("dpdp", all_results),
            "sebi_compliance": self._get_category_report("sebi", all_results),
            "rbi_compliance": self._get_category_report("rbi", all_results),
            "mca_compliance": self._get_category_report("mca", all_results),
            "checked_at": start_time.isoformat(),
            "total_rules_checked": len(all_results),
            "checked_by": "hybrid" if llm_results else "rule_engine",
        }

        return report

    def _run_rule_check(self, rule: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Run a rule-based compliance check.

        Args:
            rule: Rule definition dictionary.
            text: Document text to check.

        Returns:
            Check result dictionary.
        """
        result = {
            "rule_id": rule["rule_id"],
            "rule_name": rule["rule_name"],
            "category": rule["category"],
            "severity": rule["severity"],
            "status": "pass",
            "detail": "",
            "recommendation": "",
        }

        text_lower = text.lower()
        rule_id = rule["rule_id"]

        if rule_id == "GST-001":
            # Check for GSTIN presence
            gstins = GSTIN_PATTERN.findall(text)
            if not gstins:
                result["status"] = "fail"
                result["detail"] = "No valid GSTIN found in the document"
                result["recommendation"] = "Add supplier GSTIN to the invoice"
            else:
                # Validate found GSTINs
                for gstin in gstins:
                    valid, msg = self.validator.validate_gstin(gstin)
                    if not valid:
                        result["status"] = "warning"
                        result["detail"] = f"GSTIN {gstin} may be invalid: {msg}"
                        result["recommendation"] = "Verify GSTIN on GST portal"

        elif rule_id == "GST-002":
            # Check for invoice number
            import re
            invoice_match = re.search(
                r'(?:invoice|inv|bill)\s*(?:no\.?|number|#)\s*:?\s*([A-Z0-9\-/]+)',
                text, re.IGNORECASE
            )
            if not invoice_match:
                result["status"] = "fail"
                result["detail"] = "Invoice number not found"
                result["recommendation"] = "Add a clearly labeled invoice number"
            elif len(invoice_match.group(1)) > 16:
                result["status"] = "fail"
                result["detail"] = "Invoice number exceeds 16 characters"
                result["recommendation"] = "Invoice number must not exceed 16 characters per GST rules"

        elif rule_id == "GST-003":
            # Check for HSN/SAC codes
            if "hsn" not in text_lower and "sac" not in text_lower:
                result["status"] = "warning"
                result["detail"] = "HSN/SAC code not found"
                result["recommendation"] = "Include HSN code for goods or SAC code for services"

        elif rule_id == "GST-004":
            # Check for tax breakdown
            has_cgst = "cgst" in text_lower
            has_sgst = "sgst" in text_lower or "utgst" in text_lower
            has_igst = "igst" in text_lower
            has_gst = "gst" in text_lower

            if not has_gst and not has_cgst and not has_igst:
                result["status"] = "fail"
                result["detail"] = "No GST tax breakdown found"
                result["recommendation"] = "Show CGST+SGST or IGST separately on invoice"
            elif has_cgst and not has_sgst and not has_igst:
                result["status"] = "warning"
                result["detail"] = "CGST found but SGST/IGST not clearly mentioned"
                result["recommendation"] = "Ensure both CGST and SGST/IGST are shown"

        elif rule_id == "GST-005":
            # Check for place of supply
            if "place of supply" not in text_lower:
                result["status"] = "warning"
                result["detail"] = "Place of supply not explicitly mentioned"
                result["recommendation"] = "Add 'Place of Supply' field for inter-state transactions"

        elif rule_id == "SEBI-003":
            # KYC requirements check
            pans = PAN_PATTERN.findall(text)
            has_photo_ref = any(word in text_lower for word in ["photograph", "photo", "passport size"])
            has_address_proof = any(word in text_lower for word in ["address proof", "utility bill", "bank statement"])

            if not pans:
                result["status"] = "fail"
                result["detail"] = "PAN number not found in KYC document"
                result["recommendation"] = "Include PAN card details for KYC"

        elif rule_id == "MCA-001":
            # CIN display check
            import re
            cin_pattern = r'[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}'
            if not re.search(cin_pattern, text):
                result["status"] = "warning"
                result["detail"] = "Corporate Identification Number (CIN) not found"
                result["recommendation"] = "Company documents should display CIN as per Companies Act"

        elif rule_id == "MCA-002":
            # Registered office address check
            has_reg_office = any(
                phrase in text_lower
                for phrase in ["registered office", "regd. office", "regd office", "corporate office"]
            )
            if not has_reg_office:
                result["status"] = "warning"
                result["detail"] = "Registered office address not clearly mentioned"
                result["recommendation"] = "Include registered office address on company documents"

        return result

    async def _run_llm_checks(
        self, text: str, rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run LLM-based compliance checks.

        Args:
            text: Document text.
            rules: List of rules to check via LLM.

        Returns:
            List of check results.
        """
        regulations = list(set(r["category"] for r in rules))
        llm_result = await self.llm_service.analyze_compliance(text, regulations)

        results = []
        findings = llm_result.get("findings", [])

        # Map LLM findings back to our rules
        for rule in rules:
            matched_finding = None
            for finding in findings:
                if (finding.get("regulation", "").lower() in rule["regulation"].lower() or
                        finding.get("rule", "").lower() in rule["rule_name"].lower()):
                    matched_finding = finding
                    break

            if matched_finding:
                status_map = {"pass": "pass", "fail": "fail", "warning": "warning"}
                results.append({
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "status": status_map.get(matched_finding.get("status", ""), "warning"),
                    "detail": matched_finding.get("detail", ""),
                    "recommendation": matched_finding.get("recommendation", ""),
                })
            else:
                results.append({
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "status": "pass",
                    "detail": "No issues detected by AI analysis",
                    "recommendation": "",
                })

        return results

    def _calculate_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall compliance score (0-100)."""
        if not results:
            return 100.0

        severity_weights = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
        }

        total_possible = sum(
            severity_weights.get(r["severity"], 5) for r in results
        )
        deductions = sum(
            severity_weights.get(r["severity"], 5)
            for r in results
            if r["status"] == "fail"
        )
        warnings_deduction = sum(
            severity_weights.get(r["severity"], 5) * 0.3
            for r in results
            if r["status"] == "warning"
        )

        score = max(0, 100 - ((deductions + warnings_deduction) / total_possible * 100))
        return round(score, 1)

    def _determine_status(self, score: float, results: List[Dict[str, Any]]) -> str:
        """Determine overall compliance status."""
        critical_failures = [
            r for r in results
            if r["status"] == "fail" and r["severity"] == "critical"
        ]

        if critical_failures:
            return "non_compliant"
        elif score >= 90:
            return "compliant"
        elif score >= 60:
            return "partial"
        else:
            return "non_compliant"

    def _get_category_report(
        self, category: str, results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get compliance report for a specific category."""
        category_results = [r for r in results if r["category"] == category]
        if not category_results:
            return None

        passed = sum(1 for r in category_results if r["status"] == "pass")
        failed = sum(1 for r in category_results if r["status"] == "fail")
        warnings = sum(1 for r in category_results if r["status"] == "warning")

        return {
            "total_checks": len(category_results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "score": round(passed / len(category_results) * 100, 1) if category_results else 0,
            "details": category_results,
        }

    def _generate_recommendations(
        self,
        violations: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate actionable recommendations from violations and warnings."""
        recommendations = []

        # Critical violations first
        for v in sorted(violations, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4)):
            if v.get("recommendation"):
                recommendations.append(f"[{v['severity'].upper()}] {v['recommendation']}")

        # Then warnings
        for w in warnings[:5]:  # Limit warnings
            if w.get("recommendation"):
                recommendations.append(f"[WARNING] {w['recommendation']}")

        return recommendations
