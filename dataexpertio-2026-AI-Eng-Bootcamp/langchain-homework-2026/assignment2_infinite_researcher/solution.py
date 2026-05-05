"""
Assignment 2: The Infinite Researcher
======================================
This research agent searches the web and compiles reports, but it NEVER STOPS.
It keeps exploring deeper and deeper until it crashes or drains your API budget.

Run this and observe the runaway behavior:
    python starter.py

Your job: Add stopping conditions, cost controls, and fix the prompt.
"""

import json
import os
import time
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Simulated web search & reading (no real API calls needed for testing)
# ---------------------------------------------------------------------------

_SIMULATED_SEARCH_RESULTS = {
    "default": [
        {"title": "Comprehensive Guide to {topic}", "url": "https://example.com/guide", "snippet": "An in-depth look at {topic} covering all major aspects..."},
        {"title": "{topic}: What Experts Say", "url": "https://example.com/experts", "snippet": "Leading researchers weigh in on {topic}..."},
        {"title": "The History and Future of {topic}", "url": "https://example.com/history", "snippet": "From its origins to modern developments, {topic} has evolved..."},
        {"title": "10 Things You Didn't Know About {topic}", "url": "https://example.com/10things", "snippet": "Surprising facts and lesser-known aspects of {topic}..."},
        {"title": "{topic} vs Alternatives: A Deep Dive", "url": "https://example.com/comparison", "snippet": "How does {topic} compare to competing approaches..."},
    ]
}

_SEARCH_CALL_COUNT = 0
_READ_CALL_COUNT = 0


@tool
def web_search(query: str) -> str:
    """Search the web for information on a topic.

    Args:
        query: Search query string.
    """
    global _SEARCH_CALL_COUNT
    _SEARCH_CALL_COUNT += 1

    results = []
    for r in _SIMULATED_SEARCH_RESULTS["default"]:
        results.append(
            f"  - [{r['title'].format(topic=query)}]({r['url']})\n"
            f"    {r['snippet'].format(topic=query)}"
        )

    # Every search returns results that hint at MORE things to explore
    return (
        f"Search results for '{query}' ({len(results)} results):\n\n"
        + "\n".join(results)
        + f"\n\nRelated searches: '{query} advanced techniques', "
        f"'{query} common pitfalls', '{query} case studies', "
        f"'{query} latest research 2026', '{query} expert opinions', "
        f"'{query} implementation details', '{query} theoretical foundations'"
    )


@tool
def read_webpage(url: str) -> str:
    """Read and extract content from a webpage.

    Args:
        url: The URL to read.
    """
    global _READ_CALL_COUNT
    _READ_CALL_COUNT += 1

    # Simulated page content that always suggests more avenues to explore
    return (
        f"Content from {url}:\n\n"
        f"This is a comprehensive article covering the topic in detail. "
        f"Key points include:\n"
        f"1. The fundamental principles are more nuanced than commonly understood\n"
        f"2. Recent studies (see references below) challenge earlier assumptions\n"
        f"3. Practical applications vary significantly across industries\n"
        f"4. Expert consensus is still evolving on several sub-topics\n"
        f"5. There are important connections to adjacent fields worth exploring\n\n"
        f"References cited in this article:\n"
        f"- 'Advanced Analysis of Sub-Topic A' (https://example.com/subtopic-a)\n"
        f"- 'Contrarian View on Sub-Topic B' (https://example.com/subtopic-b)\n"
        f"- 'Meta-Analysis of Related Research' (https://example.com/meta)\n"
        f"- 'Industry Report 2026' (https://example.com/report)\n\n"
        f"The author recommends further reading on at least 3 of these references "
        f"for a complete understanding."
    )


@tool
def save_notes(content: str) -> str:
    """Save research notes for later compilation into the final report.

    Args:
        content: The research notes to save.
    """
    # In the real version this writes to a file; here we just acknowledge
    return f"✅ Notes saved ({len(content)} chars). Continue researching for a comprehensive report."


# ---------------------------------------------------------------------------
# FIXED AGENT — Bounded tools, convergence prompt, explicit finish
# ---------------------------------------------------------------------------

MAX_SEARCHES = 3
MAX_NOTES = 3
REQUIRED_KEYS = {"executive_summary", "key_points", "pros", "cons", "conclusion"}


def _validate_report(report_str: str) -> tuple[bool, str]:
    try:
        d = json.loads(report_str)
    except json.JSONDecodeError:
        return False, "Invalid JSON"
    missing = REQUIRED_KEYS - set(d.keys())
    if missing:
        return False, f"Missing: {sorted(missing)}"
    if not isinstance(d.get("key_points"), list) or len(d["key_points"]) < 2:
        return False, "key_points needs 2+"
    if not isinstance(d.get("pros"), list) or len(d["pros"]) < 1:
        return False, "pros needs 1+"
    if not isinstance(d.get("cons"), list) or len(d["cons"]) < 1:
        return False, "cons needs 1+"
    return True, "OK"


