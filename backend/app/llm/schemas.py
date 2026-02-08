"""Pydantic schemas for LLM outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    """Result of email intent classification."""

    intent: str = Field(description="The classified intent category")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(default="", description="Brief explanation of classification")


class EntitiesResult(BaseModel):
    """Extracted entities from text."""

    dates: list[str] = Field(default_factory=list, description="Extracted date references")
    people: list[str] = Field(default_factory=list, description="Extracted person names")
    topics: list[str] = Field(default_factory=list, description="Key topics identified")
    action_items: list[str] = Field(default_factory=list, description="Action items found")


class GenerationResult(BaseModel):
    """Result of response generation."""

    response: str = Field(description="Generated email response")
    tone: str = Field(default="professional", description="Tone of the response")
    confidence: float = Field(ge=0.0, le=1.0, description="Generation confidence")


class DecisionResult(BaseModel):
    """Result of tool selection decision."""

    selected_tools: list[str] = Field(
        default_factory=list, description="Tools to invoke"
    )
    reasoning: str = Field(default="", description="Why these tools were selected")
    params: dict[str, dict] = Field(
        default_factory=dict,
        description="Parameters for each selected tool",
    )
