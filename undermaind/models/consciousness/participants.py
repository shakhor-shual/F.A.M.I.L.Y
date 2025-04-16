"""
Модель участников взаимодействия в проекте F.A.M.I.L.Y.
Представляет сущности категорий "Ты" и "Оно", с которыми взаимодействует АМИ.
"""

from sqlalchemy import Column, Integer, String, Text, SmallInteger, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base


class Participant(Base):
    """
    Модель участников взаимодействия - сущностей, с которыми общается АМИ.
    Включает людей, другие АМИ, системы и самого АМИ (самореференция).
    """
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    participant_type = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    last_interaction = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    familiarity_level = Column(SmallInteger, default=0)
    trust_level = Column(SmallInteger, default=0)
    description = Column(Text)
    interaction_count = Column(Integer, default=1)
    meta_data = Column(JSONB)
    
    # Поддержка временных сущностей для решения "Парадокса первичности"
    is_ephemeral = Column(Boolean, default=False)
    provisional_data = Column(JSONB)
    
    # Отношения будут определены централизованно в __init__.py
    
    def __repr__(self):
        return f"<Participant(id={self.id}, name='{self.name}', type='{self.participant_type}')>"
    
    @classmethod
    def get_or_create_unknown(cls, session):
        """
        Получает или создает специальную запись для неизвестных участников.
        Используется при работе с категорией "Неизвестного".
        
        Args:
            session: Сессия SQLAlchemy
            
        Returns:
            Participant: Объект неизвестного участника
        """
        unknown = session.query(cls).filter(cls.name == 'UNKNOWN').first()
        if not unknown:
            unknown = cls(
                name='UNKNOWN',
                participant_type='other',
                is_ephemeral=True,
                description='Специальная сущность для неидентифицированных источников'
            )
            session.add(unknown)
            session.commit()
        return unknown