# -*- coding: utf-8 -*-
"""
PostgreSQL Migration Test Suite
Tests all DB-touching endpoints to verify the migration is working.
Cleans up all test data at the end via TRUNCATE.
"""
import sys
import os
import asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import httpx

BASE_URL = "http://localhost:8000"

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []

def check(label: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"  {status}  {label}"
    if detail:
        msg += f"  [{detail}]"
    print(msg)
    results.append((label, condition))
    return condition

async def run_tests():
    print("\n" + "="*60)
    print("  PostgreSQL Migration - Integration Test Suite")
    print("="*60)

    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:

        # ── TEST 1: Health endpoint ────────────────────────────────────────────
        print("\n--> [1] Health endpoint")
        try:
            resp = await client.get(f"{BASE_URL}/health")
            data = resp.json()
            check("GET /health - status 200",   resp.status_code == 200)
            check("status == ok",               data.get("status") == "ok")
            check("version field present",      "version" in data)
        except Exception as e:
            check("GET /health reachable",      False, str(e))

        # ── TEST 2: Login ──────────────────────────────────────────────────────
        print("\n--> [2] Authentication")
        try:
            resp = await client.post(
                f"{BASE_URL}/login",
                data={"username": "admin", "password": "hr2026", "role": "hr"},
            )
            check("POST /login - status 200 (after redirect)", resp.status_code == 200)
            check("Session cookie set", "session" in client.cookies)
        except Exception as e:
            check("POST /login reachable", False, str(e))

        # ── TEST 3: /api/history – DB read ─────────────────────────────────────
        print("\n--> [3] History endpoint (DB read)")
        initial_count = 0
        try:
            resp = await client.get(f"{BASE_URL}/api/history")
            data = resp.json()
            check("GET /api/history - status 200",  resp.status_code == 200)
            check("status == success",              data.get("status") == "success")
            check("history key present",            "history" in data)
            check("history is a list",              isinstance(data.get("history"), list))
            initial_count = len(data.get("history", []))
            print(f"         Existing records: {initial_count}")
        except Exception as e:
            check("GET /api/history reachable", False, str(e))

        # ── TEST 4: Write a record via /user/submit ────────────────────────────
        print("\n--> [4] Resume submission - DB write (Pending record)")
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as ac2:
                await ac2.post(
                    f"{BASE_URL}/login",
                    data={"username": "applicant", "password": "apply2026", "role": "user"},
                )
                resp = await ac2.post(
                    f"{BASE_URL}/user/submit",
                    files={"resume": (
                        "test_migration_resume.txt",
                        b"Python developer with 5 years experience in Django FastAPI PostgreSQL",
                        "text/plain"
                    )},
                )
                check("POST /user/submit - status 200", resp.status_code == 200)
                if resp.status_code == 200:
                    body = resp.json()
                    check("status == success", body.get("status") == "success", str(body))
        except Exception as e:
            check("POST /user/submit reachable", False, str(e))

        # ── TEST 5: Verify record was written ─────────────────────────────────
        print("\n--> [5] Verify DB write - record count increased")
        written_id = None
        try:
            resp = await client.get(f"{BASE_URL}/api/history?limit=100")
            data = resp.json()
            new_count = len(data.get("history", []))
            check(
                "Record count increased by 1",
                new_count == initial_count + 1,
                f"{initial_count} -> {new_count}"
            )
            if new_count > 0:
                latest = data["history"][0]
                check(
                    "Filename saved correctly",
                    latest.get("filename") == "test_migration_resume.txt",
                    str(latest.get("filename"))
                )
                check(
                    "Classification is Pending",
                    latest.get("classification") == "Pending",
                    str(latest.get("classification"))
                )
                check("created_at is populated", latest.get("created_at") is not None)
                written_id = latest.get("id")
                print(f"         Written record ID: {written_id}")
        except Exception as e:
            check("DB write verification", False, str(e))

        # ── TEST 6: Export CSV ─────────────────────────────────────────────────
        print("\n--> [6] Export endpoint (DB -> CSV)")
        try:
            resp = await client.get(f"{BASE_URL}/api/export?format=csv")
            check("GET /api/export - status 200",       resp.status_code == 200)
            check("Content-Type is text/csv",           "text/csv" in resp.headers.get("content-type", ""))
            check("CSV has content",                    len(resp.text) > 10)
            check("CSV has filename column",            "filename" in resp.text)
        except Exception as e:
            check("GET /api/export reachable", False, str(e))

        # ── TEST 7: Export JSON ────────────────────────────────────────────────
        print("\n--> [7] Export as JSON")
        try:
            resp = await client.get(f"{BASE_URL}/api/export?format=json")
            check("GET /api/export json - status 200",  resp.status_code == 200)
            body = resp.json()
            check("status == success",  body.get("status") == "success")
            check("data key present",   "data" in body)
            check("data is a list",     isinstance(body.get("data"), list))
        except Exception as e:
            check("GET /api/export json reachable", False, str(e))

    # ── CLEANUP: Truncate all test data ───────────────────────────────────────
    print("\n--> [8] Cleanup - removing all test data from PostgreSQL")
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        DATABASE_URL = (
            "postgresql+asyncpg://"
            f"{os.environ.get('POSTGRES_USER', 'postgres')}:"
            f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}"
            f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:"
            f"{os.environ.get('POSTGRES_PORT', '5432')}/"
            f"{os.environ.get('POSTGRES_DB', 'resume_screener')}"
        )
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE resume_analyses RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE job_descriptions RESTART IDENTITY CASCADE"))
        await engine.dispose()
        check("TRUNCATE resume_analyses",   True, "all rows removed, ID sequence reset to 1")
        check("TRUNCATE job_descriptions",  True, "all rows removed, ID sequence reset to 1")
        print("         PostgreSQL tables are now empty.")
    except Exception as e:
        check("Cleanup TRUNCATE", False, str(e))

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    pct    = int(passed / total * 100) if total else 0
    print(f"  Result: {passed}/{total} tests passed ({pct}%)")
    if passed == total:
        print("  ALL TESTS PASSED - Migration verified successfully.")
    else:
        failed = [label for label, ok in results if not ok]
        print(f"  FAILED: {', '.join(failed)}")
    print("="*60 + "\n")
    return passed == total

if __name__ == "__main__":
    ok = asyncio.run(run_tests())
    sys.exit(0 if ok else 1)
