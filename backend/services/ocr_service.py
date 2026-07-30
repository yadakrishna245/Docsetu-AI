"""
DocSetu AI - OCR Service
Multi-language OCR engine supporting Hindi, English, Tamil, Telugu, Kannada.
Handles PDF text extraction, image OCR, and scanned documents.
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    TESSERACT_AVAILABLE = False

from PIL import Image
from PyPDF2 import PdfReader

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Tesseract path
if TESSERACT_AVAILABLE and settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


# Language code mapping for Tesseract
LANGUAGE_MAP = {
    "english": "eng",
    "hindi": "hin",
    "tamil": "tam",
    "telugu": "tel",
    "kannada": "kan",
    "malayalam": "mal",
    "bengali": "ben",
    "gujarati": "guj",
    "marathi": "mar",
    "punjabi": "pan",
    "urdu": "urd",
}


class OCRService:
    """OCR service for extracting text from documents and images."""

    def __init__(self, languages: Optional[List[str]] = None):
        """
        Initialize OCR service.

        Args:
            languages: List of languages to use for OCR.
                       Defaults to configured Tesseract languages.
        """
        if languages:
            self.lang_string = "+".join(
                LANGUAGE_MAP.get(lang.lower(), lang) for lang in languages
            )
        else:
            self.lang_string = settings.tesseract_lang

    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a file (PDF or image).

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary containing extracted text and metadata.
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".pdf":
            return await self._extract_from_pdf(file_path)
        elif extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]:
            return await self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    async def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF file.
        First attempts direct text extraction, falls back to OCR for scanned PDFs.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Dictionary with extracted text and metadata.
        """
        result = {
            "text": "",
            "page_count": 0,
            "method": "direct",
            "language_detected": None,
            "pages": [],
            "is_scanned": False,
        }

        try:
            reader = PdfReader(file_path)
            result["page_count"] = len(reader.pages)

            extracted_pages = []
            total_text = []

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append({
                    "page_number": i + 1,
                    "text": page_text,
                    "char_count": len(page_text),
                })
                total_text.append(page_text)

            full_text = "\n\n".join(total_text)

            # If very little text extracted, it's likely a scanned PDF
            if len(full_text.strip()) < 100 and result["page_count"] > 0:
                logger.info("PDF appears to be scanned. Attempting OCR...")
                result["is_scanned"] = True
                result["method"] = "ocr"
                ocr_result = await self._ocr_pdf_pages(file_path)
                result["text"] = ocr_result["text"]
                result["pages"] = ocr_result["pages"]
            else:
                result["text"] = full_text
                result["pages"] = extracted_pages

            # Detect language
            result["language_detected"] = self._detect_language(result["text"])

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            # Fallback to OCR
            try:
                result["method"] = "ocr_fallback"
                ocr_result = await self._ocr_pdf_pages(file_path)
                result["text"] = ocr_result["text"]
                result["pages"] = ocr_result["pages"]
                result["is_scanned"] = True
            except Exception as ocr_error:
                logger.error(f"OCR fallback also failed: {ocr_error}")
                raise ValueError(f"Failed to extract text from PDF: {e}")

        return result

    async def _ocr_pdf_pages(self, file_path: str) -> Dict[str, Any]:
        """
        OCR each page of a PDF by converting to images.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Dictionary with OCR'd text and page data.
        """
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(file_path, dpi=300)
            pages = []
            all_text = []

            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(
                    image, lang=self.lang_string
                )
                pages.append({
                    "page_number": i + 1,
                    "text": page_text,
                    "char_count": len(page_text),
                })
                all_text.append(page_text)

            return {
                "text": "\n\n".join(all_text),
                "pages": pages,
            }
        except ImportError:
            logger.warning("pdf2image not available. Cannot OCR PDF pages.")
            raise ValueError("pdf2image library required for scanned PDF processing")

    async def _extract_from_image(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from an image using Tesseract OCR.

        Args:
            file_path: Path to the image file.

        Returns:
            Dictionary with extracted text and metadata.
        """
        result = {
            "text": "",
            "page_count": 1,
            "method": "ocr",
            "language_detected": None,
            "pages": [],
            "is_scanned": True,
            "confidence": 0.0,
        }

        try:
            image = Image.open(file_path)

            # Preprocess image for better OCR
            image = self._preprocess_image(image)

            # Extract text
            text = pytesseract.image_to_string(image, lang=self.lang_string)

            # Get detailed data with confidence
            data = pytesseract.image_to_data(
                image, lang=self.lang_string, output_type=pytesseract.Output.DICT
            )

            # Calculate average confidence
            confidences = [
                int(c) for c in data["conf"] if int(c) > 0
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            result["text"] = text
            result["confidence"] = round(avg_confidence, 2)
            result["pages"] = [{
                "page_number": 1,
                "text": text,
                "char_count": len(text),
            }]
            result["language_detected"] = self._detect_language(text)

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise ValueError(f"Failed to OCR image: {e}")

        return result

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image: PIL Image object.

        Returns:
            Preprocessed PIL Image.
        """
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Convert to grayscale
        image = image.convert("L")

        # Apply threshold for better text detection
        threshold = 128
        image = image.point(lambda p: 255 if p > threshold else 0)

        return image

    def _detect_language(self, text: str) -> Optional[str]:
        """
        Simple heuristic-based language detection for Indian languages.

        Args:
            text: Extracted text to analyze.

        Returns:
            Detected language name or None.
        """
        if not text:
            return None

        # Unicode ranges for Indian scripts
        script_ranges = {
            "hindi": (0x0900, 0x097F),       # Devanagari
            "tamil": (0x0B80, 0x0BFF),       # Tamil
            "telugu": (0x0C00, 0x0C7F),      # Telugu
            "kannada": (0x0C80, 0x0CFF),     # Kannada
            "malayalam": (0x0D00, 0x0D7F),   # Malayalam
            "bengali": (0x0980, 0x09FF),     # Bengali
            "gujarati": (0x0A80, 0x0AFF),    # Gujarati
            "punjabi": (0x0A00, 0x0A7F),     # Gurmukhi
        }

        char_counts: Dict[str, int] = {lang: 0 for lang in script_ranges}
        english_count = 0
        total_alpha = 0

        for char in text:
            code = ord(char)
            if char.isalpha():
                total_alpha += 1
                if code < 128:
                    english_count += 1
                else:
                    for lang, (start, end) in script_ranges.items():
                        if start <= code <= end:
                            char_counts[lang] += 1
                            break

        if total_alpha == 0:
            return None

        # Find dominant script
        max_script = max(char_counts, key=char_counts.get)
        max_count = char_counts[max_script]

        if max_count > english_count and max_count > total_alpha * 0.1:
            return max_script
        elif english_count > total_alpha * 0.5:
            return "english"
        elif max_count > 0:
            return max_script

        return "english"

    async def extract_from_bytes(
        self, file_bytes: bytes, filename: str
    ) -> Dict[str, Any]:
        """
        Extract text from file bytes (for in-memory processing).

        Args:
            file_bytes: File content as bytes.
            filename: Original filename for type detection.

        Returns:
            Dictionary with extracted text and metadata.
        """
        extension = Path(filename).suffix.lower()

        with tempfile.NamedTemporaryFile(
            suffix=extension, delete=False
        ) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            return await self.extract_text(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
