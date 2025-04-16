"""
Модель информационных ресурсов в проекте F.A.M.I.L.Y.
Представляет внешние неагентивные источники информации для АМИ.
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base


class InformationResource(Base):
    """
    Модель информационных ресурсов - внешних источников категории "Оно",
    с которыми взаимодействует АМИ (файлы, веб-страницы, API и т.д.).
    """
    __tablename__ = 'information_resources'
    
    id = Column(Integer, primary_key=True)
    uri = Column(String, nullable=False)
    title = Column(String)
    resource_type = Column(String, nullable=False)
    first_accessed = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    last_accessed = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    access_count = Column(Integer, default=1)
    content_hash = Column(String)
    summary = Column(Text)
    related_experiences = Column(ARRAY(Integer))
    participant_id = Column(Integer, ForeignKey('participants.id'))
    meta_data = Column(JSONB)
    
    # Отношения будут определены централизованно в __init__.py
    
    def __repr__(self):
        return f"<InformationResource(id={self.id}, uri='{self.uri}', type='{self.resource_type}')>"