"""Keep detecting gaps when ffprobe omits an AAC priming packet duration."""

import io
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from verify_continuity import inspect


class ContinuityTests(unittest.TestCase):
    def inspect_packets(self, packets, **stream_overrides):
        stream = {"index": 0, "codec_name": "aac", "profile": "LC", "sample_rate": "48000",
                  "initial_padding": 1024, **stream_overrides}
        process = MagicMock()
        process.__enter__.return_value = process
        process.stdout = io.StringIO(packets)
        process.wait.return_value = 0
        with patch("verify_continuity.subprocess.check_output", return_value=json.dumps({"streams": [stream]})), \
                patch("verify_continuity.subprocess.Popen", return_value=process):
            return inspect(Path("fixture.mkv"), 1)

    def test_missing_priming_duration(self):
        for first in ("duration_time=N/A", "unused=0"):
            with self.subTest(first=first):
                report = self.inspect_packets(f"stream_index=0|pts_time=-0.021|{first}\n"
                                              "stream_index=0|pts_time=0.000|duration_time=0.021\n"
                                              "stream_index=0|pts_time=0.021|duration_time=0.021\n")
                self.assertEqual(report["tracks"]["0"]["packets"], 3)
                self.assertEqual(report["tracks"]["0"]["inferred_priming_durations"], 1)

    def test_gap_after_priming_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "missing or overlapping packet"):
            self.inspect_packets("stream_index=0|pts_time=-0.021|duration_time=N/A\n"
                                 "stream_index=0|pts_time=0.021|duration_time=0.021\n")

    def test_other_unknown_durations_are_rejected(self):
        cases = [
            ("stream_index=0|pts_time=-0.021|duration_time=N/A\n", {"initial_padding": 0}),
            ("stream_index=0|pts_time=0|duration_time=N/A\n", {}),
            ("stream_index=0|pts_time=-0.021|duration_time=0.021\n"
             "stream_index=0|pts_time=0|duration_time=N/A\n", {}),
        ]
        for packets, overrides in cases:
            with self.subTest(packets=packets, overrides=overrides):
                with self.assertRaisesRegex(AssertionError, "unknown packet duration"):
                    self.inspect_packets(packets, **overrides)


if __name__ == "__main__":
    unittest.main()
