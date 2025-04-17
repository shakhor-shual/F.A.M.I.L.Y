"""
Интеграционные тесты для модели ExperienceSource.

Проверяет взаимодействие модели ExperienceSource с базой данных,
включая создание, чтение, обновление и удаление записей.
"""

import pytest
from datetime import datetime, timedelta

from undermaind.models.consciousness import ExperienceSource


@pytest.mark.integration
class TestExperienceSource:
    """Тесты для модели ExperienceSource."""
    
    def test_create_experience_source(self, db_session_postgres):
        """Проверяет создание нового источника опыта и его сохранение в БД."""
        # Создаем новый источник опыта
        source = ExperienceSource(
            name="Test Human User",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT,
            agency_level=5,
            first_interaction=datetime.now(),
            last_interaction=datetime.now(),
            interaction_count=1,
            is_ephemeral=False,
            familiarity_level=3,
            trust_level=4,
            description="Тестовый пользователь для интеграционных тестов"
        )
        
        # Сохраняем в БД
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Проверяем, что запись создана и имеет ID
        assert source.id is not None, "Источник опыта должен получить ID при сохранении в БД"
        
        # Получаем запись из БД для проверки
        db_source = db_session_postgres.query(ExperienceSource).filter_by(id=source.id).first()
        assert db_source is not None, "Источник опыта должен существовать в БД после сохранения"
        assert db_source.name == "Test Human User", "Имя источника должно соответствовать заданному"
        assert db_source.source_type == ExperienceSource.SOURCE_TYPE_HUMAN, "Тип источника должен соответствовать заданному"
        assert db_source.information_category == ExperienceSource.CATEGORY_SUBJECT, "Категория должна соответствовать заданной"
    
    def test_update_experience_source(self, db_session_postgres):
        """Проверяет обновление существующего источника опыта в БД."""
        # Создаем новый источник опыта
        source = ExperienceSource(
            name="Initial Name",
            source_type=ExperienceSource.SOURCE_TYPE_SYSTEM,
            information_category=ExperienceSource.CATEGORY_OBJECT,
            agency_level=2,
            description="Исходное описание"
        )
        
        # Сохраняем в БД
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Обновляем запись
        source.name = "Updated Name"
        source.description = "Обновленное описание"
        source.agency_level = 3
        source.update_interaction_metrics()  # Вызываем метод обновления метрик взаимодействия
        
        db_session_postgres.commit()
        
        # Получаем обновленную запись из БД для проверки
        updated_source = db_session_postgres.query(ExperienceSource).filter_by(id=source.id).first()
        assert updated_source.name == "Updated Name", "Имя должно быть обновлено"
        assert updated_source.description == "Обновленное описание", "Описание должно быть обновлено"
        assert updated_source.agency_level == 3, "Уровень агентивности должен быть обновлен"
        assert updated_source.interaction_count == 2, "Счетчик взаимодействий должен быть увеличен"
    
    def test_delete_experience_source(self, db_session_postgres):
        """Проверяет удаление источника опыта из БД."""
        # Создаем новый источник опыта
        source = ExperienceSource(
            name="Temporary Source",
            source_type=ExperienceSource.SOURCE_TYPE_RESOURCE,
            information_category=ExperienceSource.CATEGORY_OBJECT,
            is_ephemeral=True
        )
        
        # Сохраняем в БД
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        source_id = source.id
        
        # Удаляем запись
        db_session_postgres.delete(source)
        db_session_postgres.commit()
        
        # Проверяем, что запись удалена
        deleted_source = db_session_postgres.query(ExperienceSource).filter_by(id=source_id).first()
        assert deleted_source is None, "Источник опыта должен быть удален из БД"
    
    def test_get_or_create_unknown_source(self, db_session_postgres):
        """Проверяет создание и получение неизвестного источника опыта."""
        # Получаем неизвестный источник (должен быть создан)
        unknown_source = ExperienceSource.get_or_create_unknown_source(db_session_postgres)
        
        # Проверяем, что источник создан корректно
        assert unknown_source is not None, "Неизвестный источник должен быть создан"
        assert unknown_source.name == "UNKNOWN", "Имя неизвестного источника должно быть 'UNKNOWN'"
        assert unknown_source.source_type == ExperienceSource.SOURCE_TYPE_OTHER, "Тип неизвестного источника должен быть 'other'"
        assert unknown_source.is_ephemeral, "Неизвестный источник должен быть эфемерным"
        
        # Вызываем метод повторно и проверяем, что возвращается тот же объект
        same_unknown_source = ExperienceSource.get_or_create_unknown_source(db_session_postgres)
        assert same_unknown_source.id == unknown_source.id, "Повторные вызовы должны возвращать тот же объект неизвестного источника"
    
    def test_get_or_create_self_source(self, db_session_postgres):
        """Проверяет создание и получение источника 'self' (АМИ)."""
        # Получаем источник self (должен быть создан)
        self_source = ExperienceSource.get_or_create_self_source(db_session_postgres)
        
        # Проверяем, что источник создан корректно
        assert self_source is not None, "Источник 'self' должен быть создан"
        assert self_source.name == "self", "Имя источника 'self' должно быть 'self'"
        assert self_source.source_type == ExperienceSource.SOURCE_TYPE_SELF, "Тип источника 'self' должен быть 'self'"
        assert self_source.information_category == ExperienceSource.CATEGORY_SELF, "Категория источника 'self' должна быть 'self'"
        assert self_source.agency_level == 10, "Уровень агентивности источника 'self' должен быть максимальным"
        
        # Вызываем метод повторно и проверяем, что возвращается тот же объект
        same_self_source = ExperienceSource.get_or_create_self_source(db_session_postgres)
        assert same_self_source.id == self_source.id, "Повторные вызовы должны возвращать тот же объект источника 'self'"
    
    def test_to_dict_method(self, db_session_postgres):
        """Проверяет метод to_dict для сериализации объекта ExperienceSource."""
        # Создаем исходные данные для теста
        test_time = datetime.now()
        
        # Создаем новый источник опыта с заданными значениями для всех полей
        source = ExperienceSource(
            name="Dict Test Source",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT,
            agency_level=7,
            first_interaction=test_time,
            last_interaction=test_time,
            interaction_count=5,
            is_ephemeral=False,
            familiarity_level=4,
            trust_level=3,
            uri="https://example.com",
            resource_type=ExperienceSource.RESOURCE_TYPE_WEBPAGE,
            description="Тестовый источник для проверки метода to_dict"
        )
        
        # Получаем словарь
        source_dict = source.to_dict()
        
        # Проверяем соответствие значений в словаре
        assert source_dict["name"] == "Dict Test Source", "Имя в словаре должно соответствовать атрибуту объекта"
        assert source_dict["source_type"] == ExperienceSource.SOURCE_TYPE_HUMAN, "Тип источника в словаре должен соответствовать атрибуту объекта"
        assert source_dict["information_category"] == ExperienceSource.CATEGORY_SUBJECT, "Категория в словаре должна соответствовать атрибуту объекта"
        assert source_dict["agency_level"] == 7, "Уровень агентивности в словаре должен соответствовать атрибуту объекта"
        assert source_dict["interaction_count"] == 5, "Количество взаимодействий в словаре должно соответствовать атрибуту объекта"
        assert source_dict["description"] == "Тестовый источник для проверки метода to_dict", "Описание в словаре должно соответствовать атрибуту объекта"
    
    def test_create_class_method(self, db_session_postgres):
        """Проверяет создание источника опыта через классовый метод create."""
        # Создаем источник через метод create
        source = ExperienceSource.create(
            db_session_postgres,
            name="Created Via Method",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT,
            agency_level=5,
            description="Создано через метод create"
        )
        
        # Проверяем, что объект создан и имеет ID
        assert source.id is not None, "Источник должен получить ID"
        assert source.name == "Created Via Method", "Имя должно соответствовать"
        
        # Проверяем, что запись существует в БД
        db_source = ExperienceSource.get_by_id(db_session_postgres, source.id)
        assert db_source is not None, "Источник должен быть найден в БД"
        assert db_source.id == source.id, "ID должны совпадать"
    
    def test_get_by_id(self, db_session_postgres):
        """Проверяет получение источника по ID."""
        # Создаем тестовый источник
        source = ExperienceSource(
            name="Get By ID Test",
            source_type=ExperienceSource.SOURCE_TYPE_SYSTEM,
            information_category=ExperienceSource.CATEGORY_OBJECT
        )
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Получаем источник по ID
        found_source = ExperienceSource.get_by_id(db_session_postgres, source.id)
        assert found_source is not None, "Источник должен быть найден"
        assert found_source.id == source.id, "ID должны совпадать"
        assert found_source.name == "Get By ID Test", "Имя должно совпадать"
        
        # Проверяем поиск несуществующего ID
        nonexistent = ExperienceSource.get_by_id(db_session_postgres, 99999)
        assert nonexistent is None, "Должен вернуться None для несуществующего ID"
    
    def test_find_by_name(self, db_session_postgres):
        """Проверяет поиск источника по имени."""
        # Создаем тестовый источник
        source = ExperienceSource(
            name="Unique Name Test",
            source_type=ExperienceSource.SOURCE_TYPE_SYSTEM,
            information_category=ExperienceSource.CATEGORY_OBJECT
        )
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Поиск по имени
        found_source = ExperienceSource.find_by_name(db_session_postgres, "Unique Name Test")
        assert found_source is not None, "Источник должен быть найден"
        assert found_source.id == source.id, "ID должны совпадать"
        
        # Проверяем поиск несуществующего имени
        nonexistent = ExperienceSource.find_by_name(db_session_postgres, "Nonexistent Name")
        assert nonexistent is None, "Должен вернуться None для несуществующего имени"