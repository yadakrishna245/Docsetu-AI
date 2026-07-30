"""
DocSetu AI - Analysis Router
AI-powered document analysis: entity extraction, Q&A, comparison, and summarization.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config import get_settings
from db import get_db
from models.database import Document, Analysis, User
from models.schemas import (
    EntityExtractionResponse,
    QARequest,
    QAResponse,
    CompareRequest,
    CompareResponse,
    SummaryResponse,
)
from routers.auth import get_current_user
from services.llm_service import LLMService
from utils.indian_regex import extract_all_patterns

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


def _get_document_or_404(doc_id: str, user_id: str, db: Session) -> Document:
    """Get document or raise 404."""
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == user_id)
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
    return document


@router.post("/extract/{doc_id}", response_model=EntityExtractionResponse)
async def extract_entities(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract entities from a document using regex and LLM.

    Extracts: PAN, GST, Aadhaar, dates, amounts, parties, addresses, etc.

    Args:
        doc_id: Document ID to analyze.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Extracted entities with confidence scores.
    """
    start_time = time.time()
    document = _get_document_or_404(doc_id, current_user.id, db)

    # Phase 1: Regex-based extraction
    regex_entities = extract_all_patterns(document.extracted_text)

    # Phase 2: LLM-based extraction for deeper analysis
    llm_entities = {}
    try:
        llm_service = LLMService()
        llm_result = await llm_service.extract_entities(document.extracted_text)
        llm_entities = llm_result.get("entities", {})
    except Exception as e:
        logger.warning(f"LLM entity extraction failed, using regex only: {e}")

    # Merge results (regex takes precedence for structured patterns)
    merged_entities = {**llm_entities}
    for key, values in regex_entities.items():
        if key in merged_entities:
            # Combine and deduplicate
            existing = set(merged_entities[key]) if isinstance(merged_entities[key], list) else set()
            merged_entities[key] = list(existing.union(set(values)))
        else:
            merged_entities[key] = values

    # Extract specific fields
    amounts = []
    if "amounts" in merged_entities:
        for amt in merged_entities["amounts"]:
            if isinstance(amt, dict):
                amounts.append(amt)
            else:
                amounts.append({"value": amt, "currency": "INR", "context": ""})

    dates = merged_entities.get("dates", []) + merged_entities.get("dates_words", [])
    parties = merged_entities.get("parties", [])

    processing_time = int((time.time() - start_time) * 1000)

    # Save analysis to database
    analysis = Analysis(
        document_id=doc_id,
        analysis_type="entity_extraction",
        entities=merged_entities,
        amounts=amounts,
        dates=dates,
        parties=parties,
        result_json=merged_entities,
        status="completed",
        processing_time_ms=processing_time,
        llm_provider=settings.llm_provider,
        model_used=settings.openai_model if settings.llm_provider == "openai" else settings.gemini_model,
        completed_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()

    return EntityExtractionResponse(
        document_id=doc_id,
        entities=merged_entities,
        amounts=amounts,
        dates=dates,
        parties=parties,
        confidence=0.85 if llm_entities else 0.65,
        processing_time_ms=processing_time,
    )


@router.post("/qa", response_model=QAResponse)
async def question_answer(
    request: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ask a question about a document using LLM.

    Args:
        request: Q&A request with document ID and question.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        AI-generated answer based on document content.
    """
    document = _get_document_or_404(request.document_id, current_user.id, db)

    # Truncate text to context window
    context_text = document.extracted_text[:request.context_window]

    try:
        llm_service = LLMService()
        result = await llm_service.answer_question(context_text, request.question)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question",
        )

    # Save analysis
    analysis = Analysis(
        document_id=request.document_id,
        analysis_type="qa",
        result_json={"question": request.question, "answer": result["answer"]},
        summary=result["answer"],
        status="completed",
        processing_time_ms=result.get("processing_time_ms", 0),
        tokens_used=result.get("tokens_used", 0),
        llm_provider=result.get("provider", ""),
        model_used=result.get("model", ""),
        completed_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()

    return QAResponse(
        document_id=request.document_id,
        question=request.question,
        answer=result["answer"],
        confidence=0.8,
        tokens_used=result.get("tokens_used"),
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(
    request: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare two documents and identify similarities/differences.

    Args:
        request: Comparison request with two document IDs.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Comparison results with similarities, differences, and score.
    """
    doc1 = _get_document_or_404(request.document_id_1, current_user.id, db)
    doc2 = _get_document_or_404(request.document_id_2, current_user.id, db)

    try:
        llm_service = LLMService()
        result = await llm_service.compare_documents(
            doc1.extracted_text, doc2.extracted_text
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Document comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare documents",
        )

    return CompareResponse(
        document_id_1=request.document_id_1,
        document_id_2=request.document_id_2,
        similarities=result.get("similarities", []),
        differences=result.get("differences", []),
        overall_similarity_score=result.get("overall_similarity_score", 0.0),
        summary=result.get("summary", ""),
    )


@router.post("/summarize/{doc_id}", response_model=SummaryResponse)
async def summarize_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI summary of a document.

    Args:
        doc_id: Document ID to summarize.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Document summary with key points.
    """
    document = _get_document_or_404(doc_id, current_user.id, db)

    try:
        llm_service = LLMService()
        result = await llm_service.summarize_document(document.extracted_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to summarize document",
        )

    # Save analysis
    analysis = Analysis(
        document_id=doc_id,
        analysis_type="summary",
        summary=result.get("summary", ""),
        result_json=result,
        status="completed",
        processing_time_ms=result.get("processing_time_ms", 0),
        tokens_used=result.get("tokens_used", 0),
        llm_provider=result.get("provider", ""),
        model_used=result.get("model", ""),
        completed_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()

    return SummaryResponse(
        document_id=doc_id,
        summary=result.get("summary", ""),
        key_points=result.get("key_points", []),
        document_type=result.get("document_type"),
        word_count=len(document.extracted_text.split()),
        processing_time_ms=result.get("processing_time_ms", 0),
    )
