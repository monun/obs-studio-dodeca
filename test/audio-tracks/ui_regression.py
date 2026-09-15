"""Check live Qt routing, keyboard access, persistence, estimates and warnings."""

import argparse
import json
import time
from pathlib import Path

from integration import OBS
from ui_client import UI


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    args = parser.parse_args()
    obs, ui = OBS(), UI(args.ui)
    result = {}
    source = next(i for i in obs.call("GetInputList")["inputs"] if i["inputName"] == "Tone 12")
    root = "audioTracks_" + source["inputUuid"]
    ui.call("invoke", object="OBSBasic", method="on_actionAdvAudioProperties_triggered")
    time.sleep(0.2)
    names = [f"{root}/audioTrack{i}" for i in range(1, 13)]
    result["source_controls"] = ui.call("snapshot", names=names)["widgets"]
    assert all(w["focus_policy"] and str(i) in w["accessible"] and "Tone 12" in w["accessible"]
               for i, w in enumerate(result["source_controls"].values(), 1))
    ui.call("key", object=names[-1], key="Key_Space")
    assert obs.tracks("Tone 12")["12"] is False
    ui.call("key", object=names[-1], key="Key_Space")
    assert obs.tracks("Tone 12")["12"] is True
    for i in range(11):
        assert ui.call("key", object=names[i], key="Key_Tab")["focus"] == f"audioTrack{i + 2}"
    ui.call("screenshot", object="OBSAdvAudio", file="advanced-audio-keyboard.png")
    ui.call("close", object="OBSAdvAudio")
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.3)
    values = {"listWidget": 3, "outputMode": "Advanced", "advOutTabs": 3, "advOutRecType": "Standard",
              "advOutRecFormat": "mkv", "advOutTrack10Bitrate": "192", "advOutTrack11Bitrate": "224",
              "advOutTrack12Bitrate": "256", "advOutTrack10Name": "Music 10", "advOutTrack11Name": "Game 11",
              "advOutTrack12Name": "Microphone 12", "advRBSecMax": 600, "streamDelaySec": 600,
              "advOutTrack12": True, "vodTrack11": True, "vodTrackEnabled": True}
    values.update({f"advOutRecTrack{i}": i in (1, 7, 12) for i in range(1, 13)})
    ui.call("set", values=values)
    labels = ui.call("labels", object="OBSBasicSettings")["labels"]
    result["replay_estimate_with12"] = labels
    assert any("112 MB" in label["text"] for label in labels), labels
    ui.call("set", values={"advOutRecTrack12": False})
    labels = ui.call("labels", object="OBSBasicSettings")["labels"]
    result["replay_estimate_without12"] = labels
    assert any("94 MB" in label["text"] for label in labels), labels
    ui.call("set", values={"advOutRecTrack12": True, "listWidget": 8})
    result["stream_delay"] = ui.call("snapshot", names=["streamDelayInfo"])["widgets"]
    assert "111 MB" in result["stream_delay"]["streamDelayInfo"]["text"], result["stream_delay"]
    # Saving no recording tracks must leave the settings dialog open with an explanation.
    ui.call("set", values={f"advOutRecTrack{i}": False for i in range(1, 13)})
    ui.call("button", object="buttonBox", button="Ok")
    time.sleep(0.2)
    result["empty_record_warning"] = ui.call("messages", dismiss=True)["messages"]
    assert result["empty_record_warning"]
    ui.call("set", values={f"advOutRecTrack{i}": i in (1, 7, 12) for i in range(1, 13)})
    ui.call("set", values={"streamDelaySec": 0, "advRBSecMax": 8})
    ui.call("button", object="buttonBox", button="Ok")
    time.sleep(0.3)
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.3)
    names = [f"advOutTrack{i}{suffix}" for i in (10, 11, 12) for suffix in ("Bitrate", "Name")]
    names += ["advOutRecTrack1", "advOutRecTrack7", "advOutRecTrack12", "advOutTrack12", "vodTrack11"]
    result["reloaded"] = ui.call("snapshot", names=names)["widgets"]
    assert result["reloaded"]["advOutTrack12Name"]["text"] == "Microphone 12"
    assert result["reloaded"]["advOutTrack12Bitrate"]["text"] == "256"
    assert all(result["reloaded"][name]["checked"] for name in names[-5:])
    ui.call("set", values={"listWidget": 3, "advOutTabs": 1})
    ui.call("screenshot", object="OBSBasicSettings", file="recording-controls.png")
    ui.call("button", object="buttonBox", button="Cancel")
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print("PASS keyboard routing, accessible names, upper-track persistence, estimates and empty-selection warning")
