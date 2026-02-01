#!/usr/bin/env bash
# run.sh — запуск Python-wizard с предварительной подготовкой окружения (AUTO mode)
# Usage: bash run.sh [--quiet]
# Env: QUIET_BOOT=0 to disable quiet mode (verbose startup)

WIZ_PY="${WIZ_PY:-lora_wizard.py}"           # основной Python-скрипт wizard
WIZ_SH="${WIZ_SH:-lora_wizard_nihao.sh}"     # оболочка (bash) для wizard

fix_crlf() {
  local f="$1"
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" || true
    chmod +x "$f" || true
  fi
}

# Исправляем CRLF -> LF для всех скриптов .sh, .py и .toml в текущей директории
fix_crlf "$0"
fix_crlf "$WIZ_SH"
fix_crlf "$WIZ_PY"
for f in ./*.sh ./*.py ./*.toml; do
  [ -e "$f" ] || continue
  fix_crlf "$f"
done

# Проверка и установка зависимостей (только для Debian/Ubuntu при наличии root)
need_cmd() { command -v "$1" >/dev/null 2>&1; }
is_root() { [ "$(id -u 2>/dev/null || echo 9999)" -eq 0 ]; }
if is_root && need_cmd apt-get; then
  # apt-based Linux с правами root: пытаемся установить отсутствующие пакеты
  if ! need_cmd git || ! need_cmd git-lfs || ! need_cmd python3 || ! need_cmd pip3; then
    echo "[INFO] Installing required system packages..." 
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y >/dev/null 2>&1 || apt update -y >/dev/null 2>&1
    apt-get install -y git git-lfs python3 python3-pip ca-certificates >/dev/null 2>&1 || apt install -y git git-lfs python3 python3-pip ca-certificates >/dev/null 2>&1
  fi
  if ! need_cmd hf; then
    echo "[INFO] Installing Hugging Face CLI (huggingface_hub)..."
    python3 -m pip install -U huggingface_hub >/dev/null 2>&1
  fi
fi

# Запуск основного wizard-скрипта (Python)
# Передаем аргументы (--quiet поддерживается) и сохраняем QUIET_BOOT если указан
if [ "${QUIET_BOOT:-1}" = "1" ]; then
  exec python3 "$WIZ_PY" --quiet "$@"
else
  exec python3 "$WIZ_PY" "$@"
fi
