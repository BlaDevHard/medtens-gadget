"""Leitor UART em QThread — parseia linhas do firmware ATmega."""
from __future__ import annotations

import re
import time

import serial
from PyQt6.QtCore import QThread, pyqtSignal

# Exemplos de linhas do firmware:
#   "Tensao AC: 127.43 V"
#   "QUEDA NA REDE"
_RE_VRMS = re.compile(r"Tensao AC:\s*([-+]?\d+\.?\d*)\s*V", re.IGNORECASE)
_RE_QUEDA = re.compile(r"QUEDA NA REDE", re.IGNORECASE)


class SerialReader(QThread):
    """Lê linhas da UART e emite sinais Qt com as medições.

    Sinais:
        vrms_received(float): tensão RMS em Volts
        outage(): detectou "QUEDA NA REDE"
        connection_changed(bool, str): True=conectado, str=mensagem
    """

    vrms_received = pyqtSignal(float)
    outage = pyqtSignal()
    connection_changed = pyqtSignal(bool, str)

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 9600, parent=None):
        super().__init__(parent)
        self._port = port
        self._baud = baud
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        while not self._stop:
            try:
                with serial.Serial(self._port, self._baud, timeout=1) as ser:
                    self.connection_changed.emit(True, f"{self._port} @ {self._baud}")
                    buf = b""
                    while not self._stop:
                        chunk = ser.read(128)
                        if chunk:
                            buf += chunk
                            while b"\n" in buf:
                                line, _, buf = buf.partition(b"\n")
                                self._parse(line.decode("ascii", errors="replace").strip())
            except serial.SerialException as exc:
                self.connection_changed.emit(False, f"{exc}")
                # backoff antes de tentar reconectar
                for _ in range(20):
                    if self._stop:
                        return
                    time.sleep(0.1)

    def _parse(self, line: str) -> None:
        if not line:
            return
        if _RE_QUEDA.search(line):
            self.outage.emit()
            return
        m = _RE_VRMS.search(line)
        if m:
            try:
                self.vrms_received.emit(float(m.group(1)))
            except ValueError:
                pass
