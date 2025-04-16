#!/usr/bin/env python3
"""
Утилита командной строки для инициализации базы данных F.A.M.I.L.Y.
Аналог FAMILY_DB_init.sh
"""

import sys
import argparse
import logging
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from undermaind.utils.db_init import DatabaseInitializer

def main():
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(
        description="Инициализация базы данных F.A.M.I.L.Y."
    )
    
    parser.add_argument(
        "-c", "--config",
        help="Путь к файлу конфигурации (по умолчанию: ./family_db.conf)",
        default="./family_db.conf"
    )
    parser.add_argument(
        "-f", "--family-pass",
        help="Пароль для пользователя family_admin (переопределяет значение из конфига)"
    )
    parser.add_argument(
        "-d", "--db-host",
        help="Хост базы данных (переопределяет значение из конфига)"
    )
    parser.add_argument(
        "-p", "--db-port",
        help="Порт базы данных (переопределяет значение из конфига)",
        type=int
    )
    parser.add_argument(
        "-D", "--drop",
        help="Удалить существующую базу данных (без создания новой)",
        action="store_true"
    )
    parser.add_argument(
        "-R", "--recreate",
        help="Пересоздать базу данных (удалить и создать заново)",
        action="store_true"
    )

    args = parser.parse_args()

    try:
        # Создаем инициализатор
        initializer = DatabaseInitializer(
            config_path=args.config
        )
        
        # Применяем параметры командной строки
        if args.family_pass:
            initializer.admin_password = args.family_pass
        if args.db_host:
            initializer.db_host = args.db_host
        if args.db_port:
            initializer.db_port = args.db_port

        # Выполняем операцию в зависимости от параметров
        if args.drop:
            if initializer.drop_database(force=True):
                logging.info("База данных успешно удалена")
                sys.exit(0)
            else:
                logging.error("Ошибка при удалении базы данных")
                sys.exit(1)
        elif args.recreate:
            if initializer.initialize_database(recreate=True):
                logging.info("База данных успешно пересоздана")
                sys.exit(0)
            else:
                logging.error("Ошибка при пересоздании базы данных")
                sys.exit(1)
        else:
            if initializer.initialize_database():
                logging.info("База данных успешно инициализирована")
                sys.exit(0)
            else:
                logging.error("Ошибка при инициализации базы данных")
                sys.exit(1)

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()