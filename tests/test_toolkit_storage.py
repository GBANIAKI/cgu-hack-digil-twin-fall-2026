from personatwin.storage import Store


def test_toolkit_questions_accept_dynamic_ids(tmp_path):
    store = Store(str(tmp_path / "toolkit.db"))

    questions = [
        {
            "id": "PRIVATE_SCENARIO_X9",
            "type": "scenario",
            "wording": "A test scenario",
            "options": {"A": "Option A", "B": "Option B"},
            "word_limit": 60,
            "prompt": "Official prompt text",
        }
    ]

    assert store.import_toolkit_questions(questions) == 1
    assert store.get_toolkit_question("PRIVATE_SCENARIO_X9") == questions[0]


def test_reference_answers_are_stored_separately(tmp_path):
    store = Store(str(tmp_path / "toolkit.db"))

    payload = {
        "items": [{"id": "B01", "response": 4}],
        "scenarios": [
            {"id": "PRIVATE_S7", "choice": "B", "explanation": "My explanation"}
        ],
        "writing": [
            {"id": "PRIVATE_W8", "text": "My original writing sample."}
        ],
        "skipped": [],
    }

    assert store.import_reference_answers("PERSON01", payload) == 3

    scenario = store.get_reference_answer("PERSON01", "PRIVATE_S7")
    writing = store.get_reference_answer("PERSON01", "PRIVATE_W8")

    assert scenario["answer_type"] == "scenario"
    assert scenario["answer"]["choice"] == "B"
    assert writing["answer_type"] == "writing"
    assert writing["answer"]["text"] == "My original writing sample."


def test_comparison_runs_can_share_question_id(tmp_path):
    store = Store(str(tmp_path / "toolkit.db"))

    responses = [
        {"run_id": "R01", "question_id": "S02", "text": "Candidate response one."},
        {"run_id": "R03", "question_id": "S02", "text": "Candidate response two."},
    ]

    assert store.add_comparison_responses(responses) == 2
    assert store.get_comparison_response("R01")["question_id"] == "S02"
    assert store.get_comparison_response("R03")["question_id"] == "S02"
    assert len(store.list_comparison_responses()) == 2


def test_duplicate_run_ids_are_rejected(tmp_path):
    store = Store(str(tmp_path / "toolkit.db"))

    responses = [
        {"run_id": "R01", "question_id": "S02", "text": "First response."},
        {"run_id": "R01", "question_id": "S04", "text": "Second response."},
    ]

    try:
        store.add_comparison_responses(responses)
        assert False, "Expected duplicate run_id to be rejected."
    except ValueError as exc:
        assert "Duplicate run_id" in str(exc)


def test_toolkit_evaluation_is_saved_and_retrieved(tmp_path):
    store = Store(str(tmp_path / "toolkit.db"))

    result = {
        "overall_fidelity": 0.8,
        "evidence_sufficiency": "sufficient",
        "matches": [],
        "mismatches": [],
        "limitations": [],
    }

    store.save_toolkit_evaluation("R01", "PERSON01", "S02", result)

    evaluations = store.list_toolkit_evaluations()

    assert len(evaluations) == 1
    assert evaluations[0]["run_id"] == "R01"
    assert evaluations[0]["question_id"] == "S02"
    assert evaluations[0]["result"]["overall_fidelity"] == 0.8