"""Exercise restart, replay, pause, native split and OBS remux using real outputs."""

import argparse
import json
import time
from pathlib import Path

from integration import OBS, record
from matrix import configure
from ui_client import UI
from verify_media import inspect
from verify_remux import compare


def parameter(obs, name, value, category="AdvOut"):
    obs.call("SetProfileParameter", {"parameterCategory": category, "parameterName": name, "parameterValue": str(value)})


def wait_stopped(obs):
    deadline = time.monotonic() + 15
    while obs.call("GetRecordStatus")["outputActive"]:
        assert time.monotonic() < deadline
        time.sleep(0.1)


def verify(result, tracks):
    result["inspection"] = inspect(Path(result["recording"]), tracks, video_sync=True)
    result["replay_inspections"] = [inspect(Path(path), tracks, video_sync=True) for path in result.get("replays", [])]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    parser.add_argument("--cases", default="restart,split,remux")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    obs, ui = OBS(), UI(args.ui)
    all_tracks = list(range(1, 13))
    base = {"outputMode": "Advanced", "advOutRecType": "Standard", "advOutRecFormat": "mkv",
            "advOutRecAEncoder": "ffmpeg_aac", "advOutRecPath": str(args.directory), "autoRemux": False,
            "advReplayBuf": True, "advRBSecMax": 8, "advOutSplitFile": False}
    base.update({f"advOutRecTrack{i}": True for i in all_tracks})
    configure(ui, base)
    report = {}
    if "restart" in args.cases:
        report["twelve"] = verify(record(obs, 10, replay=True, pause=True), all_tracks)
        # Modify only the profile key: retain the SAME output handler/encoder objects.
        parameter(obs, "RecTracks", 1 << 11)
        report["last_only"] = verify(record(obs, 8), [12])
        report["last_only"]["outputs"] = ui.call("outputs")["outputs"]
        assert [e["mix"] for e in report["last_only"]["outputs"]["record"]] == [11]
        parameter(obs, "RecTracks", (1 << 6) | (1 << 11))
        report["replay_restart"] = verify(record(obs, 10, replay=True), [7, 12])
        report["replay_restart"]["outputs"] = ui.call("outputs")["outputs"]
        assert [e["mix"] for e in report["replay_restart"]["outputs"]["replay"]] == [6, 11]
        print("PASS twelve -> last-only recording, replay restart and pause", flush=True)
    if "split" in args.cases:
        for format_ in ("hybrid_mp4", "hybrid_mov"):
            configure(ui, {**base, "advOutRecFormat": format_, "advOutSplitFile": True})
            parameter(obs, "RecSplitFileType", "Manual")
            before = set(args.directory.iterdir())
            obs.call("StartRecord")
            time.sleep(8)
            obs.call("SplitRecordFile")
            time.sleep(8)
            obs.call("StopRecord")
            wait_stopped(obs)
            files = sorted(set(args.directory.iterdir()) - before)
            files = [p for p in files if p.suffix in (".mp4", ".mov")]
            assert len(files) == 2, files
            report[format_ + "_split"] = [inspect(p, all_tracks, video_sync=True) for p in files]
            print(f"PASS {format_}: both split files retain twelve tracks", flush=True)
    if "remux" in args.cases:
        configure(ui, base)
        manual = record(obs, 8)
        source = Path(manual["recording"])
        target = source.with_name(source.stem + "-manual.mp4")
        ui.call("invoke", object="OBSBasic", method="on_actionRemux_triggered")
        time.sleep(0.3)
        ui.call("table", object="OBSRemux/tableView", cells=[{"row": 0, "column": 1, "value": str(source)},
                                                           {"row": 0, "column": 2, "value": str(target)}])
        ui.call("invoke", object="OBSRemux", method="beginRemux")
        deadline = time.monotonic() + 20
        while True:
            rows = ui.call("table", object="OBSRemux/tableView")["rows"]
            # The model clears its insertion row while processing and restores it on completion.
            if target.exists() and len(rows) >= 2:
                break
            assert time.monotonic() < deadline, rows
            time.sleep(0.2)
        time.sleep(0.5)
        report["manual_remux"] = compare(source, target)
        ui.call("messages", dismiss=True)
        ui.call("close", object="OBSRemux")
        configure(ui, {**base, "autoRemux": True})
        auto = record(obs, 8)
        source = Path(auto["recording"])
        target = source.with_suffix(".mp4")
        deadline = time.monotonic() + 20
        while not target.exists() or target.stat().st_size < source.stat().st_size * 0.9:
            assert time.monotonic() < deadline, target
            time.sleep(0.2)
        time.sleep(1)
        report["auto_remux"] = compare(source, target)
        print("PASS OBS manual and automatic remux: names and packet payloads preserved", flush=True)
    (args.directory / "scenarios.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
