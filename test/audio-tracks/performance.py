"""Measure 1/6/12 selected recording tracks using the same twelve-source scene."""

import argparse
import json
import statistics
import time
from pathlib import Path

from integration import OBS, record
from matrix import configure
from scenarios import parameter
from ui_client import UI
from verify_media import inspect


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--ui", default="/work/ui")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    obs = OBS()
    configure(UI(args.ui), {"outputMode": "Advanced", "advOutRecType": "Standard", "advOutRecFormat": "mkv",
                            "advOutRecAEncoder": "ffmpeg_aac", "advOutRecPath": str(args.directory),
                            "advOutSplitFile": False, "autoRemux": False})
    for i in range(1, 13):
        parameter(obs, f"Track{i}Bitrate", 160)
    report = []
    for count in (1, 6, 12):
        parameter(obs, "RecTracks", (1 << count) - 1)
        time.sleep(2)
        result = record(obs, args.seconds)
        result["tracks"] = count
        result["inspection"] = inspect(Path(result["recording"]), list(range(1, count + 1)), video_sync=True)
        result["mean_cpu_percent"] = statistics.mean(s["cpuUsage"] for s in result["stats"])
        result["mean_memory_mb"] = statistics.mean(s["memoryUsage"] for s in result["stats"])
        result["file_bytes"] = Path(result["recording"]).stat().st_size
        report.append(result)
        print(json.dumps({k: result[k] for k in ("tracks", "mean_cpu_percent", "mean_memory_mb", "file_bytes")}), flush=True)
    (args.directory / "performance.json").write_text(json.dumps(report, indent=2) + "\n")
