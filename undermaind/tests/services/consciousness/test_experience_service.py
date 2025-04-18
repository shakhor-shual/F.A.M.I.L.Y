"""
Интеграционные тесты для ExperienceProcessingService.

Проверяет функциональность сервиса обработки опыта,
включая создание, поиск, связывание опытов, а также
работу с атрибутами, контекстами и источниками.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from undermaind.services.consciousness.experience_service import (
    ExperienceProcessingService,
    InvalidExperienceDataError,
    ExperienceNotFoundError
)
from undermaind.models.consciousness import (
    Experience,
    ExperienceAttribute,
    ExperienceContext,
    ExperienceSource,
    ExperienceConnection
)


@pytest.mark.integration
class TestExperienceProcessingService:
    """Тесты для сервиса обработки опыта."""
    
    @pytest.fixture
    def service(self):
        """Фикстура, создающая экземпляр сервиса для тестов."""
        return ExperienceProcessingService()
    
    @pytest.fixture
    def context(self, db_session_postgres):
        """Фикстура, создающая тестовый контекст."""
        context = ExperienceContext(
            title="Тестовый контекст",
            description="Контекст для тестирования ExperienceProcessingService",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION
        )
        db_session_postgres.add(context)
        db_session_postgres.commit()
        return context
    
    @pytest.fixture
    def source(self, db_session_postgres):
        """Фикстура, создающая тестовый источник."""
        source = ExperienceSource(
            name="Тестовый источник",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT
        )
        db_session_postgres.add(source)
        db_session_postgres.commit()
        return source
    
    def test_create_experience(self, service):
        """Проверка создания нового опыта."""
        # Создаем опыт через сервис
        experience = service.create_experience(
            content="Тестовый опыт через сервис",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            subjective_position=Experience.POSITION_REFLECTIVE,
            salience=8
        )
        
        # Проверяем, что опыт создан корректно
        assert experience is not None, "Опыт должен быть создан"
        assert experience.id is not None, "Опыт должен иметь ID"
        assert experience.content == "Тестовый опыт через сервис", "Содержание должно соответствовать"
        assert experience.experience_type == Experience.TYPE_THOUGHT, "Тип должен соответствовать"
        assert experience.information_category == Experience.CATEGORY_SELF, "Категория должна соответствовать"
        assert experience.subjective_position == Experience.POSITION_REFLECTIVE, "Позиция должна соответствовать"
        assert experience.salience == 8, "Значимость должна соответствовать"
        
    def test_create_experience_with_context(self, service, context):
        """Проверка создания опыта с контекстом."""
        # Создаем опыт с привязкой к контексту
        experience = service.create_experience(
            content="Опыт в контексте",
            experience_type=Experience.TYPE_COMMUNICATION,
            information_category=Experience.CATEGORY_SUBJECT,
            subjective_position=Experience.POSITION_ADDRESSEE,
            context_id=context.id
        )
        
        # Проверяем связь с контекстом
        assert experience.context_id == context.id, "ID контекста должен быть установлен"
        assert experience.has_context, "Свойство has_context должно быть True"
    
    def test_create_experience_with_source(self, service, source):
        """Проверка создания опыта с источником."""
        # Создаем опыт с привязкой к источнику
        experience = service.create_experience(
            content="Опыт от источника",
            experience_type=Experience.TYPE_PERCEPTION,
            information_category=Experience.CATEGORY_SUBJECT,
            subjective_position=Experience.POSITION_OBSERVER,
            source_id=source.id
        )
        
        # Проверяем связь с источником
        assert experience.source_id == source.id, "ID источника должен быть установлен"
        assert experience.has_source, "Свойство has_source должно быть True"
    
    def test_create_experience_with_attributes(self, service, db_session_postgres):
        """Проверка создания опыта с атрибутами."""
        # Создаем опыт с атрибутами
        attributes = {
            "color": "blue",
            "importance": "high",
            "numeric_value": "42"
        }
        
        experience = service.create_experience(
            content="Опыт с атрибутами",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            subjective_position=Experience.POSITION_REFLECTIVE,
            attributes=attributes
        )
        
        # Проверяем, что ID опыта получен
        assert experience.id is not None, "Опыт должен получить ID"
        
        # Получаем атрибуты из БД
        db_attributes = db_session_postgres.query(ExperienceAttribute).filter_by(experience_id=experience.id).all()
        
        # Проверяем, что все атрибуты созданы
        assert len(db_attributes) == 3, "Должны быть созданы все 3 атрибута"
        
        # Создаем словарь атрибутов для удобства сравнения
        attr_dict = {attr.attribute_key: attr.attribute_value for attr in db_attributes}
        
        # Проверяем значения атрибутов
        assert attr_dict["color"] == "blue", "Значение атрибута color должно соответствовать"
        assert attr_dict["importance"] == "high", "Значение атрибута importance должно соответствовать"
        assert attr_dict["numeric_value"] == "42", "Значение атрибута numeric_value должно соответствовать"
    
    def test_invalid_experience_data(self, service):
        """Проверка обработки некорректных данных при создании опыта."""
        # Проверяем пустое содержание
        with pytest.raises(InvalidExperienceDataError) as excinfo:
            service.create_experience(
                content="",
                experience_type=Experience.TYPE_THOUGHT,
                information_category=Experience.CATEGORY_SELF
            )
        assert "содержание" in str(excinfo.value).lower(), "Должна быть ошибка о пустом содержании"
        
        # Проверяем отсутствие обязательных параметров
        with pytest.raises(InvalidExperienceDataError):
            service.create_experience(
                content="Тестовый опыт",
                experience_type=None,
                information_category=Experience.CATEGORY_SELF
            )
    
    def test_create_thought_experience(self, service):
        """Проверка создания опыта типа 'мысль'."""
        # Создаем опыт-мысль
        thought = service.create_thought_experience(
            content="Тестовая мысль",
            salience=9
        )
        
        # Проверяем, что опыт создан с правильными параметрами
        assert thought.experience_type == Experience.TYPE_THOUGHT, "Тип должен быть TYPE_THOUGHT"
        assert thought.information_category == Experience.CATEGORY_SELF, "Категория должна быть CATEGORY_SELF"
        assert thought.subjective_position == Experience.POSITION_REFLECTIVE, "Позиция должна быть POSITION_REFLECTIVE"
        assert thought.salience == 9, "Значимость должна соответствовать"
    
    def test_create_communication_experience(self, service):
        """Проверка создания опыта типа 'коммуникация'."""
        # Создаем входящую коммуникацию
        incoming = service.create_communication_experience(
            content="Входящее сообщение",
            is_incoming=True
        )
        
        # Проверяем параметры входящей коммуникации
        assert incoming.experience_type == Experience.TYPE_COMMUNICATION, "Тип должен быть TYPE_COMMUNICATION"
        assert incoming.communication_direction == Experience.DIRECTION_INCOMING, "Направление должно быть DIRECTION_INCOMING"
        assert incoming.subjective_position == Experience.POSITION_ADDRESSEE, "Позиция должна быть POSITION_ADDRESSEE"
        
        # Создаем исходящую коммуникацию
        outgoing = service.create_communication_experience(
            content="Исходящее сообщение",
            is_incoming=False
        )
        
        # Проверяем параметры исходящей коммуникации
        assert outgoing.experience_type == Experience.TYPE_COMMUNICATION, "Тип должен быть TYPE_COMMUNICATION"
        assert outgoing.communication_direction == Experience.DIRECTION_OUTGOING, "Направление должно быть DIRECTION_OUTGOING"
        assert outgoing.subjective_position == Experience.POSITION_ADDRESSER, "Позиция должна быть POSITION_ADDRESSER"
    
    def test_get_experience_by_id(self, service, db_session_postgres):
        """Проверка получения опыта по ID."""
        # Создаем опыт
        experience = Experience(
            content="Тестовый опыт для получения по ID",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Получаем опыт по ID
        retrieved = service.get_experience_by_id(experience.id)
        
        # Проверяем соответствие
        assert retrieved.id == experience.id, "ID должны совпадать"
        assert retrieved.content == experience.content, "Содержание должно совпадать"
        
        # Проверяем поведение с несуществующим ID
        with pytest.raises(ExperienceNotFoundError) as excinfo:
            service.get_experience_by_id(99999)
        assert "не найден" in str(excinfo.value).lower(), "Должна быть ошибка о ненайденном опыте"
    
    def test_find_experiences(self, service, db_session_postgres, context, source):
        """Проверка поиска опытов по различным критериям."""
        # Создаем несколько опытов с разными параметрами
        exp1 = Experience(
            content="Опыт 1",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            context_id=context.id
        )
        
        exp2 = Experience(
            content="Опыт 2",
            experience_type=Experience.TYPE_PERCEPTION,
            information_category=Experience.CATEGORY_SUBJECT,
            source_id=source.id
        )
        
        exp3 = Experience(
            content="Опыт 3",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF
        )
        
        db_session_postgres.add_all([exp1, exp2, exp3])
        db_session_postgres.commit()
        
        # Поиск по типу опыта
        thoughts = service.find_experiences(experience_type=Experience.TYPE_THOUGHT)
        assert len(thoughts) >= 2, "Должно быть найдено не менее 2 опытов типа THOUGHT"
        assert all(e.experience_type == Experience.TYPE_THOUGHT for e in thoughts), "Все найденные опыты должны быть типа THOUGHT"
        
        # Поиск по контексту
        with_context = service.find_experiences(context_id=context.id)
        assert len(with_context) >= 1, "Должен быть найден хотя бы 1 опыт с указанным контекстом"
        assert all(e.context_id == context.id for e in with_context), "Все найденные опыты должны иметь указанный контекст"
        
        # Поиск по источнику
        with_source = service.find_experiences(source_id=source.id)
        assert len(with_source) >= 1, "Должен быть найден хотя бы 1 опыт с указанным источником"
        assert all(e.source_id == source.id for e in with_source), "Все найденные опыты должны иметь указанный источник"
        
        # Комбинированный поиск
        combined = service.find_experiences(
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF
        )
        assert len(combined) >= 2, "Должно быть найдено не менее 2 опытов по комбинированному запросу"
        assert all(e.experience_type == Experience.TYPE_THOUGHT and 
                  e.information_category == Experience.CATEGORY_SELF 
                  for e in combined), "Все найденные опыты должны соответствовать критериям"
    
    def test_create_connection(self, service, db_session_postgres):
        """Проверка создания связи между опытами."""
        # Создаем два опыта для связывания
        exp1 = Experience(
            content="Исходный опыт для связи",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF
        )
        
        exp2 = Experience(
            content="Целевой опыт для связи",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF
        )
        
        db_session_postgres.add_all([exp1, exp2])
        db_session_postgres.commit()
        
        # Создаем связь между опытами
        connection = service.create_connection(
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_SEMANTIC,
            strength=7,
            description="Тестовая связь"
        )
        
        # Проверяем параметры созданной связи
        assert connection.source_experience_id == exp1.id, "ID исходного опыта должен соответствовать"
        assert connection.target_experience_id == exp2.id, "ID целевого опыта должен соответствовать"
        assert connection.connection_type == ExperienceConnection.TYPE_SEMANTIC, "Тип связи должен соответствовать"
        assert connection.strength == 7, "Сила связи должна соответствовать"
        assert connection.description == "Тестовая связь", "Описание должно соответствовать"
        
        # Проверяем создание двунаправленной связи
        bidir_connection = service.create_connection(
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_TEMPORAL,
            bidirectional=True
        )
        
        assert bidir_connection.direction == ExperienceConnection.DIRECTION_BI, "Связь должна быть двунаправленной"
        
        # Проверяем ошибку при несуществующем опыте
        with pytest.raises(ExperienceNotFoundError):
            service.create_connection(
                source_experience_id=99999,
                target_experience_id=exp2.id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC
            )
    
    def test_find_connected_experiences(self, service, db_session_postgres):
        """Проверка поиска связанных опытов."""
        # Создаем группу связанных опытов
        exp1 = Experience(content="Центральный опыт", experience_type=Experience.TYPE_THOUGHT)
        exp2 = Experience(content="Связанный опыт 1", experience_type=Experience.TYPE_THOUGHT)
        exp3 = Experience(content="Связанный опыт 2", experience_type=Experience.TYPE_PERCEPTION)
        exp4 = Experience(content="Связанный опыт 3", experience_type=Experience.TYPE_COMMUNICATION)
        
        db_session_postgres.add_all([exp1, exp2, exp3, exp4])
        db_session_postgres.commit()
        
        # Создаем связи разных типов
        conn1 = ExperienceConnection(
            source_experience_id=exp1.id,
            target_experience_id=exp2.id,
            connection_type=ExperienceConnection.TYPE_SEMANTIC,
            strength=9
        )
        
        conn2 = ExperienceConnection(
            source_experience_id=exp3.id,
            target_experience_id=exp1.id,
            connection_type=ExperienceConnection.TYPE_CAUSAL,
            strength=7
        )
        
        conn3 = ExperienceConnection(
            source_experience_id=exp1.id,
            target_experience_id=exp4.id,
            connection_type=ExperienceConnection.TYPE_TEMPORAL,
            strength=5
        )
        
        db_session_postgres.add_all([conn1, conn2, conn3])
        db_session_postgres.commit()
        
        # Ищем связанные опыты
        connected = service.find_connected_experiences(exp1.id)
        
        # Проверяем, что найдены все связанные опыты
        assert len(connected) == 3, "Должны быть найдены все 3 связанных опыта"
        
        # Проверяем фильтрацию по типу связи
        semantic_connected = service.find_connected_experiences(
            exp1.id,
            connection_types=[ExperienceConnection.TYPE_SEMANTIC]
        )
        assert len(semantic_connected) == 1, "Должен быть найден 1 опыт с семантической связью"
        assert semantic_connected[0][0].id == exp2.id, "Должен быть найден правильный опыт"
        
        # Проверяем фильтрацию по силе связи
        strong_connected = service.find_connected_experiences(
            exp1.id,
            min_strength=8
        )
        assert len(strong_connected) == 1, "Должен быть найден 1 опыт с сильной связью"
        assert strong_connected[0][1].strength >= 8, "Сила связи должна соответствовать фильтру"
    
    def test_get_or_create_source(self, service, db_session_postgres):
        """Проверка получения или создания источника."""
        # Создаем источник через сервис
        source1 = service.get_or_create_source(
            name="Новый тестовый источник",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT
        )
        
        assert source1 is not None, "Источник должен быть создан"
        assert source1.id is not None, "Источник должен получить ID"
        assert source1.name == "Новый тестовый источник", "Имя должно соответствовать"
        
        # Повторно запрашиваем тот же источник (должен быть найден, а не создан заново)
        source2 = service.get_or_create_source(
            name="Новый тестовый источник",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT
        )
        
        assert source2.id == source1.id, "Должен быть возвращен существующий источник"
        assert source2.interaction_count > source1.interaction_count, "Счетчик взаимодействий должен быть увеличен"
    
    def test_add_attributes_to_experience(self, service, db_session_postgres):
        """Проверка добавления атрибутов к опыту."""
        # Создаем опыт
        experience = Experience(
            content="Опыт для атрибутов",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Добавляем атрибуты
        attributes = {
            "tag": "important",
            "category": "personal",
            "rating": 5
        }
        
        added_attrs = service.add_attributes_to_experience(
            experience_id=experience.id,
            attributes=attributes
        )
        
        # Проверяем результат
        assert len(added_attrs) == 3, "Должно быть добавлено 3 атрибута"
        
        # Проверяем, что атрибуты сохранены в БД
        db_attributes = db_session_postgres.query(ExperienceAttribute).filter_by(experience_id=experience.id).all()
        assert len(db_attributes) == 3, "В БД должно быть 3 атрибута"
        
        # Создаем словарь атрибутов для проверки
        attr_dict = {attr.attribute_key: attr.attribute_value for attr in db_attributes}
        
        # Проверяем значения
        assert attr_dict["tag"] == "important", "Значение атрибута tag должно соответствовать"
        assert attr_dict["category"] == "personal", "Значение атрибута category должно соответствовать"
        assert attr_dict["rating"] == "5", "Значение атрибута rating должно соответствовать"
        
        # Тестируем обновление существующего атрибута
        updated_attrs = service.add_attributes_to_experience(
            experience_id=experience.id,
            attributes={"rating": 8}
        )
        
        # Проверяем обновленное значение
        updated_db_attrs = db_session_postgres.query(ExperienceAttribute).filter_by(
            experience_id=experience.id,
            attribute_key="rating"
        ).first()
        
        assert updated_db_attrs.attribute_value == "8", "Значение атрибута должно быть обновлено"
    
    def test_update_experience(self, service, db_session_postgres):
        """Проверка обновления полей опыта."""
        # Создаем опыт
        experience = Experience(
            content="Исходный опыт",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            subjective_position=Experience.POSITION_REFLECTIVE,
            salience=5
        )
        db_session_postgres.add(experience)
        db_session_postgres.commit()
        
        # Обновляем опыт
        updated = service.update_experience(
            experience_id=experience.id,
            content="Обновленный опыт",
            salience=9,
            subjective_position=Experience.POSITION_OBSERVER
        )
        
        # Проверяем обновленные поля
        assert updated.content == "Обновленный опыт", "Содержание должно быть обновлено"
        assert updated.salience == 9, "Значимость должна быть обновлена"
        assert updated.subjective_position == Experience.POSITION_OBSERVER, "Позиция должна быть обновлена"
        
        # Подтверждаем сохранение в БД
        db_exp = db_session_postgres.query(Experience).filter_by(id=experience.id).first()
        assert db_exp.content == "Обновленный опыт", "Обновленное содержание должно быть сохранено в БД"
        
        # Проверяем ошибку при несуществующем опыте
        with pytest.raises(ExperienceNotFoundError):
            service.update_experience(experience_id=99999, content="Не существует")
    
    @patch('undermaind.services.consciousness.experience_service.vectorize_text')
    def test_find_similar_experiences(self, mock_vectorize, service, db_session_postgres):
        """Проверка поиска похожих опытов (с использованием заглушки)."""
        # Создаем несколько опытов
        exp1 = Experience(content="Первый опыт", experience_type=Experience.TYPE_THOUGHT)
        exp2 = Experience(content="Второй опыт", experience_type=Experience.TYPE_THOUGHT)
        exp3 = Experience(content="Третий опыт", experience_type=Experience.TYPE_THOUGHT)
        
        db_session_postgres.add_all([exp1, exp2, exp3])
        db_session_postgres.commit()
        
        # Устанавливаем заглушку для функции векторизации
        mock_vectorize.return_value = [0.1] * 1536  # Упрощенный вектор
        
        # Вызываем поиск похожих опытов
        similar = service.find_similar_experiences("Тестовый запрос", limit=2)
        
        # Проверяем, что функция векторизации была вызвана
        mock_vectorize.assert_called_with("Тестовый запрос")
        
        # Проверяем результат (так как это заглушка, просто проверяем формат)
        assert isinstance(similar, list), "Результат должен быть списком"
        
        # Примечание: так как функциональность семантического поиска обозначена как заглушка,
        # мы не можем полноценно протестировать точность поиска, только формат результата
    
    def test_activate_context(self, service, db_session_postgres):
        """Проверка активации контекста."""
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст для активации",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION,
            active_status=False  # Изначально неактивный
        )
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Активируем контекст через сервис
        activated = service.activate_context(context.id)
        
        # Проверяем, что контекст активирован
        assert activated.active_status is True, "Контекст должен быть активирован"
        
        # Проверяем состояние в БД
        db_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert db_context.active_status is True, "Контекст должен быть активирован в БД"