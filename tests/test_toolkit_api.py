
from fastapi.testclient import TestClient

from personatwin import api
from personatwin.storage import Store
from personatwin.service import PersonaTwinService


class FakeJudge:
    def __init__(self):
        self.calls = []

    def evaluate_toolkit_response(
        self, question, reference_answer, candidate_response
    ):
        self.calls.append(question["id"])

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
            "rationale": "API test evaluation.",
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


def make_client(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "toolkit_api.db"))
    service = PersonaTwinService(store=store)
    fake_judge = FakeJudge()
    service.judge = fake_judge

    monkeypatch.setattr(api, "service", service)

    return TestClient(api.app), fake_judge


def test_toolkit_api_end_to_end(tmp_path, monkeypatch):
    client, fake_judge = make_client(tmp_path, monkeypatch)

    # 1. Import official question definitions.
    question_payload = {
        "questions": [
            {
                "id": "PRIVATE_API_S91",
                "type": "scenario",
                "wording": "How would you resolve a disagreement?",
                "options": {
                    "A": "Reply in writing.",
                    "B": "Arrange a conversation.",
                    "C": "Ask a colleague.",
                    "D": "Take no action.",
                },
                "word_limit": None,
                "prompt": "Exact official prompt text.",
            }
        ]
    }

    response = client.post(
        "/toolkit/questions/import",
        json=question_payload,
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1

    # 2. Retrieve question definitions.
    response = client.get("/toolkit/questions")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "PRIVATE_API_S91"
    assert response.json()[0]["prompt"] == "Exact official prompt text."

    # 3. Reference import must require consent.
    reference_payload = {
        "person_id": "API_PERSON01",
        "items": [],
        "scenarios": [
            {
                "id": "PRIVATE_API_S91",
                "choice": "B",
                "explanation": "A conversation resolves disagreements.",
            }
        ],
        "writing": [],
        "skipped": [],
    }

    response = client.post(
        "/toolkit/reference-answers/import",
        json=reference_payload,
    )

    assert response.status_code == 403

    # Record participant consent.
    response = client.post(
        "/consent",
        json={
            "person_id": "API_PERSON01",
            "consent": True,
            "purpose": "voluntary coaching and reflection",
            "recipient": None,
            "text_version": "1.0",
        },
    )

    assert response.status_code == 200

    # Import reference answers after consent.
    response = client.post(
        "/toolkit/reference-answers/import",
        json=reference_payload,
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1

    # 4. Import two candidate runs for the same question.
    comparison_payload = {
        "responses": [
            {
                "run_id": "API_R01",
                "question_id": "PRIVATE_API_S91",
                "text": "B. I would arrange a conversation.",
            },
            {
                "run_id": "API_R03",
                "question_id": "PRIVATE_API_S91",
                "text": "A. I would reply in writing.",
            },
        ]
    }

    response = client.post(
        "/toolkit/comparison-responses/import",
        json=comparison_payload,
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 2

    # 5. Evaluate the first candidate.
    response = client.post(
        "/toolkit/evaluate",
        json={
            "person_id": "API_PERSON01",
            "run_id": "API_R01",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["run_id"] == "API_R01"
    assert result["question_id"] == "PRIVATE_API_S91"
    assert result["evaluation"]["evidence_sufficiency"] == "sufficient"
    assert result["evaluation"]["scenario_choice_comparison"]["match"] is True

    # 6. Retrieve saved evaluations.
    response = client.get("/toolkit/evaluations")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["run_id"] == "API_R01"

    # Only one candidate was evaluated, so the judge was called once.
    assert len(fake_judge.calls) == 1


def test_toolkit_api_rejects_unknown_question_id(
    tmp_path, monkeypatch
):
    client, fake_judge = make_client(tmp_path, monkeypatch)

    response = client.post(
        "/toolkit/comparison-responses/import",
        json={
            "responses": [
                {
                    "run_id": "UNKNOWN_R01",
                    "question_id": "UNKNOWN_QUESTION",
                    "text": "Candidate response.",
                }
            ]
        },
    )

    assert response.status_code == 422
    assert len(fake_judge.calls) == 0


def test_toolkit_api_missing_reference_returns_insufficient(
    tmp_path, monkeypatch
):
    client, fake_judge = make_client(tmp_path, monkeypatch)

    # Import a question.
    response = client.post(
        "/toolkit/questions/import",
        json={
            "questions": [
                {
                    "id": "NO_REFERENCE_S01",
                    "type": "scenario",
                    "wording": "A test scenario.",
                    "options": {"A": "First", "B": "Second"},
                    "word_limit": None,
                    "prompt": "Exact test prompt.",
                }
            ]
        },
    )

    assert response.status_code == 200

    # Record consent.
    response = client.post(
        "/consent",
        json={
            "person_id": "API_PERSON02",
            "consent": True,
            "purpose": "voluntary coaching and reflection",
            "recipient": None,
            "text_version": "1.0",
        },
    )

    assert response.status_code == 200

    # Import candidate response without a participant reference.
    response = client.post(
        "/toolkit/comparison-responses/import",
        json={
            "responses": [
                {
                    "run_id": "NO_REFERENCE_R01",
                    "question_id": "NO_REFERENCE_S01",
                    "text": "B. I would choose the second option.",
                }
            ]
        },
    )

    assert response.status_code == 200

    # Evaluation must not call the AI judge.
    response = client.post(
        "/toolkit/evaluate",
        json={
            "person_id": "API_PERSON02",
            "run_id": "NO_REFERENCE_R01",
        },
    )

    assert response.status_code == 200
    assert response.json()["evaluation"]["evidence_sufficiency"] == "insufficient"
    assert response.json()["evaluation"]["overall_fidelity"] is None

    assert len(fake_judge.calls) == 0
