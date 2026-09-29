"""RLS lab for HNJOBTRACK: prove what Postgres itself enforces, independent of the FastAPI code.

Throwaway Postgres (Docker postgres:16-alpine, or a locally installed Postgres 14+) + a Supabase-shaped shim (roles, auth.uid(), default grants) + the repo's
supabase/schema.sql + optional extra migrations + a two-user seed, then a table of probes.

Usage (from the repo root, using the backend venv which has psycopg installed; see training/lab/README.md):
    backend/.venv/Scripts/python training/lab/rls/rls_lab.py up          # start container hnjobtrack-training-pg on :55491
    backend/.venv/Scripts/python training/lab/rls/rls_lab.py run [extra.sql ...]
    backend/.venv/Scripts/python training/lab/rls/rls_lab.py down        # ALWAYS do this when finished
No Docker? Use a local Postgres install instead (PG_BIN defaults to C:/Program Files/PostgreSQL/18/bin):
    backend/.venv/Scripts/python training/lab/rls/rls_lab.py native-up   # initdb + start on :55491 (data in %TEMP%)
    backend/.venv/Scripts/python training/lab/rls/rls_lab.py native-down # stop it (the data dir stays in %TEMP%)
`run` recreates a fresh database (hnjobs_lab) every time, so it is safe to re-run with different migrations.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

import psycopg

NAME, PORT, PASSWORD = "hnjobtrack-training-pg", 55491, "training"
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
ADA = "11111111-1111-1111-1111-111111111111"
BOB = "22222222-2222-2222-2222-222222222222"
BOB_JOB = "bbbbbbbb-0000-0000-0000-000000000002"

# (id, question, actor, sql).  actor: "ada" = authenticated request with Ada's verified JWT,
# "anon" = only the anon key (it is public: NEXT_PUBLIC_SUPABASE_ANON_KEY), "service" = service-role key.
PROBES = [
    ("P1", "ada lists saved_jobs", "ada", "select user_id, notes from saved_jobs"),
    ("P2", "ada changes Bob's saved-job status", "ada", f"update saved_jobs set status='rejected' where job_id='{BOB_JOB}'"),
    ("P3", "ada changes her own saved-job status", "ada", f"update saved_jobs set status='applied' where user_id='{ADA}'"),
    ("P4", "ada deletes her own saved job", "ada", f"delete from saved_jobs where user_id='{ADA}'"),
    ("P5", "ada deletes her own preferences", "ada", f"delete from user_preferences where user_id='{ADA}'"),
    ("P6", "ada reads Bob's preferences", "ada", f"select skills from user_preferences where user_id='{BOB}'"),
    ("P7", "anon rewrites a listing's apply_url", "anon", "update job_listings set apply_url='https://evil.example/x' where company='Acme'"),
    ("P8", "anon inserts a fake HN thread", "anon", "insert into hn_threads (hn_post_id,title,month) values ('1','fake','2026-10-01')"),
    ("P9", "anon reads notifications_log", "anon", "select count(*) from notifications_log"),
    ("P10", "service role lists saved_jobs", "service", "select user_id, notes from saved_jobs"),
    ("P11", "anon reads job listings (must keep working)", "anon", "select count(*) from job_listings"),
]


def docker(*args: str, timeout: int = 90) -> str:
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout).stdout.strip()


def connect(db: str = "postgres") -> psycopg.Connection:
    return psycopg.connect(host="127.0.0.1", port=PORT, user="postgres", password=PASSWORD, dbname=db, autocommit=True)


def up() -> None:
    docker("rm", "-f", NAME)
    docker("run", "-d", "--name", NAME, "-e", f"POSTGRES_PASSWORD={PASSWORD}", "-p", f"{PORT}:5432", "postgres:16-alpine")
    for _ in range(60):
        try:
            connect().close()
            print(f"{NAME} ready on 127.0.0.1:{PORT}")
            return
        except psycopg.OperationalError:
            time.sleep(1)
    sys.exit("postgres did not become ready")


def down() -> None:
    docker("rm", "-f", NAME)
    print(f"removed {NAME}")


PG_BIN = pathlib.Path(os.environ.get("PG_BIN", "C:/Program Files/PostgreSQL/18/bin"))
PG_DATA = pathlib.Path(tempfile.gettempdir()) / "hnjobtrack-training-pgdata"


def native_up() -> None:
    if not (PG_DATA / "PG_VERSION").exists():
        subprocess.run([str(PG_BIN / "initdb"), "-D", str(PG_DATA), "-U", "postgres", "--auth=trust", "-E", "UTF8",
                        "--no-locale"], check=True, capture_output=True, timeout=180)
    subprocess.run([str(PG_BIN / "pg_ctl"), "-D", str(PG_DATA), "-o", f"-p {PORT} -c listen_addresses=127.0.0.1",
                    "-l", str(PG_DATA / "server.log"), "-w", "start"], check=True, timeout=120)
    print(f"local postgres ready on 127.0.0.1:{PORT} (data: {PG_DATA})")


def native_down() -> None:
    subprocess.run([str(PG_BIN / "pg_ctl"), "-D", str(PG_DATA), "-w", "stop"], timeout=120)


def run(extras: list[str]) -> None:
    with connect() as c:
        c.execute("drop database if exists hnjobs_lab with (force)")
        c.execute("create database hnjobs_lab")
    with connect("hnjobs_lab") as c:
        for f in [HERE / "00_supabase_shim.sql", REPO / "supabase" / "schema.sql", *map(pathlib.Path, extras), HERE / "10_seed.sql"]:
            c.execute(f.read_text(encoding="utf-8"))
            print(f"applied {f.name}")
        print()
        print(f"{'id':<4} {'actor':<8} {'result':<22} question")
        for pid, question, actor, sql in PROBES:
            print(f"{pid:<4} {actor:<8} {probe(c, actor, sql):<22} {question}")


def probe(c: psycopg.Connection, actor: str, sql: str) -> str:
    role = {"ada": "authenticated", "anon": "anon", "service": "service_role"}[actor]
    claims = json.dumps({"sub": ADA, "role": "authenticated"}) if actor == "ada" else ""
    try:
        with c.transaction(force_rollback=True):
            c.execute(f"set local role {role}")
            c.execute("select set_config('request.jwt.claims', %s, true)", (claims,))
            cur = c.execute(sql)
            if cur.description:
                rows = cur.fetchall()
                return f"count={rows[0][0]}" if sql.lstrip().startswith("select count") else f"{len(rows)} row(s)"
            return f"{cur.statusmessage}"
    except psycopg.Error as e:
        return f"ERROR {e.sqlstate}"


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["run"]
    {"up": up, "down": down, "native-up": native_up, "native-down": native_down, "run": lambda: run(rest)}[cmd]()
