#!/usr/bin/env python3
"""
Утилита командной строки для инициализации АМИ.
Аналог AMI_init.sh
"""

import sys
import argparse
import logging
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from undermaind.utils.ami_init import AmiInitializer

def main():
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(
        description="Инициализация АМИ в базе данных F.A.M.I.L.Y."
    )
    
    parser.add_argument(
        "-c", "--config",
        help="Путь к файлу конфигурации (по умолчанию: ./family_db.conf)",
        default="./family_db.conf"
    )
    parser.add_argument(
        "-u", "--ami-user",
        help="Имя пользователя АМИ",
        required=True
    )
    parser.add_argument(
        "-p", "--ami-pass",
        help="Пароль пользователя АМИ"
    )
    parser.add_argument(
        "-D", "--drop",
        help="Удалить существующего АМИ",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--force",
        help="Принудительное удаление (с -D), даже если есть активные подключения",
        action="store_true"
    )

    args = parser.parse_args()

    # Проверяем, что пароль указан при создании АМИ
    if not args.drop and not args.ami_pass:
        parser.error("Пароль (-p) обязателен при создании АМИ")

    try:
        # Создаем инициализатор
        initializer = AmiInitializer(
            ami_name=args.ami_user,
            ami_password=args.ami_pass,
            config_path=args.config
        )

        # Выполняем операцию в зависимости от параметров
        if args.drop:
            if initializer.drop_ami(force=args.force):
                logging.info(f"АМИ {args.ami_user} успешно удален")
                sys.exit(0)
            else:
                logging.error(f"Ошибка при удалении АМИ {args.ami_user}")
                sys.exit(1)
        else:
            if initializer.create_ami():
                logging.info(f"АМИ {args.ami_user} успешно создан")
                sys.exit(0)
            else:
                logging.error(f"Ошибка при создании АМИ {args.ami_user}")
                sys.exit(1)

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()