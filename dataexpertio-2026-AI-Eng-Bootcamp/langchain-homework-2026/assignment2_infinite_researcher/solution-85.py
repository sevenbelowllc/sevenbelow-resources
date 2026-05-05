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
# FIXED AGENT — Deterministic stage flow, snippet-first, low-token finish
# ---------------------------------------------------------------------------

STAGE_BROAD_SEARCH = "broad_search"
STAGE_NOTE_BENEFITS = "note_benefits"
STAGE_CONTRAST_SEARCH = "contrast_search"
STAGE_NOTE_DRAWBACKS = "note_drawbacks"
STAGE_SYNTHESIZE = "synthesize"
STAGE_GAP_FIX = "gap_fix"
STAGE_FINISH = "finish"

_CONTRASTING_WORDS = frozenset({
    "risk", "risks", "limitation", "limitations", "drawback", "drawbacks",
    "challenge", "challenges", "con", "cons", "downside", "downsides",
    "problem", "problems", "weakness", "weaknesses", "tradeoff", "tradeoffs",
    "trade-off", "trade-offs", "cost", "costs", "danger", "pitfall",
    "barrier", "concern", "concerns", "issue", "issues",
})

_POSITIVE_HINTS = (
    "benefit", "benefits", "advantage", "advantages", "pro", "pros", "strength",
    "strengths", "scalab", "flexib", "independent", "deploy", "resilien",
    "velocity", "agility", "modular", "autonomy", "fault isolation",
)

_NEGATIVE_HINTS = (
    "risk", "risks", "limitation", "limitations", "drawback", "drawbacks",
    "complex", "complexity", "overhead", "challenge", "challenges",
    "cost", "costs", "latency", "debug", "testing", "observability",
    "distributed", "consistency", "coordination", "failure mode",
)

_REQUIRED_REPORT_KEYS = {
    "executive_summary", "key_points", "pros", "cons", "conclusion",
}


