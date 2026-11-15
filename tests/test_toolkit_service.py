
from personatwin.storage import Store
from personatwin.service import PersonaTwinService


class FakeJudge:
    """Mock judge that records calls without contacting an AI provider."""

    def __init__(self):
        self.calls = []

    def evaluate_toolkit_response(
        self, question, reference_answer, candidate_response
    ):
        self.calls.append({
            "question_id": question["id"],
            "reference_answer": reference_answer,
            "candidate_response": candidate_response,
        })

        return {
            "preference_fidelity": 0.8,
            "reasoning_fidelity": 0.7,
            "communication_fidelity": 0.9,
            "situational_fidelity": 0.8,
            "overall_fidelity": 0.8,
            "evidence_sufficiency": "sufficient",
            "matches": [],
            "mismatches": [],
            "limitations": [],
            "rationale": "Mock evaluation.",
        }

    @staticmethod
    def _insufficient(reason):
        return {
            "preference_fidelity": None,
            "reasoning_fidelity": None,
            "communication_fidelity": None,
            "situational_fidelity": None,
            "overall_fidelity": None,
            "evidence_sufficiency": "insufficient",
            "matches": [],
            "mismatches": [],
            "limitations": [reason],
            "rationale": reason,
        }


def make_service(tmp_path):
    store = Store(str(tmp_path / "toolkit_service.db"))
    service = PersonaTwinService(store=store)
    service.judge = FakeJudge()
    return service


def grant_consent(service, person_id="PERSON01"):
    service.store.add_consent(
        person_id,
        True,
        "voluntary coaching and reflection",
        None,
        "1.0",
    )


def import_scenario_question(service, question_id="PRIVATE_S9"):
    return service.import_toolkit_questions([
        {
            "id": question_id,
            "type": "scenario",
            "wording": "How would you handle a disagreement?",
            "options": {
                "A": "Reply in writing.",
                "B": "Arrange a conversation.",
                "C": "Ask a colleague.",
                "D": "Take no action.",
            },
            "word_limit": None,
            "prompt": "Exact official prompt text.",
        }
    ])


def test_service_imports_dynamic_question_ids(tmp_path):
    service = make_service(tmp_path)

    result = import_scenario_question(
        service, "UNSEEN_PRIVATE_QUESTION_91"
    )

    assert result["imported"] == 1

    question = service.store.get_toolkit_question(
        "UNSEEN_PRIVATE_QUESTION_91"
    )

    assert question["id"] == "UNSEEN_PRIVATE_QUESTION_91"
    assert question["prompt"] == "Exact official prompt text."


def test_reference_import_requires_consent(tmp_path):
    service = make_service(tmp_path)

    payload = {
        "items": [],
        "scenarios": [
            {
                "id": "PRIVATE_S9",
                "choice": "B",
                "explanation": "A conversation is more effective.",
            }
        ],
        "writing": [],
        "skipped": [],
    }

    try:
        service.import_toolkit_reference_answers(
            "PERSON01", payload
        )
        assert False, "Expected consent to be required."
    except PermissionError:
        pass

    assert service.store.get_reference_answer(
        "PERSON01", "PRIVATE_S9"
    ) is None


def test_reference_import_succeeds_with_consent(tmp_path):
    service = make_service(tmp_path)
    grant_consent(service)

    payload = {
        "items": [],
        "scenarios": [
            {
                "id": "PRIVATE_S9",
                "choice": "B",
                "explanation": "A conversation is more effective.",
            }
        ],
        "writing": [],
        "skipped": [],
    }

    result = service.import_toolkit_reference_answers(
        "PERSON01", payload
    )

    assert result["imported"] == 1

    saved = service.store.get_reference_answer(
        "PERSON01", "PRIVATE_S9"
    )

    assert saved["answer"]["choice"] == "B"


