"""Use loopback receivers to check broadcast/VOD roles and concurrent outputs."""

import argparse
import json
import subprocess
import time
from pathlib import Path

from integration import OBS, record
from matrix import configure
from scenarios import parameter, verify
from ui_client import UI
from verify_media import inspect


def wait_stream(obs, active):
    deadline = time.monotonic() + 15
    while obs.call("GetStreamStatus")["outputActive"] != active:
        assert time.monotonic() < deadline, f"Stream did not become {active}"
        time.sleep(0.1)


def receiver(directory, name, url):
    log = (directory / f"{name}-receiver.log").open("w")
    arguments = ["ffmpeg", "-hide_banner", "-y"]
    if url.startswith("rtmp"):
        arguments += ["-listen", "1"]
    arguments += ["-i", url]
    # FFmpeg 6 decodes primary RTMP audio; its demuxer cannot identify the
    # Enhanced RTMP VOD audio tag. Verify that role via the OBS output encoder.
    arguments += ["-map", "0:v:0", "-map", "0:a:0"] if url.startswith("rtmp") else ["-map", "0"]
    arguments += ["-c", "copy", str(directory / f"{name}.mkv")]
    process = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT)
    log.close()
    time.sleep(0.3)
    assert process.poll() is None, "Receiver failed to start"
    return process


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    parser.add_argument("--cases", default="concurrent,same,unsupported,simple,srt")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    obs, ui = OBS(), UI(args.ui)
    url = "rtmp://127.0.0.1:1935/live/tracks"
    base = {"outputMode": "Advanced", "advOutRecType": "Standard", "advOutRecFormat": "mkv",
            "advOutRecAEncoder": "ffmpeg_aac", "advOutRecPath": str(args.directory), "autoRemux": False,
            "advReplayBuf": True, "advRBSecMax": 8, "advOutSplitFile": False, "advOutTrack12": True,
            "vodTrack11": True, "vodTrackEnabled": True}
    base.update({f"advOutRecTrack{i}": True for i in range(1, 13)})
    report = {}
    for case in args.cases.split(","):
        service = {"streamServiceType": "rtmp_custom", "streamServiceSettings": {"server": url.rsplit("/", 1)[0], "key": "tracks"}}
        obs.call("SetStreamServiceSettings", service)
        configure(ui, base)
        parameter(obs, "VodTrackEnabled", "true")
        expected = [11, 10]
        receive_url = url
        if case == "same":
            configure(ui, {"vodTrack12": True})
            expected = [11]
        elif case == "unsupported":
            service["streamServiceType"] = "rtmp_common"
            service["streamServiceSettings"]["service"] = "YouTube - RTMPS"
            obs.call("SetStreamServiceSettings", service)
            expected = [11]
        elif case == "simple":
            configure(ui, {"outputMode": "Simple", "simpleOutAdvanced": True, "simpleVodTrack": True})
            parameter(obs, "VodTrackEnabled", "true", "SimpleOutput")
            expected = [0, 1]
        elif case == "srt":
            service["streamServiceSettings"]["server"] = "srt://127.0.0.1:9000?mode=caller"
            service["streamServiceSettings"]["key"] = ""
            obs.call("SetStreamServiceSettings", service)
            parameter(obs, "StreamMultiTrackAudioMixes", 1 | 2 | 4 | 64 | 1024 | 2048)
            expected = [0, 1, 2, 6, 10, 11]
            receive_url = "srt://127.0.0.1:9000?mode=listener"
        elif case != "concurrent":
            raise ValueError(case)
        process = receiver(args.directory, case, receive_url)
        try:
            obs.call("StartStream")
            wait_stream(obs, True)
            outputs = ui.call("outputs")["outputs"]
            assert [e["mix"] for e in outputs["stream"]] == expected, outputs
            result = {"outputs": outputs}
            if case == "concurrent":
                result["first"] = verify(record(obs, 10, replay=True), list(range(1, 13)))
                assert obs.call("GetStreamStatus")["outputActive"]
                result["restart"] = verify(record(obs, 10, replay=True), list(range(1, 13)))
                assert [e["mix"] for e in ui.call("outputs")["outputs"]["stream"]] == expected
            else:
                time.sleep(8)
            result["stream_status"] = obs.call("GetStreamStatus")
            assert result["stream_status"]["outputBytes"] > 0
            obs.call("StopStream")
            wait_stream(obs, False)
            assert process.wait(timeout=15) == 0, "Receiver failed; inspect its log"
            if case == "srt":
                result["inspection"] = inspect(args.directory / "srt.mkv", [i + 1 for i in expected], video_sync=True)
            else:
                result["primary_inspection"] = inspect(args.directory / f"{case}.mkv", [expected[0] + 1], video_sync=True)
                result["vod_verification"] = "OBS output encoder role and mix index"
            report[case] = result
            print(f"PASS {case}: streaming mixes {[i + 1 for i in expected]}", flush=True)
        finally:
            if obs.call("GetStreamStatus")["outputActive"]:
                obs.call("StopStream")
                wait_stream(obs, False)
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
        (args.directory / "streaming.json").write_text(json.dumps(report, indent=2) + "\n")
