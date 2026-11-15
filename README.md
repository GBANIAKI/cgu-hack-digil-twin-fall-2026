# PersonaTwin AI

**An evidence-grounded, portable and explainable digital personality twin for cross-LLM behavioral simulation and evaluation.**

This repository is a Python prototype of the CGU Hackathon Digital Twin Track application. It implements the assessment-to-profile converter, evidence-linked Markdown profile, configurable dual-LLM generation, an uncertainty-aware AI judge, SQLite persistence, consent events, and the required evaluation workflow.

> **Important:** This is a hackathon/research prototype, not a validated psychological instrument or production employee-monitoring system. It must not be used for hiring, promotion, employee ranking, discipline, or judgments about professional suitability. Generated text is an AI simulation, not the person's actual statement, approval, or commitment.

## 1. What is implemented

| Capability | Implementation |
|---|---|
| Common Kit parsing | `personatwin/converter.py` validates and normalizes the fixed inventory, scenario, and writing IDs. |
| Deterministic profile generation | `build_me_md()` creates `me.md` without an LLM. |
| Fixed scoring key | `personatwin/kit.py` contains the supplied 50 items, reverse-key map, domains, scenario prompts, and writing prompts. |
| Evidence traceability | Profile claims cite answer IDs; `check_claims()` checks missing, unknown, and test-question references. |
| Cross-LLM generation | `LLM_A` and `LLM_B` use configurable OpenAI-compatible chat-completions endpoints. |
| Explainable judge | `personatwin/judge.py` requests structured scores, matches, mismatches, limitations, and evidence sufficiency. |
| Baseline comparison | Generation can run with or without a personality profile. |
| Wethos comparison | Four externally supplied Wethos outputs can be imported and evaluated. |
| Persistence | SQLite stores consent events, assessments, profile versions, generations, and evaluations. |
| API and CLI | FastAPI endpoints and a command-line converter are included. |

## 2. Project structure

```text
personatwin_ai_python/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── personatwin/
│   ├── __init__.py
│   ├── api.py
│   ├── cli.py
│   ├── converter.py
│   ├── judge.py
│   ├── kit.py
│   ├── providers.py
│   ├── schemas.py
│   ├── service.py
│   └── storage.py
└── tests/
    └── test_core.py
```

## 3. Requirements and installation

Python 3.11 or newer is recommended.

### Windows CMD

```bat
cd personatwin_ai_python
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and configure both generation models and the judge model. Do not commit `.env` or expose API keys in source code.

### Configure providers

Each provider must expose an OpenAI-compatible `POST /chat/completions` endpoint.

```dotenv
LLM_A_BASE_URL=https://api.openai.com/v1
LLM_A_API_KEY=your-key
LLM_A_MODEL=your-model-name

LLM_B_BASE_URL=https://api.openai.com/v1
LLM_B_API_KEY=your-key
LLM_B_MODEL=your-second-model-name

JUDGE_BASE_URL=https://api.openai.com/v1
JUDGE_API_KEY=your-judge-key
JUDGE_MODEL=your-judge-model-name
```

The two generation providers can be different vendors. A separate judge model is recommended. The judge is not ground truth; its results must be reported as experimental AI-judge assessments. Evaluation endpoints that submit personal reference answers require an active consent record.

## 4. Run the API

```bat
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation. Health check: `GET /health`.

Set a different SQLite database path with `PERSONATWIN_DB`.

## 5. Run the deterministic converter

The converter accepts the Common Kit build-answer JSON format. Example:

```json
{
  "person_id": "VOLUNTEER_001",
  "items": [
    {"id": "B01", "response": 4},
    {"id": "B02", "response": 2}
  ],
  "scenarios": [
    {"id": "S01", "choice": "D", "explanation": "I would raise the risk as a question first."}
  ],
  "writing": [
    {"id": "W01", "text": "Hello team, I know this is disappointing news. The project has been cancelled."}
  ],
  "skipped": []
}
```

