#!/bin/bash

# Скрипт для запуска MCP-сервера документации F.A.M.I.L.Y. в фоновом режиме
# Автор: АМИ
# Дата: 18 апреля 2025 г.

# Путь к директории сервера
SERVER_DIR="$(dirname "$(readlink -f "$0")")"
LOG_FILE="$SERVER_DIR/documentation_server.log"

# Переход в директорию сервера
cd "$SERVER_DIR" || exit 1

# Проверка наличия виртуального окружения
if [ -d "venv" ]; then
    echo "Активирую виртуальное окружение..."
    source venv/bin/activate
fi

# Проверка установленных зависимостей
echo "Проверка зависимостей..."
pip install -r requirements.txt > /dev/null 2>&1

# Запуск сервера в фоновом режиме
echo "Запускаю MCP-сервер документации F.A.M.I.L.Y..."
nohup python3 run_server.py > "$LOG_FILE" 2>&1 &
PID=$!

# Проверка успешности запуска
sleep 2
if ps -p $PID > /dev/null; then
    echo "Сервер успешно запущен (PID: $PID)"
    echo "Сервер доступен по адресу: http://localhost:8080"
    echo "Логи записываются в файл: $LOG_FILE"
else
    echo "Ошибка запуска сервера. Проверьте логи: $LOG_FILE"
    exit 1
fi

# Инструкции для VS Code
echo ""
echo "Для интеграции с VS Code убедитесь, что в проекте создан файл:"
echo ".vscode/mcp.json"
echo "с конфигурацией для подключения к внешнему HTTP-серверу."
echo ""
echo "Для остановки сервера выполните команду:"
echo "pkill -f \"python3 run_server.py\""