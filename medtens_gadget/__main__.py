"""Ponto de entrada do gadget."""
from __future__ import annotations

import argparse
import os
import signal
import sys

from importlib import resources

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .gadget_window import GadgetWindow
from .http_reader import HttpReader
from .serial_reader import SerialReader


def _load_app_icon() -> QIcon:
    """Carrega o ícone empacotado em medtens_gadget/assets/icon.svg.

    Usa importlib.resources para funcionar tanto em instalação editável
    quanto em wheel/pip install.
    """
    try:
        path = resources.files("medtens_gadget").joinpath("assets/icon.svg")
        with resources.as_file(path) as real_path:
            return QIcon(str(real_path))
    except (FileNotFoundError, ModuleNotFoundError):
        # Fallback: ícone do tema do sistema (instalado via .local/share/icons)
        return QIcon.fromTheme("medtens-gadget")

# Ordem de autodetecção. ACM vem antes porque o Arduino Uno oficial aparece
# como /dev/ttyACM0 (CDC), enquanto clones com CH340/CP210x aparecem como
# /dev/ttyUSB0.
_AUTODETECT_CANDIDATES = ("/dev/ttyACM0", "/dev/ttyUSB0")

# Fallback HTTP: ESP-01 do MedTens na LAN local. Quando o UNO roda por fonte
# sem USB, /dev/ttyACM* some e o gadget passa a ler via ESP.
_DEFAULT_HTTP_URL = "http://192.168.1.18/json"


def autodetect_port() -> str | None:
    """Retorna a primeira porta existente em _AUTODETECT_CANDIDATES.

    Retorna None se nenhuma existir — nesse caso o chamador deve optar
    pelo caminho HTTP.
    """
    for candidate in _AUTODETECT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser(prog="medtens-gadget")
    parser.add_argument(
        "--port",
        default=None,
        help="porta serial (padrão: autodetecta entre "
        + ", ".join(_AUTODETECT_CANDIDATES)
        + "; se nada for encontrado, usa HTTP)",
    )
    parser.add_argument("--baud", type=int, default=9600, help="baud rate")
    parser.add_argument(
        "--http",
        default=None,
        help=(
            "URL do endpoint /json do ESP-01. Se usada, força modo HTTP "
            f"(padrão como fallback: {_DEFAULT_HTTP_URL})"
        ),
    )
    parser.add_argument(
        "--http-interval",
        type=float,
        default=1.0,
        help="intervalo de polling HTTP em segundos (padrão 1.0)",
    )
    args = parser.parse_args()

    # Resolve modo: explícito por --http > explícito por --port > autodetect
    use_http = False
    http_url = args.http or _DEFAULT_HTTP_URL
    if args.http is not None:
        use_http = True
    elif args.port is not None:
        use_http = False
    else:
        detected = autodetect_port()
        if detected is None:
            use_http = True
            print(
                f"[medtens-gadget] nenhuma porta serial em "
                f"{', '.join(_AUTODETECT_CANDIDATES)}; usando HTTP {http_url}",
                file=sys.stderr,
            )
        else:
            args.port = detected
            print(f"[medtens-gadget] porta autodetectada: {args.port}", file=sys.stderr)

    # Ctrl+C fecha o app no terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("MedTens Gadget")
    app.setDesktopFileName("medtens-gadget")

    icon = _load_app_icon()
    app.setWindowIcon(icon)

    window = GadgetWindow()
    window.setWindowIcon(icon)

    if use_http:
        reader = HttpReader(url=http_url, interval=args.http_interval)
    else:
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
