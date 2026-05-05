"""
_run_capture.py — Run an assignment script and capture LLM token usage.

Usage:
    python _run_capture.py <script_path> <output_json_path>

Monkeypatches ChatOpenAI to inject a token-tracking callback, runs the
target script's main(), and writes usage data to the output JSON file.
"""

import importlib.util
import json
import sys
from pathlib import Path

# ---- token tracker (langchain_core callback) --------------------------------

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

_usage = {
    "model": None,
    "input_tokens": 0,
    "output_tokens": 0,
    "calls": 0,
    "estimated_input_tokens": 0,  # from on_llm_start (char-based estimate)
    "failed_calls": 0,
}


def _estimate_tokens_from_messages(messages) -> int:
    """Rough estimate: 1 token ≈ 4 chars for English text."""
    total_chars = 0
    if isinstance(messages, list):
        for msg_list in messages:
            if isinstance(msg_list, list):
                for msg in msg_list:
                    total_chars += len(str(msg))
            else:
                total_chars += len(str(msg_list))
    return total_chars // 4


class _TokenTracker(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts=None, **kwargs):
        """Capture estimated input tokens BEFORE the API call."""
        messages = kwargs.get("messages") or prompts or []
        _usage["estimated_input_tokens"] += _estimate_tokens_from_messages(messages)

    def on_llm_end(self, response: LLMResult, **kwargs):
        _usage["calls"] += 1
        for gen_list in response.generations:
            for gen in gen_list:
                msg = getattr(gen, "message", None)
                if msg and hasattr(msg, "usage_metadata") and msg.usage_metadata:
                    _usage["input_tokens"] += msg.usage_metadata.get(
                        "input_tokens", 0
                    )
                    _usage["output_tokens"] += msg.usage_metadata.get(
                        "output_tokens", 0
                    )
                # Try to get model from response_metadata
                if msg and hasattr(msg, "response_metadata"):
                    rm = msg.response_metadata or {}
                    if "model_name" in rm:
                        _usage["model"] = rm["model_name"]
                    elif "model" in rm:
                        _usage["model"] = rm["model"]
        if response.llm_output:
            _usage["model"] = response.llm_output.get(
                "model_name", response.llm_output.get("model", _usage["model"])
            )

    def on_llm_error(self, error, **kwargs):
        """Track calls that failed (e.g. context overflow)."""
        _usage["failed_calls"] += 1


_tracker = _TokenTracker()

# ---- monkeypatch ChatOpenAI to always include our tracker --------------------

import langchain_openai  # noqa: E402

_orig_init = langchain_openai.ChatOpenAI.__init__


def _patched_init(self, *args, **kwargs):
    cbs = list(kwargs.get("callbacks") or [])
    cbs.append(_tracker)
    kwargs["callbacks"] = cbs
    # Note: streaming left as-is; some proxies require it.
    # Token usage captured via on_llm_end or estimated via on_llm_start.
    # Capture model name from constructor as fallback
    if "model" in kwargs and _usage["model"] is None:
        _usage["model"] = kwargs["model"]
    _orig_init(self, *args, **kwargs)


langchain_openai.ChatOpenAI.__init__ = _patched_init

# ---- run the target script ---------------------------------------------------


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <script_path> <output_json>", file=sys.stderr)
        sys.exit(2)

    script_path = sys.argv[1]
    output_path = sys.argv[2]

    spec = importlib.util.spec_from_file_location("_target", script_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_target"] = mod

    # Many scripts do os.chdir / load_dotenv relative to their own dir
    import os

    os.chdir(Path(script_path).parent)

    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"⚠ Import error: {e}", file=sys.stderr)
        Path(output_path).write_text(json.dumps(_usage))
        return

    try:
        mod.main()
    except SystemExit:
        pass  # some scripts call sys.exit on env check failures
    except Exception as e:
        print(f"⚠ Runtime error: {e}", file=sys.stderr)

    Path(output_path).write_text(json.dumps(_usage))


if __name__ == "__main__":
    main()
