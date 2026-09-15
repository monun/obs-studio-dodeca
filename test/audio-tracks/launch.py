"""Launch a test OBS installation and wait until its local websocket is ready."""

import argparse
import os
import socket
import subprocess
import time
from pathlib import Path

from integration import OBS


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("log", type=Path)
    parser.add_argument("--port", type=int, default=4455)
    parser.add_argument("--scale", default="1")
    parser.add_argument("--executable", type=Path, help="Override the frontend executable for an incremental UI build")
    args = parser.parse_args()
    with socket.socket() as connection:
        assert connection.connect_ex(("127.0.0.1", args.port)) != 0, f"Port {args.port} is already in use"
    environment = dict(os.environ, XDG_CONFIG_HOME=str(args.config), QT_SCALE_FACTOR=args.scale)
    environment["LD_LIBRARY_PATH"] = str(args.installation / "lib/x86_64-linux-gnu")
    environment["PYTHONPATH"] = str(args.installation / "lib/x86_64-linux-gnu/obs-scripting")
    with args.log.open("w") as log:
        process = subprocess.Popen([str(args.executable or args.installation / "bin/obs"), "--multi", "--disable-shutdown-check",
                                    "--disable-missing-files-check"], cwd=args.installation / "bin",
                                   env=environment, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError(f"OBS exited with {process.returncode}; see {args.log}")
        try:
            client = OBS(args.port)
            client.call("GetVersion")
            client.socket.close()
            print(f"OBS ready, pid={process.pid}, port={args.port}")
            break
        except ConnectionRefusedError:
            time.sleep(0.2)
    else:
        raise TimeoutError(f"OBS startup timed out; see {args.log}")
