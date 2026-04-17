# MedTens Gadget

Widget de desktop para monitoramento em tempo real do sistema **MedTens**
(qualidade de energia elétrica — Antonina-PR). Exibe tensão RMS instantânea,
sparkline dos últimos 5 minutos, status da conexão e contador de quedas.

## Fonte de dados

Nesta versão inicial, lê o **firmware ATmega328P** diretamente pela UART
(`/dev/ttyUSB0`, 9600 8N1). O firmware publica linhas como:

```
Tensao AC: 127.43 V
QUEDA NA REDE
```

Versões futuras substituirão a fonte UART por MQTT (quando o gateway ESP01
estiver pronto) sem alterar a camada de UI.

## Requisitos

- Python 3.10+
- Usuário no grupo `dialout` (para ler `/dev/ttyUSB0` sem `sudo`)
- Dependências: `PyQt6`, `pyserial`, `pyqtgraph`

## Instalação

```bash
cd ~/Projetos/medtens-gadget
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Execução

```bash
source .venv/bin/activate
medtens-gadget                        # autodetecta /dev/ttyACM0 → /dev/ttyUSB0
medtens-gadget --port /dev/ttyUSB1    # porta explícita
medtens-gadget --baud 9600            # baud customizado
```

Arraste o widget com o mouse para reposicionar. Clique-direito para menu
(fechar, fixar posição, resetar contador).

## Arquitetura

```
┌────────────┐  UART 9600   ┌──────────────┐   sinal Qt    ┌──────────────┐
│ ATmega328P │ ───────────► │ SerialReader │ ────────────► │ GadgetWindow │
│ /dev/ttyUSB0│             │  QThread     │               │  PyQt6       │
└────────────┘              └──────────────┘               └──────────────┘
```

- `SerialReader` roda em `QThread` separado (não bloqueia a UI)
- `GadgetWindow` é frameless, sempre-no-topo, fundo translúcido
- Comunicação thread↔UI via sinais Qt (thread-safe)

## Licença

A definir.
