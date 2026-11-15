"""Deterministic Common Kit answer-to-me.md converter. No LLM is used here."""
from __future__ import annotations
import datetime as dt
import json
import re
from pathlib import Path
from .kit import BUILD_IDS, DOMAIN_TEXT, DOMAINS, ITEMS, SCENARIOS, TEST_IDS, WRITING

VERSION = "1.0.0"
ID_RE = re.compile(r"\b([BSW]\d{2})\b")

def clean_answers(data: dict) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    items, scenarios, writing = {}, {}, {}
    for rec in data.get("items", []):
        rid, resp = rec.get("id"), rec.get("response")
        if rid in TEST_IDS:
            warnings.append(f"{rid} is a test question and was removed."); continue
        if rid not in ITEMS:
            warnings.append(f"Unknown inventory ID {rid} ignored."); continue
        if type(resp) is not int or not 1 <= resp <= 5:
            warnings.append(f"{rid} has invalid response {resp!r}; treated as skipped."); continue
        items[rid] = resp
    for rec in data.get("scenarios", []):
        rid = rec.get("id")
        if rid in TEST_IDS:
            warnings.append(f"{rid} is a test question and was removed."); continue
        if rid not in SCENARIOS:
            warnings.append(f"Unknown scenario ID {rid} ignored."); continue
        choice = str(rec.get("choice", "")).strip().upper()
        if choice not in SCENARIOS[rid]["options"]:
            warnings.append(f"{rid} has invalid choice {choice!r}; ignored."); continue
        scenarios[rid] = {"choice": choice, "explanation": str(rec.get("explanation", "")).strip()}
    for rec in data.get("writing", []):
        rid = rec.get("id")
        if rid in TEST_IDS:
            warnings.append(f"{rid} is a test question and was removed."); continue
        if rid not in WRITING:
            warnings.append(f"Unknown writing ID {rid} ignored."); continue
        text = str(rec.get("text", "")).strip()
        if text: writing[rid] = text
        else: warnings.append(f"{rid} is empty and was ignored.")
    skipped = set(data.get("skipped", [])) | (set(ITEMS) - set(items))
    return {"person_id": str(data.get("person_id", "UNKNOWN")), "items": items,
            "scenarios": scenarios, "writing": writing, "skipped": sorted(skipped)}, warnings

def load_answers(source):
    data = source if isinstance(source, dict) else json.loads(Path(source).read_text(encoding="utf-8"))
    return clean_answers(data)

def score_domains(items: dict) -> dict:
    out = {}
    for domain, (positive, reverse) in DOMAINS.items():
        keyed, missing = {}, []
        for item_id in positive + reverse:
            if item_id not in items: missing.append(item_id)
            else: keyed[item_id] = items[item_id] if item_id in positive else 6 - items[item_id]
        if len(missing) >= 3 or not keyed:
            mean, band = None, None
        else:
            mean = round(sum(keyed.values()) / len(keyed), 2)
            band = "lower" if mean <= 2.4 else "higher" if mean >= 3.6 else "middle"
        out[domain] = {"keyed": keyed, "missing": missing, "positive": positive,
                       "reverse": reverse, "mean": mean, "band": band, "n": len(keyed)}
    return out

CONTRACTION_RE = re.compile(r"\b(?:\w+n't|\w+'(?:re|ve|ll|m|d)|(?:it|that|let|there|here|what|he|she|who|where|how)'s)\b", re.I)
EMOJI_RE = re.compile("[\\U0001F300-\\U0001FAFF☀-➿]")
GREETINGS = ("hi", "hey", "hello", "hiya", "morning", "good morning", "dear", "team", "all", "folks", "everyone")

def writing_features(text: str) -> dict:
    t = text.strip(); words = re.findall(r"[A-Za-z0-9']+", t)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]
    low = t.lower()
    return {"words": len(words), "sentences": len(sentences),
            "avg_sentence_words": round(len(words) / max(1, len(sentences)), 1),
            "greeting": any(low.startswith(g) for g in GREETINGS),
            "first_words": " ".join(t.split()[:2]), "exclamations": t.count("!"),
            "questions": t.count("?"), "contractions": [m.group(0) for m in CONTRACTION_RE.finditer(t)],
            "emoji": bool(EMOJI_RE.search(t)), "line_breaks": t.count("\n"),
            "we_language": len(re.findall(r"\b(we|let's|us|our)\b", t, re.I)),
            "apology": bool(re.search(r"\b(sorry|apolog)", t, re.I)),
            "thanks": bool(re.search(r"\b(thanks|thank you|appreciate)", t, re.I))}

