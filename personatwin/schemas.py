from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class InventoryAnswer(BaseModel):
    id: str
    response: int = Field(ge=1, le=5)
class ScenarioAnswer(BaseModel):
    id: str
    choice: str = Field(min_length=1, max_length=1)
    explanation: str = ""
class WritingAnswer(BaseModel):
    id: str
    text: str = Field(min_length=1)
class AssessmentPayload(BaseModel):
    person_id: str = "UNKNOWN"
    items: list[InventoryAnswer] = []
    scenarios: list[ScenarioAnswer] = []
    writing: list[WritingAnswer] = []
    skipped: list[str] = []
    consent: bool = False
    consent_text_version: str = "1.0"
class ProfileGenerateRequest(BaseModel):
    assessment: AssessmentPayload
    review_status: str = "Not yet reviewed by the person."
class ProfileCorrectionRequest(BaseModel):
    assessment: AssessmentPayload
    review_status: str = "Reviewed by the person."
class LLMGenerateRequest(BaseModel):
    profile_id: str
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    use_profile: bool = True
    temperature: float = Field(default=0.2, ge=0, le=2)
    both_models: bool = False
class EvaluationInput(BaseModel):
    person_id: str | None = None
    scenario_id: str
    scenario_prompt: str
    response: str
    model: str
    profile_id: str | None = None
    reference_answers: dict[str, Any] = Field(default_factory=dict)
    source: Literal["profile", "baseline", "wethos"] = "profile"
class ConsentRequest(BaseModel):
    person_id: str
    consent: bool
    purpose: str = "voluntary coaching, reflection, and communication support"
    recipient: str | None = None
    text_version: str = "1.0"
class WethosImportRequest(BaseModel):
    person_id: str
    outputs: list[EvaluationInput]
    reference_answers: dict[str, Any] = Field(default_factory=dict)
class CompareRequest(BaseModel):
    profile_id: str
    reference_answers: dict[str, Any]
    scenarios: list[dict[str, Any]]


# ---------------------------------------------------------------------
# Official Digital Personality Modeling Toolkit data contracts
# ---------------------------------------------------------------------

class ToolkitQuestion(BaseModel):
    """A question definition supplied by the official toolkit."""
    id: str = Field(min_length=1)
    type: Literal["scenario", "writing"]
    wording: str = Field(min_length=1)
    options: dict[str, str] | None = None
    word_limit: int | None = Field(default=None, ge=1)
    prompt: str = Field(min_length=1)


class ToolkitQuestionFile(BaseModel):
    """Question definitions may contain previously unseen question IDs."""
    questions: list[ToolkitQuestion] = Field(default_factory=list)


class ReferenceScenarioAnswer(BaseModel):
    """A participant's reference answer to a scenario question."""
    id: str = Field(min_length=1)
    choice: str = Field(min_length=1, max_length=1)
    explanation: str = ""


class ReferenceWritingAnswer(BaseModel):
    """A participant's reference answer to a writing question."""
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class ReferenceAnswersImportRequest(BaseModel):
    """
    Participant reference answers from the toolkit test/private-question
    file. These answers are separate from the build assessment and must
    never be passed through the Common Kit profile converter.
    """
    person_id: str = Field(min_length=1)
    items: list[InventoryAnswer] = Field(default_factory=list)
    scenarios: list[ReferenceScenarioAnswer] = Field(default_factory=list)
    writing: list[ReferenceWritingAnswer] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)


class ComparisonResponse(BaseModel):
    """One independently identifiable candidate response."""
    run_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class ComparisonResponseFile(BaseModel):
    """Imported candidate responses; multiple runs may share a question ID."""
    responses: list[ComparisonResponse] = Field(default_factory=list)


class ToolkitEvaluationRequest(BaseModel):
    """Request to evaluate one imported candidate response."""
    person_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
