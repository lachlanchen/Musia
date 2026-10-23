#!/usr/bin/env python3
"""Generate the optional AgInTi wire contract from the canonical Python models."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from musia.creator.agent import SYSTEM
from musia.creator.contracts import AgentReply, ProducerRequest


def schema(model):
    value = model.model_json_schema()
    # Each independently compiled schema owns its definitions; no external refs.
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "deploy/containers/agent/contract.json"
    text = json.dumps({"version": 1, "system": SYSTEM, "request": schema(ProducerRequest),
                       "reply": schema(AgentReply)}, ensure_ascii=True, indent=2) + "\n"
    if args.check:
        if not path.exists() or path.read_text() != text:
            raise SystemExit("Agent contract is stale; regenerate it")
    else:
        path.write_text(text)


if __name__ == "__main__":
    main()
