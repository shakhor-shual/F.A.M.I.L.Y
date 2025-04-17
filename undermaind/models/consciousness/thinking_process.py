"""
Модель процессов мышления АМИ.

Этот модуль определяет модель SQLAlchemy для таблицы thinking_processes,
которая представляет собой процессы мышления АМИ - последовательности
этапов размышлений, приводящие к выводам или решениям.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, TEXT, Boolean, TIMESTAMP, 
    SmallInteger, ForeignKey, ARRAY, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from undermaind.models.base import Base
from undermaind.models.consciousness.experience_contexts import ExperienceContext
from undermaind.models.consciousness.experience import Experience
from undermaind.models.consciousness.thinking_phase import ThinkingPhase

class ThinkingProcess(Base):
    """
    Модель процесса мышления АМИ.
    
    Представляет собой структурированный процесс мышления, включающий:
    - Последовательность фаз
    - Связи с контекстом и опытом
    - Мониторинг прогресса
    """
    __tablename__ = 'thinking_processes'
    __table_args__ = (
        CheckConstraint(
            "process_type IN ('reasoning', 'problem_solving', 'reflection', "
            "'planning', 'decision_making', 'creative', 'learning', 'other')",
            name='valid_process_type'
        ),
        CheckConstraint(
            'progress_percentage BETWEEN 0 AND 100',
            name='valid_progress_percentage'
        ),
        {'schema': 'ami_test_user'}
    )

    # Основные поля
    id = Column(Integer, primary_key=True)
    process_name = Column(String, nullable=False)
    process_type = Column(String, nullable=False)
    
    # Временные метки
    start_time = Column(TIMESTAMP(timezone=True), default=datetime.now)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Статус и прогресс
    active_status = Column(Boolean, default=True)
    completed_status = Column(Boolean, default=False)
    progress_percentage = Column(SmallInteger, default=0)
    
    # Связи
    context_id = Column(Integer, ForeignKey('ami_test_user.experience_contexts.id'))
    triggered_by_experience_id = Column(Integer, ForeignKey('ami_test_user.experiences.id'))
    
    # Результаты
    results = Column(TEXT)
    result_experience_ids = Column(ARRAY(Integer))
    
    # Метаданные
    description = Column(TEXT)
    meta_data = Column(JSONB)
    
    # Отношения
    context = relationship('ExperienceContext')
    trigger_experience = relationship('Experience', foreign_keys=[triggered_by_experience_id])
    phases = relationship('ThinkingPhase', back_populates='process', cascade='all, delete-orphan')

    # Константы для типов процессов
    TYPE_REASONING = 'reasoning'
    TYPE_PROBLEM_SOLVING = 'problem_solving'
    TYPE_REFLECTION = 'reflection'
    TYPE_PLANNING = 'planning'
    TYPE_DECISION_MAKING = 'decision_making'
    TYPE_CREATIVE = 'creative'
    TYPE_LEARNING = 'learning'
    TYPE_OTHER = 'other'

    def __init__(self, **kwargs):
        """Инициализация процесса мышления."""
        super().__init__(**kwargs)
        self.start_time = kwargs.get('start_time', datetime.now())
        self.active_status = kwargs.get('active_status', True)
        self.completed_status = kwargs.get('completed_status', False)
        self.progress_percentage = kwargs.get('progress_percentage', 0)

    @classmethod
    def create(cls, session, process_name: str, process_type: str, **kwargs) -> 'ThinkingProcess':
        """
        Создает новый процесс мышления.
        
        Args:
            session: Сессия SQLAlchemy
            process_name: Название процесса
            process_type: Тип процесса
            **kwargs: Дополнительные параметры
            
        Returns:
            ThinkingProcess: Созданный процесс мышления
        """
        process = cls(
            process_name=process_name,
            process_type=process_type,
            **kwargs
        )
        session.add(process)
        session.flush()
        return process

    @classmethod
    def get_by_id(cls, session, process_id: int) -> Optional['ThinkingProcess']:
        """
        Получает процесс мышления по ID.
        
        Args:
            session: Сессия SQLAlchemy
            process_id: ID процесса
            
        Returns:
            Optional[ThinkingProcess]: Найденный процесс или None
        """
        return session.query(cls).filter(cls.id == process_id).first()

    @classmethod
    def get_active_processes(cls, session) -> List['ThinkingProcess']:
        """
        Получает список активных процессов мышления.
        
        Args:
            session: Сессия SQLAlchemy
            
        Returns:
            List[ThinkingProcess]: Список активных процессов
        """
        return session.query(cls).filter(cls.active_status == True).all()

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты процесса мышления.
        
        Args:
            **kwargs: Пары ключ-значение для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def complete(self) -> None:
        """Отмечает процесс мышления как завершенный."""
        self.active_status = False
        self.completed_status = True
        self.end_time = datetime.now()
        self.progress_percentage = 100

    def update_progress(self, percentage: int) -> None:
        """
        Обновляет процент выполнения процесса.
        
        Args:
            percentage: Новый процент выполнения (0-100)
        """
        # Ограничиваем значение в диапазоне 0-100
        self.progress_percentage = max(0, min(100, percentage))

    def add_phase(self, phase: 'ThinkingPhase') -> None:
        """
        Добавляет новую фазу к процессу мышления.
        
        Args:
            phase: Объект фазы мышления
        """
        self.phases.append(phase)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            'id': self.id,
            'process_name': self.process_name,
            'process_type': self.process_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'active_status': self.active_status,
            'completed_status': self.completed_status,
            'progress_percentage': self.progress_percentage,
            'context_id': self.context_id,
            'triggered_by_experience_id': self.triggered_by_experience_id,
            'results': self.results,
            'result_experience_ids': self.result_experience_ids,
            'description': self.description,
            'meta_data': self.meta_data
        }

    def __repr__(self) -> str:
        status = "активный" if self.active_status else "завершенный"
        return f"<ThinkingProcess(id={self.id}, name='{self.process_name}', type='{self.process_type}', status='{status}')>"