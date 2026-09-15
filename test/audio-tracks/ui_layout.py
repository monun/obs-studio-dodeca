"""Check translated 12-track controls and scrolling at the running Qt scale."""

import argparse
import json
import time
from pathlib import Path

from integration import OBS
from ui_client import UI


def check_controls(ui, names, expected_scale, prefix, legacy_prefix):
    widgets = {}
    for index, name in enumerate(names, 1):
        ui.call("ensure_visible", object=name)
        widget = ui.call("snapshot", names=[name])["widgets"][name]
        widgets[name] = widget
        assert widget["visible"] and widget["exposed"], (name, widget)
        assert widget["width"] >= widget["minimum_width"], widget
        assert widget["scale"] == expected_scale, widget
        expected = f"{legacy_prefix if index <= 6 else prefix} {index}"
        assert expected in widget["accessible"], widget
    return widgets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--scale", type=int, default=1)
    args = parser.parse_args()
    obs, ui = OBS(), UI(args.ui)
    prefix = "트랙" if args.locale == "ko-KR" else "Track"
    legacy_prefix = "Spur" if args.locale == "de-DE" else prefix
    result = {"locale": args.locale, "scale": args.scale}
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.3)
    ui.call("index", object="outputMode", index=1)
    ui.call("index", object="advOutRecType", index=0)
    ui.call("set", values={"listWidget": 3, "advOutTabs": 1, "advOutRecFormat": "mkv"})
    names = [f"advOutRecTrack{i}" for i in range(1, 13)]
    result["recording"] = check_controls(ui, names, args.scale, prefix, legacy_prefix)
    for index in range(11):
        assert ui.call("key", object=names[index], key="Key_Tab")["focus"] == names[index + 1]
    ui.call("screenshot", object="OBSBasicSettings", file=f"recording-{args.locale}-{args.scale}x.png")
    ui.call("set", values={"advOutTabs": 0})
    result["streaming"] = check_controls(ui, [f"advOutTrack{i}" for i in range(1, 13)], args.scale, prefix, legacy_prefix)
    result["vod"] = check_controls(ui, [f"vodTrack{i}" for i in range(1, 13)], args.scale, prefix, legacy_prefix)
    for group in ("advOutTrack", "vodTrack"):
        for index, key, expected in ((6, "Key_Right", 7), (11, "Key_Right", 12)):
            ui.call("set", values={f"{group}{index}": True})
            ui.call("key", object=f"{group}{index}", key=key)
            name = f"{group}{expected}"
            assert ui.call("snapshot", names=[name])["widgets"][name]["checked"]
    ui.call("screenshot", object="OBSBasicSettings", file=f"streaming-{args.locale}-{args.scale}x.png")
    ui.call("set", values={"advOutTabs": 2})
    ui.call("key", object="advOutTrack11Name", key="Key_Tab")
    assert ui.call("snapshot", names=["advOutTrack12Bitrate"])["widgets"]["advOutTrack12Bitrate"]["focused"]
    ui.call("key", object="advOutTrack12Bitrate", key="Key_Tab")
    time.sleep(0.2)
    result["audio12"] = ui.call("snapshot", names=["advOutTrack12Name"])["widgets"]["advOutTrack12Name"]
    assert result["audio12"]["focused"] and result["audio12"]["exposed"], result["audio12"]
    assert result["audio12"]["group_title"] == f"{prefix} 12", result["audio12"]
    ui.call("screenshot", object="OBSBasicSettings", file=f"audio12-{args.locale}-{args.scale}x.png")
    ui.call("button", object="buttonBox", button="Cancel")
    source = next(i for i in obs.call("GetInputList")["inputs"] if i["inputName"] == "Tone 01")
    root = "audioTracks_" + source["inputUuid"]
    ui.call("invoke", object="OBSBasic", method="on_actionAdvAudioProperties_triggered")
    time.sleep(0.2)
    names = [f"{root}/audioTrack{i}" for i in range(1, 13)]
    ui.call("key", object=names[-1], key="Key_Tab")
    ui.call("ensure_visible", object=names[-1])
    result["source"] = check_controls(ui, names, args.scale, prefix, legacy_prefix)
    assert all("Tone 01" in widget["accessible"] for widget in result["source"].values())
    ui.call("screenshot", object="OBSAdvAudio", file=f"source-{args.locale}-{args.scale}x.png")
    ui.call("close", object="OBSAdvAudio")
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS {args.locale} at {args.scale * 100}%: labels, accessibility, layout and keyboard scrolling")
