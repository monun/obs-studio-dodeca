"""Drive an isolated OBS with obs-websocket and the opt-in test-input module.

Dependencies: Python 3, websocket-client; inspection also uses FFmpeg and NumPy.
Only connect this runner to a disposable test profile and scene collection.
"""

import argparse
import json
import time
from pathlib import Path

import websocket


class OBS:
    def __init__(self, port=4455):
        self.socket = websocket.create_connection(f"ws://127.0.0.1:{port}", timeout=15)
        hello = json.loads(self.socket.recv())
        assert hello["op"] == 0
        assert "authentication" not in hello["d"], "Use an isolated, local test server"
        self.socket.send(json.dumps({"op": 1, "d": {"rpcVersion": 1, "eventSubscriptions": 2047}}))
        assert json.loads(self.socket.recv())["op"] == 2
        self.sequence = 0
        self.events = []

    def call(self, method, data=None, *, success=True):
        self.sequence += 1
        request_id = str(self.sequence)
        self.socket.send(json.dumps({"op": 6, "d": {
            "requestType": method, "requestId": request_id, "requestData": data or {}}}))
        while True:
            message = json.loads(self.socket.recv())
            if message["op"] == 5:
                self.events.append(message["d"])
            if message["op"] == 7 and message["d"]["requestId"] == request_id:
                response = message["d"]
                assert response["requestStatus"]["result"] == success, response
                return response.get("responseData", {}) if success else response["requestStatus"]

    def tracks(self, name):
        return self.call("GetInputAudioTracks", {"inputName": name})["inputAudioTracks"]

    def assign(self, name, tracks):
        self.call("SetInputAudioTracks", {"inputName": name, "inputAudioTracks": tracks})


def fixture(obs, count, sources=None):
    scene = "Audio track regression"
    scenes = obs.call("GetSceneList")["scenes"]
    if not any(item["sceneName"] == scene for item in scenes):
        obs.call("CreateScene", {"sceneName": scene})
    existing = {item["inputName"] for item in obs.call("GetInputList")["inputs"]}
    if "Sync video" not in existing:
        obs.call("CreateInput", {"sceneName": scene, "inputName": "Sync video", "inputKind": "sync_video"})
    for track in range(1, (sources or count) + 1):
        name = f"Tone {track:02d}"
        if name not in existing:
            obs.call("CreateInput", {"sceneName": scene, "inputName": name, "inputKind": "sync_audio",
                                     "inputSettings": {"frequency": 300 + 100 * (track - 1), "buffer_ms": 200}})
            assert all(obs.tracks(name).values()), obs.tracks(name)
        obs.assign(name, {str(i): i == track for i in range(1, count + 1)})
    obs.call("SetCurrentProgramScene", {"sceneName": scene})
    return scene


def websocket_regression(obs):
    name = "Tone 12"
    expected = {str(i): i == 12 for i in range(1, 13)}
    assert obs.tracks(name) == expected
    obs.assign(name, {"12": False})
    expected["12"] = False
    assert obs.tracks(name) == expected
    obs.assign(name, {"12": True})
    expected["12"] = True
    obs.assign(name, {str(i): i == 1 for i in range(1, 7)})
    expected["1"] = True
    assert obs.tracks(name) == expected, "Legacy partial request cleared upper tracks"
    obs.call("SetInputAudioTracks", {"inputName": name, "inputAudioTracks": {"1": False, "12": 1}}, success=False)
    assert obs.tracks(name) == expected, "Invalid request partially mutated routing"
    obs.assign(name, {"1": False})
    obs.tracks(name)  # Drain responses/events preceding this request.
    events = [event["eventData"] for event in obs.events if event["eventType"] == "InputAudioTracksChanged"
              and event["eventData"]["inputName"] == name]
    assert events and events[-1]["inputAudioTracks"] == obs.tracks(name)
    return {"partial_upper": True, "legacy_partial": True, "atomic_type_rejection": True, "events": True}


def record(obs, seconds, replay=False, pause=False):
    if replay:
        obs.call("StartReplayBuffer")
    obs.call("StartRecord")
    start = time.monotonic()
    stats = []
    paused = False
    while time.monotonic() - start < seconds:
        time.sleep(min(5, max(0.1, seconds - (time.monotonic() - start))))
        stats.append(obs.call("GetStats"))
        if pause and not paused and time.monotonic() - start > seconds / 2:
            obs.call("PauseRecord")
            time.sleep(2)
            obs.call("ResumeRecord")
            paused = True
    replays = []
    if replay:
        for _ in range(2):
            obs.call("SaveReplayBuffer")
            time.sleep(2)
            replays.append(obs.call("GetLastReplayBufferReplay")["savedReplayPath"])
        obs.call("StopReplayBuffer")
    path = obs.call("StopRecord")["outputPath"]
    deadline = time.monotonic() + 15
    while obs.call("GetRecordStatus")["outputActive"] or (
            replay and obs.call("GetReplayBufferStatus")["outputActive"]):
        assert time.monotonic() < deadline, "OBS did not finish stopping the outputs"
        time.sleep(0.1)
    return {"recording": path, "replays": replays, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4455)
    parser.add_argument("--tracks", type=int, default=12)
    parser.add_argument("--sources", type=int, choices=(6, 12), help="Use twelve sources even in the six-track baseline")
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--pause", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    obs = OBS(args.port)
    fixture(obs, args.tracks, args.sources)
    report = {"version": obs.call("GetVersion"), "tracks": args.tracks}
    if args.tracks == 12:
        report["websocket"] = websocket_regression(obs)
    time.sleep(2)
    report.update(record(obs, args.seconds, args.replay, args.pause))
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("version", "stats")}, indent=2))


if __name__ == "__main__":
    main()
