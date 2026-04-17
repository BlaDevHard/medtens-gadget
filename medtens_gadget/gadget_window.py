"""Janela do gadget — frameless, sempre-no-topo, arrastável."""
from __future__ import annotations

import time
from collections import deque

import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QAction, QColor, QFont, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

# Classificação PRODIST 8 para tensão nominal 127 V (leitura de tensão atendida)
# Faixas adaptadas (valores de referência; ajustar conforme calibração):
#   Adequada: 117 a 133 V
#   Precária: 110 a 116 V  ou  134 a 135 V
#   Crítica : < 110 V  ou  > 135 V
V_NOMINAL = 127.0
LIM_ADEQUADA = (117.0, 133.0)
LIM_PRECARIA = (110.0, 135.0)

WINDOW_SECONDS = 300  # 5 minutos


def classify(v: float) -> str:
    """Retorna 'adequada' | 'precaria' | 'critica' | 'queda'."""
    if v < 10.0:
        return "queda"
    if LIM_ADEQUADA[0] <= v <= LIM_ADEQUADA[1]:
        return "adequada"
    if LIM_PRECARIA[0] <= v <= LIM_PRECARIA[1]:
        return "precaria"
    return "critica"


_COLOR = {
    "adequada": "#4ade80",   # verde
    "precaria": "#facc15",   # amarelo
    "critica":  "#f87171",   # vermelho
    "queda":    "#a78bfa",   # roxo (sem dados)
    "offline":  "#6b7280",   # cinza
}


class GadgetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(280, 180)

        # Estado
        self._times: deque[float] = deque()
        self._vrms: deque[float] = deque()
        self._outage_count = 0
        self._connected = False
        self._last_vrms: float | None = None
        self._drag_pos: QPoint | None = None

        self._build_ui()

        # Timer para "envelhecimento" do gráfico
        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._prune_and_redraw)
        self._tick.start()

        # Heartbeat para detectar UART silenciosa
        self._last_data_ts = 0.0
        self._stale_timer = QTimer(self)
        self._stale_timer.setInterval(2000)
        self._stale_timer.timeout.connect(self._check_stale)
        self._stale_timer.start()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self._card = QFrame(self)
        self._card.setObjectName("card")
        self._card.setStyleSheet(
            """
            QFrame#card {
                background-color: rgba(17, 24, 39, 220);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 12px;
            }
            QLabel { color: #e5e7eb; }
            QLabel#vrms { font-size: 48px; font-weight: 700; }
            QLabel#unit { font-size: 18px; color: #9ca3af; }
            QLabel#status, QLabel#outages, QLabel#classe {
                font-size: 11px; color: #9ca3af;
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._card)

        v = QVBoxLayout(self._card)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(4)

        # Título
        title = QLabel("MedTens — Antonina-PR")
        title.setStyleSheet("font-size:11px; color:#9ca3af; font-weight:600;")
        v.addWidget(title)

        # Leitura grande
        row = QHBoxLayout()
        row.setSpacing(6)
        self._vrms_label = QLabel("—")
        self._vrms_label.setObjectName("vrms")
        self._vrms_label.setStyleSheet(f"color: {_COLOR['offline']};")
        row.addWidget(self._vrms_label, 0, Qt.AlignmentFlag.AlignBottom)
        unit = QLabel("V")
        unit.setObjectName("unit")
        row.addWidget(unit, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        self._class_label = QLabel("aguardando…")
        self._class_label.setObjectName("classe")
        row.addWidget(self._class_label, 0, Qt.AlignmentFlag.AlignBottom)
        v.addLayout(row)

        # Sparkline
        pg.setConfigOptions(antialias=True)
        self._plot = pg.PlotWidget()
        self._plot.setFixedHeight(60)
        self._plot.setBackground(None)
        self._plot.hideAxis("left")
        self._plot.hideAxis("bottom")
        self._plot.showGrid(x=False, y=False)
        self._curve = self._plot.plot(pen=pg.mkPen(color=_COLOR["adequada"], width=2))
        # Linhas de referência
        self._plot.addLine(y=V_NOMINAL, pen=pg.mkPen(color="#6b7280", style=Qt.PenStyle.DashLine, width=1))
        v.addWidget(self._plot)

        # Rodapé
        footer = QHBoxLayout()
        self._status_label = QLabel("● offline")
        self._status_label.setObjectName("status")
        self._status_label.setStyleSheet(f"color: {_COLOR['offline']};")
        footer.addWidget(self._status_label)
        footer.addStretch(1)
        self._outage_label = QLabel("quedas: 0")
        self._outage_label.setObjectName("outages")
        footer.addWidget(self._outage_label)
        v.addLayout(footer)

    # ---------- Slots ----------
    def on_vrms(self, v: float) -> None:
        now = time.monotonic()
        self._last_data_ts = now
        self._times.append(now)
        self._vrms.append(v)
        self._last_vrms = v
        self._prune_and_redraw()

        cls = classify(v)
        self._vrms_label.setText(f"{v:.1f}")
        self._vrms_label.setStyleSheet(f"color: {_COLOR[cls]};")
        self._class_label.setText(cls)
        self._curve.setPen(pg.mkPen(color=_COLOR[cls], width=2))

    def on_outage(self) -> None:
        self._outage_count += 1
        self._outage_label.setText(f"quedas: {self._outage_count}")
        self._last_data_ts = time.monotonic()
        self._vrms_label.setText("⚡")
        self._vrms_label.setStyleSheet(f"color: {_COLOR['queda']};")
        self._class_label.setText("queda")

    def on_connection(self, ok: bool, msg: str) -> None:
        self._connected = ok
        if ok:
            self._status_label.setText(f"● {msg}")
            self._status_label.setStyleSheet("color: #4ade80; font-size:11px;")
        else:
            self._status_label.setText(f"● {msg[:40]}")
            self._status_label.setStyleSheet(f"color: {_COLOR['offline']}; font-size:11px;")

    # ---------- Internos ----------
    def _prune_and_redraw(self) -> None:
        now = time.monotonic()
        cutoff = now - WINDOW_SECONDS
        while self._times and self._times[0] < cutoff:
            self._times.popleft()
            self._vrms.popleft()
        if self._times:
            xs = [t - now for t in self._times]  # tempo relativo (negativo = passado)
            self._curve.setData(xs, list(self._vrms))

    def _check_stale(self) -> None:
        if self._last_data_ts == 0:
            return
        if time.monotonic() - self._last_data_ts > 5.0 and self._connected:
            self._vrms_label.setStyleSheet(f"color: {_COLOR['offline']};")
            self._class_label.setText("sem dados")

    def reset_counter(self) -> None:
        self._outage_count = 0
        self._outage_label.setText("quedas: 0")

    # ---------- Drag & menu ----------
    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_pos is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._drag_pos = None

    def contextMenuEvent(self, e) -> None:
        menu = QMenu(self)
        act_reset = QAction("Resetar contador de quedas", self)
        act_reset.triggered.connect(self.reset_counter)
        menu.addAction(act_reset)
        menu.addSeparator()
        act_close = QAction("Fechar", self)
        act_close.triggered.connect(self.close)
        menu.addAction(act_close)
        menu.exec(e.globalPos())
