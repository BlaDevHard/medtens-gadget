# Changelog

Todas as mudanças notáveis deste projeto serão documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adere a [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.2.0] — 2026-04-18

### Adicionado
- Decoração nativa do Sistema Operacional (OS) — botões de minimizar e
  fechar desenhados pelo window manager.
- Menu de contexto com submenu "Posicionar" oferecendo snap para os
  quatro cantos da tela e centralizar (usa `availableGeometry`, respeita
  a barra de tarefas/painel do OS).
- Item "Minimizar" no menu de contexto (atalho adicional aos botões
  nativos); janela minimiza para a taskbar/dock normal do OS.
- Título da janela "MedTens — Antonina-PR".

### Alterado
- Janela deixou de ser frameless e translúcida — agora é uma janela
  decorada normal, mantendo `WindowStaysOnTopHint`.
- `Qt.WindowType.Tool` substituído por `Qt.WindowType.Window` para que
  a janela apareça corretamente na taskbar quando minimizada.
- Fundo do card agora é opaco sólido (`#111827`), sem transparência.

### Removido
- Handlers de arraste manual por mouse (`mousePressEvent`,
  `mouseMoveEvent`, `mouseReleaseEvent`) e estado `_drag_pos` —
  redundantes com a decoração nativa.
- `Qt.WidgetAttribute.WA_TranslucentBackground`.
- Imports não utilizados (`QPoint`, `QMouseEvent`, `QColor`, `QFont`).

## [0.1.0] — 2026-04-17

### Adicionado
- Leitor UART em `QThread` separado (`SerialReader`) com reconexão automática e
  *backoff* de 2 s.
- Parser de linhas emitidas pelo firmware ATmega328P: `Tensao AC: X V` e
  `QUEDA NA REDE`.
- Janela `GadgetWindow` frameless, sempre-no-topo, com fundo translúcido:
  - Tensão RMS em número grande com cor conforme faixa PRODIST
    (adequada/precária/crítica) para 127 V nominal.
  - Sparkline dos últimos 5 minutos com linha de referência em 127 V.
  - Indicador de status da conexão UART no rodapé.
  - Contador de quedas desde o boot.
  - Arraste com mouse e menu de contexto (resetar contador, fechar).
- Autodetecção de porta serial: tenta `/dev/ttyACM0` e depois `/dev/ttyUSB0`.
- Pacote Python instalável (`pyproject.toml`) com entrypoint `medtens-gadget`.
