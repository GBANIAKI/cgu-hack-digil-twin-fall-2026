
from __future__ import annotations

import json
import re

from .providers import ProviderRegistry, ProviderError


JUDGE_SYSTEM = """You are an evidence-grounded evaluator of simulated responses. You are NOT diagnosing personality. Compare the candidate response only with supplied reference answers and profile evidence. Do not reward grammar, length, confidence, sophistication, corporate polish, or generic helpfulness. Distinguish semantic content from communication style. Do not infer traits absent from evidence. If evidence is inadequate, set evidence_sufficiency to insufficient and explain why. A response is an AI simulation, never the person's real statement. Return only valid JSON with keys: preference_fidelity, reasoning_fidelity, communication_fidelity, situational_fidelity, overall_fidelity, evidence_sufficiency, matches, mismatches, limitations, rationale. Scores are numbers from 0 to 1 or null when not assessable. matches/mismatches are arrays of objects with claim, evidence_ids, explanation."""


TOOLKIT_JUDGE_SYSTEM = """
You are an evidence-grounded evaluator of candidate responses
against a participant's own reference answer.

You are NOT diagnosing personality and must not make psychological,
clinical, employment, or hiring suitability judgments.

Evaluate only the evidence supplied:
- The official question wording.
- The question type.
- The available answer options, if applicable.
- The participant's reference answer.
- The candidate response.

For scenario questions:
- Compare the candidate's selected choice with the participant's choice.
- Compare the reasoning and explanation with the participant's explanation.
- Do not assume that different wording means different reasoning.
- Do not treat a different choice as automatically wrong or inferior.

For writing questions:
- Compare the candidate's meaning, expressed preferences,
  intent, tone, and communication approach with the participant's
  reference writing.
- Do not reward grammar, length, confidence, sophistication,
  corporate polish, or generic helpfulness.
- Distinguish semantic content from communication style.

Evidence rules:
- Do not invent participant preferences, reasoning, or traits.
- Do not infer missing reference answers.
- Do not assume a model name, source, or generation method.
- If the evidence is inadequate, use null scores and set
  evidence_sufficiency to "insufficient".
- Cite the supplied question ID in evidence_ids when applicable.

Return only valid JSON with these keys:
preference_fidelity,
reasoning_fidelity,
communication_fidelity,
situational_fidelity,
overall_fidelity,
evidence_sufficiency,
matches,
mismatches,
limitations,
rationale.

Scores must be numbers from 0 to 1, or null when not assessable.
evidence_sufficiency must be "sufficient", "insufficient", or "uncertain".
matches and mismatches must be arrays of objects containing:
claim, evidence_ids, explanation.
limitations must be an array of strings.
"""


class PersonalityJudge:

    def __init__(self, providers: ProviderRegistry):
        self.providers = providers

    # -------------------------------------------------------------
    # Existing evaluation workflow
    # -------------------------------------------------------------

    def evaluate(self, payload: dict) -> dict:
        evidence = payload.get("reference_answers") or {}

        if not evidence:
            return self._insufficient(
                "No reference answers were supplied."
            )

        user = {
            "scenario_id": payload["scenario_id"],
            "scenario": payload["scenario_prompt"],
            "candidate_response": payload["response"],
            "model": payload["model"],
            "source": payload.get("source", "profile"),
            "reference_answers": evidence,
            "profile_excerpt": payload.get("profile_excerpt", ""),
        }

        try:
            raw = self.providers.get("JUDGE").complete(
                [
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {
                        "role": "user",
                        "content": json.dumps(user, ensure_ascii=False),
                    },
                ],
                temperature=0,
                json_mode=True,
            )

            result = json.loads(raw)
            return self._validate(result)

        except (
            ProviderError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            return self._insufficient(
                f"Judge unavailable or returned invalid output: {exc}"
            )

    # -------------------------------------------------------------
    # Official Digital Personality Modeling Toolkit evaluation
    # -------------------------------------------------------------

    def evaluate_toolkit_response(
        self,
        question: dict,
        reference_answer: dict,
        candidate_response: str,
    ) -> dict:

        """
        Evaluate an imported candidate response against the participant's
        reference answer for the same question.

        This method does not infer model or source metadata.
        """

        if not question or not reference_answer:
            return self._insufficient(
                "Question definition or participant reference answer is missing."
            )

        question_id = question.get("id")

        if not question_id:
            return self._insufficient(
                "The question definition has no question ID."
            )

        if (
            not isinstance(candidate_response, str)
            or not candidate_response.strip()
        ):
            return self._insufficient(
                "The candidate response is empty or invalid."
            )

        answer_type = reference_answer.get("answer_type")
        answer = reference_answer.get("answer")

        if not isinstance(answer, dict):
            return self._insufficient(
                "The participant reference answer has an invalid format."
            )

        if answer_type not in {"scenario", "writing"}:
            return self._insufficient(
                "The reference answer has an unsupported answer type."
            )

        if answer_type != question.get("type"):
            return self._insufficient(
                "The question type does not match the reference answer type."
            )

        evaluation_input = {
            "question": {
                "id": question_id,
                "type": question.get("type"),
                "wording": question.get("wording"),
                "options": question.get("options"),
                "word_limit": question.get("word_limit"),
            },
            "participant_reference_answer": answer,
            "candidate_response": candidate_response,
        }

        try:
            raw = self.providers.get("JUDGE").complete(
                [
                    {
                        "role": "system",
                        "content": TOOLKIT_JUDGE_SYSTEM,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            evaluation_input,
                            ensure_ascii=False,
                        ),
                    },
                ],
                temperature=0,
                json_mode=True,
            )

            result = json.loads(raw)

            return self._validate(result)

        except (
            ProviderError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            return self._insufficient(
                f"Toolkit judge unavailable or returned invalid output: {exc}"
            )

    # -------------------------------------------------------------
    # Shared validation
    # -------------------------------------------------------------

    @staticmethod
    def _validate(result):

        dimensions = [
            "preference_fidelity",
            "reasoning_fidelity",
            "communication_fidelity",
            "situational_fidelity",
            "overall_fidelity",
        ]

        for key in dimensions:
            value = result.get(key)

            if value is not None:
                result[key] = max(
                    0.0,
                    min(1.0, float(value)),
                )

        result.setdefault("evidence_sufficiency", "uncertain")

        if result["evidence_sufficiency"] not in {
            "sufficient",
            "insufficient",
            "uncertain",
        }:
            result["evidence_sufficiency"] = "uncertain"

        for key in ("matches", "mismatches", "limitations"):
            if not isinstance(result.get(key), list):
                result[key] = []

        result.setdefault("rationale", "")

        result["interpretation_notice"] = (
            "Experimental AI-judge output; not a validated "
            "psychological measurement or ground truth."
        )

        return result

    # -------------------------------------------------------------
    # Insufficient evidence handling
    # -------------------------------------------------------------

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
            "interpretation_notice": (
                "No fidelity score assigned because evidence was insufficient."
            ),
        }
