"""Keep a process group owned until the supervisor closes its control pipe."""

import os
import signal


def main() -> None:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    os.write(1, b"1")
    while os.read(0, 4096):
        pass


if __name__ == "__main__":
    main()