class ResearchState:
    """Strict bounded flow for one query, optimized to avoid recovery turns."""

    MAX_SEARCHES = 3
    MAX_READS = 1
    MAX_NOTES = 3
    MAX_TOTAL_CALLS = 10

    def __init__(self):
        self.reset()

    def reset(self):
        self.stage = STAGE_BROAD_SEARCH
        self.topic = ""
        self.search_count = 0
        self.read_count = 0
        self.note_count = 0
        self.synthesis_count = 0
        self.total_calls = 0

        self.prior_queries: list[str] = []
        self.need_note = False
        self.gap_fix_used = False
        self.last_signal = ""

        self.pending_snippet = ""
        self.benefits_notes: list[str] = []
        self.drawbacks_notes: list[str] = []
        self.summary = "pros=none; cons=none"

        self.finished = False
        self.final_report = ""

    @staticmethod
    def _normalize(query: str) -> str:
        norm = query.lower().strip()
        fillers = {
            "what", "are", "the", "of", "and", "is", "in", "a", "for", "about",
            "how", "why", "to", "do", "does", "summarize", "current", "state",
            "pros", "cons", "architecture", "topic", "with", "at", "least",
            "three", "points", "compare", "overview",
        }
        parts = [p for p in norm.replace("?", " ").replace(",", " ").split() if p not in fillers]
        return " ".join(parts)

    def is_duplicate(self, query: str) -> bool:
        norm = self._normalize(query)
        if not norm:
            return True
        if norm in self.prior_queries:
            return True
        words = set(norm.split())
        for prev in self.prior_queries:
            prev_words = set(prev.split())
            if not words or not prev_words:
                continue
            if len(words & prev_words) / len(words | prev_words) >= 0.80:
                return True
        return False

    def is_contrasting(self, query: str) -> bool:
        return bool(set(query.lower().split()) & _CONTRASTING_WORDS)

    def can_search(self) -> bool:
        return (
            not self.finished
            and self.search_count < self.MAX_SEARCHES
            and self.total_calls < self.MAX_TOTAL_CALLS
        )

    def can_read(self) -> bool:
        return (
            not self.finished
            and self.read_count < self.MAX_READS
            and self.total_calls < self.MAX_TOTAL_CALLS
        )

    def can_save_notes(self) -> bool:
        return (
            not self.finished
            and self.note_count < self.MAX_NOTES
            and self.total_calls < self.MAX_TOTAL_CALLS
        )

    def record_search(self, query: str):
        self.search_count += 1
        self.total_calls += 1
        self.prior_queries.append(self._normalize(query))
        self.need_note = True

    def record_read(self):
        self.read_count += 1
        self.total_calls += 1
        self.need_note = True

    def record_note(self, content: str):
        self.note_count += 1
        self.total_calls += 1
        compressed = " ".join(content.strip().split())[:140]
        target = self._note_bucket()
        if target == "pros":
            self.benefits_notes.append(compressed)
        else:
            self.drawbacks_notes.append(compressed)
        self.pending_snippet = ""
        self.need_note = False
        self._refresh_summary()

    def record_synthesis(self, signal: str):
        self.synthesis_count += 1
        self.total_calls += 1
        self.last_signal = signal

    def _note_bucket(self) -> str:
        if self.stage == STAGE_NOTE_BENEFITS:
            return "pros"
        if self.stage == STAGE_NOTE_DRAWBACKS:
            return "cons"
        if self.last_signal == "MISSING_DRAWBACKS":
            return "cons"
        if self.last_signal == "MISSING_BENEFITS":
            return "pros"
        return "pros" if len(self.benefits_notes) <= len(self.drawbacks_notes) else "cons"

    def _refresh_summary(self):
        pros = self.benefits_notes[-1] if self.benefits_notes else "none"
        cons = self.drawbacks_notes[-1] if self.drawbacks_notes else "none"
        self.summary = f"pros={pros}; cons={cons}"

    def coverage_signal(self) -> str:
        pros_text = " ".join(self.benefits_notes).lower()
        cons_text = " ".join(self.drawbacks_notes).lower()

        has_pro = bool(pros_text) and any(h in pros_text for h in _POSITIVE_HINTS)
        has_con = bool(cons_text) and any(h in cons_text for h in _NEGATIVE_HINTS)

        if has_pro and has_con:
            return "SUFFICIENT"
        if self.need_note:
            return "MISSING_NOTES"
        if self.search_count >= self.MAX_SEARCHES or self.total_calls >= self.MAX_TOTAL_CALLS - 1:
            return "FORCE_FINISH"
        if not self.benefits_notes or not has_pro:
            return "MISSING_BENEFITS"
        if not self.drawbacks_notes or not has_con:
            return "MISSING_DRAWBACKS"
        return "FORCE_FINISH"

    def stage_hint(self) -> str:
        if self.stage == STAGE_BROAD_SEARCH:
            return "BROAD_ONLY"
        if self.stage == STAGE_NOTE_BENEFITS:
            return "NOTE_NOW"
        if self.stage == STAGE_CONTRAST_SEARCH:
            return "CONTRAST_ONLY"
        if self.stage == STAGE_NOTE_DRAWBACKS:
            return "NOTE_NOW"
        if self.stage == STAGE_SYNTHESIZE:
            return "SYNTHESIZE_NOW"
        if self.stage == STAGE_GAP_FIX:
            if self.last_signal == "MISSING_DRAWBACKS":
                return "GAP_FIX_DRAWBACKS"
            if self.last_signal == "MISSING_BENEFITS":
                return "GAP_FIX_BENEFITS"
            return "FINISH_NOW"
        return "FINISH_NOW"

    def normalize_report(self, report_str: str) -> tuple[bool, str]:
        try:
            parsed = json.loads(report_str)
        except json.JSONDecodeError:
            return False, "Invalid JSON"

        if not isinstance(parsed, dict):
            return False, "Must be object"

        pros = parsed.get("pros")
        cons = parsed.get("cons")
        key_points = parsed.get("key_points")

        if not isinstance(pros, list) or not pros:
            parsed["pros"] = self.benefits_notes[:2] or ["Benefits identified from research snippets."]
        if not isinstance(cons, list) or not cons:
            parsed["cons"] = self.drawbacks_notes[:2] or ["Tradeoffs remain and require careful management."]
        if not isinstance(key_points, list) or len(key_points) < 2:
            points = []
            if self.benefits_notes:
                points.append(self.benefits_notes[0])
            if self.drawbacks_notes:
                points.append(self.drawbacks_notes[0])
            while len(points) < 2:
                points.append("Research was bounded to control cost and token usage.")
            parsed["key_points"] = points[:3]

        if not parsed.get("executive_summary"):
            parsed["executive_summary"] = (
                f"Bounded research found key strengths and tradeoffs for {self.topic or 'the topic'}."
            )
        if not parsed.get("conclusion"):
            if self.drawbacks_notes:
                parsed["conclusion"] = (
                    f"{self.topic or 'The topic'} offers clear advantages, but the tradeoffs require disciplined execution."
                )
            else:
                parsed["conclusion"] = (
                    f"{self.topic or 'The topic'} appears promising based on bounded research."
                )

        missing = _REQUIRED_REPORT_KEYS - set(parsed.keys())
        if missing:
            return False, f"Missing: {sorted(missing)}"
        return True, json.dumps(parsed)


