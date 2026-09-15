"""Decode every OBS test track and check tone identity, separation and sync gates."""

import argparse
import json
import subprocess
from pathlib import Path
from fractions import Fraction

import numpy as np


def run(*args):
    return subprocess.check_output(args)


def inspect(path, tracks, starts=(0,), seconds=8, names=None, video_sync=False):
    probe = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)))
    audio = [stream for stream in probe["streams"] if stream["codec_type"] == "audio"]
    assert len(audio) == len(tracks), (path, len(audio), tracks)
    titles = [stream.get("tags", {}).get("title", stream.get("tags", {}).get("handler_name")) for stream in audio]
    if names is not None:
        assert titles == names, (path, "track names", titles, names)
    # AAC uses 1024 samples; the OBS Opus encoder uses 20 ms packets.
    codec_ms = max(1024 * 1000 / int(s["sample_rate"]) if s["codec_name"] == "aac" else 20 for s in audio)
    tick_ms = max(float(Fraction(s["time_base"])) * 1000 for s in audio)
    tolerance_ms = codec_ms + tick_ms + 1  # 1 ms envelope measurement resolution
    report = {"path": str(path), "bytes": path.stat().st_size, "streams": audio, "windows": []}
    for start in starts:
        window = {"start": start, "tracks": []}
        envelopes = []
        for index, track in enumerate(tracks):
            raw = run("ffmpeg", "-v", "error", "-ss", str(start), "-i", str(path), "-t", str(seconds),
                      "-map", f"0:a:{index}", "-ac", "1", "-ar", "48000", "-f", "f32le", "-")
            samples = np.frombuffer(raw, dtype="<f4")
            assert len(samples) >= 48000, (path, track, "not enough decoded audio")
            assert np.isfinite(samples).all()
            expected = 300 + 100 * (track - 1)
            spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
            frequencies = np.fft.rfftfreq(len(samples), 1 / 48000)
            peak = float(frequencies[spectrum.argmax()])
            assert abs(peak - expected) < 2, (path, track, peak, expected)
            signal = spectrum[(frequencies > expected - 2) & (frequencies < expected + 2)].max()
            other = max(spectrum[(frequencies > freq - 2) & (frequencies < freq + 2)].max()
                        for freq in range(300, 1401, 100) if freq != expected)
            separation = float(20 * np.log10(max(other, 1e-12) / signal))
            assert separation < -35, (path, track, "crosstalk", separation)
            blocks = samples[:len(samples) // 48 * 48].reshape(-1, 48)
            envelope = np.sqrt(np.mean(blocks ** 2, axis=1))
            envelopes.append(envelope > envelope.max() * 0.2)
            tags = audio[index].get("tags", {})
            window["tracks"].append({"track": track, "frequency": peak, "other_tones_db": separation,
                                     "title": tags.get("title", tags.get("handler_name"))})
        # Each binary envelope represents 1 ms of decoded PCM.
        reference = np.flatnonzero(np.diff(envelopes[0].astype(int)) > 0)
        reference = reference[(reference > 250) & (reference < len(envelopes[0]) - 250)]
        assert len(reference), "Missing synchronization pulses"
        errors = []
        for envelope in envelopes[1:]:
            edges = np.flatnonzero(np.diff(envelope.astype(int)) > 0)
            assert len(edges) and len(reference), "Missing synchronization pulses"
            errors.extend(float(np.min(abs(edges - edge))) for edge in reference)
        max_error = max(errors, default=0)
        assert max_error <= tolerance_ms, (path, "inter-track sync", max_error, tolerance_ms)
        window["max_intertrack_ms"] = max_error
        if video_sync:
            video = next(s for s in probe["streams"] if s["codec_type"] == "video")
            fps = float(Fraction(video["avg_frame_rate"]))
            raw = run("ffmpeg", "-v", "error", "-ss", str(start), "-i", str(path), "-t", str(seconds),
                      "-map", "0:v:0", "-vf", "crop=32:32:0:0,scale=1:1", "-pix_fmt", "gray", "-f", "rawvideo", "-")
            pixels = np.frombuffer(raw, dtype=np.uint8)
            edges = (np.flatnonzero(np.diff((pixels > 128).astype(int)) > 0) + 1) * 1000 / fps
            assert len(edges), "Missing video synchronization pulses"
            # A delayed custom FFmpeg video encoder can end before the audio.
            # Compare synchronization only where both decoded streams exist.
            common_ms = min(len(envelopes[0]), len(pixels) * 1000 / fps)
            video_reference = reference[reference < common_ms - 250]
            assert len(video_reference), "No shared audio/video synchronization pulses"
            video_errors = [float(np.min(abs(edges - edge - 1))) for edge in video_reference]
            window["audio_window_ms"] = len(envelopes[0])
            window["video_window_ms"] = len(pixels) * 1000 / fps
            window["compared_video_pulses"] = len(video_reference)
            window["max_audio_video_ms"] = max(video_errors, default=0)
            assert window["max_audio_video_ms"] <= tolerance_ms + 1000 / fps, (path, "audio/video sync", window)
        report["windows"].append(window)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--tracks", default=",".join(map(str, range(1, 13))))
    parser.add_argument("--starts", default="0")
    parser.add_argument("--names", help="Comma-separated expected names in file stream order")
    parser.add_argument("--video-sync", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.file, list(map(int, args.tracks.split(","))), list(map(float, args.starts.split(","))),
                     names=args.names.split(",") if args.names else None, video_sync=args.video_sync)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"file": str(args.file), "audio_streams": len(result["streams"]),
                      "windows": [{"start": w["start"], "max_intertrack_ms": w["max_intertrack_ms"]}
                                  for w in result["windows"]]}))


if __name__ == "__main__":
    main()
