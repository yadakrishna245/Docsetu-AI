"""
DocSetu AI - Documents Integration Tests
Tests for document upload, listing, retrieval, and deletion.
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from tests.conftest import MINIMAL_PDF_BYTES


class TestDocumentUpload:
    """Tests for POST /api/documents/upload."""

    async def test_upload_pdf_success(self, test_client: AsyncClient, test_user: dict):
        """Test successful PDF upload."""
        mock_ocr_result = {
            "text": "Extracted text from PDF.",
            "language_detected": "en",
            "page_count": 1,
            "method": "pdfplumber",
            "is_scanned": False,
            "confidence": 0.95,
        }

        with patch("services.background_tasks.process_document_ocr"):
            response = await test_client.post(
                "/api/documents/upload",
                files={"file": ("invoice.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
                headers=test_user["headers"],
            )

        assert response.status_code in (201, 202)
        data = response.json()
        assert "id" in data
        assert data["filename"] == "invoice.pdf"
        assert data["status"] in ("processed", "uploaded", "processing", "failed")
        assert "message" in data

    async def test_upload_invalid_file_type_fails(self, test_client: AsyncClient, test_user: dict):
        """Test that uploading an unsupported file type returns 400."""
        invalid_content = b"This is not a valid document."

        response = await test_client.post(
            "/api/documents/upload",
            files={"file": ("malware.exe", invalid_content, "application/octet-stream")},
            headers=test_user["headers"],
        )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    async def test_upload_txt_file_fails(self, test_client: AsyncClient, test_user: dict):
        """Test that uploading a .txt file returns 400 (not in allowed extensions)."""
        txt_content = b"Hello, this is a text file."

        response = await test_client.post(
            "/api/documents/upload",
            files={"file": ("notes.txt", txt_content, "text/plain")},
            headers=test_user["headers"],
        )

        assert response.status_code == 400

    async def test_upload_without_auth_fails(self, test_client: AsyncClient):
        """Test that uploading without authentication returns 401."""
        response = await test_client.post(
            "/api/documents/upload",
            files={"file": ("doc.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )

        assert response.status_code == 401


class TestDocumentList:
    """Tests for GET /api/documents/."""

    async def test_list_documents(self, test_client: AsyncClient, test_user: dict, test_document: dict):
        """Test listing documents returns user's documents."""
        response = await test_client.get(
            "/api/documents/",
            headers=test_user["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["total"] >= 1
        assert len(data["documents"]) >= 1

    async def test_list_documents_without_auth_fails(self, test_client: AsyncClient):
        """Test listing documents without token returns 401."""
        response = await test_client.get("/api/documents/")
        assert response.status_code == 401

    async def test_list_documents_pagination(self, test_client: AsyncClient, test_user: dict, test_document: dict):
        """Test that pagination parameters work."""
        response = await test_client.get(
            "/api/documents/?page=1&page_size=5",
            headers=test_user["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestDocumentGetById:
    """Tests for GET /api/documents/{id}."""

    async def test_get_document_by_id(self, test_client: AsyncClient, test_user: dict, test_document: dict):
        """Test retrieving a specific document by ID."""
        doc_id = test_document["id"]

        response = await test_client.get(
            f"/api/documents/{doc_id}",
            headers=test_user["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert "filename" in data
        assert "original_filename" in data
        assert "file_type" in data
        assert "file_size" in data
        assert "status" in data
        assert "owner_id" in data
        assert "created_at" in data

    async def test_get_nonexistent_document_returns_404(self, test_client: AsyncClient, test_user: dict):
        """Test that requesting a non-existent document returns 404."""
        response = await test_client.get(
            "/api/documents/nonexistent-id-12345",
            headers=test_user["headers"],
        )

        assert response.status_code == 404

    async def test_get_document_without_auth_fails(self, test_client: AsyncClient, test_document: dict):
        """Test that getting a document without auth returns 401."""
        response = await test_client.get(f"/api/documents/{test_document['id']}")
        assert response.status_code == 401


class TestDocumentDelete:
    """Tests for DELETE /api/documents/{id}."""

    async def test_delete_document(self, test_client: AsyncClient, test_user: dict, test_document: dict):
        """Test successful document deletion."""
        doc_id = test_document["id"]

        response = await test_client.delete(
            f"/api/documents/{doc_id}",
            headers=test_user["headers"],
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = await test_client.get(
            f"/api/documents/{doc_id}",
            headers=test_user["headers"],
        )
        assert get_response.status_code == 404

    async def test_delete_nonexistent_document_returns_404(self, test_client: AsyncClient, test_user: dict):
        """Test that deleting a non-existent document returns 404."""
        response = await test_client.delete(
            "/api/documents/nonexistent-id-12345",
            headers=test_user["headers"],
        )

        assert response.status_code == 404

    async def test_delete_document_without_auth_fails(self, test_client: AsyncClient, test_document: dict):
        """Test that deleting without auth returns 401."""
        response = await test_client.delete(f"/api/documents/{test_document['id']}")
        assert response.status_code == 401
