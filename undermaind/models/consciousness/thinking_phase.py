"""
Модель фазы процесса мышления АМИ.

Этот модуль определяет модель SQLAlchemy для таблицы thinking_phases,
которая представляет собой этапы/фазы процесса мышления АМИ.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, TEXT, Boolean, TIMESTAMP, 
    ForeignKey, ARRAY, CheckConstraint
)
from sqlalchemy.orm import relationship

from undermaind.models.base import Base

class ThinkingPhase(Base):
    """
    Модель фазы мышления.
    
    Представляет собой отдельную фазу/этап процесса мышления, включающий:
    - Содержание фазы
    - Входные и выходные опыты
    - Порядковый номер в процессе
    """
    __tablename__ = 'thinking_phases'
    __table_args__ = (
        CheckConstraint(
            "phase_type IN ('analysis', 'synthesis', 'evaluation', "
            "'decision', 'action', 'reflection', 'other')",
            name='valid_phase_type'
        ),
        {'schema': 'ami_test_user'}
    )

    # Основные поля
    id = Column(Integer, primary_key=True)
    phase_name = Column(String, nullable=False)
    phase_type = Column(String, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    content = Column(TEXT, nullable=False)
    
    # Статус и время
    start_time = Column(TIMESTAMP(timezone=True), default=datetime.now)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    active_status = Column(Boolean, default=True)
    completed_status = Column(Boolean, default=False)
    completion_time = Column(TIMESTAMP(timezone=True))
    
    # Связи
    thinking_process_id = Column(Integer, ForeignKey('ami_test_user.thinking_processes.id'))
    input_experience_ids = Column(ARRAY(Integer), server_default='{}')
    output_experience_ids = Column(ARRAY(Integer), server_default='{}')
    
    # Отношения
    process = relationship('ThinkingProcess', back_populates='phases')

    # Константы для типов фаз
    TYPE_ANALYSIS = 'analysis'
    TYPE_SYNTHESIS = 'synthesis'
    TYPE_EVALUATION = 'evaluation'
    TYPE_DECISION = 'decision'
    TYPE_ACTION = 'action'
    TYPE_REFLECTION = 'reflection'
    TYPE_OTHER = 'other'

    def __init__(self, **kwargs):
        """Инициализация фазы мышления."""
        super().__init__(**kwargs)
        self.start_time = kwargs.get('start_time', datetime.now())
        self.end_time = kwargs.get('end_time', None)
        self.active_status = kwargs.get('active_status', True)
        self.completed_status = kwargs.get('completed_status', False)
        self.completion_time = kwargs.get('completion_time', None)
        self.input_experience_ids = kwargs.get('input_experience_ids', [])
        self.output_experience_ids = kwargs.get('output_experience_ids', [])

    @classmethod
    def create(cls, session, thinking_process_id: int, phase_name: str, 
               phase_type: str, sequence_number: int, content: str, **kwargs) -> 'ThinkingPhase':
        """
        Создает новую фазу мышления.
        
        Args:
            session: Сессия SQLAlchemy
            thinking_process_id: ID процесса мышления
            phase_name: Название фазы
            phase_type: Тип фазы
            sequence_number: Порядковый номер
            content: Содержание фазы
            **kwargs: Дополнительные параметры
            
        Returns:
            ThinkingPhase: Созданная фаза мышления
        """
        # Проверяем, есть ли уже фаза с таким номером
        existing_phase = session.query(cls).filter_by(
            thinking_process_id=thinking_process_id,
            sequence_number=sequence_number
        ).first()
        
        # Если есть, увеличиваем номер для новой фазы
        if existing_phase:
            # Получаем максимальный номер
            max_sequence = session.query(cls).filter_by(
                thinking_process_id=thinking_process_id
            ).with_entities(cls.sequence_number).order_by(cls.sequence_number.desc()).scalar()
            sequence_number = max_sequence + 1 if max_sequence else 1
        
        phase = cls(
            thinking_process_id=thinking_process_id,
            phase_name=phase_name,
            phase_type=phase_type,
            sequence_number=sequence_number,
            content=content,
            **kwargs
        )
        session.add(phase)
        session.flush()
        return phase

    @classmethod
    def get_by_id(cls, session, phase_id: int) -> Optional['ThinkingPhase']:
        """
        Получает фазу мышления по ID.
        
        Args:
            session: Сессия SQLAlchemy
            phase_id: ID фазы
            
        Returns:
            Optional[ThinkingPhase]: Найденная фаза или None
        """
        return session.query(cls).filter(cls.id == phase_id).first()

    def complete(self) -> None:
        """Отмечает фазу как завершенную."""
        self.completed_status = True
        self.completion_time = datetime.now()
        self.active_status = False
        self.end_time = self.completion_time

    def add_input_experience(self, experience) -> None:
        """
        Добавляет входной опыт к фазе.
        
        Args:
            experience: Объект опыта
        """
        if experience.id not in self.input_experience_ids:
            self.input_experience_ids.append(experience.id)

    def add_output_experience(self, experience) -> None:
        """
        Добавляет выходной опыт к фазе.
        
        Args:
            experience: Объект опыта
        """
        if experience.id not in self.output_experience_ids:
            self.output_experience_ids.append(experience.id)

    def __repr__(self) -> str:
        status = "завершенная" if self.completed_status else "активная"
        return f"<ThinkingPhase(id={self.id}, name='{self.phase_name}', type='{self.phase_type}', status='{status}')>"