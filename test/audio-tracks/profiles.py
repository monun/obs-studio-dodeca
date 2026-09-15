"""Check fresh defaults, six-track profile preservation and profile switching."""

import argparse
import json
import time
from pathlib import Path

from integration import OBS
from scenarios import parameter


def get(obs, name, category="AdvOut"):
    return obs.call("GetProfileParameter", {"parameterCategory": category, "parameterName": name})


def switch(obs, name):
    obs.call("SetCurrentProfile", {"profileName": name})
    deadline = time.monotonic() + 10
    while obs.call("GetProfileList")["currentProfileName"] != name:
        assert time.monotonic() < deadline
        time.sleep(0.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    obs = OBS()
    original = obs.call("GetProfileList")["currentProfileName"]
    name = "Six-track profile regression"
    profiles = set(obs.call("GetProfileList")["profiles"])
    assert name not in profiles, "Use a fresh disposable configuration"
    obs.call("CreateProfile", {"profileName": name})
    time.sleep(0.5)
    report = {"new_recording_default": get(obs, "RecTracks"),
              "new_bitrates": [get(obs, f"Track{i}Bitrate") for i in range(1, 13)]}
    assert report["new_recording_default"]["parameterValue"] == "1"
    assert all(value["parameterValue"] == "160" for value in report["new_bitrates"])
    for i in range(1, 7):
        parameter(obs, f"Track{i}Name", f"Legacy {i}")
        parameter(obs, f"Track{i}Bitrate", 128 + 16 * i)
    parameter(obs, "RecTracks", 37)
    parameter(obs, "TrackIndex", 6)
    parameter(obs, "VodTrackIndex", 3)
    switch(obs, original)
    switch(obs, name)
    report["legacy_reloaded"] = {key: get(obs, key) for key in ["RecTracks", "TrackIndex", "VodTrackIndex"] +
                                  [f"Track{i}{suffix}" for i in range(1, 13) for suffix in ("Name", "Bitrate")]}
    legacy = report["legacy_reloaded"]
    assert legacy["RecTracks"]["parameterValue"] == "37"
    assert legacy["TrackIndex"]["parameterValue"] == "6"
    assert legacy["VodTrackIndex"]["parameterValue"] == "3"
    for i in range(1, 7):
        assert legacy[f"Track{i}Name"]["parameterValue"] == f"Legacy {i}"
        assert legacy[f"Track{i}Bitrate"]["parameterValue"] == str(128 + 16 * i)
    for i in range(7, 13):
        assert legacy[f"Track{i}Bitrate"]["parameterValue"] == "160"
        assert legacy[f"Track{i}Name"]["parameterValue"] in (None, "")
    switch(obs, original)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS new recording defaults, preserved six-track settings and profile switching")