def style_claims(writing: dict) -> list[str]:
    if not writing: return []
    feats = {wid: writing_features(txt) for wid, txt in sorted(writing.items())}; ids = list(feats)
    cite = lambda xs: "[" + ", ".join(xs) + "]"
    claims = ["Message length: " + ", ".join(f"{feats[w]['words']} words ({w})" for w in ids) + f". Match this approximate length. {cite(ids)}"]
    avg = sum(f["avg_sentence_words"] for f in feats.values()) / len(feats)
    claims.append(f"Sentences average about {avg:.0f} words. {cite(ids)}")
    greetings = [w for w in ids if feats[w]["greeting"]]; no_greeting = [w for w in ids if not feats[w]["greeting"]]
    if greetings:
        claims.append("Opens with a greeting in " + ", ".join(greetings) + ("; starts directly in " + ", ".join(no_greeting) if no_greeting else "") + f". {cite(ids)}")
    else: claims.append(f"Does not open with a greeting in the supplied samples. {cite(ids)}")
    ex = [w for w in ids if feats[w]["exclamations"]]
    claims.append((f"Uses exclamation marks in {', '.join(ex)}. {cite(ex)}") if ex else f"Uses no exclamation marks in the supplied samples. {cite(ids)}")
    con = [w for w in ids if feats[w]["contractions"]]
    if con:
        examples = sorted({c for w in con for c in feats[w]["contractions"]})[:4]
        claims.append(f"Uses contractions ({', '.join(examples)}). {cite(con)}")
    else: claims.append(f"Does not use contractions in the supplied samples. {cite(ids)}")
    for key, phrase in [("questions", "Includes a question or request"), ("we_language", "Uses inclusive we/let's/us language"), ("apology", "Uses an apology or sympathy phrase"), ("emoji", "Uses emoji"), ("line_breaks", "Uses line breaks")]:
        present = [w for w in ids if feats[w][key]]
        if present: claims.append(f"{phrase}. {cite(present)}")
    return claims

def conflict_claims(scores: dict, answers: dict) -> list[str]:
    out = []
    for domain, result in scores.items():
        high = [i for i, v in result["keyed"].items() if v >= 4]
        low = [i for i, v in result["keyed"].items() if v <= 2]
        if len(high) >= 2 and len(low) >= 2:
            out.append(f"{domain}: answers point in different directions. Higher-keyed: {', '.join(high[:3])}; lower-keyed: {', '.join(low[:3])}. The average may hide this split; treat the result cautiously. [{', '.join(high[:3] + low[:3])}]")
    sc = answers["scenarios"]
    if sc.get("S01") and sc.get("S05") and ((sc["S01"]["choice"] == "A") != (sc["S05"]["choice"] == "A")):
        out.append(f"Handles the two disagreement situations differently: chose {sc['S01']['choice']} in S01 and {sc['S05']['choice']} in S05. Do not assume one fixed style. [S01, S05]")
    return out

