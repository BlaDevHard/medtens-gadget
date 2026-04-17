"""Ponto de entrada do gadget."""
from __future__ import annotations

import argparse
import os
import signal
import sys

from PyQt6.QtWidgets import QApplication

from .gadget_window import GadgetWindow
from .serial_reader import SerialReader

# Ordem de autodetecção. ACM vem antes porque o Arduino Uno oficial aparece
# como /dev/ttyACM0 (CDC), enquanto clones com CH340/CP210x aparecem como
# /dev/ttyUSB0.
_AUTODETECT_CANDIDATES = ("/dev/ttyACM0", "/dev/ttyUSB0")


def autodetect_port() -> str:
    """Retorna a primeira porta existente em _AUTODETECT_CANDIDATES.

    Se nenhuma existir, retorna o primeiro candidato mesmo assim — deixa o
    erro de abertura acontecer no SerialReader (que já tem retry+backoff).
    """
    for candidate in _AUTODETECT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return _AUTODETECT_CANDIDATES[0]


def main() -> int:
    parser = argparse.ArgumentParser(prog="medtens-gadget")
    parser.add_argument(
        "--port",
        default=None,
        help="porta serial (padrão: autodetecta entre "
        + ", ".join(_AUTODETECT_CANDIDATES)
        + ")",
    )
    parser.add_argument("--baud", type=int, default=9600, help="baud rate")
    args = parser.parse_args()

    if args.port is None:
        args.port = autodetect_port()
        print(f"[medtens-gadget] porta autodetectada: {args.port}", file=sys.stderr)

    # Ctrl+C fecha o app no terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = GadgetWindow()
    reader = SerialReader(port=args.port, baud=args.baud)
    reader.vrms_received.connect(window.on_vrms)
    reader.outage.connect(window.on_outage)
    reader.connection_changed.connect(window.on_connection)

    window.show()
    reader.start()

    exit_code = app.exec()
    reader.stop()
    reader.wait(2000)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