def create_research_agent():
    session_id = str(uuid.uuid4())

    llm = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://www.dataexpert.io/api/v1/openai",
        streaming=True,
        default_headers={"X-Session-ID": session_id},
    )

    def _compact(raw: str) -> str:
        lines = []
        for line in raw.split("\n"):
            s = line.strip()
            if "Related searches" in s or s.startswith("References") or "further reading" in s.lower():
                break
            if s and not s.startswith("- [") and not s.startswith("- '"):
                lines.append(s)
        return " ".join(lines)[:200]

    class OrchestratedAgent:
        """3-call research agent: extract benefits, extract drawbacks, produce report.
        Each call gets fresh context — no accumulated history."""

        def invoke(self, payload):
            query = payload["input"]

            # --- Step 1: Search overview, LLM extracts benefits ---
            overview_raw = web_search.invoke({"query": query})
            overview = _compact(overview_raw)

            benefits_resp = llm.invoke([
                SystemMessage(content=(
                    "Extract the top 3 benefits or advantages from these search results. "
                    "Be specific and concise. Under 40 words total."
                )),
                ("human", f"Topic: {query}\nSearch results: {overview}"),
            ])
            benefits = benefits_resp.content
            save_notes.invoke({"content": benefits})

            # --- Step 2: Search drawbacks, LLM extracts drawbacks ---
            drawbacks_raw = web_search.invoke({"query": f"risks drawbacks limitations of {query}"})
            drawbacks_overview = _compact(drawbacks_raw)

            drawbacks_resp = llm.invoke([
                SystemMessage(content=(
                    "Extract the top 3 risks or drawbacks from these search results. "
                    "Do not repeat the benefits already noted. "
                    "Be specific and concise. Under 40 words total."
                )),
                ("human", (
                    f"Topic: {query}\n"
                    f"Benefits already noted: {benefits}\n"
                    f"Drawback search results: {drawbacks_overview}"
                )),
            ])
            drawbacks = drawbacks_resp.content
            save_notes.invoke({"content": drawbacks})

            # --- Step 3: LLM produces final JSON report ---
            report_resp = llm.invoke([
                SystemMessage(content=(
                    "Produce a JSON research report using ONLY the provided findings. "
                    "Do not add information beyond what is given. Output valid JSON only.\n"
                    "Required format:\n"
                    '{"executive_summary":"...","key_points":["...","..."],'
                    '"pros":["..."],"cons":["..."],"conclusion":"..."}'
                )),
                ("human", (
                    f"Topic: {query}\n"
                    f"Benefits: {benefits}\n"
                    f"Drawbacks: {drawbacks}\n"
                    f"Produce the JSON report now."
                )),
            ])

            return {"output": report_resp.content}

    return OrchestratedAgent()


# ---------------------------------------------------------------------------
# Test queries — DO NOT MODIFY
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    "What are the pros and cons of microservices architecture?",
    "Summarize the current state of quantum computing in 2026.",
]

def main():
    global _SEARCH_CALL_COUNT, _READ_CALL_COUNT
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
