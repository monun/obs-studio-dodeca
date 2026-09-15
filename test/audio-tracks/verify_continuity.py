"""Stream ffprobe packet timestamps to check every audio packet in a long recording."""

import argparse
import json
import subprocess
from pathlib import Path


def inspect(path, count):
    metadata = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a", "-show_streams", "-of", "json", str(path)]))
    streams = {str(stream["index"]): stream for stream in metadata["streams"]}
    command = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_packets", "-show_entries",
               "packet=stream_index,pts_time,duration_time", "-of", "compact=p=0:nk=0", str(path)]
    tracks = {}
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as process:
        for line in process.stdout:
            packet = dict(part.split("=", 1) for part in line.strip().split("|") if "=" in part)
            if "stream_index" not in packet:
                continue
            index, pts = packet["stream_index"], float(packet["pts_time"])
            inferred = packet.get("duration_time", "N/A") == "N/A"
            if inferred:
                # FFmpeg 8 may omit the first AAC-LC priming packet's duration in MKV.
                # Only accept the test encoder's known 1024-sample priming packet.
                stream = streams[index]
                assert (index not in tracks and pts < 0 and stream["codec_name"] == "aac"
                        and stream.get("profile") == "LC" and stream.get("initial_padding") == 1024), (
                            index, "unknown packet duration", packet)
                duration = 1024 / int(stream["sample_rate"])
            else:
                duration = float(packet["duration_time"])
            state = tracks.setdefault(index, {"packets": 0, "first": pts, "last": pts, "duration": duration,
                                              "max_gap_error_ms": 0, "inferred_priming_durations": 0})
            if state["packets"]:
                error = (pts - state["last"] - state["duration"]) * 1000
                assert pts > state["last"], (index, "non-monotonic timestamp", pts)
                state["max_gap_error_ms"] = max(state["max_gap_error_ms"], abs(error))
                assert abs(error) <= 2.1, (index, "missing or overlapping packet", pts, error)
            state["inferred_priming_durations"] += int(inferred)
            state.update(packets=state["packets"] + 1, last=pts, duration=duration)
        assert process.wait() == 0
    assert len(tracks) == count, tracks
    assert len({s["packets"] for s in tracks.values()}) == 1, "Track packet counts differ"
    assert max(s["first"] for s in tracks.values()) - min(s["first"] for s in tracks.values()) <= 0.0011
    assert max(s["last"] for s in tracks.values()) - min(s["last"] for s in tracks.values()) <= 0.0011
    return {"path": str(path), "tracks": tracks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--tracks", type=int, default=12)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.file, args.tracks)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS continuous packets on {args.tracks} tracks")