def create_research_agent():
    session_id = str(uuid.uuid4())
    searches = [0]
    notes = [0]
    finished = [False]

    llm = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://www.dataexpert.io/api/v1/openai",
        streaming=True,
        default_headers={"X-Session-ID": session_id},
    )

    @tool
    def bounded_web_search(query: str) -> str:
        """Search the web for information on a topic.

        Args:
            query: Search query string.
        """
        if finished[0] or searches[0] >= MAX_SEARCHES:
            return "LIMIT_REACHED. Call finish_research now."
        web_search.invoke({"query": query})
        searches[0] += 1
        snippets = [r["snippet"].format(topic=query)[:50]
                    for r in _SIMULATED_SEARCH_RESULTS["default"][:3]]
        return "; ".join(snippets)

    @tool
    def bounded_save_notes(content: str) -> str:
        """Save concise research notes.

        Args:
            content: Research notes to save.
        """
        if finished[0] or notes[0] >= MAX_NOTES:
            return "LIMIT_REACHED. Call finish_research now."
        save_notes.invoke({"content": content})
        notes[0] += 1
        return "Saved."

    @tool
    def finish_research(report: str) -> str:
        """Submit final JSON report. Required keys: executive_summary, key_points (list, 2+), pros (list, 1+), cons (list, 1+), conclusion.

        Args:
            report: JSON string with all required keys.
        """
        ok, msg = _validate_report(report)
        if not ok:
            return f"REJECTED: {msg}. Fix and resubmit."
        finished[0] = True
        return "ACCEPTED"

    SYSTEM_PROMPT = (
        "You are a bounded research agent. Follow this sequence exactly:\n"
        "1. Search for a broad overview of the topic.\n"
        "2. Save notes summarizing the key benefits you found.\n"
        "3. Search for risks, drawbacks, or limitations of the topic.\n"
        "4. Save notes summarizing the key drawbacks you found.\n"
        "5. Call finish_research with a complete JSON report.\n\n"
        "Rules:\n"
        "- Budget: 3 searches, 3 notes. Do not exceed.\n"
        "- Do not follow references or related searches.\n"
        "- Do not repeat findings already noted.\n"
        "- Obey all tool limit signals immediately.\n"
        "- Output format for finish_research (valid JSON):\n"
        '  {"executive_summary":"...","key_points":["...","..."],'
        '"pros":["..."],"cons":["..."],"conclusion":"..."}'
    )

    tools = [bounded_web_search, bounded_save_notes, finish_research]

    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
    )

    class ResettingAgent:
        """Resets budget between queries."""
        def __init__(self, agent):
            self._agent = agent

        def invoke(self, payload):
            searches[0] = 0
            notes[0] = 0
            finished[0] = False
            result = self._agent.invoke(
                {"messages": [("user", payload["input"])]},
                config={"recursion_limit": 25},
            )
            last_msg = result["messages"][-1]
            content = getattr(last_msg, "content", str(last_msg))
            return {"output": content}

    return ResettingAgent(agent)


# ---------------------------------------------------------------------------
# Test queries — DO NOT MODIFY
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    "What are the pros and cons of microservices architecture?",
    "Summarize the current state of quantum computing in 2026.",
]

def _check_env():
    """Print env vars and test OpenAI connectivity."""
    openai_key = os.getenv("OPENAI_API_KEY") or ""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or ""
    def mask(val: str) -> str:
        return val[:8] + "..." + val[-4:] if len(val) > 12 else ("(empty)" if not val else val[:4] + "...")
    print("\n=== ENV CHECK ===")
    print(f"  OPENAI_API_KEY:    {mask(openai_key)}")
    print(f"  ANTHROPIC_API_KEY: {mask(anthropic_key)}")
    chat_completions_url = "https://www.dataexpert.io/api/v1/openai/chat/completions"
    print(f"\n=== OPENAI CONNECTIVITY TEST ===\n  POST {chat_completions_url}")
    try:
        import httpx
        resp = httpx.post(
            chat_completions_url,
            headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json",
                     "X-Session-ID": str(uuid.uuid4())},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
            timeout=10,
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Body:   {resp.text[:300]}")
    except Exception as e:
        print(f"  Request failed: {e}")
    print("=================\n")


def main():
    global _SEARCH_CALL_COUNT, _READ_CALL_COUNT

    _check_env()
    agent = create_research_agent()

    for query in TEST_QUERIES:
        _SEARCH_CALL_COUNT = 0
        _READ_CALL_COUNT = 0
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")

        try:
            result = agent.invoke({"input": query})
            print(f"\nRESPONSE: {result['output'][:500]}...")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")

        elapsed = time.time() - start_time
        print(f"\n📊 Stats:")
        print(f"   Search calls: {_SEARCH_CALL_COUNT}")
        print(f"   Page reads:   {_READ_CALL_COUNT}")
        print(f"   Time:         {elapsed:.1f}s")
        print(f"   (Imagine each search = $0.01, each LLM call = $0.05)")
        print(f"   Estimated cost: ${_SEARCH_CALL_COUNT * 0.01 + (_SEARCH_CALL_COUNT + _READ_CALL_COUNT) * 0.05:.2f}")


if __name__ == "__main__":
    main()
