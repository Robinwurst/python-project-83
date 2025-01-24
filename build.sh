#!/usr/bin/env bash
# Устанавливаем uv, если он ещё не установлен
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Добавляем uv в PATH
export PATH="$HOME/.local/bin:$PATH"

# Устанавливаем зависимости
uv sync