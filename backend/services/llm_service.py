"""
DocSetu AI - LLM Service
Integration with OpenAI and Google Gemini for document intelligence.
Provides entity extraction, Q&A, summarization, and compliance analysis.
"""

import json
import logging
import time
from typing import Optional, Dict, Any, List

import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """LLM service supporting OpenAI and Google Gemini."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            provider: LLM provider ('openai' or 'gemini'). Defaults to config.
        """
        self.provider = provider or settings.llm_provider
        self._validate_config()

    def _validate_config(self):
        """Validate that required API keys are configured."""
        if self.provider == "openai" and not settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
        elif self.provider == "gemini" and not settings.gemini_api_key:
            logger.warning("Gemini API key not configured")
        elif self.provider == "kimi" and not settings.kimi_api_key:
            logger.warning("Kimi API key not configured")

    async def _call_kimi(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> Dict[str, Any]:
        """
        Call Kimi K3 API (OpenAI-compatible format).

        Kimi K3: 2.8T params, 1M context, $3/M input, $0.30/M cached input, $15/M output.
        API docs: https://platform.moonshot.ai

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.

        Returns:
            API response with content and metadata.
        """
        headers = {
            "Authorization": f"Bearer {settings.kimi_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.kimi_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.moonshot.ai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            "model": data.get("model", settings.kimi_model),
        }

    async def _call_openai(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> Dict[str, Any]:
        """
        Call OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.

        Returns:
            API response with content and metadata.
        """
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            "model": data.get("model", settings.openai_model),
        }

    async def _call_gemini(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Call Google Gemini API.

        Args:
            prompt: Text prompt for Gemini.
            temperature: Sampling temperature.

        Returns:
            API response with content and metadata.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"

        headers = {"Content-Type": "application/json"}
        params = {"key": settings.gemini_api_key}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4000,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url, headers=headers, params=params, json=payload
            )
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "content": content,
            "tokens_used": data.get("usageMetadata", {}).get("totalTokenCount", 0),
            "model": settings.gemini_model,
        }

    async def _generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Generate response from configured LLM provider.

        Args:
            system_prompt: System context/instructions.
            user_prompt: User query/document content.
            temperature: Sampling temperature.

        Returns:
            LLM response with content and metadata.
        """
        start_time = time.time()

        try:
            if self.provider == "openai":
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                result = await self._call_openai(messages, temperature)
            elif self.provider == "kimi":
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                result = await self._call_kimi(messages, temperature)
            elif self.provider == "gemini":
                combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
                result = await self._call_gemini(combined_prompt, temperature)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

            result["processing_time_ms"] = int((time.time() - start_time) * 1000)
            result["provider"] = self.provider
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error ({self.provider}): {e.response.status_code} - {e.response.text}")
            raise ValueError(f"LLM API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            raise

    async def extract_entities(self, document_text: str) -> Dict[str, Any]:
        """
        Extract entities from document text using LLM.

        Args:
            document_text: Full text of the document.

        Returns:
            Dictionary with extracted entities.
        """
        system_prompt = """You are an expert Indian document analyst. Extract all entities from the given document text.
        
Return a JSON object with these keys:
- pan_numbers: List of PAN numbers found
- gst_numbers: List of GSTIN numbers found
- aadhaar_numbers: List of Aadhaar numbers found (masked for privacy)
- dates: List of all dates mentioned (in DD/MM/YYYY format)
- amounts: List of objects with {value, currency, context} for each monetary amount
- parties: List of person/organization names mentioned
- addresses: List of addresses found
- phone_numbers: List of phone numbers
- email_addresses: List of email addresses
- document_type: Type of document (invoice, contract, ID card, etc.)
- document_date: Primary date of the document
- reference_numbers: Any reference/invoice/order numbers

Only include entities you are confident about. Return valid JSON only."""

        user_prompt = f"Extract all entities from this Indian document:\n\n{document_text[:8000]}"

        result = await self._generate(system_prompt, user_prompt)

        try:
            # Parse JSON from response
            content = result["content"]
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            entities = json.loads(content)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse LLM entity extraction response as JSON")
            entities = {"raw_response": result["content"]}

        return {
            "entities": entities,
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "model": result.get("model", ""),
            "provider": result.get("provider", ""),
        }

    async def answer_question(self, document_text: str, question: str) -> Dict[str, Any]:
        """
        Answer a question about a document.

        Args:
            document_text: Full text of the document.
            question: User's question.

        Returns:
            Dictionary with answer and metadata.
        """
        system_prompt = """You are DocSetu AI, an expert Indian document analyst. 
