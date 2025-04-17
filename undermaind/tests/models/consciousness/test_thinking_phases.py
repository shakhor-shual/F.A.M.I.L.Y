"""
Интеграционные тесты для модели ThinkingPhase.

Проверяет взаимодействие модели ThinkingPhase с базой данных,
включая создание, чтение, обновление фаз мышления и их связи
с процессами мышления и опытом.
"""

import pytest
from datetime import datetime, timedelta

from undermaind.models.consciousness import ThinkingProcess, ThinkingPhase
from undermaind.models.consciousness import Experience

@pytest.mark.integration
class TestThinkingPhase:
    """Тесты для модели ThinkingPhase."""
    
    def test_create_thinking_phase(self, db_session_postgres):
        """Проверяет создание новой фазы мышления."""
        # Создаем процесс мышления для фазы
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс для фазы",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        # Создаем фазу мышления
        phase = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Тестовая фаза",
            phase_type=ThinkingPhase.TYPE_ANALYSIS,
            sequence_number=1,
            content="Содержание фазы"
        )
        
        # Сохраняем в БД
        db_session_postgres.commit()
        
        # Проверяем, что фаза создана корректно
        assert phase.id is not None, "Фаза должна получить ID"
        assert phase.phase_name == "Тестовая фаза"
        assert phase.phase_type == ThinkingPhase.TYPE_ANALYSIS
        assert phase.sequence_number == 1
        assert phase.content == "Содержание фазы"
        assert phase.completed_status is False
        assert phase.thinking_process_id == process.id
        
        # Получаем фазу из БД для проверки сохранения
        db_phase = ThinkingPhase.get_by_id(db_session_postgres, phase.id)
        assert db_phase is not None
        assert db_phase.phase_name == phase.phase_name
        assert db_phase.phase_type == phase.phase_type
    
    def test_phase_completion(self, db_session_postgres):
        """Проверяет завершение фазы мышления."""
        # Создаем процесс и фазу
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс для завершения",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        phase = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Завершаемая фаза",
            phase_type=ThinkingPhase.TYPE_ANALYSIS,
            sequence_number=1,
            content="Фаза для проверки завершения"
        )
        
        # Завершаем фазу
        phase.complete()
        db_session_postgres.commit()
        
        # Проверяем статус
        assert phase.completed_status is True
        assert phase.completion_time is not None
        
        # Проверяем через новый запрос
        db_phase = ThinkingPhase.get_by_id(db_session_postgres, phase.id)
        assert db_phase.completed_status is True
    
    def test_phase_with_experiences(self, db_session_postgres):
        """Проверяет работу с входными и выходными опытами фазы."""
        # Создаем процесс и фазу
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс с опытами",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        phase = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Фаза с опытами",
            phase_type=ThinkingPhase.TYPE_ANALYSIS,
            sequence_number=1,
            content="Фаза для проверки связей с опытом"
        )
        
        # Создаем опыты
        input_exp = Experience.create(
            db_session_postgres,
            content="Входной опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_THOUGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        output_exp = Experience.create(
            db_session_postgres,
            content="Выходной опыт",
            information_category=Experience.CATEGORY_SELF,
            experience_type=Experience.TYPE_INSIGHT,
            subjective_position=Experience.POSITION_REFLECTIVE
        )
        
        # Добавляем опыты к фазе
        phase.add_input_experience(input_exp)
        phase.add_output_experience(output_exp)
        db_session_postgres.commit()
        
        # Проверяем связи
        assert input_exp.id in phase.input_experience_ids
        assert output_exp.id in phase.output_experience_ids
        
        # Проверяем через новый запрос
        db_phase = ThinkingPhase.get_by_id(db_session_postgres, phase.id)
        assert input_exp.id in db_phase.input_experience_ids
        assert output_exp.id in db_phase.output_experience_ids
    
    def test_phase_sequence_validation(self, db_session_postgres):
        """Проверяет валидацию порядкового номера фазы."""
        # Создаем процесс
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс для проверки последовательности",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        # Создаем фазу с нормальным номером
        phase1 = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Фаза 1",
            phase_type=ThinkingPhase.TYPE_ANALYSIS,
            sequence_number=1,
            content="Первая фаза"
        )
        db_session_postgres.commit()
        
        # Проверяем, что номер сохранен корректно
        assert phase1.sequence_number == 1
        
        # Создаем фазу с тем же номером
        phase2 = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Фаза 2",
            phase_type=ThinkingPhase.TYPE_SYNTHESIS,
            sequence_number=1,
            content="Вторая фаза"
        )
        db_session_postgres.commit()
        
        # Номера должны быть автоматически скорректированы
        assert phase2.sequence_number == 2
    
    def test_phase_relationships(self, db_session_postgres):
        """Проверяет отношения фазы с процессом мышления."""
        # Создаем процесс
        process = ThinkingProcess.create(
            db_session_postgres,
            process_name="Процесс для отношений",
            process_type=ThinkingProcess.TYPE_REASONING
        )
        
        # Создаем несколько фаз
        phase1 = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Первая фаза",
            phase_type=ThinkingPhase.TYPE_ANALYSIS,
            sequence_number=1,
            content="Содержание первой фазы"
        )
        
        phase2 = ThinkingPhase.create(
            db_session_postgres,
            thinking_process_id=process.id,
            phase_name="Вторая фаза",
            phase_type=ThinkingPhase.TYPE_SYNTHESIS,
            sequence_number=2,
            content="Содержание второй фазы"
        )
        
        db_session_postgres.commit()
        
        # Проверяем связь с процессом через фазу
        assert phase1.process == process
        assert phase2.process == process
        
        # Проверяем связь с фазами через процесс
        assert len(process.phases) == 2
        assert phase1 in process.phases
        assert phase2 in process.phases
        
        # Проверяем порядок фаз
        sorted_phases = sorted(process.phases, key=lambda x: x.sequence_number)
        assert sorted_phases[0] == phase1
        assert sorted_phases[1] == phase2