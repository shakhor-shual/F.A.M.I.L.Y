"""
Интеграционные тесты для модели ThinkingProcess.

Проверяет взаимодействие модели ThinkingProcess с базой данных,
включая создание, чтение, обновление процессов мышления и работу с фазами.
"""

import pytest
from datetime import datetime, timedelta

from undermaind.models.consciousness import ThinkingProcess, ThinkingPhase
from undermaind.models.consciousness import Experience, ExperienceContext

@pytest.mark.integration
class TestThinkingProcess:
    """Тесты для модели ThinkingProcess."""
    
    def test_create_thinking_process(self, db_session_postgres):
        """Проверяет создание нового процесса мышления."""
        # Создаем процесс мышления
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Тестовый процесс",
            process_type=ThinkingProcess.TYPE_REASONING,
            description="Тестовое описание процесса"
        )
        
        # Сохраняем в БД
        db_session_postgres.commit()
        
        # Проверяем, что процесс создан корректно
        assert process.id is not None, "Процесс должен получить ID"
        assert process.process_name == "Тестовый процесс"
        assert process.process_type == ThinkingProcess.TYPE_REASONING
        assert process.description == "Тестовое описание процесса"
        assert process.active_status is True
        assert process.completed_status is False
        assert process.progress_percentage == 0
        
        # Получаем процесс из БД для проверки сохранения
        db_process = ThinkingProcess.get_by_id(db_session_postgres, process.id)
        assert db_process is not None
        assert db_process.process_name == process.process_name
        assert db_process.process_type == process.process_type
    
    def test_add_thinking_phase(self, db_session_postgres):
        """Проверяет добавление фазы к процессу мышления."""
        # Создаем процесс мышления
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс с фазами",
            process_type=ThinkingProcess.TYPE_PROBLEM_SOLVING
        )
        
        # Создаем фазу
        phase = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Анализ проблемы",
            phase_type=ThinkingPhase.TYPE_ANALYSIS,
            sequence_number=1,
            content="Анализ исходных данных"
        )
        
        # Добавляем фазу к процессу
        process.add_phase(phase)
        db_session_postgres.commit()
        
        # Проверяем связь
        assert phase in process.phases
        assert len(process.phases) == 1
        
        # Проверяем через новый запрос
        db_process = ThinkingProcess.get_by_id(db_session_postgres, process.id)
        assert len(db_process.phases) == 1
        assert db_process.phases[0].phase_name == "Анализ проблемы"
        assert db_process.phases[0].phase_type == ThinkingPhase.TYPE_ANALYSIS
    
    def test_thinking_process_completion(self, db_session_postgres):
        """Проверяет завершение процесса мышления."""
        # Создаем процесс
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Завершаемый процесс",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        # Завершаем процесс
        process.complete()
        db_session_postgres.commit()
        
        # Проверяем статус
        assert process.active_status is False
        assert process.completed_status is True
        assert process.progress_percentage == 100
        assert process.end_time is not None
        
        # Проверяем через новый запрос
        db_process = ThinkingProcess.get_by_id(db_session_postgres, process.id)
        assert not db_process.active_status
        assert db_process.completed_status
        assert db_process.progress_percentage == 100
    
    def test_update_process_progress(self, db_session_postgres):
        """Проверяет обновление прогресса процесса мышления."""
        # Создаем процесс
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс с прогрессом",
            process_type=ThinkingProcess.TYPE_PROBLEM_SOLVING
        )
        
        # Обновляем прогресс
        process.update_progress(50)
        db_session_postgres.commit()
        
        # Проверяем прогресс
        assert process.progress_percentage == 50
        
        # Проверяем через новый запрос
        db_process = ThinkingProcess.get_by_id(db_session_postgres, process.id)
        assert db_process.progress_percentage == 50
        
        # Проверяем ограничение на диапазон
        process.update_progress(120)  # Должно ограничиться до 100
        assert process.progress_percentage == 100
        
        process.update_progress(-10)  # Должно ограничиться до 0
        assert process.progress_percentage == 0
    
    def test_get_active_processes(self, db_session_postgres):
        """Проверяет получение списка активных процессов."""
        # Создаем активный процесс
        active_process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Активный процесс",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        # Создаем и завершаем другой процесс
        completed_process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Завершенный процесс",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        completed_process.complete()
        
        db_session_postgres.commit()
        
        # Получаем список активных процессов
        active_processes = ThinkingProcess.get_active_processes(db_session_postgres)
        
        # Проверяем фильтрацию по статусу
        assert len(active_processes) > 0
        assert active_process.id in [p.id for p in active_processes]
        assert completed_process.id not in [p.id for p in active_processes]

    def test_process_with_context(self, db_session_postgres):
        """Проверяет связь процесса мышления с контекстом."""
        # Создаем контекст
        context = ExperienceContext(
            title="Контекст для процесса",
            context_type=ExperienceContext.CONTEXT_TYPE_TASK
        )
        db_session_postgres.add(context)
        db_session_postgres.commit()
        
        # Создаем процесс с привязкой к контексту
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс в контексте",
            process_type=ThinkingProcess.TYPE_REASONING,
            context_id=context.id
        )
        db_session_postgres.commit()
        
        # Проверяем связь с контекстом
        assert process.context_id == context.id
        assert process.context == context
        
        # Проверяем через новый запрос
        db_process = ThinkingProcess.get_by_id(db_session_postgres, process.id)
        assert db_process.context.title == "Контекст для процесса"