def build_me_md(answers: dict, review_status="Not yet reviewed by the person.", generated_at=None):
    scores = score_domains(answers["items"]); pid = answers["person_id"]
    generated = generated_at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# me.md: Personality profile for {pid}", "",
      "> **AI-generated representation.** This file describes selected self-reported tendencies, not the whole person. Responses generated from it are simulations, not the person's actual statements, approvals, or commitments.", "",
      f"- Person code: {pid}", f"- Generated: {generated} by converter v{VERSION}", f"- Review status: {review_status}",
      "- Intended use: voluntary coaching, reflection, and communication support. Not for hiring, promotion, discipline, or employee ranking.",
      "- Source IDs in square brackets identify the answers supporting each claim.", "",
      "## Instructions for the AI model reading this file", "",
      "Use only evidence in this file. Prioritize the person's actual scenario choices and writing samples over broad trait scores. Do not invent preferences or infer skills, competence, protected traits, or job suitability.",
      "For a multiple-choice scenario, follow the requested answer format and word limit. For a writing task, match the observed length, greeting habits, punctuation, and tone without exaggerating them. Where evidence is mixed or missing, acknowledge uncertainty rather than inventing an answer. Clearly treat your output as a simulation.", "",
      "## 1. Measured traits (self-report inventory)", "",
      "Source: the 50 IPIP Big Five marker items in the supplied Common Kit, scored using its fixed key. Negatively keyed items are reverse-scored as 6 minus the answer. Ranges: 1.0-2.4 lower, 2.5-3.5 middle, 3.6-5.0 higher. These are self-descriptions, not measures of ability.", ""]
    for domain, r in scores.items():
        ids = sorted(r["keyed"])
        if r["mean"] is None:
            lines.append(f"- **{domain}: not scored.** {len(r['missing'])} items were skipped; no claim is made. [{', '.join(ids) or 'none'}]"); continue
        strongest = sorted(r["keyed"], key=lambda k: abs(r["keyed"][k] - 3), reverse=True)[:2]
        evidence = "; ".join(f'{i} "{ITEMS[i]}" answered {answers["items"][i]}' for i in strongest)
        lines.append(f"- **{domain}: {r['mean']:.2f}/5 ({r['band']} range; {r['n']} of 10 items answered).** This person {DOMAIN_TEXT[domain][r['band']]}. Selected item evidence: {evidence}. [{', '.join(ids)}]")
    lines += ["", "Interpretation limit: B05 and B40 concern vocabulary and difficult words. Responses may reflect language background or schooling as well as the construct, so interpret Intellect/Imagination cautiously. No score indicates intelligence, competence, or job suitability. [B05, B40]", "", "## 2. Reported choices in workplace scenarios", "", "Choices and explanations below are the participant's own submitted responses.", ""]
    for sid, rec in sorted(answers["scenarios"].items()):
        scenario = SCENARIOS[sid]; option = scenario["options"][rec["choice"]]; pattern = scenario["patterns"][rec["choice"]]
        lines.append(f'- **{sid}.** Situation: {scenario["wording"]} Chose **{rec["choice"]}** ("{option}"). Their reason: "{rec["explanation"]}" In this situation, the choice suggests the person {pattern}. [{sid}]')
    if not answers["scenarios"]: lines.append("- No scenario answers were provided. [none]")
    lines += ["", "## 3. Writing style", "", "The following are participant-provided writing samples. Use them as limited examples, not a complete account of communication style.", ""]
    for wid, txt in sorted(answers["writing"].items()):
        lines.append(f'- **{wid}.** Task: {WRITING[wid]} Sample: "{txt.replace(chr(10), " / ")}" [{wid}]')
    lines += ["", "Observed style features (mechanically counted from the samples):", ""]
    lines.extend(f"- {claim}" for claim in style_claims(answers["writing"]))
    lines += ["", "## 4. Conflicting or mixed evidence", ""]
    conflicts = conflict_claims(scores, answers)
    lines.extend(f"- {c}" for c in conflicts) if conflicts else lines.append("- No conflicts were detected by the limited automatic checks. This does not mean none exist. [none]")
    skipped = sorted(set(answers.get("skipped", [])) & BUILD_IDS)
    lines += ["", "## 5. What this profile does not cover", "",
      "- The profile is limited to the supplied inventory items, three scenario prompts, and two short writing tasks.",
      "- It does not establish the person's knowledge, skills, background, beliefs, or likely behavior in unobserved situations.",
      "- Skipping a question is not a personality signal.",
      "- People may behave differently across contexts and over time. Treat every statement as a tentative tendency, not a rule."]
    if skipped: lines.append(f"- Skipped or unavailable build questions: {', '.join(skipped)}. No claim is made from them.")
    lines += ["", "## Appendix: item-level evidence (for human review)", "", "| ID | Statement | Answer | Scored as | Trait |", "|---|---|---:|---:|---|"]
    owners = {i: d for d, (pos, rev) in DOMAINS.items() for i in pos + rev}; reversed_ids = {i for pos, rev in DOMAINS.values() for i in rev}
    for item_id in sorted(ITEMS):
        if item_id in answers["items"]:
            raw = answers["items"][item_id]; scored = 6 - raw if item_id in reversed_ids else raw
            lines.append(f"| {item_id} | {ITEMS[item_id]} | {raw} | {scored}{' (reversed)' if item_id in reversed_ids else ''} | {owners[item_id]} |")
        else: lines.append(f"| {item_id} | {ITEMS[item_id]} | skipped | n/a | {owners[item_id]} |")
    return "\n".join(lines) + "\n", scores

def check_claims(markdown: str, answers: dict) -> list[str]:
    flags = []; answered = set(answers["items"]) | set(answers["scenarios"]) | set(answers["writing"]); section = ""
    for line_no, line in enumerate(markdown.splitlines(), 1):
        if line.startswith("## "): section = line; continue
        if not line.startswith("- ") or not section.startswith(("## 1", "## 2", "## 3", "## 4")): continue
        if "[none]" in line: continue
        cited = ID_RE.findall(line[line.rfind("[") :]) if "[" in line else []
        if not cited: flags.append(f"Line {line_no}: claim has no source ID: {line[:100]}"); continue
        invalid = [x for x in cited if x in TEST_IDS or x not in answered]
        if invalid: flags.append(f"Line {line_no}: invalid or unanswered source IDs: {invalid}")
    return flags

def convert(source, output="me.md", review_status="Not yet reviewed by the person."):
    answers, warnings = load_answers(source); markdown, scores = build_me_md(answers, review_status=review_status)
    flags = check_claims(markdown, answers)
    Path(output).write_text(markdown, encoding="utf-8")
    return {"output": str(output), "person_id": answers["person_id"], "warnings": warnings, "flags": flags,
            "scores": {k: {"mean": v["mean"], "band": v["band"], "answered": v["n"], "missing": v["missing"]} for k, v in scores.items()}}