Save as `answers.json`, then run:

```bat
python -m personatwin.cli convert answers.json -o me.md
```

The converter is deterministic: it does not call an LLM. Invalid IDs, invalid Likert values, and development-only test IDs are excluded with warnings. Missing answers remain missing; skipping is not interpreted as a personality signal. A domain is not scored if three or more of its ten items are missing, following the supplied converter rule.

## 6. API workflow

### Step 1: Record consent

```http
POST /consent
Content-Type: application/json
```

```json
{
  "person_id": "VOLUNTEER_001",
  "consent": true,
  "purpose": "voluntary coaching, reflection, and communication support",
  "recipient": null,
  "text_version": "1.0"
}
```

The latest consent event controls whether new profile generation and profile-conditioned processing are permitted. A `consent: false` event blocks future processing. This prototype records consent but does not replace a legally reviewed consent process.

### Step 2: Validate assessment answers

```http
POST /assessments/validate
```

Submit the assessment object with `person_id`, `items`, `scenarios`, and `writing`. The response reports accepted records and warnings.

### Step 3: Generate the profile

```http
POST /profiles
```

```json
{
  "review_status": "Not yet reviewed by the person.",
  "assessment": {
    "person_id": "VOLUNTEER_001",
    "consent": true,
    "items": [{"id": "B01", "response": 4}],
    "scenarios": [{"id": "S01", "choice": "D", "explanation": "I would raise the risk as a question first."}],
    "writing": [{"id": "W01", "text": "Hello team, the project has been cancelled."}],
    "skipped": []
  }
}
```

The application requires an active consent event first. It creates a new immutable profile version and returns a `profile_id` and the generated Markdown. In a real user interface, the employee must review and approve the profile before export or sharing. Submit corrected assessment answers to `/profiles` again to create a new version.

### Step 4: Download `me.md`

```http
GET /profiles/{profile_id}/download
```

### Step 5: Generate with one or both LLMs

```http
POST /generate
```

```json
{
  "profile_id": "PROFILE_UUID",
  "use_profile": true,
  "both_models": true,
  "temperature": 0.2,
  "scenarios": [
    {"id": "Q01", "prompt": "Your team has proposed a deadline you believe is unrealistic. What would you do?"}
  ]
}
```

The exact same stored `me.md` is supplied to both configured models. For a no-profile baseline, set `use_profile` to `false`. Baseline outputs are not represented as a person's likely behavior.

### Step 6: Evaluate an output

```http
POST /evaluate
```

```json
{
  "scenario_id": "Q01",
  "scenario_prompt": "Your team has proposed a deadline you believe is unrealistic. What would you do?",
  "response": "I would ask the team to review the assumptions behind the deadline.",
  "model": "LLM_A",
  "profile_id": "PROFILE_UUID",
  "source": "profile",
  "reference_answers": {
    "items": {"B03": 4, "B13": 5},
    "scenarios": {"S01": {"choice": "D", "explanation": "I would raise the risk as a question first."}},
    "writing": {"W01": "Hello team, ..."}
  }
}
```

The judge returns four fidelity dimensions, a composite score where assessable, evidence sufficiency, matches, mismatches, limitations, and rationale. It must abstain when it cannot access adequate reference evidence. Scores are heuristic model outputs, not psychometric scores.

## 7. Required 20-output evaluation

The matrix endpoint generates and evaluates the 16 project outputs: four scenarios for each of (1) LLM A with profile, (2) LLM B with profile, (3) LLM A without profile, and (4) LLM B without profile.

```http
POST /evaluation/matrix
```

```json
{
  "profile_id": "PROFILE_UUID",
  "reference_answers": {
    "items": {"B03": 4, "B13": 5},
    "scenarios": {"S01": {"choice": "D", "explanation": "I would raise the risk as a question first."}},
    "writing": {"W01": "The participant's actual reference writing sample."}
  },
  "scenarios": [
    {"id": "Q01", "prompt": "Scenario one..."},
    {"id": "Q02", "prompt": "Scenario two..."},
    {"id": "Q03", "prompt": "Scenario three..."},
    {"id": "Q04", "prompt": "Scenario four..."}
  ]
}
```

