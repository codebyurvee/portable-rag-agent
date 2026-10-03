import sqlite3

import pytest

from database import db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_agent.db")


def test_init_creates_table(db_path):
    db.init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='query_runs'"
        ).fetchone()
    assert row is not None


def test_insert_and_retrieve(db_path):
    db.init_db(db_path)
    run_id = db.record_run(
        query="When is the deadline?",
        framework="core",
        status="success",
        answer="October 3, 2026.",
        tools_used=["rag_search"],
        path=db_path,
    )
    assert run_id == 1
    runs = db.list_runs(db_path)
    assert len(runs) == 1
    r = runs[0]
    assert r["query"] == "When is the deadline?"
    assert r["framework"] == "core"
    assert r["status"] == "success"
    assert r["tools_used"] == "rag_search"
    assert r["timestamp"]


def test_multiple_runs_coexist(db_path):
    db.init_db(db_path)
    db.record_run("q1", "core", "success", "a1", ["calculator"], path=db_path)
    db.record_run("q2", "langgraph", "no_answer", "", [], path=db_path)
    runs = db.list_runs(db_path)
    assert len(runs) == 2
    assert runs[0]["framework"] == "core"
    assert runs[1]["framework"] == "langgraph"


def test_user_values_are_parameterized_not_executed(db_path):
    db.init_db(db_path)
    # a value that would drop the table if string-concatenated into SQL
    malicious = "'); DROP TABLE query_runs; --"
    db.record_run(malicious, "core", "success", malicious, ["rag_search"], path=db_path)
    runs = db.list_runs(db_path)
    assert len(runs) == 1
    assert runs[0]["query"] == malicious  # stored verbatim as data


def test_database_path_is_configurable(tmp_path, monkeypatch):
    custom = str(tmp_path / "custom" / "agent.db")
    monkeypatch.setenv("DATABASE_PATH", custom)
    db.init_db()  # no explicit path -> uses env
    db.record_run("q", "core", "success", "a", [])
    runs = db.list_runs()
    assert len(runs) == 1
