"""
Модель для контекстов опыта АМИ.

Этот модуль определяет модель SQLAlchemy для таблицы experience_contexts,
которая хранит информацию о контекстах взаимодействия - ситуативных рамках,
в которых происходит опыт АМИ.
"""

from sqlalchemy import Column, Integer, String, TEXT, Boolean, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any

from undermaind.models.base import Base
import numpy as np

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Заглушка для векторного типа, если не установлен pgvector
    class Vector:
        def __init__(self, dimensions):
            self.dimensions = dimensions


class ExperienceContext(Base):
    """
    Модель контекста опыта АМИ.
    
    Контекст - это долговременная ситуативная рамка, в которой происходит опыт.
    Можно представить как "сцену", на которой разворачивается опыт.
    """
    __tablename__ = 'experience_contexts'
    
    # Используем схему, соответствующую имени АМИ
    __table_args__ = {'schema': 'ami_test_user'}
    
    # Основные поля
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    context_type = Column(String, nullable=False)
    parent_context_id = Column(Integer, ForeignKey('experience_contexts.id'), nullable=True)
    
    # Временные метаданные
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    closed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    active_status = Column(Boolean, default=True)
    
    # Связи и отношения
    participants = Column(ARRAY(Integer))
    related_contexts = Column(ARRAY(Integer))
    
    # Содержание и семантика
    summary = Column(TEXT)
    summary_vector = Column(Vector(1536))
    tags = Column(ARRAY(String))
    
    # Дополнительные данные
    meta_data = Column(JSONB)
    
    # Отношение к родительскому контексту
    parent_context = relationship('ExperienceContext', remote_side=[id], backref='child_contexts')
    
    # Константы для типов контекстов
    CONTEXT_TYPE_CONVERSATION = 'conversation'
    CONTEXT_TYPE_TASK = 'task'
    CONTEXT_TYPE_RESEARCH = 'research'
    CONTEXT_TYPE_LEARNING = 'learning'
    CONTEXT_TYPE_REFLECTION = 'reflection'
    CONTEXT_TYPE_INTERNAL_DIALOGUE = 'internal_dialogue'
    CONTEXT_TYPE_RESOURCE_INTERACTION = 'resource_interaction'
    CONTEXT_TYPE_SYSTEM_INTERACTION = 'system_interaction'
    CONTEXT_TYPE_OTHER = 'other'
    
    def close(self):
        """Закрывает контекст."""
        self.active_status = False
        self.closed_at = datetime.now()
    
    def add_participant(self, participant_id):
        """
        Добавляет участника в контекст.
        
        Args:
            participant_id: ID источника опыта (ExperienceSource)
        """
        if self.participants is None:
            self.participants = []
            
        if participant_id not in self.participants:
            self.participants.append(participant_id)
    
    def add_related_context(self, context_id):
        """
        Добавляет связанный контекст.
        
        Args:
            context_id: ID связанного контекста
        """
        if self.related_contexts is None:
            self.related_contexts = []
            
        if context_id not in self.related_contexts:
            self.related_contexts.append(context_id)
    
    def add_tag(self, tag):
        """
        Добавляет тег к контексту.
        
        Args:
            tag: Тег для добавления
        """
        if self.tags is None:
            self.tags = []
            
        if tag not in self.tags:
            self.tags.append(tag)
    
    def set_summary_vector(self, vector):
        """
        Устанавливает векторное представление для резюме контекста.
        
        Args:
            vector: Векторное представление (numpy array или list)
        """
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        self.summary_vector = vector
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует модель в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        return {
            'id': self.id,
            'title': self.title,
            'context_type': self.context_type,
            'parent_context_id': self.parent_context_id,
            'created_at': self.created_at,
            'closed_at': self.closed_at,
            'active_status': self.active_status,
            'participants': self.participants,
            'related_contexts': self.related_contexts,
            'summary': self.summary,
            'tags': self.tags
        }
        
    def __repr__(self) -> str:
        status = "активный" if self.active_status else "закрытый"
        return f"<ExperienceContext(id={self.id}, title='{self.title}', status='{status}')>"