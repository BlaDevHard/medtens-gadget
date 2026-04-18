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

A janela usa decoração nativa do Sistema Operacional. Clique-direito
abre menu com:
- Submenu **Posicionar** — snap para os 4 cantos da tela ou centralizar
- **Resetar contador de quedas**
- **Minimizar** / **Fechar**

## Integração com o desktop (ícone e menu)

A partir da versão **0.3.0** o pacote traz um ícone próprio em Scalable
Vector Graphics (SVG) (`medtens_gadget/assets/icon.svg`) e arquivos de
integração em `packaging/`.

### Instalar atalho no menu de aplicações

```bash
./packaging/install-desktop.sh             # Exec=medtens-gadget (usa o que estiver no PATH)
./packaging/install-desktop.sh --venv      # aponta Exec para .venv/bin/medtens-gadget
```

O script copia:
- `medtens_gadget/assets/icon.svg` → `~/.local/share/icons/hicolor/scalable/apps/medtens-gadget.svg`
- `packaging/medtens-gadget.desktop` → `~/.local/share/applications/medtens-gadget.desktop`

e atualiza os caches (`gtk-update-icon-cache`, `update-desktop-database`)
quando disponíveis. Depois disso, o MedTens aparece no menu de
aplicações do GNOME/KDE com o ícone próprio.

### Desinstalar

```bash
./packaging/install-desktop.sh --uninstall
```

### Autostart (opcional)

Para iniciar automaticamente junto com a sessão gráfica, basta copiar o
`.desktop` para `~/.config/autostart/`:

```bash
cp ~/.local/share/applications/medtens-gadget.desktop ~/.config/autostart/
```

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
