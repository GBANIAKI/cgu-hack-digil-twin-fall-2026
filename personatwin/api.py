from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from .schemas import (
    AssessmentPayload,
    ProfileGenerateRequest,
    ConsentRequest,
    LLMGenerateRequest,
    EvaluationInput,
    WethosImportRequest,
    CompareRequest,
    ToolkitQuestionFile,
    ReferenceAnswersImportRequest,
    ComparisonResponseFile,
    ToolkitEvaluationRequest,
)
from .service import PersonaTwinService
from .storage import Store

app = FastAPI(title="PersonaTwin AI", version="1.0.0", description="Evidence-grounded portable digital personality profile prototype")
service = PersonaTwinService(Store(os.getenv("PERSONATWIN_DB", "personatwin.db")))

def translate_error(exc):
    if isinstance(exc, PermissionError): raise HTTPException(403, str(exc))
    if isinstance(exc, ValueError): raise HTTPException(422, str(exc))
    raise HTTPException(500, str(exc))

@app.get("/health")
def health(): return {"status": "ok", "application": "PersonaTwin AI"}

@app.post("/consent")
def record_consent(req: ConsentRequest):
    service.store.add_consent(req.person_id, req.consent, req.purpose, req.recipient, req.text_version)
    return {"person_id": req.person_id, "consent_recorded": True, "active": req.consent,
            "message": "This records the latest consent choice. A withdrawal blocks future profile-conditioned processing."}

@app.post("/assessments/validate")
def validate_assessment(req: AssessmentPayload):
    from .converter import clean_answers
    answers, warnings = clean_answers(req.model_dump())
    return {"valid": not warnings, "accepted_items": len(answers["items"]), "accepted_scenarios": len(answers["scenarios"]),
            "accepted_writing_samples": len(answers["writing"]), "warnings": warnings}

@app.post("/profiles")
def create_profile(req: ProfileGenerateRequest):
    try: return service.create_profile(req.assessment.model_dump(), req.review_status)
    except Exception as exc: translate_error(exc)

@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str):
    profile = service.store.get_profile(profile_id)
    if not profile: raise HTTPException(404, "Profile not found")
    return {k: profile[k] for k in ("id", "person_id", "version", "review_status", "created_at", "active", "scores")}

@app.get("/profiles/{profile_id}/download", response_class=PlainTextResponse)
def download_profile(profile_id: str):
    profile = service.store.get_profile(profile_id)
    if not profile: raise HTTPException(404, "Profile not found")
    return PlainTextResponse(profile["markdown"], media_type="text/markdown; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="me.md"'})

@app.post("/generate")
def generate(req: LLMGenerateRequest):
    try:
        outputs = [service.generate(req.profile_id, model, scenario, req.use_profile, req.temperature)
                   for model in (("LLM_A", "LLM_B") if req.both_models else ("LLM_A",)) for scenario in req.scenarios]
        return {"outputs": outputs}
    except Exception as exc: translate_error(exc)

@app.post("/evaluate")
def evaluate(req: EvaluationInput):
    try: return service.evaluate(req.model_dump())
    except Exception as exc: translate_error(exc)

@app.post("/evaluation/matrix")
def evaluation_matrix(req: CompareRequest):
    try: return service.run_matrix(req.profile_id, req.scenarios, req.reference_answers)
    except Exception as exc: translate_error(exc)

@app.post("/evaluation/wethos")
def evaluate_wethos(req: WethosImportRequest):
    try: return service.import_wethos([x.model_dump() for x in req.outputs], req.reference_answers, req.person_id)
    except Exception as exc: translate_error(exc)

@app.get("/generations")
def generations(profile_id: str | None = None): return service.store.list_generations(profile_id)
@app.get("/evaluations")
def evaluations(): return service.store.list_evaluations()


# ---------------------------------------------------------------------
# Official Digital Personality Modeling Toolkit API
# ---------------------------------------------------------------------

@app.post("/toolkit/questions/import")
def import_toolkit_questions(req: ToolkitQuestionFile):
    try:
        return service.import_toolkit_questions(
            [question.model_dump() for question in req.questions]
        )
    except Exception as exc:
        translate_error(exc)


@app.get("/toolkit/questions")
def list_toolkit_questions():
    return service.store.list_toolkit_questions()


@app.post("/toolkit/reference-answers/import")
def import_toolkit_reference_answers(
    req: ReferenceAnswersImportRequest,
):
    try:
        payload = req.model_dump(exclude={"person_id"})

        return service.import_toolkit_reference_answers(
            person_id=req.person_id,
            payload=payload,
        )
    except Exception as exc:
        translate_error(exc)


@app.post("/toolkit/comparison-responses/import")
def import_toolkit_comparison_responses(
    req: ComparisonResponseFile,
):
    try:
        return service.import_toolkit_comparison_responses(
            [response.model_dump() for response in req.responses]
        )
    except Exception as exc:
        translate_error(exc)


@app.post("/toolkit/evaluate")
def evaluate_toolkit_response(req: ToolkitEvaluationRequest):
    try:
        return service.evaluate_toolkit_response(
            person_id=req.person_id,
            run_id=req.run_id,
        )
    except Exception as exc:
        translate_error(exc)


@app.get("/toolkit/evaluations")
def list_toolkit_evaluations():
    return service.store.list_toolkit_evaluations()
