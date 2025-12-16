from src.core.engine import Engine
from src.utils import GameSettings
import sys


def _apply_cli_args(argv: list[str]) -> None:
    # Enable online mode with --online or -o
    if any(a in ("--online", "-o") for a in argv):
        GameSettings.IS_ONLINE = True

    # Allow overriding server URL: --server=<url> or --server <url>
    for i, a in enumerate(argv):
        if a.startswith("--server="):
            GameSettings.ONLINE_SERVER_URL = a.split("=", 1)[1]
        elif a == "--server" and i + 1 < len(argv):
            GameSettings.ONLINE_SERVER_URL = argv[i + 1]


if __name__ == "__main__":
    _apply_cli_args(sys.argv[1:])
    engine = Engine()
    engine.run()