def test_multiple_runs_for_same_question_are_evaluated_separately(
    tmp_path,
):
    service = make_service(tmp_path)
    grant_consent(service)
    import_scenario_question(service, "PRIVATE_S9")

    service.import_toolkit_reference_answers(
        "PERSON01",
        {
            "items": [],
            "scenarios": [
                {
                    "id": "PRIVATE_S9",
                    "choice": "B",
                    "explanation": "I prefer a conversation.",
                }
            ],
            "writing": [],
            "skipped": [],
        },
    )

    imported = service.import_toolkit_comparison_responses([
        {
            "run_id": "R01",
            "question_id": "PRIVATE_S9",
            "text": "B. I would arrange a conversation.",
        },
        {
            "run_id": "R03",
            "question_id": "PRIVATE_S9",
            "text": "A. I would reply in writing.",
        },
    ])

    assert imported["imported"] == 2

    first = service.evaluate_toolkit_response(
        "PERSON01", "R01"
    )
    second = service.evaluate_toolkit_response(
        "PERSON01", "R03"
    )

    assert first["question_id"] == "PRIVATE_S9"
    assert second["question_id"] == "PRIVATE_S9"

    assert (
        first["evaluation"]["scenario_choice_comparison"]["match"]
        is True
    )

    assert (
        second["evaluation"]["scenario_choice_comparison"]["match"]
        is False
    )

    assert len(service.judge.calls) == 2

    saved = service.store.list_toolkit_evaluations()

    assert len(saved) == 2
    assert {item["run_id"] for item in saved} == {"R01", "R03"}


def test_missing_reference_does_not_call_ai_judge(tmp_path):
    service = make_service(tmp_path)
    grant_consent(service)
    import_scenario_question(service, "PRIVATE_S9")

    service.import_toolkit_comparison_responses([
        {
            "run_id": "R10",
            "question_id": "PRIVATE_S9",
            "text": "B. I would arrange a conversation.",
        }
    ])

    result = service.evaluate_toolkit_response(
        "PERSON01", "R10"
    )

    evaluation = result["evaluation"]

    assert evaluation["evidence_sufficiency"] == "insufficient"
    assert evaluation["overall_fidelity"] is None
    assert len(service.judge.calls) == 0

    saved = service.store.list_toolkit_evaluations()

    assert len(saved) == 1
    assert saved[0]["run_id"] == "R10"


def test_reference_must_match_exact_question_id(tmp_path):
    service = make_service(tmp_path)
    grant_consent(service)

    import_scenario_question(service, "S02")
    import_scenario_question(service, "S04")

    service.import_toolkit_reference_answers(
        "PERSON01",
        {
            "items": [],
            "scenarios": [
                {
                    "id": "S04",
                    "choice": "B",
                    "explanation": "Reference for S04 only.",
                }
            ],
            "writing": [],
            "skipped": [],
        },
    )

    service.import_toolkit_comparison_responses([
        {
            "run_id": "R20",
            "question_id": "S02",
            "text": "B. Candidate response for S02.",
        }
    ])

    result = service.evaluate_toolkit_response(
        "PERSON01", "R20"
    )

    assert result["evaluation"]["evidence_sufficiency"] == "insufficient"
    assert result["evaluation"]["overall_fidelity"] is None
    assert len(service.judge.calls) == 0


def test_ambiguous_scenario_choice_is_not_guessed(tmp_path):
    service = make_service(tmp_path)
    grant_consent(service)
    import_scenario_question(service, "PRIVATE_S9")

    service.import_toolkit_reference_answers(
        "PERSON01",
        {
            "items": [],
            "scenarios": [
                {
                    "id": "PRIVATE_S9",
                    "choice": "B",
                    "explanation": "I prefer discussion.",
                }
            ],
            "writing": [],
            "skipped": [],
        },
    )

    service.import_toolkit_comparison_responses([
        {
            "run_id": "R30",
            "question_id": "PRIVATE_S9",
            "text": "I would arrange a conversation.",
        }
    ])

    result = service.evaluate_toolkit_response(
        "PERSON01", "R30"
    )

    comparison = result["evaluation"]["scenario_choice_comparison"]

    assert comparison["candidate_choice"] is None
    assert comparison["match"] is None
    assert comparison["status"] == "inconclusive"
