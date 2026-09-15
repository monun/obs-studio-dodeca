"""Check that portable test profiles use OBS's UTF-8 configuration encoding."""

import configparser
from pathlib import Path
import tempfile
import unittest

from prepare import prepare


class PrepareTests(unittest.TestCase):
    def test_unicode_recording_path(self):
        with tempfile.TemporaryDirectory(prefix="obs-audio-tracks-") as directory:
            for tracks in (6, 12):
                with self.subTest(tracks=tracks):
                    root = Path(directory) / "한글 시험" / str(tracks)
                    recordings = root / "녹화"
                    prepare(root / "config", recordings, tracks=tracks)
                    profile = root / "config/obs-studio/basic/profiles/Tracks/basic.ini"
                    settings = configparser.ConfigParser()
                    settings.read_string(profile.read_text(encoding="utf-8"))
                    self.assertEqual(settings["AdvOut"]["RecFilePath"], str(recordings))
                    self.assertEqual(settings.getint("AdvOut", "RecTracks"), (1 << tracks) - 1)


if __name__ == "__main__":
    unittest.main()
