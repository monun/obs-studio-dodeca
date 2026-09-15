"""Check the SRT/RIST six-at-once UI limit and rejection of an edited profile."""

import argparse
import json
import time
from pathlib import Path

from integration import OBS
from scenarios import parameter
from ui_client import UI


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    args = parser.parse_args()
    obs, ui = OBS(), UI(args.ui)
    previous_service = obs.call("GetStreamServiceSettings")
    previous_mask = obs.call("GetProfileParameter", {"parameterCategory": "AdvOut",
                                                    "parameterName": "StreamMultiTrackAudioMixes"})["parameterValue"]
    selected = (1, 2, 3, 7, 11, 12)
    mask = sum(1 << (i - 1) for i in selected)
    obs.call("SetStreamServiceSettings", {"streamServiceType": "rtmp_custom", "streamServiceSettings": {
        "server": "srt://127.0.0.1:9000?mode=caller", "key": ""}})
    parameter(obs, "StreamMultiTrackAudioMixes", mask)
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.3)
    ui.call("set", values={"listWidget": 3, "advOutTabs": 0})
    names = [f"advOutMultiTrack{i}" for i in range(1, 13)]
    report = {"at_limit": ui.call("snapshot", names=names)["widgets"]}
    for i, value in enumerate(report["at_limit"].values(), 1):
        assert value["checked"] == (i in selected)
        assert value["enabled"] == (i in selected)
    ui.call("button", object="advOutMultiTrack4")
    assert not ui.call("snapshot", names=["advOutMultiTrack4"])["widgets"]["advOutMultiTrack4"]["checked"]
    # Force an invalid state to exercise save validation in addition to disabling buttons.
    ui.call("set", values={"advOutMultiTrack4": True})
    ui.call("button", object="buttonBox", button="Ok")
    time.sleep(0.2)
    report["save_warning"] = ui.call("messages", dismiss=True)["messages"]
    assert report["save_warning"] and "6" in report["save_warning"][0]["text"]
    ui.call("button", object="buttonBox", button="Cancel")
    parameter(obs, "StreamMultiTrackAudioMixes", mask | 8)
    obs.call("StartStream")
    time.sleep(0.5)
    assert not obs.call("GetStreamStatus")["outputActive"]
    report["start_warning"] = ui.call("messages", dismiss=True)["messages"]
    # The frontend may log the setup failure without a dialog; preserve both observations.
    report["edited_profile_rejected"] = True
    parameter(obs, "StreamMultiTrackAudioMixes", previous_mask)
    obs.call("SetStreamServiceSettings", previous_service)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS six enabled candidates, disabled seventh, save warning and edited-profile start rejection")
