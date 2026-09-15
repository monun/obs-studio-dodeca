"""Check nested scenes, a transition, mute, gain and sync offset on upper tracks."""

import argparse
import json
import time
from pathlib import Path

import numpy as np

from integration import OBS, record
from matrix import configure
from scenarios import parameter, wait_stopped
from ui_client import UI
from verify_media import inspect, run


def pcm(path, index):
    return np.frombuffer(run("ffmpeg", "-v", "error", "-i", str(path), "-map", f"0:a:{index}",
                             "-ac", "1", "-ar", "48000", "-f", "f32le", "-"), dtype="<f4")


def gate(samples):
    blocks = samples[:len(samples) // 48 * 48].reshape(-1, 48)
    rms = np.sqrt(np.mean(blocks ** 2, axis=1))
    return np.flatnonzero(np.diff((rms > rms.max() * 0.2).astype(int)) > 0), float(np.median(rms[rms > rms.max() * 0.8]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    obs, ui = OBS(), UI(args.ui)
    configure(ui, {"outputMode": "Advanced", "advOutRecType": "Standard", "advOutRecFormat": "mkv",
                   "advOutRecAEncoder": "ffmpeg_aac", "advOutRecPath": str(args.directory),
                   "advOutSplitFile": False, "autoRemux": False})
    parameter(obs, "RecTracks", 4095)
    existing = {s["sceneName"] for s in obs.call("GetSceneList")["scenes"]}
    for scene in ("Nested A", "Nested B"):
        if scene not in existing:
            obs.call("CreateScene", {"sceneName": scene})
            obs.call("CreateSceneItem", {"sceneName": scene, "sourceName": "Audio track regression"})
    obs.call("SetCurrentSceneTransition", {"transitionName": "Fade"})
    obs.call("SetCurrentSceneTransitionDuration", {"transitionDuration": 1000})
    obs.call("SetCurrentProgramScene", {"sceneName": "Nested A"})
    time.sleep(2)
    obs.call("StartRecord")
    time.sleep(8)
    obs.call("SetCurrentProgramScene", {"sceneName": "Nested B"})
    time.sleep(8)
    path = Path(obs.call("StopRecord")["outputPath"])
    wait_stopped(obs)
    report = {"nested_transition": inspect(path, list(range(1, 13)), starts=(0, 8), video_sync=True)}
    baseline = pcm(path, 11)
    _, baseline_rms = gate(baseline)
    obs.call("SetInputMute", {"inputName": "Tone 07", "inputMuted": True})
    obs.call("CreateSourceFilter", {"sourceName": "Tone 12", "filterName": "Regression gain",
                                     "filterKind": "gain_filter", "filterSettings": {"db": -6.0}})
    # Exercise adjustment of an already configured offset. Upstream's live 0 ->
    # nonzero transition keeps push_back until the source buffer is reset.
    obs.call("SetInputAudioSyncOffset", {"inputName": "Tone 12", "inputAudioSyncOffset": 1})
    time.sleep(0.1)
    obs.call("SetInputAudioSyncOffset", {"inputName": "Tone 12", "inputAudioSyncOffset": 100})
    assert obs.call("GetInputAudioSyncOffset", {"inputName": "Tone 12"})["inputAudioSyncOffset"] == 100
    try:
        time.sleep(2)
        result = record(obs, 8)
        path = Path(result["recording"])
        assert np.max(abs(pcm(path, 6))) < 0.00001, "Muted track 7 is audible"
        reference, _ = gate(pcm(path, 0))
        delayed, rms = gate(pcm(path, 11))
        reference = reference[(reference > 250) & (reference < 7500)]
        shifts = [float(delayed[np.argmin(abs(delayed - edge))] - edge) for edge in reference]
        assert all(abs(shift - 100) <= 23 for shift in shifts), shifts
        gain_db = float(20 * np.log10(rms / baseline_rms))
        assert abs(gain_db + 6) < 0.2, gain_db
        report["mute_gain_offset"] = {"recording": str(path), "track7_silent": True,
                                       "track12_gain_db": gain_db, "track12_delay_ms": shifts}
    finally:
        obs.call("SetInputMute", {"inputName": "Tone 07", "inputMuted": False})
        obs.call("RemoveSourceFilter", {"sourceName": "Tone 12", "filterName": "Regression gain"})
        obs.call("SetInputAudioSyncOffset", {"inputName": "Tone 12", "inputAudioSyncOffset": 0})
        obs.call("SetCurrentProgramScene", {"sceneName": "Audio track regression"})
    (args.directory / "routing.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS nested scenes, transition, upper-track mute, gain and 100 ms sync offset")
