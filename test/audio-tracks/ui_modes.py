"""Check mode-specific track controls, FFmpeg validation and service-controlled bitrates."""

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
    obs.call("SetStreamServiceSettings", {"streamServiceType": "rtmp_custom", "streamServiceSettings": {
        "server": "rtmp://127.0.0.1:1935/live", "key": "tracks"}})
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.3)
    ui.call("set", values={"outputMode": "Advanced", "listWidget": 3, "advOutTabs": 1,
                            "advOutRecType": "Custom Output (FFmpeg)", "advOutFFFormat": "matroska",
                            "advOutFFVEncoder": "libx264", "advOutFFAEncoder": "aac"})
    assert not ui.call("snapshot", names=["advReplayBuf"])["widgets"]["advReplayBuf"]["enabled"]
    ui.call("set", values={f"advOutFFTrack{i}": False for i in range(1, 13)})
    ui.call("button", object="buttonBox", button="Ok")
    time.sleep(0.2)
    report = {"empty_ffmpeg_warning": ui.call("messages", dismiss=True)["messages"]}
    assert report["empty_ffmpeg_warning"]
    ui.call("set", values={"advOutFFTrack12": True})
    ui.call("button", object="buttonBox", button="Ok")
    time.sleep(0.3)
    assert obs.call("GetProfileParameter", {"parameterCategory": "AdvOut", "parameterName": "FFAudioMixes"})["parameterValue"] == "2048"
    ui.call("invoke", object="OBSBasic", method="on_action_Settings_triggered")
    time.sleep(0.3)
    ui.call("set", values={"listWidget": 3, "advOutTabs": 1})
    report["ffmpeg_reloaded"] = ui.call("snapshot", names=[f"advOutFFTrack{i}" for i in range(1, 13)])["widgets"]
    assert all(v["checked"] == (i == 12) for i, v in enumerate(report["ffmpeg_reloaded"].values(), 1))
    ui.call("set", values={"advOutRecType": "Standard", "advOutRecFormat": "flv", "flvTrack12": True})
    report["flv"] = ui.call("snapshot", names=["flvTrack12", "advOutRecTrack12"])["widgets"]
    assert report["flv"]["flvTrack12"]["visible"] and not report["flv"]["advOutRecTrack12"]["visible"]
    ui.call("set", values={"advOutRecFormat": "mkv", "advOutRecAEncoder": "ffmpeg_aac",
                            "advOutTrack10Bitrate": "192", "advOutTrack11Bitrate": "224", "advOutTrack12Bitrate": "256"})
    ui.call("set", values={"advOutRecAEncoder": "ffmpeg_opus"})
    report["opus_bitrates"] = ui.call("snapshot", names=[f"advOutTrack{i}Bitrate" for i in (10, 11, 12)])["widgets"]
    assert [w["text"] for w in report["opus_bitrates"].values()] == ["192", "224", "256"]
    ui.call("set", values={"advOutRecAEncoder": "ffmpeg_aac", "enableMultitrackVideo": True,
                            "advOutTrack12": True, "vodTrack11": True, "vodTrackEnabled": True,
                            "advOutRecTrack11": False, "advOutRecTrack12": False})
    report["service_bitrates"] = ui.call("snapshot", names=[f"advOutTrack{i}Bitrate" for i in (10, 11, 12)])["widgets"]
    assert [w["enabled"] for w in report["service_bitrates"].values()] == [True, False, False]
    ui.call("set", values={"advOutRecTrack12": True})
    assert ui.call("snapshot", names=["advOutTrack12Bitrate"])["widgets"]["advOutTrack12Bitrate"]["enabled"]
    ui.call("set", values={"enableMultitrackVideo": False})
    ui.call("set", values={"outputMode": "Simple", "simpleOutputVBitrate": 1000,
                            "simpleOutputABitrate": "160", "simpleOutAdvanced": True,
                            "simpleVodTrack": True, "streamDelaySec": 600, "listWidget": 8})
    report["simple_delay_with_vod"] = ui.call("snapshot", names=["streamDelayInfo"])["widgets"]["streamDelayInfo"]["text"]
    assert "99 MB" in report["simple_delay_with_vod"]
    ui.call("set", values={"simpleVodTrack": False})
    report["simple_delay_without_vod"] = ui.call("snapshot", names=["streamDelayInfo"])["widgets"]["streamDelayInfo"]["text"]
    assert "87 MB" in report["simple_delay_without_vod"]
    ui.call("button", object="buttonBox", button="Cancel")
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS FFmpeg empty/single selection, FLV controls, codec changes and service bitrate states")
