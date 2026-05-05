"""
token_report.py — LangChain LLM token usage and cost report.

Runs each discovered starter.py / solution.py script via ``_run_capture.py``,
captures real LLM token usage, and produces console + file reports.

Use ``--no-run`` to skip execution and only show file-size metrics.

Outputs always include a **starter vs solution by assignment** section first (console,
``token_report.md``, ``token_report.json`` key ``starter_vs_solution_by_assignment``,
and ``token_report_starter_vs_solution.csv``).

Also writes per-assignment reports under ``by_assignment/`` (MD/JSON) with the same
breakdown plus token rows for that ``chain``.

Usage:
    python token_report.py
    python token_report.py --out-dir ./reports
    python token_report.py --aggregate-only
    python token_report.py --no-run          # file metrics only, skip execution
    python token_report.py --scripts solution  # only run solution.py files
    python token_report.py --scripts starter   # only run starter.py files
"""

import argparse
import csv
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Pricing  ($ per 1 000 000 tokens, as of April 2026)
# ---------------------------------------------------------------------------

PRICING: dict[str, dict[str, float]] = {
    # Anthropic
    "claude-opus-4-6":          {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6":        {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5":         {"input":  0.80, "output":  4.00},
    "claude-haiku-4-5-20251001":{"input":  0.80, "output":  4.00},
    # OpenAI
    "gpt-4o":                   {"input":  2.50, "output": 10.00},
    "gpt-4o-mini":              {"input":  0.15, "output":  0.60},
    "gpt-4-turbo":              {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo":            {"input":  0.50, "output":  1.50},
}

UNKNOWN_RATE = {"input": 0.0, "output": 0.0}

# Path to the capture wrapper (lives next to this script)
_CAPTURE_SCRIPT = Path(__file__).resolve().parent / "_run_capture.py"


# ---------------------------------------------------------------------------
# Script runner — execute an assignment script and capture real token usage
# ---------------------------------------------------------------------------

def run_script(script_path: Path, timeout: int = 300) -> dict:
    """Run a script via _run_capture.py and return token usage dict.

    Returns:
        {"model": str|None, "input_tokens": int, "output_tokens": int,
         "calls": int, "elapsed": float, "error": str|None}
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    t0 = time.time()
    error = None
    try:
        result = subprocess.run(
            [sys.executable, str(_CAPTURE_SCRIPT), str(script_path), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=script_path.parent,
        )
        if result.returncode != 0:
            error = (result.stderr or result.stdout or "").strip()[-500:]
    except subprocess.TimeoutExpired:
        error = f"Timed out after {timeout}s"
    elapsed = time.time() - t0

    usage = {"model": None, "input_tokens": 0, "output_tokens": 0, "calls": 0}
    if tmp_path.exists():
        try:
            usage = json.loads(tmp_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
        tmp_path.unlink(missing_ok=True)

    usage["elapsed"] = round(elapsed, 1)
    usage["error"] = error
    return usage


def discover_runnable_scripts(
    root: Path,
    script_filter: str = "all",
    assignment_filter: str | None = None,
) -> list[tuple[str, Path, str]]:
    """Return (chain_name, script_path, script_filename) for each runnable script.

    script_filter:     'all', 'starter', or 'solution'
    assignment_filter: None for all assignments, or a substring/number to match
                       (e.g. '1', 'context', 'assignment2_infinite_researcher')
    """
    results = []
    for chain, adir in discover_assignments(root):
        if assignment_filter and assignment_filter not in chain:
            continue
        scripts: list[Path] = []
        if script_filter in ("all", "starter"):
            s = adir / "starter.py"
            if s.is_file():
                scripts.append(s)
        if script_filter in ("all", "solution"):
            for sp in solution_paths_in_assignment(adir):
                scripts.append(sp)
        for sp in scripts:
            results.append((chain, sp, sp.name))
    return results


def execute_all_scripts(
    root: Path,
    script_filter: str = "all",
    timeout: int = 300,
    assignment_filter: str | None = None,
) -> list[dict]:
    """Run all discovered scripts and return raw run dicts."""
    targets = discover_runnable_scripts(root, script_filter, assignment_filter)
    if not targets:
        print("  No scripts found to run.")
        return []

    runs: list[dict] = []
    for i, (chain, script_path, script_name) in enumerate(targets, 1):
        label = f"[{i}/{len(targets)}] {chain}/{script_name}"
        print(f"  Running {label} ...", flush=True)

        usage = run_script(script_path, timeout=timeout)

        if usage["error"]:
            print(f"    ⚠ Error: {usage['error'][:200]}")
        else:
            est = usage.get("estimated_input_tokens", 0)
            failed = usage.get("failed_calls", 0)
            extra = ""
            if est > usage["input_tokens"] * 2 and est > 1000:
                extra += f", est ~{est:,} input tokens sent"
            if failed:
                extra += f", {failed} failed calls"
            print(
                f"    ✓ {usage['calls']} LLM calls, "
                f"{usage['input_tokens']:,}+{usage['output_tokens']:,} tokens, "
                f"{usage['elapsed']}s{extra}"
            )

        run_id = f"run-{i:03d}"
        est_input = usage.get("estimated_input_tokens", 0)
        # Use the larger of API-reported or estimated tokens for accurate reporting
        effective_input = max(usage["input_tokens"], est_input)
        runs.append({
            "run_id": run_id,
            "chain": chain,
            "script": script_name,
            "model": usage["model"] or "unknown",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input_tokens": effective_input,
            "output_tokens": usage["output_tokens"],
            "api_reported_input": usage["input_tokens"],
            "estimated_input": est_input,
            "failed_calls": usage.get("failed_calls", 0),
            "elapsed": usage["elapsed"],
            "error": usage["error"],
        })

    return runs


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class RunRecord:
    run_id:         str
    chain:          str
    script:         str
    model:          str
    provider:       str
    timestamp:      str
    input_tokens:   int
    output_tokens:  int
    total_tokens:   int
    input_cost:     float   # $
    output_cost:    float   # $
    total_cost:     float   # $


def detect_provider(model: str) -> str:
    m = model.lower()
    if m.startswith("claude"):
        return "Anthropic"
    if m.startswith("gpt") or m.startswith("o1") or m.startswith("o3"):
        return "OpenAI"
    return "Unknown"


def _resolve_pricing(model: str) -> dict[str, float]:
    """Look up pricing, falling back to prefix match for versioned model IDs."""
    if model in PRICING:
        return PRICING[model]
    # Try prefix match: "gpt-4o-mini-2024-07-18" -> "gpt-4o-mini"
    for key in sorted(PRICING, key=len, reverse=True):
        if model.startswith(key):
            return PRICING[key]
    return UNKNOWN_RATE


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float]:
    rate = _resolve_pricing(model)
    input_cost  = input_tokens  / 1_000_000 * rate["input"]
    output_cost = output_tokens / 1_000_000 * rate["output"]
    return round(input_cost, 6), round(output_cost, 6)


def build_records(runs: list[dict]) -> list[RunRecord]:
    records = []
    for r in runs:
        ic, oc = compute_cost(r["model"], r["input_tokens"], r["output_tokens"])
        records.append(RunRecord(
            run_id        = r["run_id"],
            chain         = r["chain"],
            script        = r.get("script", "starter.py"),
            model         = r["model"],
            provider      = detect_provider(r["model"]),
            timestamp     = r["timestamp"],
            input_tokens  = r["input_tokens"],
            output_tokens = r["output_tokens"],
            total_tokens  = r["input_tokens"] + r["output_tokens"],
            input_cost    = ic,
            output_cost   = oc,
            total_cost    = round(ic + oc, 6),
        ))
    return records


# ---------------------------------------------------------------------------
# Console table
# ---------------------------------------------------------------------------

COLS = [
    ("Run ID",      "run_id",        10),
    ("Chain",       "chain",         32),
    ("Script",      "script",        14),
    ("Model",       "model",         24),
    ("Provider",    "provider",      10),
    ("In tok",      "input_tokens",   8),
    ("Out tok",     "output_tokens",  8),
    ("Total tok",   "total_tokens",   9),
    ("Cost $",      "total_cost",     9),
]


def fmt_val(val, width: int) -> str:
    if isinstance(val, float):
        return f"${val:.5f}".rjust(width)
    if isinstance(val, int):
        return f"{val:,}".rjust(width)
    return str(val).ljust(width)


def print_table(records: list[RunRecord]) -> None:
    header = "  ".join(label.ljust(w) for label, _, w in COLS)
    sep    = "  ".join("-" * w for _, _, w in COLS)
    print("\n" + header)
    print(sep)
    for rec in records:
        row = "  ".join(
            fmt_val(getattr(rec, field), width)
            for _, field, width in COLS
        )
        print(row)
    print(sep)

    # Totals row
    total_in  = sum(r.input_tokens  for r in records)
    total_out = sum(r.output_tokens for r in records)
    total_tok = sum(r.total_tokens  for r in records)
    total_usd = sum(r.total_cost    for r in records)

    totals = {
        "run_id": "TOTAL", "chain": "", "script": "", "model": "", "provider": "",
        "input_tokens": total_in, "output_tokens": total_out,
        "total_tokens": total_tok, "total_cost": total_usd,
    }
    row = "  ".join(
        fmt_val(totals[field], width)
        for _, field, width in COLS
    )
    print(row)
    print()


def print_summary(records: list[RunRecord]) -> None:
    total_cost = sum(r.total_cost for r in records)
    print("=== Summary ===")
    print(f"  Runs:         {len(records)}")
    print(f"  Total tokens: {sum(r.total_tokens for r in records):,}")
    print(f"  Total cost:   ${total_cost:.5f}")
    print()

    # Per-provider breakdown
    providers: dict[str, dict] = {}
    for rec in records:
        p = providers.setdefault(rec.provider, {"runs": 0, "tokens": 0, "cost": 0.0})
        p["runs"]   += 1
        p["tokens"] += rec.total_tokens
        p["cost"]   += rec.total_cost

    print("  By provider:")
    for name, data in sorted(providers.items()):
        print(f"    {name:<12} {data['runs']} runs   "
              f"{data['tokens']:>8,} tokens   ${data['cost']:.5f}")

    # Per-chain breakdown
    chains: dict[str, dict] = {}
    for rec in records:
        c = chains.setdefault(rec.chain, {"runs": 0, "tokens": 0, "cost": 0.0})
        c["runs"]   += 1
        c["tokens"] += rec.total_tokens
        c["cost"]   += rec.total_cost

    print()
    print("  By chain:")
    for name, data in sorted(chains.items()):
        print(f"    {name:<34} {data['runs']} runs   "
              f"{data['tokens']:>8,} tokens   ${data['cost']:.5f}")
    print()


# ---------------------------------------------------------------------------
# JSON / CSV output
# ---------------------------------------------------------------------------

def write_json(
    records: list[RunRecord],
    path: Path,
    starter_vs_solution: list[dict],
) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "starter_vs_solution_by_assignment": starter_vs_solution,
        "total_runs":   len(records),
        "total_tokens": sum(r.total_tokens for r in records),
        "total_cost_usd": round(sum(r.total_cost for r in records), 6),
        "runs": [asdict(r) for r in records],
    }
    path.write_text(json.dumps(payload, indent=2))
    print(f"  JSON -> {path}")


def write_csv(records: list[RunRecord], path: Path) -> None:
    fields = [f for _, f, _ in COLS] + ["input_cost", "output_cost"]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))
    print(f"  CSV  -> {path}")


def write_starter_vs_solution_csv(starter_vs_solution: list[dict], path: Path) -> None:
    fields = [
        "assignment",
        "role",
        "file",
        "lines",
        "bytes",
        "line_delta_vs_starter",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for block in starter_vs_solution:
            assign = block["assignment"]
            for row in block["comparison_rows"]:
                d = row["line_delta_vs_starter"]
                writer.writerow({
                    "assignment": assign,
                    "role": row["role"],
                    "file": row["file"],
                    "lines": row["lines"],
                    "bytes": row["bytes"],
                    "line_delta_vs_starter": "" if d is None else d,
                })
    print(f"  CSV  -> {path}")


# ---------------------------------------------------------------------------
# Per-assignment: starter / solution metrics + runs for that chain
# ---------------------------------------------------------------------------

def homework_root() -> Path:
    return Path(__file__).resolve().parent


def discover_assignments(root: Path) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    for p in sorted(root.glob("assignment*/")):
        if p.is_dir() and (p / "starter.py").is_file():
            pairs.append((p.name, p))
    return pairs


def file_stat(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "file": path.name,
        "path": str(path),
        "lines": len(text.splitlines()),
        "bytes": path.stat().st_size,
    }


def solution_paths_in_assignment(adir: Path) -> list[Path]:
    """solution.py first, then solution-*.py (e.g. solution-g8.py)."""
    out: list[Path] = []
    primary = adir / "solution.py"
    if primary.is_file():
        out.append(primary)
    for p in sorted(adir.glob("solution-*.py")):
        if p.is_file() and p not in out:
            out.append(p)
    return out


def assignment_source_table_rows(adir: Path) -> list[dict]:
    rows: list[dict] = []
    starter = adir / "starter.py"
    if starter.is_file():
        rows.append(file_stat(starter))
    for sp in solution_paths_in_assignment(adir):
        rows.append(file_stat(sp))
    return rows


def collect_starter_vs_solution_breakdown(root: Path, assignment_filter: str | None = None) -> list[dict]:
    """Structured starter vs solution metrics per assignment (for JSON / CSV / MD / console)."""
    blocks: list[dict] = []
    for chain, adir in discover_assignments(root):
        if assignment_filter and assignment_filter not in chain:
            continue
        starter_p = adir / "starter.py"
        starter = file_stat(starter_p) if starter_p.is_file() else None
        starter_lines = starter["lines"] if starter else 0
        sol_paths = solution_paths_in_assignment(adir)
        sols = [file_stat(p) for p in sol_paths]
        comparison_rows: list[dict] = []
        if starter:
            comparison_rows.append({
                "role": "starter",
                "file": starter["file"],
                "lines": starter["lines"],
                "bytes": starter["bytes"],
                "line_delta_vs_starter": None,
            })
        for st in sols:
            delta = (st["lines"] - starter_lines) if starter else None
            comparison_rows.append({
                "role": "solution",
                "file": st["file"],
                "lines": st["lines"],
                "bytes": st["bytes"],
                "line_delta_vs_starter": delta,
            })
        has_solution_py = (adir / "solution.py").is_file()
        solution_py_stat = next((s for s in sols if s["file"] == "solution.py"), None)
        delta_py = (
            (solution_py_stat["lines"] - starter["lines"])
            if (starter and solution_py_stat)
            else None
        )
        other_solution_files = [s["file"] for s in sols if s["file"] != "solution.py"]
        blocks.append({
            "assignment": chain,
            "assignment_dir": str(adir),
            "starter": starter,
            "solutions": sols,
            "has_solution_py": has_solution_py,
            "primary_solution": solution_py_stat,
            "line_delta_primary_vs_starter": delta_py,
            "other_solution_files": other_solution_files,
            "comparison_rows": comparison_rows,
        })
    return blocks


def _fmt_delta(v: int | None, for_starter: bool = False) -> str:
    if for_starter or v is None:
        return "—"
    if v >= 0:
        return f"+{v:,}"
    return f"{v:,}"


def print_starter_vs_solution_console(blocks: list[dict]) -> None:
    print()
    print("=" * 80)
    print("STARTER VS SOLUTION BY ASSIGNMENT  (lines / bytes; files not executed)")
    print("=" * 80)
    for b in blocks:
        print()
        print(f"--- {b['assignment']} ---")
        for row in b["comparison_rows"]:
            if row["role"] != "starter":
                continue
            print(
                f"  [STARTER] {row['file']:<22} {row['lines']:>5} lines  "
                f"{row['bytes']:>7,} bytes"
            )
        if not b["has_solution_py"]:
            print("  [STATUS ] (no solution.py)     No solution yet")
        for row in b["comparison_rows"]:
            if row["role"] != "solution":
                continue
            delta = _fmt_delta(row["line_delta_vs_starter"], False)
            print(
                f"  [SOLUTION] {row['file']:<21} {row['lines']:>5} lines  "
                f"{row['bytes']:>7,} bytes    Δ vs starter: {delta}"
            )
    print()
    print("=" * 80)
    print()


def build_starter_vs_solution_markdown_lines(blocks: list[dict]) -> list[str]:
    lines: list[str] = [
        "## Starter vs solution by assignment",
        "",
        "_**Required breakdown** — static line and byte counts; Python files are not executed. "
        "Token/cost tables below use live execution._",
        "",
        "### Summary (one row per assignment)",
        "",
        "| Assignment | Starter lines | Starter bytes | Primary solution | Sol lines | Δ (sol − starter) | Other solution files |",
        "|------------|--------------:|--------------:|------------------|----------:|------------------:|----------------------|",
    ]
    for b in blocks:
        st = b["starter"]
        prim = b["primary_solution"]
        st_l = f"{st['lines']:,}" if st else "—"
        st_b = f"{st['bytes']:,}" if st else "—"
        if b["has_solution_py"] and prim is not None:
            p_f = "`solution.py`"
            p_l = f"{prim['lines']:,}"
            d = b["line_delta_primary_vs_starter"]
            d_s = _fmt_delta(d) if d is not None else "—"
        else:
            p_f = "_No solution yet_"
            p_l = "—"
            d_s = "—"
        others = ", ".join(f"`{n}`" for n in b["other_solution_files"]) or "—"
        lines.append(
            f"| `{b['assignment']}` | {st_l} | {st_b} | {p_f} | {p_l} | {d_s} | {others} |"
        )
    lines += [
        "",
        "### Detail (every starter + solution file, by assignment)",
        "",
    ]
    for b in blocks:
        lines += [
            f"#### `{b['assignment']}`",
            "",
            "| Role | File | Lines | Bytes | Δ lines vs starter |",
            "|------|------|------:|------:|-------------------:|",
        ]
        for row in b["comparison_rows"]:
            if row["role"] != "starter":
                continue
            lines.append(
                f"| {row['role']} | `{row['file']}` | {row['lines']:,} | "
                f"{row['bytes']:,} | — |"
            )
        if not b["has_solution_py"]:
            lines.append(
                "| — | _No solution yet_ (no `solution.py`) | — | — | — |"
            )
        for row in b["comparison_rows"]:
            if row["role"] != "solution":
                continue
            d = row["line_delta_vs_starter"]
            d_cell = "—" if d is None else _fmt_delta(d)
            lines.append(
                f"| {row['role']} | `{row['file']}` | {row['lines']:,} | "
                f"{row['bytes']:,} | {d_cell} |"
            )
        lines.append("")
    return lines


def write_per_assignment_reports(
    records: list[RunRecord],
    root: Path,
    out_dir: Path,
    starter_blocks: list[dict],
    assignment_filter: str | None = None,
) -> None:
    sub = out_dir / "by_assignment"
    sub.mkdir(parents=True, exist_ok=True)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    block_by_chain = {b["assignment"]: b for b in starter_blocks}

    for chain, adir in discover_assignments(root):
        if assignment_filter and assignment_filter not in chain:
            continue
        chain_recs = [r for r in records if r.chain == chain]
        blk = block_by_chain.get(chain)

        lines: list[str] = [
            f"# Token report: `{chain}`",
            "",
            f"_Generated: {generated}_",
            "",
            "## Starter vs solution (required breakdown)",
            "",
            "_Static line/byte counts — files not executed._",
            "",
            "| Role | File | Lines | Bytes | Δ lines vs starter |",
            "|------|------|------:|------:|-------------------:|",
        ]
        if not blk or not blk["comparison_rows"]:
            lines += ["| — | _(no files)_ | — | — | — |", ""]
        else:
            for row in blk["comparison_rows"]:
                if row["role"] != "starter":
                    continue
                lines.append(
                    f"| {row['role']} | `{row['file']}` | {row['lines']:,} | "
                    f"{row['bytes']:,} | — |"
                )
            if blk and not blk["has_solution_py"]:
                lines.append(
                    "| — | _No solution yet_ (no `solution.py`) | — | — | — |"
                )
            for row in blk["comparison_rows"]:
                if row["role"] != "solution":
                    continue
                d = row["line_delta_vs_starter"]
                d_cell = "—" if d is None else _fmt_delta(d)
                lines.append(
                    f"| {row['role']} | `{row['file']}` | {row['lines']:,} | "
                    f"{row['bytes']:,} | {d_cell} |"
                )
            lines.append("")

        lines += [
            "## Sample token runs (live execution)",
            "",
            f"_Rows where `chain == \"{chain}\"`._",
            "",
        ]
        if not chain_recs:
            lines += ["_No runs for this assignment._", ""]
        else:
            lines += [
                "| Run ID | Script | Model | In tok | Out tok | Total tok | Cost |",
                "|--------|--------|-------|-------:|--------:|----------:|-----:|",
            ]
            for rec in chain_recs:
                lines.append(
                    f"| {rec.run_id} | `{rec.script}` | `{rec.model}` | {rec.input_tokens:,} | "
                    f"{rec.output_tokens:,} | {rec.total_tokens:,} | ${rec.total_cost:.5f} |"
                )
            sub_in = sum(r.input_tokens for r in chain_recs)
            sub_out = sum(r.output_tokens for r in chain_recs)
            sub_tot = sum(r.total_tokens for r in chain_recs)
            sub_cost = sum(r.total_cost for r in chain_recs)
            lines += [
                f"| **Subtotal** | | | **{sub_in:,}** | **{sub_out:,}** | **{sub_tot:,}** | **${sub_cost:.5f}** |",
                "",
            ]

        out_md = sub / f"token_report__{chain}.md"
        out_md.write_text("\n".join(lines))
        print(f"  MD   -> {out_md}")

        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "assignment": chain,
            "assignment_dir": str(adir),
            "starter_vs_solution": blk,
            "runs": [asdict(r) for r in chain_recs],
        }
        out_json = sub / f"token_report__{chain}.json"
        out_json.write_text(json.dumps(payload, indent=2))
        print(f"  JSON -> {out_json}")


def _tool_desc_tokens(tools) -> int:
    """Estimate token cost of tool descriptions (~4 chars per token)."""
    total = 0
    for t in tools:
        total += len(t.name) + len(t.description) + len(str(t.args_schema.model_json_schema()))
    return total // 4


def compute_middleware_metrics(adir: Path) -> list[dict] | None:
    """Compute before/after tool-routing metrics for an MCP middleware assignment.

    Imports route_query, select_tools, ALL_TOOLS, TEST_QUERIES from solution.py
    and computes per-query tool count and token savings without executing the agent.
    Returns None if the assignment doesn't have the expected exports.
    """
    solution_py = adir / "solution.py"
    if not solution_py.is_file():
        return None

    import importlib.util
    spec = importlib.util.spec_from_file_location("_mw_metrics", str(solution_py))
    if spec is None or spec.loader is None:
        return None

    # Suppress print statements during import
    import io
    import contextlib
    try:
        mod = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            spec.loader.exec_module(mod)
    except Exception:
        return None

    # Check for required exports
    route_query = getattr(mod, "route_query", None)
    select_tools = getattr(mod, "select_tools", None)
    all_tools = getattr(mod, "ALL_TOOLS", None)
    test_queries = getattr(mod, "TEST_QUERIES", None)
    if not all([route_query, select_tools, all_tools, test_queries]):
        return None

    baseline_tokens = _tool_desc_tokens(all_tools)
    baseline_count = len(all_tools)

    metrics = []
    for query in test_queries:
        servers = route_query(query)
        tools = select_tools(servers, query)
        routed_tokens = _tool_desc_tokens(tools)
        reduction = round((1 - routed_tokens / baseline_tokens) * 100) if baseline_tokens else 0
        metrics.append({
            "query": query[:80],
            "servers": servers,
            "tools_baseline": baseline_count,
            "tools_routed": len(tools),
            "tokens_baseline": baseline_tokens,
            "tokens_routed": routed_tokens,
            "tokens_saved": baseline_tokens - routed_tokens,
            "reduction_pct": reduction,
        })
    return metrics


def write_assignment_token_usage_txt(
    records: list[RunRecord],
    root: Path,
    starter_blocks: list[dict],
    assignment_filter: str | None = None,
) -> None:
    """Write token-usage.txt into each assignment directory (overwritten each run)."""
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    block_by_chain = {b["assignment"]: b for b in starter_blocks}

    for chain, adir in discover_assignments(root):
        if assignment_filter and assignment_filter not in chain:
            continue
        chain_recs = [r for r in records if r.chain == chain]
        blk = block_by_chain.get(chain)

        lines: list[str] = [
            f"Token Usage Report: {chain}",
            f"Generated: {generated}",
            "=" * 70,
            "",
            "FILE METRICS (lines / bytes)",
            "-" * 40,
        ]

        if blk:
            for row in blk["comparison_rows"]:
                delta = ""
                if row["role"] == "solution" and row["line_delta_vs_starter"] is not None:
                    d = row["line_delta_vs_starter"]
                    delta = f"  (Δ {'+' if d >= 0 else ''}{d:,} vs starter)"
                tag = "STARTER " if row["role"] == "starter" else "SOLUTION"
                lines.append(
                    f"  [{tag}] {row['file']:<22} {row['lines']:>5} lines  "
                    f"{row['bytes']:>7,} bytes{delta}"
                )
            if blk and not blk["has_solution_py"]:
                lines.append("  [STATUS ] No solution.py yet")
        lines += [""]

        if chain_recs:
            lines += [
                "TOKEN USAGE (live execution)",
                "-" * 40,
                f"  {'Script':<22} {'Model':<26} {'In tok':>8}  {'Out tok':>8}  {'Total':>8}  {'Cost':>9}",
                f"  {'-'*22} {'-'*26} {'-'*8}  {'-'*8}  {'-'*8}  {'-'*9}",
            ]
            for rec in chain_recs:
                lines.append(
                    f"  {rec.script:<22} {rec.model:<26} {rec.input_tokens:>8,}  "
                    f"{rec.output_tokens:>8,}  {rec.total_tokens:>8,}  "
                    f"${rec.total_cost:.5f}"
                )
            sub_in = sum(r.input_tokens for r in chain_recs)
            sub_out = sum(r.output_tokens for r in chain_recs)
            sub_tok = sum(r.total_tokens for r in chain_recs)
            sub_cost = sum(r.total_cost for r in chain_recs)
            lines += [
                f"  {'-'*22} {'-'*26} {'-'*8}  {'-'*8}  {'-'*8}  {'-'*9}",
                f"  {'TOTAL':<22} {'':<26} {sub_in:>8,}  {sub_out:>8,}  "
                f"{sub_tok:>8,}  ${sub_cost:.5f}",
            ]
        else:
            lines += ["TOKEN USAGE", "-" * 40, "  (no runs for this assignment)"]

        # Middleware metrics (before/after tool routing) for MCP assignments
        mw = compute_middleware_metrics(adir)
        if mw:
            lines += [
                "MIDDLEWARE METRICS (before/after tool routing)",
                "-" * 70,
                f"  {'#':<3} {'Query':<52} {'Before':>6} {'After':>6} {'Saved':>6} {'Reduction':>9}",
                f"  {'-'*3} {'-'*52} {'-'*6} {'-'*6} {'-'*6} {'-'*9}",
            ]
            for idx, m in enumerate(mw, 1):
                lines.append(
                    f"  {idx:<3} {m['query'][:52]:<52} "
                    f"{m['tokens_baseline']:>6} {m['tokens_routed']:>6} "
                    f"{m['tokens_saved']:>6} {m['reduction_pct']:>8}%"
                )
            total_saved = sum(m["tokens_saved"] for m in mw)
            avg_pct = round(sum(m["reduction_pct"] for m in mw) / len(mw))
            lines += [
                f"  {'-'*3} {'-'*52} {'-'*6} {'-'*6} {'-'*6} {'-'*9}",
                f"  {'':3} {'AVERAGE':52} "
                f"{mw[0]['tokens_baseline']:>6} {'':>6} "
                f"{total_saved:>6} {avg_pct:>8}%",
                "",
                f"  Baseline: {mw[0]['tokens_baseline']:,} tool-description tokens (all {mw[0]['tools_baseline']} tools)",
                f"  Total tokens saved across {len(mw)} queries: {total_saved:,}",
                f"  Average reduction: {avg_pct}%",
            ]
            lines.append("")

        out_path = adir / "token-usage.txt"
        out_path.write_text("\n".join(lines))
        print(f"  TXT  -> {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="LangChain token usage report")
    parser.add_argument(
        "--out-dir", default=".",
        help="Directory to write JSON and CSV output (default: current dir)",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip per-assignment files in by_assignment/",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Skip script execution; only show file-size metrics",
    )
    parser.add_argument(
        "--scripts",
        choices=["all", "starter", "solution"],
        default="all",
        help="Which scripts to run: all (default), starter, or solution",
    )
    parser.add_argument(
        "-a", "--assignment",
        default=None,
        metavar="FILTER",
        help="Run only assignments matching this filter. "
             "Shortcuts: a1, a2, a3. Or any substring (e.g. 'context', 'mcp').",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-script timeout in seconds (default: 300)",
    )
    args = parser.parse_args()

    # Expand shortcuts: a1 -> assignment1, a2 -> assignment2, etc.
    if args.assignment and len(args.assignment) == 2 and args.assignment[0] == "a" and args.assignment[1].isdigit():
        args.assignment = f"assignment{args.assignment[1]}"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    root = homework_root()
    starter_blocks = collect_starter_vs_solution_breakdown(root, args.assignment)

    # Always print file-size breakdown first
    print_starter_vs_solution_console(starter_blocks)

    if args.no_run:
        print("(--no-run: skipping script execution)\n")
        return

    # Execute scripts and capture real token usage
    print("Executing scripts to capture token usage:")
    raw_runs = execute_all_scripts(root, args.scripts, args.timeout, args.assignment)
    print()

    if not raw_runs:
        print("No runs to report.\n")
        return

    records = build_records(raw_runs)

    print_table(records)
    print_summary(records)

    print("Writing report files:")
    write_json(records, out_dir / "token_report.json", starter_blocks)
    write_csv(records,  out_dir / "token_report.csv")
    write_starter_vs_solution_csv(starter_blocks, out_dir / "token_report_starter_vs_solution.csv")

    # Aggregate markdown: starter vs solution first (hard requirement), then token sections
    def write_md_with_sources(path: Path) -> None:
        total_in  = sum(r.input_tokens  for r in records)
        total_out = sum(r.output_tokens for r in records)
        total_tok = sum(r.total_tokens  for r in records)
        total_usd = sum(r.total_cost    for r in records)
        generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines: list[str] = [
            "# LangChain Token Usage Report",
            "",
            f"_Generated: {generated}_",
            "",
        ]
        lines.extend(build_starter_vs_solution_markdown_lines(starter_blocks))
        lines += [
            "## Token / cost summary (live execution)",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Runs | {len(records)} |",
            f"| Total input tokens | {total_in:,} |",
            f"| Total output tokens | {total_out:,} |",
            f"| Total tokens | {total_tok:,} |",
            f"| **Total cost** | **${total_usd:.5f}** |",
            "",
        ]
        providers: dict[str, dict] = {}
        for rec in records:
            p = providers.setdefault(rec.provider, {"runs": 0, "tokens": 0, "cost": 0.0})
            p["runs"]   += 1
            p["tokens"] += rec.total_tokens
            p["cost"]   += rec.total_cost
        lines += [
            "## By Provider",
            "",
            "| Provider | Runs | Tokens | Cost |",
            "|----------|-----:|-------:|-----:|",
        ]
        for name, data in sorted(providers.items()):
            lines.append(f"| {name} | {data['runs']} | {data['tokens']:,} | ${data['cost']:.5f} |")
        chains: dict[str, dict] = {}
        for rec in records:
            c = chains.setdefault(rec.chain, {"runs": 0, "tokens": 0, "cost": 0.0})
            c["runs"]   += 1
            c["tokens"] += rec.total_tokens
            c["cost"]   += rec.total_cost
        lines += [
            "",
            "## By Chain",
            "",
            "| Chain | Runs | Tokens | Cost |",
            "|-------|-----:|-------:|-----:|",
        ]
        for name, data in sorted(chains.items()):
            lines.append(f"| `{name}` | {data['runs']} | {data['tokens']:,} | ${data['cost']:.5f} |")
        lines += [
            "",
            "## Run Detail",
            "",
            "| Run ID | Chain | Script | Model | Provider | In tok | Out tok | Total tok | Cost |",
            "|--------|-------|--------|-------|----------|-------:|--------:|----------:|-----:|",
        ]
        for rec in records:
            lines.append(
                f"| {rec.run_id} | `{rec.chain}` | `{rec.script}` | `{rec.model}` | {rec.provider}"
                f" | {rec.input_tokens:,} | {rec.output_tokens:,}"
                f" | {rec.total_tokens:,} | ${rec.total_cost:.5f} |"
            )
        lines += [
            f"| **TOTAL** | | | | | **{total_in:,}** | **{total_out:,}**"
            f" | **{total_tok:,}** | **${total_usd:.5f}** |",
        ]
        path.write_text("\n".join(lines))

    write_md_with_sources(out_dir / "token_report.md")
    print(f"  MD   -> {out_dir / 'token_report.md'}")

    if not args.aggregate_only:
        print()
        print("Per-assignment reports (starter/solution metrics + chain runs):")
        write_per_assignment_reports(records, root, out_dir, starter_blocks, args.assignment)

    print()
    print("Per-assignment token-usage.txt (in assignment directories):")
    write_assignment_token_usage_txt(records, root, starter_blocks, args.assignment)
    print()


if __name__ == "__main__":
    main()
