#!/bin/bash

# Скрипт для запуска MCP-сервера документации F.A.M.I.L.Y. в фоновом режиме
# Автор: АМИ
# Дата: 18 апреля 2025 г.

# Путь к директории сервера
SERVER_DIR="$(dirname "$(readlink -f "$0")")"

# Переход в директорию сервера
cd "$SERVER_DIR" || exit 1

# Проверка наличия виртуального окружения
if [ -d "../../.venv" ]; then
    echo "Активирую виртуальное окружение..."
    source ../../.venv/bin/activate
fi

# Проверка установленных зависимостей
echo "Проверка зависимостей..."
pip install -r requirements.txt > /dev/null 2>&1

# Проверка, не запущен ли уже сервер
if pgrep -f "python3 server.py" > /dev/null; then
    echo "Сервер уже запущен"
    exit 1
fi

# Запуск сервера в фоновом режиме
echo "Запускаю MCP-сервер документации F.A.M.I.L.Y..."
python3 server.py &
PID=$!

# Проверка успешности запуска
sleep 2
if ps -p $PID > /dev/null; then
    echo "Сервер успешно запущен (PID: $PID)"
    echo "Сервер доступен по адресу: http://localhost:8080"
    echo "Для остановки сервера используйте: kill $PID"
else
    echo "Ошибка запуска сервера"
    exit 1
fi

# Инструкции для VS Code
echo ""
echo "Для интеграции с VS Code используйте конфигурацию из файла:"
echo "vscode_mcp_config.json"