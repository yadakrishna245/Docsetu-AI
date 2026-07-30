"""
DocSetu AI - Documents Router
Handles document upload, listing, retrieval, and deletion.
"""

import os
import uuid
import logging
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from config import get_settings
from db import get_db
from models.database import Document, User
from models.schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentStatusResponse,
    BatchUploadResponse,
    BatchAcceptedFile,
    BatchRejectedFile,
    BatchStatusResponse,
    BatchDocumentStatus,
)
from routers.auth import get_current_user
from services.background_tasks import process_document_ocr
from utils.rbac import require_role

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/documents", tags=["Documents"])


def _ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst")),
):
    """
    Upload a document (PDF or image) for processing.

    The file is saved and a database record is created immediately.
    OCR processing happens asynchronously in the background.
    Use the /api/documents/{doc_id}/status endpoint to check progress.

    Supports: PDF, PNG, JPG, JPEG, TIFF, BMP

    Args:
        background_tasks: FastAPI background tasks handler.
        file: Uploaded file.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Upload confirmation with document ID (HTTP 202 Accepted).
    """
    _ensure_upload_dir()

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{extension}' not allowed. Supported: {settings.allowed_extensions_list}",
        )

    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB",
        )

    # Generate unique filename
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}.{extension}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except IOError as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        )

    # Create database record with status='uploaded'
    document = Document(
        id=doc_id,
        filename=safe_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=extension,
        file_size=file_size,
        mime_type=file.content_type,
        status="uploaded",
        owner_id=current_user.id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Schedule OCR processing as a background task
    background_tasks.add_task(
        process_document_ocr,
        doc_id=doc_id,
        file_path=file_path,
        db_url=settings.database_url,
    )

    logger.info(f"Document {doc_id} uploaded, OCR processing scheduled in background")

    return DocumentUploadResponse(
        id=doc_id,
        filename=file.filename,
        status="uploaded",
        message="Document uploaded successfully. OCR processing has been queued.",
    )


@router.post("/batch-upload", response_model=BatchUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload multiple documents (up to 20) for batch processing.

    Each file is validated independently. Valid files are saved and queued for
    OCR processing; invalid files are skipped and reported in the response.

    Limits:
    - Maximum 20 files per batch
    - Each file max 50MB
    - Supported types: PDF, PNG, JPG, JPEG, TIFF, BMP

    Args:
        files: List of uploaded files.
        background_tasks: FastAPI background tasks handler.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Batch response with accepted/rejected file lists (HTTP 202 Accepted).
    """
    # Enforce max 20 files per batch
    if len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 20 files per batch. You submitted {len(files)} files.",
        )

    _ensure_upload_dir()

    batch_id = str(uuid.uuid4())
    accepted: List[BatchAcceptedFile] = []
    rejected: List[BatchRejectedFile] = []

    max_size = 50 * 1024 * 1024  # 50MB per file

    for file in files:
        # Validate filename
        if not file.filename:
            rejected.append(BatchRejectedFile(filename="(no filename)", reason="Filename is required"))
            continue

        # Validate extension
        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in settings.allowed_extensions_list:
            rejected.append(BatchRejectedFile(
                filename=file.filename,
                reason=f"File type '{extension}' not allowed. Supported: {settings.allowed_extensions_list}",
            ))
            continue

        # Read and validate file size
        try:
            file_content = await file.read()
        except Exception as e:
            rejected.append(BatchRejectedFile(filename=file.filename, reason=f"Failed to read file: {str(e)}"))
            continue

        file_size = len(file_content)
        if file_size > max_size:
            rejected.append(BatchRejectedFile(
                filename=file.filename,
                reason=f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum of 50MB",
            ))
            continue

        if file_size == 0:
            rejected.append(BatchRejectedFile(filename=file.filename, reason="File is empty"))
            continue

        # Generate unique filename and save
        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}.{extension}"
        file_path = os.path.join(settings.upload_dir, safe_filename)

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except IOError as e:
            logger.error(f"Failed to save file {file.filename}: {e}")
            rejected.append(BatchRejectedFile(filename=file.filename, reason="Failed to save file on server"))
            continue

        # Create database record
        document = Document(
            id=doc_id,
            filename=safe_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=extension,
            file_size=file_size,
            mime_type=file.content_type,
            status="queued",
            batch_id=batch_id,
            owner_id=current_user.id,
        )

        db.add(document)
        accepted.append(BatchAcceptedFile(id=doc_id, filename=file.filename, status="queued"))

        # Queue background OCR processing
        background_tasks.add_task(
            process_document_ocr,
            doc_id=doc_id,
            file_path=file_path,
            db_url=settings.database_url,
        )

    # Commit all accepted documents at once
    if accepted:
        db.commit()

    logger.info(
        f"Batch {batch_id}: {len(accepted)} accepted, {len(rejected)} rejected "
        f"(user: {current_user.id})"
    )

    return BatchUploadResponse(
        batch_id=batch_id,
        total_files=len(files),
        accepted=accepted,
        rejected=rejected,
    )


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the processing status of all documents in a batch.

    Args:
        batch_id: The batch UUID returned from batch-upload.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Status of all documents belonging to the batch.
    """
    documents = (
        db.query(Document)
        .filter(Document.batch_id == batch_id, Document.owner_id == current_user.id)
        .order_by(Document.created_at)
        .all()
    )

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No documents found for batch '{batch_id}'",
        )

    return BatchStatusResponse(
        batch_id=batch_id,
        total=len(documents),
        documents=[
            BatchDocumentStatus(
                id=doc.id,
                filename=doc.original_filename,
                status=doc.status,
                error_message=doc.error_message,
                processed_at=doc.processed_at,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
    )


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the processing status of a document.

    Useful for polling after upload to check if OCR processing is complete.

    Args:
        doc_id: Document ID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Current processing status of the document.
    """
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found",
        )

    return DocumentStatusResponse(
        id=document.id,
        status=document.status,
        filename=document.original_filename,
        error_message=document.error_message,
        processed_at=document.processed_at,
        created_at=document.created_at,
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all documents for the current user with pagination.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status_filter: Optional status filter.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Paginated list of documents.
    """
    query = db.query(Document).filter(Document.owner_id == current_user.id)

    if status_filter:
        query = query.filter(Document.status == status_filter)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    documents = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific document.

    Args:
        doc_id: Document ID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Document details including extracted data.
    """
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found",
        )

    return document


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document and its associated file.

    Args:
        doc_id: Document ID.
        db: Database session.
        current_user: Authenticated user.
    """
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.owner_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found",
        )

    # Delete physical file
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except OSError as e:
        logger.warning(f"Failed to delete file {document.file_path}: {e}")

    # Delete database record (cascades to analyses and compliance reports)
    db.delete(document)
    db.commit()

    logger.info(f"Document {doc_id} deleted by user {current_user.id}")
