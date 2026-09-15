"""Check all audio packet payloads, track names and relative timestamps after remux."""

import argparse
import json
from pathlib import Path

from verify_media import run


def probe(path):
    return json.loads(run("ffprobe", "-v", "error", "-select_streams", "a", "-show_streams", "-show_packets",
                          "-show_data_hash", "sha256", "-of", "json", str(path)))


def compare(source, target):
    before, after = probe(source), probe(target)
    assert len(before["streams"]) == len(after["streams"])
    results = []
    offsets = []
    for left, right in zip(before["streams"], after["streams"]):
        lp = [p for p in before["packets"] if p["stream_index"] == left["index"]]
        rp = [p for p in after["packets"] if p["stream_index"] == right["index"]]
        assert [p["data_hash"] for p in lp] == [p["data_hash"] for p in rp], "Audio was dropped, reordered or reencoded"
        name = left.get("tags", {}).get("title", left.get("tags", {}).get("handler_name"))
        renamed = right.get("tags", {}).get("title", right.get("tags", {}).get("handler_name"))
        assert name == renamed, (name, renamed)
        offset = float(rp[0]["pts_time"]) - float(lp[0]["pts_time"])
        errors = [abs(float(b["pts_time"]) - float(a["pts_time"]) - offset) for a, b in zip(lp, rp)]
        assert max(errors) <= 0.0011, (name, "timestamp change", max(errors))
        offsets.append(offset)
        results.append({"name": name, "packets": len(lp), "payloads_identical": True,
                        "offset_seconds": offset, "max_timestamp_error_seconds": max(errors)})
    assert max(offsets) - min(offsets) <= 0.0011, ("inter-track offset changed", offsets)
    return {"source": str(source), "target": str(target), "tracks": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.source, args.target)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS: {len(result['tracks'])} audio tracks retain every encoded packet, name and relative timestamp")
