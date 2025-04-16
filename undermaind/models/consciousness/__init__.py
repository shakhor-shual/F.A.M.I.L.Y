"""
Модуль сознательного уровня памяти АМИ.
Экспортирует все модели сознательного уровня и устанавливает их отношения.
"""

from sqlalchemy.orm import relationship
from sqlalchemy import or_, and_

from .participants import Participant
from .contexts import MemoryContext
from .experiences import Experience, ExperienceType, ExperienceCategory
from .thought_chains import ThoughtChain
from .resources import InformationResource
from .connections import ExperienceConnection


def setup_consciousness_relationships():
    """
    Устанавливает отношения между моделями сознательного уровня памяти АМИ.
    Эта функция должна вызываться после импорта всех моделей.
    """
    # Отношения для Participant
    Participant.sent_experiences = relationship(
        "Experience",
        foreign_keys="[Experience.sender_participant_id]",
        back_populates="sender"
    )
    
    Participant.received_experiences = relationship(
        "Experience",
        foreign_keys="[Experience.to_participant_id]",
        back_populates="recipient"
    )
    
    Participant.resources = relationship(
        "InformationResource",
        back_populates="participant"
    )
    
    # Отношения для MemoryContext
    MemoryContext.experiences = relationship(
        "Experience",
        back_populates="context"
    )
    
    MemoryContext.thought_chains = relationship(
        "ThoughtChain",
        back_populates="context"
    )
    
    MemoryContext.child_contexts = relationship(
        "MemoryContext",
        foreign_keys="[MemoryContext.parent_context_id]",
        backref="parent_context",
        remote_side="MemoryContext.id"
    )
    
    # Отношения для Experience
    Experience.context = relationship(
        "MemoryContext",
        back_populates="experiences"
    )
    
    Experience.sender = relationship(
        "Participant",
        foreign_keys="[Experience.sender_participant_id]",
        back_populates="sent_experiences"
    )
    
    Experience.recipient = relationship(
        "Participant",
        foreign_keys="[Experience.to_participant_id]",
        back_populates="received_experiences"
    )
    
    Experience.parent_experience = relationship(
        "Experience",
        foreign_keys="[Experience.parent_experience_id]",
        backref="child_experiences",
        remote_side="Experience.id"
    )
    
    Experience.response_to = relationship(
        "Experience",
        foreign_keys="[Experience.response_to_experience_id]",
        backref="responses",
        remote_side="Experience.id"
    )
    
    Experience.initiated_thought_chains = relationship(
        "ThoughtChain",
        foreign_keys="[ThoughtChain.initial_experience_id]",
        back_populates="initial_experience"
    )
    
    Experience.source_connections = relationship(
        "ExperienceConnection",
        foreign_keys="[ExperienceConnection.source_experience_id]",
        backref="source_experience"
    )
    
    Experience.target_connections = relationship(
        "ExperienceConnection",
        foreign_keys="[ExperienceConnection.target_experience_id]",
        backref="target_experience"
    )
    
    # Расширение гибридных свойств для поддержки временных сущностей
    @Experience.effective_sender.expression
    def effective_sender_expression(cls):
        """
        Выражение SQL для гибридного свойства effective_sender.
        Позволяет использовать свойство в запросах.
        """
        return or_(
            cls.sender_participant_id != None,
            cls.provisional_sender != None
        )
    
    @Experience.effective_context.expression
    def effective_context_expression(cls):
        """
        Выражение SQL для гибридного свойства effective_context.
        Позволяет использовать свойство в запросах.
        """
        return or_(
            cls.context_id != None,
            cls.provisional_context != None
        )
    
    # Отношения для ThoughtChain
    ThoughtChain.context = relationship(
        "MemoryContext",
        back_populates="thought_chains"
    )
    
    ThoughtChain.initial_experience = relationship(
        "Experience",
        foreign_keys="[ThoughtChain.initial_experience_id]",
        back_populates="initiated_thought_chains"
    )
    
    # Отношения для InformationResource
    InformationResource.participant = relationship(
        "Participant",
        back_populates="resources"
    )
    
    # ExperienceConnection отношения уже установлены через backref


# Экспортируем модели для удобного импорта
__all__ = [
    'Participant',
    'MemoryContext',
    'Experience',
    'ExperienceType',
    'ExperienceCategory',
    'ThoughtChain',
    'InformationResource',
    'ExperienceConnection',
    'setup_consciousness_relationships'
]