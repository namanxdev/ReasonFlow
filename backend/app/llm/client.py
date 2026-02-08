"""Gemini LLM client using LangChain's Google GenAI integration."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.llm.prompts import (
    CLASSIFICATION_PROMPT,
    DECISION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)
from app.llm.schemas import (
    DecisionResult,
    EntitiesResult,
    GenerationResult,
    IntentResult,
)

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around Google Gemini via LangChain for structured LLM calls."""

    def __init__(self) -> None:
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True,
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _invoke(self, prompt: str) -> str:
        """Invoke the LLM with retry logic."""
        messages = [
            SystemMessage(content="You are a helpful AI assistant. Always respond in valid JSON."),
            HumanMessage(content=prompt),
        ]
        response = await self.llm.ainvoke(messages)
        return str(response.content)

    def _parse_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove markdown code fences
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response: %s", text[:200])
            return {}

    async def classify_intent(
        self, subject: str, body: str, sender: str
    ) -> IntentResult:
        """Classify the intent of an email."""
        prompt = CLASSIFICATION_PROMPT.format(
            subject=subject, body=body, sender=sender
        )
        response = await self._invoke(prompt)
        data = self._parse_json(response)
        return IntentResult(
            intent=data.get("intent", "other"),
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", ""),
        )

    async def generate_response(
        self,
        subject: str,
        body: str,
        sender: str,
        classification: str,
        context: str,
        tool_results: str = "",
    ) -> GenerationResult:
        """Generate a response to an email."""
        prompt = RESPONSE_GENERATION_PROMPT.format(
            subject=subject,
            body=body,
            sender=sender,
            classification=classification,
            context=context,
            tool_results=tool_results,
        )
        response = await self._invoke(prompt)
        data = self._parse_json(response)
        return GenerationResult(
            response=data.get("response", ""),
            tone=data.get("tone", "professional"),
            confidence=float(data.get("confidence", 0.5)),
        )

    async def extract_entities(self, text: str) -> EntitiesResult:
        """Extract structured entities from text."""
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)
        response = await self._invoke(prompt)
        data = self._parse_json(response)
        return EntitiesResult(
            dates=data.get("dates", []),
            people=data.get("people", []),
            topics=data.get("topics", []),
            action_items=data.get("action_items", []),
        )

    async def decide_tools(
        self,
        classification: str,
        subject: str,
        body: str,
        context: str,
    ) -> DecisionResult:
        """Decide which tools to invoke for processing an email."""
        prompt = DECISION_PROMPT.format(
            classification=classification,
            subject=subject,
            body=body,
            context=context,
        )
        response = await self._invoke(prompt)
        data = self._parse_json(response)
        return DecisionResult(
            selected_tools=data.get("selected_tools", []),
            reasoning=data.get("reasoning", ""),
            params=data.get("params", {}),
        )

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a vector embedding for the given text."""
        vectors = await self.embeddings.aembed_documents([text])
        return vectors[0]

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate vector embeddings for a batch of texts."""
        return await self.embeddings.aembed_documents(texts)


# Singleton instance
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get or create the GeminiClient singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
