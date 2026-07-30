"""
DocSetu AI - Compliance Router
Indian regulatory compliance checking endpoints.
Covers GST, DPDP Act, SEBI, RBI, and MCA regulations.
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config import get_settings
from db import get_db
from models.database import Document, ComplianceReport, User
from models.schemas import (
    ComplianceCheckRequest,
    ComplianceRulesListResponse,
    ComplianceRuleResponse,
    ComplianceReportResponse,
    ComplianceViolation,
)
from routers.auth import get_current_user
from services.compliance_engine import ComplianceEngine, COMPLIANCE_RULES
from services.pdf_service import generate_compliance_report_pdf

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


@router.post("/check/{doc_id}", response_model=ComplianceReportResponse)
async def check_compliance(
    doc_id: str,
    request: Optional[ComplianceCheckRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check a document against Indian regulatory compliance rules.

    Supports: GST, DPDP Act, SEBI, RBI, MCA regulations.

    Args:
        doc_id: Document ID to check.
        request: Optional compliance check configuration.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Comprehensive compliance report.
    """
    # Get document
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found",
        )

    if not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document has not been processed yet. Text extraction required.",
        )

    # Parse request
    regulations = request.regulations if request else None
    strict_mode = request.strict_mode if request else False

    # Run compliance checks
    try:
        engine = ComplianceEngine()
        result = await engine.check_compliance(
            document_text=document.extracted_text,
            regulations=regulations,
            strict_mode=strict_mode,
        )
    except Exception as e:
        logger.error(f"Compliance check failed for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}",
        )

    # Save compliance report to database
    report = ComplianceReport(
        document_id=doc_id,
        overall_status=result["overall_status"],
        overall_score=result["overall_score"],
        rules_checked=result["rules_checked"],
        violations=result.get("violations", []),
        recommendations=result.get("recommendations", []),
        gst_compliance=result.get("gst_compliance"),
        dpdp_compliance=result.get("dpdp_compliance"),
        sebi_compliance=result.get("sebi_compliance"),
        rbi_compliance=result.get("rbi_compliance"),
        mca_compliance=result.get("mca_compliance"),
        regulations_version="2024.1",
        checked_by=result.get("checked_by", "rule_engine"),
        status="completed",
        completed_at=datetime.utcnow(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    # Build response
    violations = [
        ComplianceViolation(
            rule_id=v.get("rule_id", ""),
            rule_name=v.get("rule_name", ""),
            severity=v.get("severity", "medium"),
            description=v.get("detail", ""),
            recommendation=v.get("recommendation", ""),
            affected_text=v.get("affected_text"),
        )
        for v in result.get("violations", [])
    ]

    return ComplianceReportResponse(
        id=report.id,
        document_id=doc_id,
        overall_status=report.overall_status,
        overall_score=report.overall_score,
        rules_checked=report.rules_checked or [],
        violations=violations,
        recommendations=result.get("recommendations", []),
        gst_compliance=report.gst_compliance,
        dpdp_compliance=report.dpdp_compliance,
        sebi_compliance=report.sebi_compliance,
        rbi_compliance=report.rbi_compliance,
        mca_compliance=report.mca_compliance,
        created_at=report.created_at,
    )


@router.get("/rules", response_model=ComplianceRulesListResponse)
async def list_compliance_rules(
    category: Optional[str] = Query(default=None, description="Filter by category (gst, dpdp, sebi, rbi, mca)"),
    current_user: User = Depends(get_current_user),
):
    """
    List all available compliance rules.

    Args:
        category: Optional category filter.
        current_user: Authenticated user.

    Returns:
        List of compliance rules with metadata.
    """
    engine = ComplianceEngine()
    rules = engine.get_rules(category)
    categories = engine.get_categories()

    rule_responses = [
        ComplianceRuleResponse(
            rule_id=r["rule_id"],
            rule_name=r["rule_name"],
            category=r["category"],
            description=r["description"],
            severity=r["severity"],
            regulation=r["regulation"],
        )
        for r in rules
    ]

    return ComplianceRulesListResponse(
        rules=rule_responses,
        total=len(rule_responses),
        categories=categories,
    )


@router.get("/report/{doc_id}", response_model=ComplianceReportResponse)
async def get_compliance_report(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the most recent compliance report for a document.

    Args:
        doc_id: Document ID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Most recent compliance report for the document.
    """
    # Verify document ownership
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found",
        )

    # Get latest report
    report = (
        db.query(ComplianceReport)
        .filter(ComplianceReport.document_id == doc_id)
        .order_by(ComplianceReport.created_at.desc())
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compliance report found for document '{doc_id}'. Run a compliance check first.",
        )

    # Build violations from stored data
    violations = []
    if report.violations:
        for v in report.violations:
            violations.append(
                ComplianceViolation(
                    rule_id=v.get("rule_id", ""),
                    rule_name=v.get("rule_name", ""),
                    severity=v.get("severity", "medium"),
                    description=v.get("detail", ""),
                    recommendation=v.get("recommendation", ""),
                    affected_text=v.get("affected_text"),
                )
            )

    return ComplianceReportResponse(
        id=report.id,
        document_id=doc_id,
        overall_status=report.overall_status,
        overall_score=report.overall_score or 0.0,
        rules_checked=report.rules_checked or [],
        violations=violations,
        recommendations=report.recommendations or [],
        gst_compliance=report.gst_compliance,
        dpdp_compliance=report.dpdp_compliance,
        sebi_compliance=report.sebi_compliance,
        rbi_compliance=report.rbi_compliance,
        mca_compliance=report.mca_compliance,
        created_at=report.created_at,
    )



@router.get("/report/{doc_id}/pdf")
async def export_compliance_report_pdf(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export the latest compliance report for a document as a PDF.

    Generates a professional PDF suitable for sharing with CAs and auditors.
    Includes compliance score, violations table, recommendations, and
    category-wise breakdown (GST, DPDP, SEBI, RBI, MCA).

    Args:
        doc_id: Document ID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        StreamingResponse with PDF content.
    """
    import io

    # Verify document ownership
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found",
        )

    # Get latest compliance report
    report = (
        db.query(ComplianceReport)
        .filter(ComplianceReport.document_id == doc_id)
        .order_by(ComplianceReport.created_at.desc())
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compliance report found for document '{doc_id}'. Run a compliance check first.",
        )

    # Prepare report data
    report_data = {
        "overall_score": report.overall_score or 0,
        "overall_status": report.overall_status,
        "violations": report.violations or [],
        "recommendations": report.recommendations or [],
        "gst_compliance": report.gst_compliance,
        "dpdp_compliance": report.dpdp_compliance,
        "sebi_compliance": report.sebi_compliance,
        "rbi_compliance": report.rbi_compliance,
        "mca_compliance": report.mca_compliance,
        "rules_checked": report.rules_checked or [],
        "created_at": report.created_at,
    }

    # Prepare document info
    document_info = {
        "id": document.id,
        "filename": document.original_filename,
        "file_type": document.file_type,
        "document_type": document.document_type,
    }

    # Generate PDF
    try:
        pdf_bytes = generate_compliance_report_pdf(report_data, document_info)
    except Exception as e:
        logger.error(f"PDF generation failed for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}",
        )

    # Return as streaming response
    pdf_stream = io.BytesIO(pdf_bytes)
    filename = f"compliance_report_{doc_id}.pdf"

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(pdf_bytes)),
        },
    )
