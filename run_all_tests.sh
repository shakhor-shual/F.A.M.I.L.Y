#!/bin/bash

# ============================================================================
# F.A.M.I.L.Y. ALL TESTS RUNNER
# Дата создания: 16 апреля 2025 г.
# ============================================================================
# Скрипт для автоматического запуска всех тестов проекта F.A.M.I.L.Y.
# Ищет и запускает все тесты в папке tests, включая модульные, 
# интеграционные и функциональные.
# ============================================================================

# Цвета для вывода информации
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Символы для вывода
CHECK_MARK="${GREEN}✓${NC}"
CROSS_MARK="${RED}✗${NC}"
INFO_MARK="${BLUE}ℹ${NC}"
WARN_MARK="${YELLOW}⚠${NC}"

# Функции для форматированного вывода
function echo_info() { echo -e "${INFO_MARK} $1"; }
function echo_success() { echo -e "${CHECK_MARK} $1"; }
function echo_warn() { echo -e "${WARN_MARK} $1"; }
function echo_error() { echo -e "${CROSS_MARK} $1"; }

# Счетчики для статистики
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo_error "Python 3 не найден. Пожалуйста, установите Python 3."
    exit 1
fi

# Переходим в корневую директорию проекта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Активируем виртуальное окружение, если оно существует
if [ -d ".venv" ]; then
    echo_info "Активируем виртуальное окружение..."
    source .venv/bin/activate
fi

# Проверяем наличие pytest
if ! python -m pytest --version &> /dev/null; then
    echo_warn "pytest не установлен. Пробуем установить..."
    pip install pytest pytest-cov pytest-mock
    if [ $? -ne 0 ]; then
        echo_error "Не удалось установить pytest. Пожалуйста, установите его вручную (pip install pytest)."
        exit 1
    fi
fi

echo_info "Запускаем все тесты проекта F.A.M.I.L.Y..."
echo_info "Дата запуска: $(date)"
echo "============================================================"

# Функция для запуска тестов в определенной категории
function run_test_category() {
    local category=$1
    local category_path="undermaind/tests/$category"
    
    if [ ! -d "$category_path" ]; then
        return
    fi
    
    # Подсчитываем количество тестовых файлов в категории
    local test_files=$(find "$category_path" -name "test_*.py" | wc -l)
    
    if [ "$test_files" -eq 0 ]; then
        echo_warn "В категории $category не найдено тестов"
        return
    fi
    
    echo_info "Запускаем тесты категории: $category (найдено $test_files файлов)"
    
    # Запускаем тесты для данной категории
    python -m pytest "$category_path" -v
    
    local result=$?
    ((TOTAL_TESTS++))
    
    if [ $result -eq 0 ]; then
        echo_success "Категория тестов $category успешно пройдена"
        ((PASSED_TESTS++))
    else
        echo_error "Категория тестов $category завершилась с ошибками"
        ((FAILED_TESTS++))
    fi
    
    echo "------------------------------------------------------------"
}

# Запускаем тесты по категориям
categories=("core" "models" "services" "utils")

for category in "${categories[@]}"; do
    run_test_category "$category"
done

# Также запускаем все интеграционные тесты
echo_info "Запускаем все интеграционные тесты..."
python -m pytest undermaind/tests -m integration -v

integration_result=$?
((TOTAL_TESTS++))

if [ $integration_result -eq 0 ]; then
    echo_success "Интеграционные тесты успешно пройдены"
    ((PASSED_TESTS++))
else
    echo_error "Интеграционные тесты завершились с ошибками"
    ((FAILED_TESTS++))
fi

echo "============================================================"

# Выводим итоговую статистику
echo_info "Итоги тестирования:"
echo_info "Всего запущено категорий тестов: $TOTAL_TESTS"
echo_success "Успешно пройдено: $PASSED_TESTS"

if [ $FAILED_TESTS -gt 0 ]; then
    echo_error "Не пройдено: $FAILED_TESTS"
else
    echo_success "Не пройдено: $FAILED_TESTS"
fi

# Определяем общий статус
if [ $FAILED_TESTS -eq 0 ]; then
    echo_success "ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!"
    exit 0
else
    echo_error "ЕСТЬ ОШИБКИ В ТЕСТАХ. Пожалуйста, исправьте их."
    exit 1
fi