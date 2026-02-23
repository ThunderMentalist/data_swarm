import json
from pathlib import Path

from data_swarm.stores.log_store import LogStore


def test_log_store_writes_jsonl(tmp_path: Path) -> None:
    logs = LogStore(tmp_path)
    logs.event("t1", "stage", "event", "msg", {"api_key": "secret"})
    line = (tmp_path / "08_logs" / "events.jsonl").read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["data"]["api_key"] == "***"
