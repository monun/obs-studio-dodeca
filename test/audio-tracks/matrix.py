"""Run recording variants through the real settings dialog and OBS outputs."""

import argparse
import json
import time
from pathlib import Path

from integration import OBS, record
from ui_client import UI
from verify_media import inspect


def configure(ui, values):
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.5)
    ui.call("set", values=values)
    ui.call("button", object="buttonBox", button="Ok")
    time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    parser.add_argument("--cases", default="mkv12,mp4,fragmented_mp4,hybrid_mp4,hybrid_mov,opus_mkv,flv12,simple_aac,simple_opus")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    obs = OBS()
    ui = UI(args.ui)
    for case in args.cases.split(","):
        values = {"outputMode": "Advanced", "advOutRecType": "Standard",
                  "advOutRecFormat": "mkv", "advOutRecAEncoder": "ffmpeg_aac", "autoRemux": False}
        values.update({f"advOutRecTrack{i}": True for i in range(1, 13)})
        tracks = list(range(1, 13))
        if case in ("mp4", "fragmented_mp4", "hybrid_mp4", "hybrid_mov"):
            values["advOutRecFormat"] = case
        elif case == "opus_mkv":
            values["advOutRecAEncoder"] = "ffmpeg_opus"
        elif case.startswith("custom_"):
            values.update(advOutRecType="Custom Output (FFmpeg)", advOutFFFormat="matroska" if "mkv" in case else "mp4",
                          advOutFFRecPath=str(args.directory), advOutFFVEncoder="libx264", advOutFFAEncoder="aac")
            if case.endswith("_12"):
                tracks = [12]
            values.update({f"advOutFFTrack{i}": i in tracks for i in range(1, 13)})
        elif case == "flv12":
            values.update(advOutRecFormat="flv", flvTrack12=True)
            tracks = [12]
        elif case.startswith("simple_"):
            values.update(outputMode="Simple", simpleOutRecQuality="Small", simpleOutRecFormat="mkv",
                          simpleOutputPath=str(args.directory), simpleOutRecAEncoder=case.split("_")[1],
                          simpleOutRecEncoder="x264")
            values.update({f"simpleOutRecTrack{i}": True for i in range(1, 13)})
        elif case != "mkv12":
            raise ValueError(case)
        configure(ui, values)
        result = record(obs, 8)
        result["case"] = case
        names = None
        if not case.startswith("simple_") and case != "flv12":
            names = [obs.call("GetProfileParameter", {"parameterCategory": "AdvOut", "parameterName": f"Track{i}Name"})["parameterValue"]
                     for i in tracks]
        result["inspection"] = inspect(Path(result["recording"]), tracks, names=names, video_sync=True)
        (args.directory / f"{case}.json").write_text(json.dumps(result, indent=2) + "\n")
        print(f"PASS {case}: {len(tracks)} streams, {result['recording']}", flush=True)


if __name__ == "__main__":
    main()