Answer the user's question based ONLY on the provided document text.
If the answer is not in the document, say so clearly.
Provide specific quotes or references from the document when possible.
For financial or legal questions about Indian documents, provide context about relevant regulations."""

        user_prompt = f"""Document Text:
---
{document_text[:6000]}
---

Question: {question}

Provide a clear, accurate answer based on the document above."""

        result = await self._generate(system_prompt, user_prompt, temperature=0.2)

        return {
            "answer": result["content"],
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "model": result.get("model", ""),
            "provider": result.get("provider", ""),
        }

    async def summarize_document(self, document_text: str) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of a document.

        Args:
            document_text: Full text of the document.

        Returns:
            Dictionary with summary and key points.
        """
        system_prompt = """You are DocSetu AI, an expert at summarizing Indian documents.
Provide a structured summary with:
1. A brief overview (2-3 sentences)
2. Key points as a bullet list
3. Important dates, amounts, and parties
4. Document type classification
5. Any action items or deadlines

Format your response as JSON:
{
    "summary": "...",
    "key_points": ["...", "..."],
    "document_type": "...",
    "important_dates": ["..."],
    "amounts_mentioned": ["..."],
    "parties_involved": ["..."],
    "action_items": ["..."]
}"""

        user_prompt = f"Summarize this Indian document:\n\n{document_text[:8000]}"

        result = await self._generate(system_prompt, user_prompt)

        try:
            content = result["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            summary_data = json.loads(content)
        except (json.JSONDecodeError, IndexError):
            summary_data = {
                "summary": result["content"],
                "key_points": [],
                "document_type": "unknown",
            }

        return {
            **summary_data,
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "model": result.get("model", ""),
            "provider": result.get("provider", ""),
        }

    async def compare_documents(self, text_1: str, text_2: str) -> Dict[str, Any]:
        """
        Compare two documents and identify similarities/differences.

        Args:
            text_1: Text of first document.
            text_2: Text of second document.

        Returns:
            Comparison results.
        """
        system_prompt = """You are DocSetu AI. Compare the two Indian documents provided.
Identify:
1. Key similarities
2. Key differences
3. Conflicting information
4. Missing information in either document
5. Overall similarity assessment

Return JSON:
{
    "similarities": [{"aspect": "...", "detail": "..."}],
    "differences": [{"aspect": "...", "doc1": "...", "doc2": "..."}],
    "conflicts": [{"aspect": "...", "detail": "..."}],
    "overall_similarity_score": 0.0-1.0,
    "summary": "..."
}"""

        user_prompt = f"""Document 1:
---
{text_1[:4000]}
---

Document 2:
---
{text_2[:4000]}
---

Compare these two documents."""

        result = await self._generate(system_prompt, user_prompt)

        try:
            content = result["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            comparison = json.loads(content)
        except (json.JSONDecodeError, IndexError):
            comparison = {"summary": result["content"], "overall_similarity_score": 0.0}

        return {
            **comparison,
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
        }

    async def analyze_compliance(self, document_text: str, regulations: List[str]) -> Dict[str, Any]:
        """
        Analyze document compliance with Indian regulations.

        Args:
            document_text: Full text of the document.
            regulations: List of regulation categories to check.

        Returns:
            Compliance analysis results.
        """
        reg_context = ", ".join(regulations) if regulations else "GST, DPDP Act, SEBI, RBI, MCA"

        system_prompt = f"""You are an Indian regulatory compliance expert. Analyze the document for compliance with: {reg_context}.

For each regulation, check:
- Required fields/disclosures present
- Format compliance
- Regulatory requirements met
- Potential violations

Return JSON:
{{
    "overall_status": "compliant|non_compliant|partial|needs_review",
    "overall_score": 0-100,
    "findings": [
        {{
            "regulation": "...",
            "status": "pass|fail|warning",
            "rule": "...",
            "detail": "...",
            "severity": "critical|high|medium|low",
            "recommendation": "..."
        }}
    ],
    "summary": "..."
}}"""

        user_prompt = f"Analyze this document for Indian regulatory compliance:\n\n{document_text[:8000]}"

        result = await self._generate(system_prompt, user_prompt, temperature=0.1)

        try:
            content = result["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            compliance_data = json.loads(content)
        except (json.JSONDecodeError, IndexError):
            compliance_data = {
                "overall_status": "needs_review",
                "overall_score": 0,
                "findings": [],
                "summary": result["content"],
            }

        return {
            **compliance_data,
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
        }
