"""
Интеграционные тесты для модели ExperienceContext.

Проверяет взаимодействие модели ExperienceContext с базой данных,
включая создание, чтение, обновление и удаление записей,
а также взаимодействие с векторными представлениями и иерархической структурой.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from undermaind.models.consciousness import ExperienceContext, ExperienceSource

try:
    # Проверяем наличие pgvector для тестов с векторами
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


@pytest.mark.integration
class TestExperienceContext:
    """Тесты для модели ExperienceContext."""
    
    def test_create_experience_context(self, db_session_postgres):
        """Проверяет создание нового контекста опыта и его сохранение в БД."""
        # Создаем новый контекст опыта
        context = ExperienceContext(
            title="Тестовый разговор",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION,
            active_status=True,
            summary="Это тестовый контекст для интеграционных тестов",
            tags=["test", "conversation", "integration"]
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Проверяем, что запись создана и имеет ID
        assert context.id is not None, "Контекст опыта должен получить ID при сохранении в БД"
        
        # Получаем запись из БД для проверки
        db_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert db_context is not None, "Контекст опыта должен существовать в БД после сохранения"
        assert db_context.title == "Тестовый разговор", "Заголовок контекста должен соответствовать заданному"
        assert db_context.context_type == ExperienceContext.CONTEXT_TYPE_CONVERSATION, "Тип контекста должен соответствовать заданному"
        assert db_context.active_status, "Статус активности должен соответствовать заданному"
        assert "test" in db_context.tags, "Теги должны быть сохранены"
    
    def test_update_experience_context(self, db_session_postgres):
        """Проверяет обновление существующего контекста опыта в БД."""
        # Создаем новый контекст опыта
        context = ExperienceContext(
            title="Исходный заголовок",
            context_type=ExperienceContext.CONTEXT_TYPE_TASK,
            summary="Исходное описание"
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Обновляем запись
        context.title = "Обновленный заголовок"
        context.summary = "Обновленное описание"
        context.add_tag("updated")
        
        db_session_postgres.commit()
        
        # Получаем обновленную запись из БД для проверки
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert updated_context.title == "Обновленный заголовок", "Заголовок должен быть обновлен"
        assert updated_context.summary == "Обновленное описание", "Описание должно быть обновлено"
        assert "updated" in updated_context.tags, "Тег должен быть добавлен"
    
    def test_close_context(self, db_session_postgres):
        """Проверяет закрытие контекста опыта."""
        # Создаем новый активный контекст опыта
        context = ExperienceContext(
            title="Активный контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION,
            active_status=True
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Закрываем контекст
        context.close()
        db_session_postgres.commit()
        
        # Получаем обновленную запись из БД для проверки
        closed_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert not closed_context.active_status, "Контекст должен быть закрыт (неактивен)"
        assert closed_context.closed_at is not None, "Должна быть установлена дата закрытия"
    
    def test_context_hierarchy(self, db_session_postgres):
        """Проверяет работу иерархической структуры контекстов (родитель-потомок)."""
        # Создаем родительский контекст
        parent_context = ExperienceContext(
            title="Родительский контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_RESEARCH
        )
        
        # Сохраняем в БД
        db_session_postgres.add(parent_context)
        db_session_postgres.commit()
        
        # Создаем дочерний контекст, связанный с родительским
        child_context = ExperienceContext(
            title="Дочерний контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_TASK,
            parent_context_id=parent_context.id
        )
        
        # Сохраняем в БД
        db_session_postgres.add(child_context)
        db_session_postgres.commit()
        
        # Проверяем связь от дочернего к родительскому
        assert child_context.parent_context_id == parent_context.id, "ID родительского контекста должен быть установлен"
        assert child_context.parent_context.id == parent_context.id, "Объект родительского контекста должен быть доступен"
        assert child_context.parent_context.title == "Родительский контекст", "Заголовок родительского контекста должен быть доступен"
        
        # Проверяем связь от родительского к дочернему
        refreshed_parent = db_session_postgres.query(ExperienceContext).filter_by(id=parent_context.id).first()
        assert len(refreshed_parent.child_contexts) > 0, "У родительского контекста должен быть минимум один дочерний контекст"
        assert refreshed_parent.child_contexts[0].id == child_context.id, "Дочерний контекст должен быть в списке дочерних"
    
    def test_add_participant(self, db_session_postgres):
        """Проверяет добавление участников в контекст."""
        # Создаем источник опыта (участника)
        source = ExperienceSource(
            name="Participant",
            source_type=ExperienceSource.SOURCE_TYPE_HUMAN,
            information_category=ExperienceSource.CATEGORY_SUBJECT
        )
        
        # Сохраняем в БД
        db_session_postgres.add(source)
        db_session_postgres.commit()
        
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст с участниками",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Добавляем участника
        context.add_participant(source.id)
        db_session_postgres.commit()
        
        # Получаем обновленный контекст из БД
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert source.id in updated_context.participants, "ID участника должен быть в списке участников контекста"
        
        # Проверяем, что добавление того же участника второй раз не дублирует его
        context.add_participant(source.id)
        db_session_postgres.commit()
        
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert updated_context.participants.count(source.id) == 1, "Участник не должен дублироваться в списке"
    
    def test_add_related_context(self, db_session_postgres):
        """Проверяет добавление связанных контекстов."""
        # Создаем два контекста
        context1 = ExperienceContext(
            title="Первый контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION
        )
        
        context2 = ExperienceContext(
            title="Второй контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_RESEARCH
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context1)
        db_session_postgres.add(context2)
        db_session_postgres.commit()
        
        # Связываем контексты
        context1.add_related_context(context2.id)
        db_session_postgres.commit()
        
        # Получаем обновленный контекст из БД
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context1.id).first()
        assert context2.id in updated_context.related_contexts, "ID связанного контекста должен быть в списке связанных контекстов"
    
    def test_add_tag(self, db_session_postgres):
        """Проверяет добавление тегов к контексту."""
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст с тегами",
            context_type=ExperienceContext.CONTEXT_TYPE_TASK
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Добавляем теги
        context.add_tag("important")
        context.add_tag("urgent")
        db_session_postgres.commit()
        
        # Получаем обновленный контекст из БД
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert "important" in updated_context.tags, "Тег должен быть добавлен"
        assert "urgent" in updated_context.tags, "Тег должен быть добавлен"
        
        # Проверяем, что добавление того же тега второй раз не дублирует его
        context.add_tag("important")
        db_session_postgres.commit()
        
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert updated_context.tags.count("important") == 1, "Тег не должен дублироваться в списке"
    
    @pytest.mark.skipif(not HAS_PGVECTOR, reason="Требуется pgvector")
    def test_set_summary_vector(self, db_session_postgres):
        """Проверяет установку векторного представления для резюме контекста."""
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст с вектором",
            context_type=ExperienceContext.CONTEXT_TYPE_RESEARCH,
            summary="Текст для векторизации"
        )
        
        # Сохраняем в БД
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Устанавливаем вектор (numpy array)
        test_vector = np.random.rand(1536)
        context.set_summary_vector(test_vector)
        db_session_postgres.commit()
        
        # Получаем обновленный контекст из БД
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert updated_context.summary_vector is not None, "Векторное представление должно быть установлено"
        
        # Устанавливаем вектор (list)
        test_vector_list = np.random.rand(1536).tolist()
        context.set_summary_vector(test_vector_list)
        db_session_postgres.commit()
        
        # Получаем обновленный контекст из БД
        updated_context = db_session_postgres.query(ExperienceContext).filter_by(id=context.id).first()
        assert updated_context.summary_vector is not None, "Векторное представление должно быть установлено"
    
    def test_to_dict_method(self, db_session_postgres):
        """Проверяет метод to_dict для сериализации объекта ExperienceContext."""
        # Создаем исходные данные для теста
        test_time = datetime.now()
        
        # Создаем родительский контекст
        parent_context = ExperienceContext(
            title="Родительский контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_RESEARCH
        )
        
        # Сохраняем в БД
        db_session_postgres.add(parent_context)
        db_session_postgres.commit()
        
        # Создаем новый контекст с заданными значениями для всех полей
        context = ExperienceContext(
            title="Dict Test Context",
            context_type=ExperienceContext.CONTEXT_TYPE_TASK,
            parent_context_id=parent_context.id,
            created_at=test_time,
            closed_at=None,
            active_status=True,
            participants=[1, 2],
            related_contexts=[3, 4],
            summary="Тестовое описание для проверки метода to_dict",
            tags=["test", "dict", "serialization"]
        )
        
        # Получаем словарь
        context_dict = context.to_dict()
        
        # Проверяем соответствие значений в словаре
        assert context_dict["title"] == "Dict Test Context", "Заголовок в словаре должен соответствовать атрибуту объекта"
        assert context_dict["context_type"] == ExperienceContext.CONTEXT_TYPE_TASK, "Тип контекста в словаре должен соответствовать атрибуту объекта"
        assert context_dict["parent_context_id"] == parent_context.id, "ID родительского контекста в словаре должен соответствовать атрибуту объекта"
        assert context_dict["active_status"] is True, "Статус активности в словаре должен соответствовать атрибуту объекта"
        assert context_dict["summary"] == "Тестовое описание для проверки метода to_dict", "Описание в словаре должно соответствовать атрибуту объекта"
        assert "test" in context_dict["tags"], "Теги в словаре должны соответствовать атрибуту объекта"