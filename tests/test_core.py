from personatwin.converter import clean_answers, score_domains, build_me_md, check_claims

def test_reverse_scoring_and_missing_threshold():
    scores = score_domains({"B01": 5, "B06": 1})
    assert scores["Extraversion"]["keyed"]["B01"] == 5
    assert scores["Extraversion"]["keyed"]["B06"] == 5
    assert scores["Extraversion"]["mean"] is None  # fewer than eight of ten answered

def test_test_questions_are_removed():
    answers, warnings = clean_answers({"items": [{"id": "B01", "response": 4}],
        "scenarios": [{"id": "S02", "choice": "A"}], "writing": [{"id": "W02", "text": "test"}]})
    assert "S02" not in answers["scenarios"] and "W02" not in answers["writing"]
    assert len(warnings) == 2

def test_profile_is_generated_and_citations_check():
    payload = {"person_id": "P001", "items": [{"id": f"B{i:02d}", "response": 3} for i in range(1, 51)],
        "scenarios": [{"id": "S01", "choice": "D", "explanation": "I would ask a question first."}],
        "writing": [{"id": "W01", "text": "Hello team, the project is cancelled."}], "skipped": []}
    answers, warnings = clean_answers(payload)
    md, scores = build_me_md(answers)
    assert "## Instructions for the AI model" in md
    assert "## Appendix: item-level evidence" in md
    assert check_claims(md, answers) == []
    assert scores["Extraversion"]["mean"] == 3.0
