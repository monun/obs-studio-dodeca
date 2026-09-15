"""Create a NEW disposable OBS configuration, without modifying existing profiles."""

import argparse
import json
from pathlib import Path


def prepare(directory, recordings, tracks=12, port=4455, bridge=None):
    root = directory / "obs-studio"
    assert not root.exists(), f"Refusing to overwrite {root}"
    profile = root / "basic/profiles/Tracks"
    profile.mkdir(parents=True)
    (root / "basic/scenes").mkdir()
    (root / "plugin_config/obs-websocket").mkdir(parents=True)
    recordings.mkdir(parents=True, exist_ok=True)
    (root / "global.ini").write_text("[General]\nEnableAutoUpdates=false\nLastVersion=536936450\n")
    (root / "user.ini").write_text("""[General]
FirstRun=true
EnableCustomServerVodTrack=true
[Basic]
Profile=Tracks
ProfileDir=Tracks
SceneCollection=Tracks
SceneCollectionFile=Tracks
ConfigOnNewProfile=false
[BasicWindow]
WarnBeforeStartingStream=false
WarnBeforeStoppingStream=false
WarnBeforeStoppingRecord=false
""")
    (profile / "basic.ini").write_text(f"""[General]
Name=Tracks
[Output]
Mode=Advanced
FilenameFormatting=tracks-%CCYY-%MM-%DD-%hh-%mm-%ss
[Video]
BaseCX=640
BaseCY=360
OutputCX=640
OutputCY=360
FPSType=0
FPSCommon=30
[Audio]
SampleRate=48000
ChannelSetup=Stereo
[AdvOut]
Encoder=obs_x264
RecEncoder=obs_x264
AudioEncoder=ffmpeg_aac
RecAudioEncoder=ffmpeg_aac
RecFilePath={recordings}
RecFormat2=mkv
RecTracks={(1 << tracks) - 1}
RecRB=true
RecRBTime=5
RecRBSize=256
TrackIndex={tracks}
VodTrackIndex={tracks - 1}
VodTrackEnabled=true
""" + "".join(f"Track{i}Name=Track{i:02d}\nTrack{i}Bitrate=160\n" for i in range(1, tracks + 1)))
    settings = {"rate_control": "CBR", "bitrate": 1000, "preset": "ultrafast", "keyint_sec": 1}
    for encoder in ("recordEncoder", "streamEncoder"):
        (profile / f"{encoder}.json").write_text(json.dumps(settings))
    (profile / "service.json").write_text(json.dumps({"type": "rtmp_custom", "settings": {
        "server": "rtmp://127.0.0.1:1935/live", "key": "tracks"}}))
    (root / "plugin_config/obs-websocket/config.json").write_text(json.dumps({
        "server_enabled": True, "server_port": port, "auth_required": False,
        "first_load": False, "alerts_enabled": False}))
    if bridge:
        (root / "basic/scenes/Tracks.json").write_text(json.dumps({"name": "Tracks", "sources": [],
            "modules": {"scripts-tool": [{"path": str(Path(__file__).with_name("ui_bridge.py")),
                                          "settings": {"directory": str(bridge)}}]}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("recordings", type=Path)
    parser.add_argument("--tracks", type=int, choices=(6, 12), default=12)
    parser.add_argument("--port", type=int, default=4455)
    parser.add_argument("--bridge", type=Path)
    args = parser.parse_args()
    prepare(args.directory, args.recordings, args.tracks, args.port, args.bridge)
