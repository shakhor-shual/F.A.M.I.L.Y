"""
Тесты для модели ExperienceConnection.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from undermaind.models.consciousness import Experience, ExperienceConnection

@pytest.mark.integration
class TestExperienceConnection:
    """Тесты для модели ExperienceConnection."""
    
    def test_create_connection(self, db_session_postgres):
        """Проверяет создание связи между опытами."""
        # Создаем два опыта для тестирования связи
        exp1 = Experience(
            content="Первый опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        exp2 = Experience(
            content="Второй опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        db_session_postgres.add_all([exp1, exp2])
        db_session_postgres.flush()
        
        # Создаем связь между опытами
        connection = ExperienceConnection.create(
            db_session_postgres,
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_ASSOCIATION,
            strength=8,
            description="Тестовая ассоциативная связь"
        )
        
        # Проверяем создание связи
        assert connection.id is not None, "Связь должна получить ID"
        assert connection.source_experience_id == exp1.id, "ID исходного опыта должен соответствовать"
        assert connection.target_experience_id == exp2.id, "ID целевого опыта должен соответствовать"
        assert connection.connection_type == ExperienceConnection.TYPE_ASSOCIATION, "Тип связи должен соответствовать"
        assert connection.strength == 8, "Сила связи должна соответствовать"
        assert connection.direction == ExperienceConnection.DIRECTION_BI, "По умолчанию связь должна быть двунаправленной"

    def test_find_connection(self, db_session_postgres):
        """Проверяет поиск существующей связи между опытами."""
        # Создаем опыты и связь
        exp1 = Experience(
            content="Первый опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        exp2 = Experience(
            content="Второй опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        db_session_postgres.add_all([exp1, exp2])
        db_session_postgres.flush()
        
        connection = ExperienceConnection.create(
            db_session_postgres,
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_TEMPORAL
        )
        
        # Ищем связь
        found_connection = ExperienceConnection.find_connection(
            db_session_postgres,
            exp1.id,
            exp2.id,
            ExperienceConnection.TYPE_TEMPORAL
        )
        
        assert found_connection is not None, "Связь должна быть найдена"
        assert found_connection.id == connection.id, "ID найденной связи должен соответствовать"

    def test_get_experience_connections(self, db_session_postgres):
        """Проверяет получение всех связей опыта."""
        # Создаем опыты
        exp1 = Experience(
            content="Центральный опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        exp2 = Experience(
            content="Связанный опыт 1",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        exp3 = Experience(
            content="Связанный опыт 2",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        db_session_postgres.add_all([exp1, exp2, exp3])
        db_session_postgres.flush()
        
        # Создаем связи
        ExperienceConnection.create(
            db_session_postgres,
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_ASSOCIATION
        )
        
        ExperienceConnection.create(
            db_session_postgres,
            source_experience_id=exp1.id,
            target_experience_id=exp3.id,
            connection_type=ExperienceConnection.TYPE_CAUSAL
        )
        
        # Получаем все связи первого опыта
        connections = ExperienceConnection.get_experience_connections(db_session_postgres, exp1.id)
        
        assert len(connections) == 2, "Должны быть найдены обе связи"
        assert all(c.source_experience_id == exp1.id for c in connections), "Все связи должны исходить из первого опыта"

    def test_connection_activation(self, db_session_postgres):
        """Проверяет механизм активации связи."""
        # Создаем опыты и связь
        exp1 = Experience(
            content="Первый опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        exp2 = Experience(
            content="Второй опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        db_session_postgres.add_all([exp1, exp2])
        db_session_postgres.flush()
        
        connection = ExperienceConnection.create(
            db_session_postgres,
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_ASSOCIATION
        )
        
        initial_activation_count = connection.activation_count
        initial_activation_time = connection.last_activated
        
        # Активируем связь
        connection.activate()
        
        assert connection.activation_count == initial_activation_count + 1, "Счетчик активаций должен увеличиться"
        assert connection.last_activated > initial_activation_time, "Время последней активации должно обновиться"

    def test_connection_strength_modification(self, db_session_postgres):
        """Проверяет механизмы усиления и ослабления связи."""
        # Создаем опыты и связь
        exp1 = Experience(
            content="Первый опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        exp2 = Experience(
            content="Второй опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        db_session_postgres.add_all([exp1, exp2])
        db_session_postgres.flush()
        
        connection = ExperienceConnection.create(
            db_session_postgres,
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_ASSOCIATION,
            strength=5
        )
        
        # Усиливаем связь
        initial_strength = connection.strength
        connection.strengthen(2)
        assert connection.strength == min(10, initial_strength + 2), "Сила связи должна увеличиться"
        
        # Ослабляем связь
        connection.weaken(1)
        assert connection.strength == min(10, initial_strength + 2) - 1, "Сила связи должна уменьшиться"