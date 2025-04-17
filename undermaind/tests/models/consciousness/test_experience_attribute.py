"""
Интеграционные тесты для модели ExperienceAttribute.

Проверяет взаимодействие модели ExperienceAttribute с базой данных,
включая создание, чтение, обновление атрибутов опыта.
"""

import pytest
from datetime import datetime

from undermaind.models.consciousness import (
    Experience, 
    ExperienceAttribute
)


@pytest.mark.integration
class TestExperienceAttribute:
    """Тесты для модели ExperienceAttribute."""
    
    def test_create_attribute(self, db_session_postgres):
        """Проверяет создание нового атрибута опыта."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для атрибутов",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем атрибут
        attribute = ExperienceAttribute(
            experience_id=experience.id,
            attribute_name="test_attribute",
            attribute_value="test_value",
            attribute_type=ExperienceAttribute.TYPE_STRING
        )
        
        # Сохраняем в БД
        db_session_postgres.add(attribute)
        db_session_postgres.commit()
        
        # Проверяем, что запись создана и имеет ID
        assert attribute.id is not None, "Атрибут должен получить ID при сохранении в БД"
        
        # Получаем запись из БД для проверки
        db_attribute = db_session_postgres.query(ExperienceAttribute).filter_by(id=attribute.id).first()
        assert db_attribute is not None, "Атрибут должен существовать в БД после сохранения"
        assert db_attribute.attribute_name == "test_attribute", "Название атрибута должно соответствовать заданному"
        assert db_attribute.attribute_value == "test_value", "Значение атрибута должно соответствовать заданному"
        assert db_attribute.attribute_type == ExperienceAttribute.TYPE_STRING, "Тип атрибута должен соответствовать заданному"

    def test_create_class_method(self, db_session_postgres):
        """Проверяет создание атрибута через классовый метод create."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для метода create",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем атрибут через метод create
        attribute = ExperienceAttribute.create(
            db_session_postgres,
            experience_id=experience.id,
            attribute_name="created_via_method",
            attribute_value="method_value",
            attribute_type=ExperienceAttribute.TYPE_STRING
        )
        
        # Проверяем, что объект создан и имеет ID
        assert attribute.id is not None, "Атрибут должен получить ID"
        assert attribute.attribute_name == "created_via_method", "Название должно соответствовать"
        assert attribute.attribute_value == "method_value", "Значение должно соответствовать"
        
        # Проверяем, что запись существует в БД
        db_attribute = ExperienceAttribute.get_by_id(db_session_postgres, attribute.id)
        assert db_attribute is not None, "Атрибут должен быть найден в БД"
        assert db_attribute.id == attribute.id, "ID должны совпадать"

    def test_get_by_id(self, db_session_postgres):
        """Проверяет получение атрибута по ID."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для get_by_id",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем тестовый атрибут
        attribute = ExperienceAttribute(
            experience_id=experience.id,
            attribute_name="get_by_id_test",
            attribute_value="test_value",
            attribute_type=ExperienceAttribute.TYPE_STRING
        )
        db_session_postgres.add(attribute)
        db_session_postgres.commit()
        
        # Получаем атрибут по ID
        retrieved_attribute = ExperienceAttribute.get_by_id(db_session_postgres, attribute.id)
        assert retrieved_attribute is not None, "Атрибут должен быть найден"
        assert retrieved_attribute.id == attribute.id, "ID должны совпадать"
        assert retrieved_attribute.attribute_name == "get_by_id_test", "Название должно соответствовать"
        
        # Проверяем несуществующий ID
        nonexistent = ExperienceAttribute.get_by_id(db_session_postgres, 99999)
        assert nonexistent is None, "Должен вернуться None для несуществующего ID"

    def test_get_experience_attributes(self, db_session_postgres):
        """Проверяет получение всех атрибутов опыта."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для get_experience_attributes",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем несколько атрибутов
        attributes = [
            ExperienceAttribute(
                experience_id=experience.id,
                attribute_name=f"test_attr_{i}",
                attribute_value=f"value_{i}",
                attribute_type=ExperienceAttribute.TYPE_STRING
            )
            for i in range(3)
        ]
        db_session_postgres.add_all(attributes)
        db_session_postgres.commit()
        
        # Получаем все атрибуты опыта
        experience_attributes = ExperienceAttribute.get_experience_attributes(
            db_session_postgres, 
            experience.id
        )
        assert len(experience_attributes) == 3, "Должны быть найдены все 3 атрибута"
        
        # Проверяем, что все атрибуты принадлежат правильному опыту
        for attr in experience_attributes:
            assert attr.experience_id == experience.id, "ID опыта должен совпадать"

    def test_find_by_name(self, db_session_postgres):
        """Проверяет поиск атрибута по имени."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для find_by_name",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем атрибут с уникальным именем
        attribute = ExperienceAttribute(
            experience_id=experience.id,
            attribute_name="unique_name",
            attribute_value="test_value",
            attribute_type=ExperienceAttribute.TYPE_STRING
        )
        db_session_postgres.add(attribute)
        db_session_postgres.commit()
        
        # Ищем атрибут по имени
        found_attribute = ExperienceAttribute.find_by_name(
            db_session_postgres,
            experience.id,
            "unique_name"
        )
        assert found_attribute is not None, "Атрибут должен быть найден"
        assert found_attribute.attribute_name == "unique_name", "Название должно совпадать"
        assert found_attribute.experience_id == experience.id, "ID опыта должен совпадать"

    def test_find_by_value(self, db_session_postgres):
        """Проверяет поиск атрибутов по значению."""
        # Создаем два опыта для теста
        experiences = [
            Experience(
                content=f"Тестовый опыт {i} для find_by_value",
                information_category=Experience.CATEGORY_SELF,
                experience_type=Experience.TYPE_THOUGHT,
                subjective_position=Experience.POSITION_REFLECTIVE
            )
            for i in range(2)
        ]
        db_session_postgres.add_all(experiences)
        db_session_postgres.commit()
        
        # Создаем атрибуты с одинаковым значением для разных опытов
        common_value = "shared_value"
        attributes = [
            ExperienceAttribute(
                experience_id=exp.id,
                attribute_name=f"test_attr_{i}",
                attribute_value=common_value,
                attribute_type=ExperienceAttribute.TYPE_STRING
            )
            for i, exp in enumerate(experiences)
        ]
        db_session_postgres.add_all(attributes)
        db_session_postgres.commit()
        
        # Ищем атрибуты по значению
        found_attributes = ExperienceAttribute.find_by_value(
            db_session_postgres,
            common_value
        )
        assert len(found_attributes) == 2, "Должны быть найдены оба атрибута"
        
        # Проверяем, что найденные атрибуты принадлежат разным опытам
        found_experience_ids = {attr.experience_id for attr in found_attributes}
        assert len(found_experience_ids) == 2, "Атрибуты должны принадлежать разным опытам"

    def test_update_attribute(self, db_session_postgres):
        """Проверяет обновление атрибута."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для обновления атрибута",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем атрибут
        attribute = ExperienceAttribute(
            experience_id=experience.id,
            attribute_name="update_test",
            attribute_value="old_value",
            attribute_type=ExperienceAttribute.TYPE_STRING
        )
        db_session_postgres.add(attribute)
        db_session_postgres.commit()
        
        # Обновляем атрибут
        attribute.update(
            attribute_value="new_value",
            attribute_type=ExperienceAttribute.TYPE_JSON
        )
        db_session_postgres.commit()
        
        # Получаем обновленный атрибут из БД для проверки
        updated_attribute = ExperienceAttribute.get_by_id(db_session_postgres, attribute.id)
        assert updated_attribute.attribute_value == "new_value", "Значение должно быть обновлено"
        assert updated_attribute.attribute_type == ExperienceAttribute.TYPE_JSON, "Тип должен быть обновлен"

    def test_to_dict_method(self, db_session_postgres):
        """Проверяет метод to_dict для сериализации объекта ExperienceAttribute."""
        # Создаем опыт для теста
        experience = Experience(
            content="Тестовый опыт для to_dict",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Создаем атрибут со всеми возможными полями
        attribute = ExperienceAttribute(
            experience_id=experience.id,
            attribute_name="dict_test",
            attribute_value="test_value",
            attribute_type=ExperienceAttribute.TYPE_STRING,
            meta_data={"test": "data"}
        )
        db_session_postgres.add(attribute)
        db_session_postgres.commit()
        
        # Получаем словарь
        attribute_dict = attribute.to_dict()
        
        # Проверяем соответствие значений в словаре
        assert attribute_dict["id"] == attribute.id, "ID в словаре должен соответствовать атрибуту объекта"
        assert attribute_dict["experience_id"] == experience.id, "ID опыта в словаре должен соответствовать атрибуту объекта"
        assert attribute_dict["attribute_name"] == "dict_test", "Название в словаре должно соответствовать атрибуту объекта"
        assert attribute_dict["attribute_value"] == "test_value", "Значение в словаре должно соответствовать атрибуту объекта"
        assert attribute_dict["attribute_type"] == ExperienceAttribute.TYPE_STRING, "Тип в словаре должен соответствовать атрибуту объекта"
        assert attribute_dict["meta_data"]["test"] == "data", "Метаданные в словаре должны соответствовать атрибуту объекта"