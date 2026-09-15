"""Check a long UTF-8 track name in native Hybrid MOV and Hybrid MP4."""

import argparse
import json
from pathlib import Path

from integration import OBS, record
from matrix import configure
from ui_client import UI
from verify_media import inspect


def audio_handlers(data, start=0, end=None):
    """Read native handler boxes independently of FFmpeg's signed-char parser."""
    end = len(data) if end is None else end
    while start < end:
        size = int.from_bytes(data[start:start + 4], "big")
        kind = data[start + 4:start + 8]
        header = 8
        if size == 1:
            size = int.from_bytes(data[start + 8:start + 16], "big")
            header = 16
        elif size == 0:
            size = end - start
        assert size >= header and start + size <= end
        if kind in (b"moov", b"trak", b"mdia"):
            yield from audio_handlers(data, start + header, start + size)
        elif kind == b"hdlr" and data[start + header + 8:start + header + 12] == b"soun":
            yield data[start + header + 24:start + size]
        start += size


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ui", default="/work/ui")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    obs, ui = OBS(), UI(args.ui)
    name = "트랙 12 " + "마이크😀" * 35
    encoded = name.encode("utf-8")
    shortened = encoded[:255].decode("utf-8", errors="ignore")
    old_name = obs.call("GetProfileParameter", {"parameterCategory": "AdvOut", "parameterName": "Track12Name"})["parameterValue"]
    try:
        for format_name in ("hybrid_mov", "hybrid_mp4"):
            values = {"outputMode": "Advanced", "advOutRecType": "Standard", "advOutRecFormat": format_name,
                      "advOutRecAEncoder": "ffmpeg_aac", "advOutRecPath": str(args.directory), "advOutTrack12Name": name}
            values.update({f"advOutRecTrack{i}": i == 12 for i in range(1, 13)})
            configure(ui, values)
            result = record(obs, 8)
            path = Path(result["recording"])
            expected = shortened if format_name == "hybrid_mov" else name
            # FFmpeg 6.1's MOV reader treats Pascal lengths >=128 as signed
            # characters. Validate the actual serialized name for this case.
            result["inspection"] = inspect(path, [12], names=[name] if format_name == "hybrid_mp4" else None, video_sync=True)
            data = path.read_bytes()
            handlers = list(audio_handlers(data))
            assert len(handlers) == 1
            payload = handlers[0]
            if format_name == "hybrid_mov":
                assert payload[0] == len(payload) - 1 <= 255
                assert payload[1:].decode("utf-8") == shortened
            else:
                assert payload == encoded + b"\0"
            assert encoded in data, "Original name is missing from the track metadata"
            result.update(original_name=name, handler_name=expected, original_bytes=len(encoded), handler_bytes=len(expected.encode("utf-8")))
            (args.directory / f"{format_name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(f"PASS {format_name}: UTF-8 handler {len(expected.encode('utf-8'))} bytes; full name retained", flush=True)
    finally:
        configure(ui, {"advOutTrack12Name": old_name, "advOutRecFormat": "mkv"})
