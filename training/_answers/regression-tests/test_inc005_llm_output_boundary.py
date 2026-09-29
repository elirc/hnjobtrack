"""INC-005 regression: one malformed LLM answer must not stop the rest of the thread from being parsed,
and nothing outside the schema's enums may be written.

Uses recorded (hand-written) gpt-4o-mini-shaped answers from training/lab/fixtures/parse_multirole.json;
2 of 6 carry the comma-joined role_type the new prompt asks for. The fake DB rejects out-of-enum values
the way Postgres does (22P02); the bad answer is the 2nd row, so the write loop dies mid-batch.

This FAILS on training/incidents/005-multi-role-type-prompt AND on main: the prompt change only produced
the input; the parser's missing validation boundary was already there. A correct fix passes.
"""
import asyncio
import json
import pathlib
import types

import pytest

THREAD = "t1"
FIXTURES = json.loads((pathlib.Path(__file__).resolve().parents[2] / "lab" / "fixtures" / "parse_multirole.json").read_text())
ANSWERS = {k: v for k, v in FIXTURES.items() if not k.startswith("_")}


class RecordedOpenAI:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    async def _create(self, **kw):
        comment_id = kw["messages"][1]["content"].split(" ", 1)[0]
        body = json.dumps(ANSWERS[comment_id])
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=body))])


@pytest.fixture
def run_parse(fake_db, monkeypatch):
    import app.services.parser as parser

    fake_db.tables["hn_threads"] = [{"id": THREAD, "status": "parsing"}]
    fake_db.tables["job_listings"] = [
        {"id": cid, "thread_id": THREAD, "hn_comment_id": cid, "parsed_at": None,
         "raw_text": f"{cid} {a['company']} | {a['role']} | hiring now, see the post for details"}
        for cid, a in ANSWERS.items()
    ]
    monkeypatch.setattr(parser, "AsyncOpenAI", lambda **_: RecordedOpenAI())

    def go():
        try:
            asyncio.run(parser.parse_thread_jobs(THREAD))
        except Exception as e:  # APScheduler/BackgroundTasks would log this and move on
            return e
        return None

    return go, fake_db


def test_every_valid_listing_is_parsed_and_the_thread_finishes(run_parse):
    go, db = run_parse
    err = go()
    rows = {r["id"]: r for r in db.tables["job_listings"]}
    valid = [cid for cid, a in ANSWERS.items() if "," not in (a["role_type"] or "")]
    unparsed = [cid for cid in valid if not rows[cid].get("parsed_at")]
    assert err is None, f"parse_thread_jobs crashed: {err!r}"
    assert not unparsed, f"valid listings left unparsed: {unparsed}"
    assert db.tables["hn_threads"][0]["status"] == "done"


def test_out_of_enum_answers_are_normalised_or_flagged_never_dropped_silently(run_parse):
    go, db = run_parse
    go()
    rows = {r["id"]: r for r in db.tables["job_listings"]}
    for cid in ("42000102", "42000104"):
        r = rows[cid]
        ok = r.get("is_flagged") or r.get("role_type") in {"full-time", "part-time", "contract", "internship", None}
        assert ok and (r.get("parsed_at") or r.get("is_flagged")), f"{cid} neither parsed validly nor flagged: {r}"
