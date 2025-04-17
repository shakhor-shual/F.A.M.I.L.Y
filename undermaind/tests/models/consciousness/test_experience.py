"""
Интеграционные тесты для модели Experience.

Проверяет взаимодействие модели Experience с базой данных,
включая создание, чтение, обновление записей, а также
работу со связями, векторами и метаданными.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from undermaind.models.consciousness import (
    Experience, 
    ExperienceContext,
    ExperienceSource
)

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


@pytest.mark.integration
class TestExperience:
    """Тесты для модели Experience."""
    
    def test_create_experience(self, db_session_postgres):
        """Проверяет создание нового опыта и его сохранение в БД."""
        # Создаем новый опыт
        experience = Experience(
            content="Тестовый опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE,
            salience=7
        )
        
        # Сохраняем в БД
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Проверяем, что запись создана и имеет ID
        assert experience.id is not None, "Опыт должен получить ID при сохранении в БД"
        
        # Получаем запись из БД для проверки
        db_experience = db_session_postgres.query(Experience).filter_by(id=experience.id).first()
        assert db_experience is not None, "Опыт должен существовать в БД после сохранения"
        assert db_experience.content == "Тестовый опыт", "Содержание должно соответствовать заданному"
        assert db_experience.information_category == Experience.CATEGORY_SELF, "Категория должна соответствовать заданной"
        assert db_experience.experience_type == Experience.TYPE_THOUGHT, "Тип должен соответствовать заданному"
        assert db_experience.subjective_position == Experience.POSITION_REFLECTIVE, "Позиция должна соответствовать заданной"
        assert db_experience.salience == 7, "Значимость должна соответствовать заданной"
        assert db_experience.provenance_type == Experience.PROVENANCE_IDENTIFIED, "Тип происхождения по умолчанию должен быть identified"
        assert not db_experience.verified_status, "Статус верификации по умолчанию должен быть False"

    def test_update_experience(self, db_session_postgres):
        """Проверяет обновление существующего опыта в БД."""
        # Создаем новый опыт
        experience = Experience(
            content="Исходное содержание",
            information_category=Experience.CATEGORY_SUBJECT,
            experience_type=Experience.TYPE_PERCEPTION,
            subjective_position=Experience.POSITION_OBSERVER
        )
        
        # Сохраняем в БД
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Обновляем запись
        experience.content = "Обновленное содержание"
        experience.salience = 8
        experience.verified_status = True
        experience.meta_data = {"test": "data"}
        
        db_session_postgres.commit()
        
        # Получаем обновленную запись из БД для проверки
        updated_experience = db_session_postgres.query(Experience).filter_by(id=experience.id).first()
        assert updated_experience.content == "Обновленное содержание", "Содержание должно быть обновлено"
        assert updated_experience.salience == 8, "Значимость должна быть обновлена"
        assert updated_experience.verified_status, "Статус верификации должен быть обновлен"
        assert updated_experience.meta_data["test"] == "data", "Метаданные должны быть обновлены"

    def test_experience_with_context(self, db_session_postgres):
        """Проверяет связь опыта с контекстом."""
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст для опыта",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION
        )
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Создаем опыт с привязкой к контексту
        experience = Experience(
            content="Опыт в контексте",
            information_category=Experience.CATEGORY_SUBJECT,
            experience_type=Experience.TYPE_COMMUNICATION,
            subjective_position=Experience.POSITION_ADDRESSEE,
            context_id=context.id
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Проверяем связь с контекстом
        assert experience.context_id == context.id, "ID контекста должен быть установлен"
        assert experience.context == context, "Объект контекста должен быть доступен"
        assert experience.has_context, "Свойство has_context должно быть True"

    def test_experience_with_source(self, db_session_postgres):
        """Проверяет связь опыта с источником."""
        # Создаем источник
        source = ExperienceSource(
            name="Тестовый источник",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT
        )
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Создаем опыт с привязкой к источнику
        experience = Experience(
            content="Опыт от источника",
            information_category=Experience.CATEGORY_SUBJECT,
            experience_type=Experience.TYPE_PERCEPTION,
            subjective_position=Experience.POSITION_OBSERVER,
            source_id=source.id
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Проверяем связь с источником
        assert experience.source_id == source.id, "ID источника должен быть установлен"
        assert experience.source == source, "Объект источника должен быть доступен"
        assert experience.has_source, "Свойство has_source должно быть True"

    def test_experience_hierarchy(self, db_session_postgres):
        """Проверяет иерархические связи между опытами."""
        # Создаем родительский опыт
        parent_experience = Experience(
            content="Родительский опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(parent_experience)
        db_session_postgres.commit()

        # Создаем дочерний опыт
        child_experience = Experience(
            content="Дочерний опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,  # Используем тот же тип, что и у родительского опыта
            subjective_position=Experience.POSITION_REFLECTIVE,
            parent_experience_id=parent_experience.id
        )
        db_session_postgres.add(child_experience)
        db_session_postgres.commit()

        # Загружаем опыты из БД для проверки
        db_parent = db_session_postgres.query(Experience).filter_by(id=parent_experience.id).first()
        db_child = db_session_postgres.query(Experience).filter_by(id=child_experience.id).first()

        # Проверяем связи
        assert db_parent.child_experiences[0].id == db_child.id, "Дочерний опыт должен быть связан с родительским"
        assert db_child.parent_experience.id == db_parent.id, "Родительский опыт должен быть связан с дочерним"

    @pytest.mark.skipif(not HAS_PGVECTOR, reason="Требуется pgvector")
    def test_content_vector(self, db_session_postgres):
        """Проверяет работу с векторным представлением содержания."""
        # Создаем опыт
        experience = Experience(
            content="Тестовый опыт для векторизации",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Устанавливаем вектор (numpy array)
        test_vector = np.random.rand(1536)
        experience.content_vector = test_vector
        db_session_postgres.commit()
        
        # Получаем обновленный опыт из БД
        updated_experience = db_session_postgres.query(Experience).filter_by(id=experience.id).first()
        assert updated_experience.content_vector is not None, "Векторное представление должно быть установлено"
        
        # Устанавливаем вектор (list)
        test_vector_list = np.random.rand(1536).tolist()
        experience.content_vector = test_vector_list
        db_session_postgres.commit()
        
        # Получаем обновленный опыт из БД
        updated_experience = db_session_postgres.query(Experience).filter_by(id=experience.id).first()
        assert updated_experience.content_vector is not None, "Векторное представление должно быть установлено"

    def test_create_class_method(self, db_session_postgres):
        """Проверяет создание опыта через классовый метод create."""
        # Создаем опыт через метод create
        experience = Experience.create(
            db_session_postgres,
            content="Created Via Method",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE,
            salience=8
        )
        
        # Проверяем, что объект создан и имеет ID
        assert experience.id is not None, "Опыт должен получить ID"
        assert experience.content == "Created Via Method", "Содержание должно соответствовать"
        assert experience.salience == 8, "Значимость должна соответствовать"
        
        # Проверяем, что запись существует в БД
        db_experience = Experience.get_by_id(db_session_postgres, experience.id)
        assert db_experience is not None, "Опыт должен быть найден в БД"
        assert db_experience.id == experience.id, "ID должны совпадать"

    def test_get_by_id(self, db_session_postgres):
        """Проверяет получение опыта по ID."""
        # Создаем тестовый опыт
        experience = Experience(
            content="Test Get By ID",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Получаем опыт по ID
        retrieved_experience = Experience.get_by_id(db_session_postgres, experience.id)
        assert retrieved_experience is not None, "Опыт должен быть найден"
        assert retrieved_experience.id == experience.id, "ID должны совпадать"
        assert retrieved_experience.content == "Test Get By ID", "Содержание должно соответствовать"
        
        # Проверяем несуществующий ID
        nonexistent = Experience.get_by_id(db_session_postgres, 99999)
        assert nonexistent is None, "Должен вернуться None для несуществующего ID"

    def test_to_dict_method(self, db_session_postgres):
        """Проверяет метод to_dict для сериализации объекта Experience."""
        # Создаем исходные данные для теста
        test_time = datetime.now()
        
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст для сериализации",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION
        )
        db_session_postgres.add(context)
        
        # Создаем источник
        source = ExperienceSource(
            name="Источник для сериализации",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT
        )
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Создаем опыт со всеми возможными полями
        experience = Experience(
            content="Dict Test Content",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE,
            communication_direction=Experience.DIRECTION_OUTGOING,
            context_id=context.id,
            source_id=source.id,
            salience=8,
            provenance_type=Experience.PROVENANCE_IDENTIFIED,
            verified_status=True,
            meta_data={"test": "data"}
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Получаем словарь
        experience_dict = experience.to_dict()
        
        # Проверяем соответствие значений в словаре
        assert experience_dict["content"] == "Dict Test Content", "Содержание в словаре должно соответствовать атрибуту объекта"
        assert experience_dict["information_category"] == Experience.CATEGORY_SELF, "Категория в словаре должна соответствовать атрибуту объекта"
        assert experience_dict["experience_type"] == Experience.TYPE_THOUGHT, "Тип в словаре должен соответствовать атрибуту объекта"
        assert experience_dict["subjective_position"] == Experience.POSITION_REFLECTIVE, "Позиция в словаре должна соответствовать атрибуту объекта"
        assert experience_dict["communication_direction"] == Experience.DIRECTION_OUTGOING, "Направление в словаре должно соответствовать атрибуту объекта"
        assert experience_dict["context_id"] == context.id, "ID контекста в словаре должен соответствовать атрибуту объекта"
        assert experience_dict["source_id"] == source.id, "ID источника в словаре должен соответствовать атрибуту объекта"
        assert experience_dict["salience"] == 8, "Значимость в словаре должна соответствовать атрибуту объекта"
        assert experience_dict["verified_status"] is True, "Статус верификации в словаре должен соответствовать атрибуту объекта"
        assert experience_dict["meta_data"]["test"] == "data", "Метаданные в словаре должны соответствовать атрибуту объекта"