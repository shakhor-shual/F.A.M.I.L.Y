"""
Модель контекстов памяти в проекте F.A.M.I.L.Y.
Контексты - это "сцены", в которых происходят переживания АМИ.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy.types as types
from ..base import Base
from undermaind.core.vectors import Vector


class MemoryContext(Base):
    """
    Модель контекстов памяти - условий, в которых происходит опыт АМИ.
    Контекст может быть разговором, задачей, исследованием и т.д.
    """
    __tablename__ = 'memory_contexts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    context_type = Column(String, nullable=False)
    parent_context_id = Column(Integer, ForeignKey('memory_contexts.id'))
    created_at = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    closed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    active_status = Column(Boolean, default=True)
    participants = Column(ARRAY(Integer))
    related_contexts = Column(ARRAY(Integer))
    summary = Column(Text)
    summary_vector = Column(Vector(1536))
    tags = Column(ARRAY(String))
    meta_data = Column(JSONB)
    
    # Отношения будут определены централизованно в __init__.py
    
    def __repr__(self):
        return f"<MemoryContext(id={self.id}, title='{self.title}', type='{self.context_type}')>"