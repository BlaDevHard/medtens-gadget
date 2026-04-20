"""Leitor HTTP em QThread — faz polling no endpoint /json do ESP-01.

Usado quando o Arduino UNO está alimentado por fonte (sem USB) e o
gadget não consegue mais abrir /dev/ttyACM*. O ESP-01 continua recebendo
as linhas UART do UNO e expõe a última leitura em JSON:

    {"v_rms": 127.43, "outage": false, "has_reading": true,
     "age_ms": 812, "fw": "0.1.0"}

Emite exatamente os mesmos sinais do SerialReader para que GadgetWindow
não precise saber qual caminho está ativo.
"""
from __future__ import annotations

import json
import time
from urllib import error as urlerror
from urllib import request as urlrequest

from PyQt6.QtCore import QThread, pyqtSignal


class HttpReader(QThread):
    """Poll periódico em http://<esp>/json.

    Sinais:
        vrms_received(float): tensão RMS em Volts
        outage(): payload marcou outage=true
        connection_changed(bool, str): True=resposta válida, str=status/erro
    """

    vrms_received = pyqtSignal(float)
    outage = pyqtSignal()
    connection_changed = pyqtSignal(bool, str)

    def __init__(self, url: str, interval: float = 1.0, timeout: float = 2.0,
                 parent=None):
        super().__init__(parent)
        self._url = url
        self._interval = interval
        self._timeout = timeout
        self._stop = False
        self._was_outage = False  # evita emitir outage repetido em cada poll
        self._last_ok = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        while not self._stop:
            t0 = time.monotonic()
            try:
                with urlrequest.urlopen(self._url, timeout=self._timeout) as resp:
                    raw = resp.read()
                payload = json.loads(raw.decode("utf-8", errors="replace"))
                self._handle(payload)
            except (urlerror.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                if self._last_ok or not self._stop:
                    self.connection_changed.emit(False, f"HTTP: {exc}")
                self._last_ok = False

            # espera o restante do intervalo, checando stop a cada 100 ms
            remaining = self._interval - (time.monotonic() - t0)
            while remaining > 0 and not self._stop:
                step = min(0.1, remaining)
                time.sleep(step)
                remaining -= step

    def _handle(self, payload: dict) -> None:
        if not self._last_ok:
            self.connection_changed.emit(True, f"HTTP {self._url}")
            self._last_ok = True

        is_outage = bool(payload.get("outage"))
        has_reading = bool(payload.get("has_reading"))
        v_rms = payload.get("v_rms")

        if is_outage:
            # só emite na borda: passou de não-outage para outage
            if not self._was_outage:
                self.outage.emit()
            self._was_outage = True
            return

        self._was_outage = False
        if has_reading and isinstance(v_rms, (int, float)):
            try:
                self.vrms_received.emit(float(v_rms))
            except (TypeError, ValueError):
                pass
