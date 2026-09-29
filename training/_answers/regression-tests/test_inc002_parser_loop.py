"""INC-002 regression: the parse pipeline must never stall the event loop that serves HTTP traffic.

The API process runs the parser (APScheduler / BackgroundTasks) on the SAME asyncio loop as the request
handlers. A heartbeat task measures the longest gap between ticks while parse_thread_jobs runs against a
fake OpenAI client that returns 429 twice per job, then succeeds.

On training/incidents/002-parser-retry-backoff this FAILS (the loop freezes for seconds at a time).
On main it passes (no retries at all, so nothing blocks, but every 429 flags the listing: see the
second test, which fails on main and passes on both the incident branch and a correct fix).
"""
import asyncio
import json
import time
import types

import httpx
import openai
import pytest

THREAD = "t1"


def _rate_limit_error() -> openai.RateLimitError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return openai.RateLimitError("Rate limit reached for gpt-4o-mini", response=httpx.Response(429, request=req), body=None)


class FlakyOpenAI:
    """Each job's first `fail_times` calls raise a 429; then a canned parse comes back."""

    def __init__(self, fail_times: int = 2):
        self.fail_times, self.calls = fail_times, {}
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    async def _create(self, **kw):
        text = kw["messages"][1]["content"]
        n = self.calls[text] = self.calls.get(text, 0) + 1
        await asyncio.sleep(0.01)  # a real network call yields to the loop
        if n <= self.fail_times:
            raise _rate_limit_error()
        body = {"company": text.split(" | ")[0], "role": "Engineer", "role_type": "full-time", "parse_confidence": 0.9}
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=json.dumps(body)))])


@pytest.fixture
def pipeline(fake_db, monkeypatch):
    import app.services.parser as parser

    fake_db.tables["hn_threads"] = [{"id": THREAD, "status": "parsing"}]
    fake_db.tables["job_listings"] = [
        {"id": f"j{i}", "thread_id": THREAD, "raw_text": f"Company{i} | Engineer | Remote | Python, Postgres, AWS", "parsed_at": None}
        for i in range(3)
    ]
    client = FlakyOpenAI()
    monkeypatch.setattr(parser, "AsyncOpenAI", lambda **_: client)
    # Keep a correct fix's asyncio.sleep backoff short so the test is fast; time.sleep is deliberately NOT patched.
    real_sleep = asyncio.sleep
    monkeypatch.setattr(parser.asyncio, "sleep", lambda d, *a, **k: real_sleep(min(d, 0.05)), raising=False)
    return parser, fake_db


async def _run_with_heartbeat(coro) -> float:
    worst, stop = 0.0, False

    async def heartbeat():
        nonlocal worst
        last = time.perf_counter()
        while not stop:
            await asyncio.sleep(0.02)
            now = time.perf_counter()
            worst, last = max(worst, now - last), now

    hb = asyncio.create_task(heartbeat())
    try:
        await coro
    finally:
        stop = True
        await hb
    return worst


def test_parse_pipeline_does_not_block_the_event_loop(pipeline):
    parser, _ = pipeline
    worst_gap = asyncio.run(_run_with_heartbeat(parser.parse_thread_jobs(THREAD)))
    assert worst_gap < 0.5, f"event loop was blocked for {worst_gap:.2f}s during parsing (every request would stall that long)"


def test_transient_429s_are_retried_not_flagged(pipeline):
    parser, db = pipeline
    asyncio.run(parser.parse_thread_jobs(THREAD))
    flagged = [j["id"] for j in db.tables["job_listings"] if j.get("is_flagged")]
    assert not flagged, f"transient 429s flagged listings instead of retrying: {flagged}"
