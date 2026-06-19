#!/bin/bash
# ami-assemble.sh — склеить зашифрованные части ami-home

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Собираю ami-home.tar.gz.gpg из частей..."
cat ami-part-gpg_* > ami-home.tar.gz.gpg
echo "✅ Файл собран: $(ls -lh ami-home.tar.gz.gpg | awk '{print $5}')"

echo ""
echo "🔓 Расшифровка (пароль спросит):"
echo "  gpg -d ami-home.tar.gz.gpg | tar -xzf -"
echo ""
echo "Или в два шага:"
echo "  gpg -o ami-home.tar.gz -d ami-home.tar.gz.gpg"
echo "  tar -xzf ami-home.tar.gz"