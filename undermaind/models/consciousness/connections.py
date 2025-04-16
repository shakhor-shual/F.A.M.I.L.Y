"""
Модель связей между опытами в проекте F.A.M.I.L.Y.
Формирует ассоциативную сеть воспоминаний АМИ.
"""

from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base


class ExperienceConnection(Base):
    """
    Модель связей между опытами - формирует ассоциативную сеть воспоминаний АМИ.
    Представляет различные типы связей: временные, причинные, ассоциативные и т.д.
    """
    __tablename__ = 'experience_connections'
    
    id = Column(Integer, primary_key=True)
    source_experience_id = Column(Integer, ForeignKey('experiences.id'), nullable=False)
    target_experience_id = Column(Integer, ForeignKey('experiences.id'), nullable=False)
    connection_type = Column(String, nullable=False)
    strength = Column(Float, default=0.5)
    created_at = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    description = Column(Text)
    meta_data = Column(JSONB)
    
    # Отношения будут определены централизованно в __init__.py
    
    def __repr__(self):
        return f"<ExperienceConnection(id={self.id}, type='{self.connection_type}', strength={self.strength})>"