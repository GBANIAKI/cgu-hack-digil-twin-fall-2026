from __future__ import annotations
import json
import re
from .converter import clean_answers, build_me_md, check_claims
from .providers import ProviderRegistry
from .judge import PersonalityJudge
from .storage import Store
from .kit import SCENARIOS

class PersonaTwinService:
    def __init__(self, store: Store | None = None, providers: ProviderRegistry | None = None):
        self.store = store or Store(); self.providers = providers or ProviderRegistry(); self.judge = PersonalityJudge(self.providers)
    def create_profile(self, payload: dict, review_status="Not yet reviewed by the person."):
        person_id = str(payload.get("person_id", "UNKNOWN"))
        if not self.store.has_consent(person_id): raise PermissionError("Active consent is required before profile generation.")
        answers, warnings = clean_answers(payload)
        assessment_id = self.store.add_assessment(person_id, {**answers, "consent": True})
        markdown, scores = build_me_md(answers, review_status=review_status)
        flags = check_claims(markdown, answers)
        if flags: raise ValueError("Profile evidence validation failed: " + "; ".join(flags))
        saved = self.store.add_profile(person_id, assessment_id, markdown,
            {k: {"mean": v["mean"], "band": v["band"], "answered": v["n"], "missing": v["missing"]} for k, v in scores.items()}, review_status)
        return {**saved, "assessment_id": assessment_id, "person_id": person_id, "markdown": markdown,
                "warnings": warnings, "evidence_check": "passed"}
    def generate(self, profile_id: str | None, model_name: str, scenario: dict, use_profile=True, temperature=0.2):
        profile = self.store.get_profile(profile_id) if profile_id else None
        if use_profile and not profile: raise ValueError("A valid profile_id is required when use_profile=true.")
        if profile and not self.store.has_consent(profile["person_id"]): raise PermissionError("Consent is no longer active; generation is blocked.")
        prompt = str(scenario.get("prompt") or scenario.get("scenario_prompt") or "").strip()
        sid = str(scenario.get("id") or scenario.get("scenario_id") or "CUSTOM")
        if not prompt: raise ValueError("Scenario prompt is required.")
        if use_profile:
            system = "You are simulating a response based only on the participant's supplied profile. Do not claim to be the participant. Do not invent unsupported preferences. Output only the requested response.\n\nPERSONALITY PROFILE:\n" + profile["markdown"]
        else:
            system = "Answer the workplace scenario as a neutral assistant without a personality profile. Do not imply that the answer represents a specific person."
        response = self.providers.get(model_name).complete([{"role": "system", "content": system}, {"role": "user", "content": prompt}], temperature=temperature)
        gid = self.store.add_generation(profile_id if use_profile else None, model_name, sid, prompt, response,
                                        "profile" if use_profile else "baseline", {"model": self.providers.get(model_name).model, "temperature": temperature, "profile_version": profile["version"] if profile else None})
        return {"generation_id": gid, "scenario_id": sid, "model": model_name, "source": "profile" if use_profile else "baseline", "response": response}
    def evaluate(self, data: dict):
        profile = self.store.get_profile(data.get("profile_id")) if data.get("profile_id") else None
        consent_person = profile["person_id"] if profile else data.get("person_id")
        if data.get("reference_answers") and (not consent_person or not self.store.has_consent(consent_person)):
            raise PermissionError("Active participant consent is required before sending reference answers to the AI judge.")
        if profile and not self.store.has_consent(profile["person_id"]): raise PermissionError("Consent is no longer active; evaluation is blocked.")
        payload = dict(data)
        if profile: payload["profile_excerpt"] = profile["markdown"][:12000]
        result = self.judge.evaluate(payload)
        eid = self.store.add_evaluation(data.get("generation_id"), data["scenario_id"], data["model"], data.get("source", "profile"), result)
        return {"evaluation_id": eid, "result": result}
    def run_matrix(self, profile_id: str, scenarios: list[dict], reference_answers: dict):
        if len(scenarios) != 4: raise ValueError("The required matrix needs exactly four scenario prompts.")
        outputs = []
        for model in ("LLM_A", "LLM_B"):
            for use_profile in (True, False):
                for scenario in scenarios:
                    generated = self.generate(profile_id, model, scenario, use_profile=use_profile)
                    evaluation = self.evaluate({**generated, "scenario_prompt": scenario["prompt"],
                        "response": generated["response"], "model": model, "profile_id": profile_id if use_profile else None,
                        "reference_answers": reference_answers, "source": generated["source"]})
                    outputs.append({**generated, **evaluation})
        return {"project_output_count": len(outputs), "outputs": outputs,
                "wethos_outputs_required": 4, "total_required_outputs": 20,
                "note": "Import and evaluate the four organizer-provided Wethos outputs separately. Volunteer reference answers are evidence, not scored outputs."}
    def import_wethos(self, outputs: list[dict], reference_answers: dict, person_id: str):
        if not self.store.has_consent(person_id): raise PermissionError("Active participant consent is required before evaluating Wethos outputs against personal reference answers.")
        if len(outputs) != 4: raise ValueError("Exactly four Wethos outputs are required.")
        results = []
        for item in outputs:
            payload = {**item, "person_id": person_id, "source": "wethos", "reference_answers": reference_answers}
            results.append(self.evaluate(payload))
        return {"wethos_evaluated": len(results), "results": results}



    # -----------------------------------------------------------------
    # Official Digital Personality Modeling Toolkit integration
    # -----------------------------------------------------------------

    def import_toolkit_questions(self, questions: list[dict]):
        """Import official question definitions, including dynamic IDs."""

        question_ids = [item["id"] for item in questions]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Duplicate question IDs found in toolkit questions.")

        return {
            "imported": self.store.import_toolkit_questions(questions)
        }

    def import_toolkit_reference_answers(
        self, person_id: str, payload: dict
    ):
        """
        Import participant reference answers separately from build answers.

        Active consent is required before storing these personal answers.
        """

        if not self.store.has_consent(person_id):
            raise PermissionError(
                "Active participant consent is required before importing reference answers."
            )

        imported = self.store.import_reference_answers(
            person_id, payload
        )

        return {
            "person_id": person_id,
            "imported": imported,
            "storage": "separate_toolkit_reference_answers",
        }

    def import_toolkit_comparison_responses(
        self, responses: list[dict]
    ):
        """Import candidate responses and verify their question definitions."""

        for item in responses:
            question = self.store.get_toolkit_question(
                item["question_id"]
            )

            if not question:
                raise ValueError(
                    f"Question definition not found for question_id "
                    f"{item['question_id']} (run_id {item['run_id']})."
                )

        imported = self.store.add_comparison_responses(responses)

        return {
            "imported": imported,
            "runs": [item["run_id"] for item in responses],
        }

    @staticmethod
    def _extract_scenario_choice(response: str) -> str | None:
        """
        Extract an explicitly formatted A-D answer from the beginning
        of a candidate response.

        Examples:
            B. Explanation...
            Option C: Explanation...
            (A) Explanation...

        Ambiguous answers are not guessed.
        """

        if not isinstance(response, str):
            return None

        match = re.match(
            r"^\s*(?:\(([A-D])\)|(?:option\s+)?([A-D])\s*[\).:\-])",
            response,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return (match.group(1) or match.group(2)).upper()

    def evaluate_toolkit_response(
        self, person_id: str, run_id: str
    ):
        """
        Evaluate one imported candidate response against the participant's
        reference answer for the exact same question ID.
        """

        if not self.store.has_consent(person_id):
            raise PermissionError(
                "Active participant consent is required before toolkit evaluation."
            )

        candidate = self.store.get_comparison_response(run_id)

        if not candidate:
            raise ValueError(
                f"Comparison response {run_id} was not found."
            )

        question_id = candidate["question_id"]

        question = self.store.get_toolkit_question(question_id)

        reference = self.store.get_reference_answer(
            person_id, question_id
        )

        # Missing evidence must never be replaced with another answer
        # or sent to the AI judge.
        if not question:
            result = self.judge._insufficient(
                f"Question definition {question_id} was not found."
            )

        elif not reference:
            result = self.judge._insufficient(
                f"No participant reference answer exists for question {question_id}."
            )

        else:
            result = self.judge.evaluate_toolkit_response(
                question=question,
                reference_answer=reference,
                candidate_response=candidate["response_text"],
            )

        # Deterministic scenario-choice comparison is separate from
        # the AI judge's semantic evaluation.
        choice_comparison = None

        if question and question.get("type") == "scenario":
            reference_choice = (
                reference["answer"].get("choice")
                if reference
                and reference.get("answer_type") == "scenario"
                else None
            )

            candidate_choice = self._extract_scenario_choice(
                candidate["response_text"]
            )

            choice_comparison = {
                "reference_choice": reference_choice,
                "candidate_choice": candidate_choice,
                "match": (
                    candidate_choice == reference_choice
                    if candidate_choice and reference_choice
                    else None
                ),
                "status": (
                    "compared"
                    if candidate_choice and reference_choice
                    else "inconclusive"
                ),
            }

        result["scenario_choice_comparison"] = choice_comparison

        # Persist the result under its original run ID.
        self.store.save_toolkit_evaluation(
            run_id=run_id,
            person_id=person_id,
            question_id=question_id,
            result=result,
        )

        return {
            "run_id": run_id,
            "person_id": person_id,
            "question_id": question_id,
            "evaluation": result,
        }
