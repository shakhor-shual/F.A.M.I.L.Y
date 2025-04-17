"""
Модель связей между опытами АМИ.

Этот модуль определяет модель SQLAlchemy для таблицы experience_connections,
которая представляет собой различные типы связей между опытами АМИ,
формирующие ассоциативную сеть воспоминаний.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, TEXT, Boolean, TIMESTAMP, 
    SmallInteger, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from undermaind.models.base import Base
from undermaind.models.consciousness.experience import Experience

class ExperienceConnection(Base):
    """
    Модель связи между опытами АМИ.
    
    Представляет собой связь между двумя опытами, включающую:
    - Тип связи (временная, причинная и т.д.)
    - Силу связи
    - Направление (одно- или двунаправленная)
    """
    __tablename__ = 'experience_connections'
    __table_args__ = (
        CheckConstraint(
            "connection_type IN ('temporal', 'causal', 'semantic', 'contextual', "
            "'thematic', 'emotional', 'analogy', 'contrast', 'elaboration', "
            "'reference', 'association', 'other')",
            name='valid_connection_type'
        ),
        CheckConstraint(
            'strength BETWEEN 1 AND 10',
            name='valid_strength_range'
        ),
        CheckConstraint(
            "direction IN ('unidirectional', 'bidirectional')",
            name='valid_direction_type'
        ),
        {'schema': 'ami_test_user'}
    )

    # Основные поля
    id = Column(Integer, primary_key=True)
    source_experience_id = Column(Integer, ForeignKey('ami_test_user.experiences.id'), nullable=False)
    target_experience_id = Column(Integer, ForeignKey('ami_test_user.experiences.id'), nullable=False)
    connection_type = Column(String, nullable=False)
    
    # Характеристики связи
    strength = Column(SmallInteger, default=5)
    direction = Column(String, default='bidirectional')
    conscious_status = Column(Boolean, default=True)
    
    # Временные метки
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    last_activated = Column(TIMESTAMP(timezone=True), default=datetime.now)
    activation_count = Column(Integer, default=1)
    
    # Метаданные
    description = Column(TEXT)
    meta_data = Column(JSONB)
    
    # Отношения
    source_experience = relationship('Experience', foreign_keys=[source_experience_id])
    target_experience = relationship('Experience', foreign_keys=[target_experience_id])

    # Константы для типов связей
    TYPE_TEMPORAL = 'temporal'
    TYPE_CAUSAL = 'causal'
    TYPE_SEMANTIC = 'semantic'
    TYPE_CONTEXTUAL = 'contextual'
    TYPE_THEMATIC = 'thematic'
    TYPE_EMOTIONAL = 'emotional'
    TYPE_ANALOGY = 'analogy'
    TYPE_CONTRAST = 'contrast'
    TYPE_ELABORATION = 'elaboration'
    TYPE_REFERENCE = 'reference'
    TYPE_ASSOCIATION = 'association'
    TYPE_OTHER = 'other'

    # Константы для направлений
    DIRECTION_UNI = 'unidirectional'
    DIRECTION_BI = 'bidirectional'

    def __init__(self, **kwargs):
        """Инициализация связи между опытами."""
        super().__init__(**kwargs)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.last_activated = kwargs.get('last_activated', datetime.now())
        self.activation_count = kwargs.get('activation_count', 1)
        self.strength = kwargs.get('strength', 5)
        self.direction = kwargs.get('direction', self.DIRECTION_BI)
        self.conscious_status = kwargs.get('conscious_status', True)

    @classmethod
    def create(cls, session, source_experience_id: int, target_experience_id: int, 
               connection_type: str, **kwargs) -> 'ExperienceConnection':
        """
        Создает новую связь между опытами.
        
        Args:
            session: Сессия SQLAlchemy
            source_experience_id: ID исходного опыта
            target_experience_id: ID целевого опыта
            connection_type: Тип связи
            **kwargs: Дополнительные параметры
            
        Returns:
            ExperienceConnection: Созданная связь
        """
        connection = cls(
            source_experience_id=source_experience_id,
            target_experience_id=target_experience_id,
            connection_type=connection_type,
            **kwargs
        )
        session.add(connection)
        session.flush()
        return connection

    @classmethod
    def get_by_id(cls, session, connection_id: int) -> Optional['ExperienceConnection']:
        """
        Получает связь по ID.
        
        Args:
            session: Сессия SQLAlchemy
            connection_id: ID связи
            
        Returns:
            Optional[ExperienceConnection]: Найденная связь или None
        """
        return session.query(cls).filter(cls.id == connection_id).first()

    @classmethod
    def get_experience_connections(cls, session, experience_id: int) -> List['ExperienceConnection']:
        """
        Получает все связи опыта.
        
        Args:
            session: Сессия SQLAlchemy
            experience_id: ID опыта
            
        Returns:
            List[ExperienceConnection]: Список связей
        """
        return session.query(cls).filter(
            (cls.source_experience_id == experience_id) |
            ((cls.target_experience_id == experience_id) & (cls.direction == cls.DIRECTION_BI))
        ).all()

    @classmethod
    def find_connection(cls, session, source_id: int, target_id: int, 
                       connection_type: str) -> Optional['ExperienceConnection']:
        """
        Ищет конкретную связь между двумя опытами.
        
        Args:
            session: Сессия SQLAlchemy
            source_id: ID исходного опыта
            target_id: ID целевого опыта
            connection_type: Тип связи
            
        Returns:
            Optional[ExperienceConnection]: Найденная связь или None
        """
        return session.query(cls).filter(
            cls.source_experience_id == source_id,
            cls.target_experience_id == target_id,
            cls.connection_type == connection_type
        ).first()

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты связи.
        
        Args:
            **kwargs: Пары ключ-значение для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def activate(self) -> None:
        """Отмечает активацию связи."""
        self.last_activated = datetime.now()
        self.activation_count += 1

    def strengthen(self, amount: int = 1) -> None:
        """
        Усиливает связь.
        
        Args:
            amount: Величина усиления (по умолчанию 1)
        """
        new_strength = min(10, self.strength + amount)
        self.strength = new_strength

    def weaken(self, amount: int = 1) -> None:
        """
        Ослабляет связь.
        
        Args:
            amount: Величина ослабления (по умолчанию 1)
        """
        new_strength = max(1, self.strength - amount)
        self.strength = new_strength

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            'id': self.id,
            'source_experience_id': self.source_experience_id,
            'target_experience_id': self.target_experience_id,
            'connection_type': self.connection_type,
            'strength': self.strength,
            'direction': self.direction,
            'conscious_status': self.conscious_status,
            'created_at': self.created_at,
            'last_activated': self.last_activated,
            'activation_count': self.activation_count,
            'description': self.description,
            'meta_data': self.meta_data
        }

    def __repr__(self) -> str:
        direction = "двунаправленная" if self.direction == self.DIRECTION_BI else "однонаправленная"
        return (f"<ExperienceConnection(id={self.id}, type='{self.connection_type}', "
                f"strength={self.strength}, direction='{direction}')>")