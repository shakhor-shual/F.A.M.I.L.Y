#!/usr/bin/env bash
set -euo pipefail

# ================================================================
# ami-assemble.sh — склеить части, расшифровать, распаковать
#
# Запускать там, куда склонирована ветка ami-home.
# Готовый архив появится рядом как ./AMI/
# ================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ARCHIVE_GPG="ami-home.tar.gz.gpg"
ARCHIVE_TAR="ami-home.tar.gz"

echo "=== 1. Склейка частей ==="
if [ -f "$ARCHIVE_GPG" ]; then
    echo "   Файл $ARCHIVE_GPG уже есть — пропускаем склейку."
else
    cat part_* > "$ARCHIVE_GPG"
    echo "   Склеено: $(du -h "$ARCHIVE_GPG" | cut -f1)"
fi

echo ""
echo "=== 2. Расшифровка ==="
if [ -f "$ARCHIVE_TAR" ]; then
    echo "   Файл $ARCHIVE_TAR уже есть — пропускаем расшифровку."
else
    echo "   Введи пароль (скопируй из сообщения):"
    gpg --batch --yes --decrypt -o "$ARCHIVE_TAR" "$ARCHIVE_GPG"
    echo "   Расшифровано: $(du -h "$ARCHIVE_TAR" | cut -f1)"
fi

echo ""
echo "=== 3. Распаковка ==="
if [ -d "./AMI" ]; then
    echo "   Директория AMI уже существует."
    echo "   Чтобы перезаписать — удали её вручную: rm -rf ./AMI"
else
    tar xzf "$ARCHIVE_TAR"
    echo "   Распаковано: ./AMI/ ($(du -sh ./AMI | cut -f1))"
fi

echo ""
echo "=== Готово ==="
echo "Запусти тестовое окружение:"
echo "  bash ami-test-restore.sh"
