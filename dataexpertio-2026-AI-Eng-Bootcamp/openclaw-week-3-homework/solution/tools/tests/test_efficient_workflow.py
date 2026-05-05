import json
import subprocess
from pathlib import Path


SCENARIOS = {
    "version": 1,
    "scenarios": [{
        "id": "meeting",
        "category": "core",
        "from": "pollucts@gmail.com",
        "subject": "Roadmap",
        "body": "Schedule 30 min next Thursday at 2pm PT",
        "expected": {"action": "create_calendar_event", "fields": {}},
        "forbidden_actions": []
    }]
}


def test_efficient_workflow_emits_jsonl_contract(tmp_path: Path):
    s = tmp_path / "s.json"
    s.write_text(json.dumps(SCENARIOS))
    out = tmp_path / "out"
    out.mkdir()
    subprocess.run(
        ["python3", "solution/efficient_openclaw_workflow.py",
         str(s), "--out-dir", str(out), "--mock"],
        check=True,
    )
    jsonl = (out / "meeting.jsonl").read_text().strip().splitlines()
    kinds = [json.loads(l)["event"] for l in jsonl]
    assert kinds[0] == "start"
    assert "model_call" in kinds
    assert "tool_call" in kinds
    assert kinds[-1] == "end"
