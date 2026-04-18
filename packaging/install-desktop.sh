#!/usr/bin/env bash
# Instala o ícone e a entry .desktop do MedTens Gadget no usuário corrente.
#
# Uso:
#   ./packaging/install-desktop.sh             # Exec=medtens-gadget (assume PATH)
#   ./packaging/install-desktop.sh --venv      # Exec aponta para .venv/bin/medtens-gadget do repo
#
# Desinstalar:
#   ./packaging/install-desktop.sh --uninstall

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICON_SRC="${REPO_ROOT}/medtens_gadget/assets/icon.svg"
DESKTOP_SRC="${REPO_ROOT}/packaging/medtens-gadget.desktop"

ICON_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DEST="${ICON_DIR}/medtens-gadget.svg"
DESKTOP_DEST="${DESKTOP_DIR}/medtens-gadget.desktop"

uninstall() {
    rm -f "${ICON_DEST}" "${DESKTOP_DEST}"
    echo "Removido: ${ICON_DEST}"
    echo "Removido: ${DESKTOP_DEST}"
    (gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true)
    (update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true)
    echo "Pronto. Desinstalado."
}

install() {
    local exec_cmd="medtens-gadget"
    if [[ "${1:-}" == "--venv" ]]; then
        exec_cmd="${REPO_ROOT}/.venv/bin/medtens-gadget"
        if [[ ! -x "${exec_cmd}" ]]; then
            echo "AVISO: ${exec_cmd} não existe. Crie o venv e instale com 'pip install -e .' antes." >&2
        fi
    fi

    mkdir -p "${ICON_DIR}" "${DESKTOP_DIR}"
    cp "${ICON_SRC}" "${ICON_DEST}"
    sed "s|^Exec=.*|Exec=${exec_cmd}|" "${DESKTOP_SRC}" > "${DESKTOP_DEST}"
    chmod 644 "${ICON_DEST}" "${DESKTOP_DEST}"

    (gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true)
    (update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true)

    echo "Ícone  instalado em: ${ICON_DEST}"
    echo ".desktop instalado em: ${DESKTOP_DEST}"
    echo "Exec:  ${exec_cmd}"
    echo
    echo "Pronto. Procure por 'MedTens' no menu de aplicações."
}

case "${1:-}" in
    --uninstall) uninstall ;;
    *)           install "${1:-}" ;;
esac
