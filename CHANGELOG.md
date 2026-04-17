# Changelog

Todas as mudanças notáveis deste projeto serão documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adere a [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
