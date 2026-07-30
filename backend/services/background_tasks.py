"""
DocSetu AI - Background Tasks Service
Handles async document processing (OCR, etc.) outside of request lifecycle.
"""

import logging
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.ocr_service import OCRService

logger = logging.getLogger(__name__)


def process_document_ocr(doc_id: str, file_path: str, db_url: str) -> None:
    """
    Process OCR for a document in the background.

    Creates its own DB session since background tasks cannot use
    the request-scoped session (which may already be closed).

    Args:
        doc_id: The document ID to process.
        file_path: Path to the uploaded file on disk.
        db_url: Database connection URL for creating a new session.
    """
    logger.info(f"[Background] Starting OCR processing for document {doc_id}")

    # Create an independent DB session for background work
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(db_url, pool_pre_ping=True)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Import here to avoid circular imports
        from models.database import Document

        document = db.query(Document).filter(Document.id == doc_id).first()

        if not document:
            logger.error(f"[Background] Document {doc_id} not found in database")
            return

        # Update status to processing
        document.status = "processing"
        db.commit()
        logger.info(f"[Background] Document {doc_id} status set to 'processing'")

        # Run OCR extraction
        ocr_service = OCRService()
        import asyncio

        # OCRService.extract_text is async, so we need to run it in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            ocr_result = loop.run_until_complete(ocr_service.extract_text(file_path))
        finally:
            loop.close()

        # Update document with OCR results
        document.extracted_text = ocr_result.get("text", "")
        document.language_detected = ocr_result.get("language_detected")
        document.page_count = ocr_result.get("page_count", 1)
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        document.metadata_json = {
            "method": ocr_result.get("method", "unknown"),
            "is_scanned": ocr_result.get("is_scanned", False),
            "confidence": ocr_result.get("confidence", None),
        }

        db.commit()
        logger.info(f"[Background] Document {doc_id} processed successfully")

    except Exception as e:
        logger.error(f"[Background] OCR processing failed for document {doc_id}: {e}")
        try:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                document.status = "failed"
                document.error_message = str(e)
                db.commit()
        except Exception as db_err:
            logger.error(
                f"[Background] Failed to update error status for document {doc_id}: {db_err}"
            )
    finally:
        db.close()
        logger.info(f"[Background] Finished processing task for document {doc_id}")
