from __future__ import annotations
import json, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone

class Store:
    def __init__(self, path="personatwin.db"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True) if self.path != ":memory:" else None
        self._init()
    def connect(self):
        db = sqlite3.connect(self.path); db.row_factory = sqlite3.Row; return db
    def _init(self):
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS consent_events(id TEXT PRIMARY KEY, person_id TEXT NOT NULL, consent INTEGER NOT NULL, purpose TEXT NOT NULL, recipient TEXT, text_version TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY, person_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, person_id TEXT NOT NULL, version INTEGER NOT NULL, assessment_id TEXT NOT NULL, markdown TEXT NOT NULL, scores TEXT NOT NULL, review_status TEXT NOT NULL, created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS generations(id TEXT PRIMARY KEY, profile_id TEXT, model TEXT NOT NULL, scenario_id TEXT NOT NULL, prompt TEXT NOT NULL, response TEXT NOT NULL, source TEXT NOT NULL, metadata TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS evaluations(id TEXT PRIMARY KEY, generation_id TEXT, scenario_id TEXT NOT NULL, model TEXT NOT NULL, source TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL);


            CREATE TABLE IF NOT EXISTS toolkit_questions (
                question_id TEXT PRIMARY KEY,
                question_type TEXT NOT NULL,
                definition TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS toolkit_reference_answers (
                person_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                answer_type TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (person_id, question_id)
            );

            CREATE TABLE IF NOT EXISTS toolkit_comparison_responses (
                run_id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                response_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS
                idx_toolkit_comparison_question
            ON toolkit_comparison_responses(question_id);

            CREATE TABLE IF NOT EXISTS toolkit_evaluations (
                run_id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            ''')
    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()
    @staticmethod
    def uid(): return str(uuid.uuid4())
    def add_consent(self, person_id, consent, purpose, recipient, text_version):
        with self.connect() as db:
            db.execute("INSERT INTO consent_events VALUES(?,?,?,?,?,?,?)", (self.uid(), person_id, int(consent), purpose, recipient, text_version, self.now()))
    def has_consent(self, person_id):
        with self.connect() as db:
            row = db.execute("SELECT consent FROM consent_events WHERE person_id=? ORDER BY created_at DESC LIMIT 1", (person_id,)).fetchone()
        return bool(row and row[0])
    def add_assessment(self, person_id, payload):
        aid = self.uid()
        with self.connect() as db: db.execute("INSERT INTO assessments VALUES(?,?,?,?)", (aid, person_id, json.dumps(payload), self.now()))
        return aid
    def add_profile(self, person_id, assessment_id, markdown, scores, review_status):
        with self.connect() as db:
            version = db.execute("SELECT COALESCE(MAX(version),0)+1 FROM profiles WHERE person_id=?", (person_id,)).fetchone()[0]
            db.execute("UPDATE profiles SET active=0 WHERE person_id=?", (person_id,))
            pid = self.uid()
            db.execute("INSERT INTO profiles VALUES(?,?,?,?,?,?,?,?,1)", (pid, person_id, version, assessment_id, markdown, json.dumps(scores), review_status, self.now()))
        return {"profile_id": pid, "version": version}
    def get_profile(self, profile_id):
        with self.connect() as db: row = db.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()
        return dict(row) if row else None
    def add_generation(self, profile_id, model, scenario_id, prompt, response, source, metadata):
        gid = self.uid()
        with self.connect() as db: db.execute("INSERT INTO generations VALUES(?,?,?,?,?,?,?,?,?)", (gid, profile_id, model, scenario_id, prompt, response, source, json.dumps(metadata), self.now()))
        return gid
    def add_evaluation(self, generation_id, scenario_id, model, source, result):
        eid = self.uid()
        with self.connect() as db: db.execute("INSERT INTO evaluations VALUES(?,?,?,?,?,?,?)", (eid, generation_id, scenario_id, model, source, json.dumps(result), self.now()))
        return eid
    def list_generations(self, profile_id=None):
        with self.connect() as db:
            if profile_id: rows = db.execute("SELECT * FROM generations WHERE profile_id=? ORDER BY created_at", (profile_id,)).fetchall()
            else: rows = db.execute("SELECT * FROM generations ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]
    def list_evaluations(self):
        with self.connect() as db: rows = db.execute("SELECT * FROM evaluations ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]


    # -----------------------------------------------------------------
    # Digital Personality Modeling Toolkit storage
    # -----------------------------------------------------------------

    def import_toolkit_questions(self, questions):
        """Save or update dynamically defined toolkit questions."""
        now = self.now()

        with self.connect() as db:
            for question in questions:
                question_id = question["id"]

                db.execute(
                    """
                    INSERT INTO toolkit_questions
                    (question_id, question_type, definition,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(question_id) DO UPDATE SET
                        question_type = excluded.question_type,
                        definition = excluded.definition,
                        updated_at = excluded.updated_at
                    """,
                    (
                        question_id,
                        question["type"],
                        json.dumps(question, ensure_ascii=False),
                        now,
                        now,
                    ),
                )

        return len(questions)

    def get_toolkit_question(self, question_id):
        """Retrieve one question definition."""
        with self.connect() as db:
            row = db.execute(
                "SELECT definition FROM toolkit_questions WHERE question_id=?",
                (question_id,),
            ).fetchone()

        return json.loads(row["definition"]) if row else None

    def list_toolkit_questions(self):
        """Retrieve all question definitions."""
        with self.connect() as db:
            rows = db.execute(
                "SELECT definition FROM toolkit_questions ORDER BY question_id"
            ).fetchall()

        return [json.loads(row["definition"]) for row in rows]

    def import_reference_answers(self, person_id, payload):
        """
        Store participant reference answers independently of the
        Common Kit build assessment.
        """
        now = self.now()
        records = []

        for item in payload.get("items", []):
            records.append((item["id"], "inventory", item))

        for item in payload.get("scenarios", []):
            records.append((item["id"], "scenario", item))

        for item in payload.get("writing", []):
            records.append((item["id"], "writing", item))

        question_ids = [record[0] for record in records]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError(
                "Duplicate question IDs found in reference answers."
            )

        with self.connect() as db:
            for question_id, answer_type, answer in records:
                db.execute(
                    """
                    INSERT INTO toolkit_reference_answers
                    (person_id, question_id, answer_type, answer,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(person_id, question_id) DO UPDATE SET
                        answer_type = excluded.answer_type,
                        answer = excluded.answer,
                        updated_at = excluded.updated_at
                    """,
                    (
                        person_id,
                        question_id,
                        answer_type,
                        json.dumps(answer, ensure_ascii=False),
                        now,
                        now,
                    ),
                )

        return len(records)

    def get_reference_answer(self, person_id, question_id):
        """Retrieve the participant's answer to a specific question."""
        with self.connect() as db:
            row = db.execute(
                """
                SELECT answer_type, answer
                FROM toolkit_reference_answers
                WHERE person_id=? AND question_id=?
                """,
                (person_id, question_id),
            ).fetchone()

        if not row:
            return None

        return {
            "answer_type": row["answer_type"],
            "answer": json.loads(row["answer"]),
        }

    def add_comparison_responses(self, responses):
        """
        Import candidate responses.

        run_id must be unique. Multiple run IDs may share a question ID.
        The operation is atomic: a duplicate prevents partial insertion.
        """
        run_ids = [item["run_id"] for item in responses]

        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Duplicate run_id values in imported responses.")

        now = self.now()

        with self.connect() as db:
            for item in responses:
                existing = db.execute(
                    "SELECT 1 FROM toolkit_comparison_responses WHERE run_id=?",
                    (item["run_id"],),
                ).fetchone()

                if existing:
                    raise ValueError(
                        f"Comparison response {item['run_id']} already exists."
                    )

            db.executemany(
                """
                INSERT INTO toolkit_comparison_responses
                (run_id, question_id, response_text, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        item["run_id"],
                        item["question_id"],
                        item["text"],
                        now,
                    )
                    for item in responses
                ],
            )

        return len(responses)

    def get_comparison_response(self, run_id):
        """Retrieve one imported candidate response."""
        with self.connect() as db:
            row = db.execute(
                """
                SELECT run_id, question_id, response_text, created_at
                FROM toolkit_comparison_responses
                WHERE run_id=?
                """,
                (run_id,),
            ).fetchone()

        return dict(row) if row else None

    def list_comparison_responses(self):
        """List imported candidate responses."""
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT run_id, question_id, response_text, created_at
                FROM toolkit_comparison_responses
                ORDER BY created_at, run_id
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def save_toolkit_evaluation(
        self, run_id, person_id, question_id, result
    ):
        """Save or update an evaluation for an imported run."""
        now = self.now()

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO toolkit_evaluations
                (run_id, person_id, question_id, result,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    person_id = excluded.person_id,
                    question_id = excluded.question_id,
                    result = excluded.result,
                    updated_at = excluded.updated_at
                """,
                (
                    run_id,
                    person_id,
                    question_id,
                    json.dumps(result, ensure_ascii=False),
                    now,
                    now,
                ),
            )

        return run_id

    def list_toolkit_evaluations(self):
        """Retrieve stored toolkit evaluation results."""
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT run_id, person_id, question_id, result,
                       created_at, updated_at
                FROM toolkit_evaluations
                ORDER BY created_at, run_id
                """
            ).fetchall()

        results = []

        for row in rows:
            item = dict(row)
            item["result"] = json.loads(item["result"])
            results.append(item)

        return results
