"""Send local JSON commands to ui_bridge.py loaded in the test OBS instance."""

import argparse
import json
import time
from pathlib import Path


class UI:
    def __init__(self, directory):
        self.directory = Path(directory)

    def call(self, action, **arguments):
        request_id = time.time_ns()
        request = {"id": request_id, "action": action, **arguments}
        temporary = self.directory / "ui-request.tmp"
        temporary.write_text(json.dumps(request))
        temporary.replace(self.directory / "ui-request.json")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            response_path = self.directory / "ui-response.json"
            if response_path.exists():
                response = json.loads(response_path.read_text())
                if response["id"] == request_id:
                    assert response["success"], response
                    return response
            time.sleep(0.1)
        raise TimeoutError(request)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("command", help="JSON object with action and arguments")
    args = parser.parse_args()
    print(json.dumps(UI(args.directory).call(**json.loads(args.command)), indent=2))
