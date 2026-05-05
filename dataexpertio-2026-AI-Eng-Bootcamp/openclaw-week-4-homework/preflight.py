"""Diagnose .env + DataExpert proxy + LLM wiring in one shot.

Run from openclaw-week-4-homework/ with venv active:
    python preflight.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

print("--- .env ---")
for k in [
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_BASE_URL",
    "OPENCLAW_SESSION_ID",
    "LANGSMITH_API_KEY",
    "LANGSMITH_PROJECT",
]:
    v = os.environ.get(k, "MISSING")
    if "KEY" in k and v != "MISSING":
        v = v[:8] + "..." + v[-4:]
    print(f"  {k}: {v}")

key = os.environ.get("ANTHROPIC_API_KEY", "")
if not key or "REPLACE_ME" in key:
    print("\nERROR: ANTHROPIC_API_KEY missing or placeholder. Edit .env.")
    sys.exit(1)
if not os.environ.get("ANTHROPIC_BASE_URL"):
    print("\nERROR: ANTHROPIC_BASE_URL missing. Set to https://www.dataexpert.io/api/v1/anthropic in .env.")
    sys.exit(1)

print("\n--- raw HTTP ping to proxy ---")
import httpx

base = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")
url = f"{base}/v1/messages"
headers = {
    "x-api-key": key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
    "x-session-id": os.environ.get("OPENCLAW_SESSION_ID", "preflight"),
}
body = {
    "model": "claude-haiku-4-5",
    "max_tokens": 16,
    "messages": [{"role": "user", "content": "ping"}],
}
try:
    r = httpx.post(url, headers=headers, json=body, timeout=30.0)
    print(f"  HTTP {r.status_code}")
    snippet = r.text[:300]
    print(f"  body: {snippet}")
    if r.status_code != 200:
        print("\nERROR: proxy ping failed. See body above.")
        sys.exit(1)
except Exception as exc:
    print(f"  EXCEPTION: {type(exc).__name__}: {exc}")
    sys.exit(1)

print("\n--- LangChain init_chat_model ping ---")
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    "anthropic:claude-haiku-4-5",
    api_key=key,
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
    default_headers={"x-session-id": headers["x-session-id"]},
    streaming=True,
)
try:
    out = llm.invoke("ping")
    print(f"  OK; response: {str(out.content)[:120]}")
except Exception as exc:
    print(f"  EXCEPTION: {type(exc).__name__}: {exc}")
    sys.exit(1)

print("\nALL GREEN — agent should work now. Run: python fixed_openclaw_agent.py")
