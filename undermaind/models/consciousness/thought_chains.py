"""
Модель цепочек мыслей в проекте F.A.M.I.L.Y.
Представляет последовательности связанных мыслей АМИ.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base
from undermaind.core.vectors import Vector


class ThoughtChain(Base):
    """
    Модель цепочек мыслей - последовательностей размышлений АМИ по определённой теме.
    Содержит связанные мысли и итоговый вывод размышления.
    """
    __tablename__ = 'thought_chains'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    context_id = Column(Integer, ForeignKey('memory_contexts.id'))
    initial_experience_id = Column(Integer, ForeignKey('experiences.id'))
    complete_status = Column(Boolean, default=False)
    thought_pattern = Column(String, nullable=False)
    thoughts = Column(ARRAY(Integer), nullable=False)
    conclusion = Column(Text)
    conclusion_vector = Column(Vector(1536))
    meta_data = Column(JSONB)
    
    # Отношения будут определены централизованно в __init__.py
    
    def __repr__(self):
        return f"<ThoughtChain(id={self.id}, title='{self.title}', pattern='{self.thought_pattern}', complete={self.complete_status})>"