"""Ingester unit test — mocks the v4 Langfuse client surface.

v4 API: client.start_as_current_observation(...) is a context manager;
child observations are created via client.start_observation(...).end().
"""
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make the repo root importable as `solution.tools.ingest_traces`.
_HW_ROOT = Path(__file__).resolve().parents[3]
if str(_HW_ROOT) not in sys.path:
    sys.path.insert(0, str(_HW_ROOT))

from solution.tools import ingest_traces  # noqa: E402


FIXTURE_REAL = """\
{"type":"session","version":3,"id":"abc","timestamp":"2026-04-22T10:00:00Z","cwd":"/"}
{"type":"message","id":"m1","timestamp":"2026-04-22T10:00:01Z","message":{"role":"assistant","content":[{"type":"tool_use","name":"zapier__gmail_send_email","input":{"to":"pollucts@gmail.com"}}],"usage":{"input":10,"output":20,"cacheRead":0,"cacheWrite":0}}}
{"type":"message","id":"m2","timestamp":"2026-04-22T10:00:02Z","message":{"role":"assistant","content":[{"type":"text","text":"HEARTBEAT_OK"}],"usage":{"input":1,"output":5,"cacheRead":0,"cacheWrite":0}}}
"""


@contextmanager
def _noop_cm(*a, **kw):
    yield None


def test_ingest_emits_root_span_and_children(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text(FIXTURE_REAL)

    client = MagicMock()

    # start_as_current_observation returns a context manager yielding a root span
    root_span = MagicMock()

    @contextmanager
    def _root_cm(*args, **kwargs):
        yield root_span

    client.start_as_current_observation.side_effect = _root_cm
    client.get_current_trace_id.return_value = "trace-abc"
    # each start_observation call returns a mock observation object with .end()
    client.start_observation.return_value = MagicMock()

    with patch.object(ingest_traces, "Langfuse", return_value=client), \
         patch.object(ingest_traces, "propagate_attributes", _noop_cm):
        trace_id = ingest_traces.run(
            jsonl=p,
            track="real",
            variant="V1",
            scenario="meeting",
            host="http://localhost:3333",
            public_key="pk",
            secret_key="sk",
        )

    assert trace_id == "trace-abc"
    # One root span opened via context manager
    client.start_as_current_observation.assert_called_once()
    root_kwargs = client.start_as_current_observation.call_args.kwargs
    assert root_kwargs["name"] == "openclaw.real.V1.meeting"
    assert root_kwargs["as_type"] == "span"

    # Child observations: 1 tool_use span + 1 assistant.text generation = 2 start_observation calls
    assert client.start_observation.call_count == 2
    names = [c.kwargs.get("name") for c in client.start_observation.call_args_list]
    types = [c.kwargs.get("as_type") for c in client.start_observation.call_args_list]
    assert "zapier__gmail_send_email" in names
    assert "assistant.text" in names
    assert "span" in types and "generation" in types

    client.flush.assert_called_once()