The four organizer-provided Wethos responses must then be imported through `POST /evaluation/wethos`. Include the four outputs and the same reference-answer object. This results in 20 generated outputs evaluated in total. The volunteer's four actual answers are reference evidence and must never be counted among the 20 outputs.

Example Wethos request body:

```json
{
  "person_id": "VOLUNTEER_001",
  "reference_answers": {
    "items": {"B03": 4},
    "scenarios": {"S01": {"choice": "D", "explanation": "I would ask a question first."}},
    "writing": {"W01": "Actual reference sample"}
  },
  "outputs": [
    {"scenario_id": "Q01", "scenario_prompt": "Scenario one...", "response": "Wethos response 1", "model": "Wethos", "source": "wethos"},
    {"scenario_id": "Q02", "scenario_prompt": "Scenario two...", "response": "Wethos response 2", "model": "Wethos", "source": "wethos"},
    {"scenario_id": "Q03", "scenario_prompt": "Scenario three...", "response": "Wethos response 3", "model": "Wethos", "source": "wethos"},
    {"scenario_id": "Q04", "scenario_prompt": "Scenario four...", "response": "Wethos response 4", "model": "Wethos", "source": "wethos"}
  ]
}
```

## 8. Scoring and interpretation

The converter uses the exact supplied scoring key: positively keyed items retain their 1-5 answer; reverse-keyed items are scored as `6 - response`. Domain means are descriptive summaries of self-report answers. The converter's lower/middle/higher bands are inherited from the supplied Common Kit converter rules.

The AI judge reports:

- Preference fidelity.
- Reasoning fidelity.
- Communication fidelity.
- Situational fidelity.
- Overall fidelity.
- Evidence sufficiency.
- Evidence-linked matches and mismatches.
- Limitations and rationale.

Do not assume the composite judge score is a validated psychological construct. Do not compare people or use the score for employment decisions. Compare judge outputs with anonymous human ratings and report the small hackathon sample as preliminary evidence only.

## 9. Tests

```bat
pytest -q
```

## 10. Known limitations and production work still required

This implementation is a complete runnable prototype backend, not a fully deployed enterprise product. Before real-world use, add:

1. Authentication, authorization, and per-person access control. The prototype API does not yet implement user login or enforce ownership on profile IDs.
2. A secure employee review and correction interface, including explicit approval before profile sharing.
3. Encryption at rest, retention/deletion workflows, audit-log hardening, and secrets management appropriate to deployment.
4. A legally reviewed consent notice and a documented data-processing agreement with each model provider.
5. Strict request-size limits, rate limits, provider retries, timeouts, and robust error monitoring.
6. Human evaluation and calibration of the judge, thresholds, and score interpretation. The judge currently relies on a configured LLM and returns an abstention result if the provider fails.
7. Organizer Common Kit validation: confirm the final official Sections 7, 8, 11, 12, and 13 and update interfaces only where those official specifications require it.
8. Review of the supplied inventory's wording and cultural/language fairness. In particular, vocabulary-related items may be confounded by language background or education.

## 11. Ethical operating rules

- Obtain voluntary, informed consent before processing personal assessment data.
- Explain which model providers receive profile and scenario content.
- Do not send real assessment answers or personal data to a provider without appropriate authorization.
- Keep raw answers private; share only the reviewed profile when the participant chooses to do so.
- Do not treat a digital twin as the person or as an authorized agent.
- Do not use this system for hiring, promotion, discipline, ranking, or employment suitability decisions.
- Treat uncertainty and insufficient evidence as valid outcomes.
- Never treat the AI judge or Wethos output as ground truth.
