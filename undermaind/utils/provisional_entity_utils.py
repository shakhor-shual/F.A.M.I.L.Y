"""
Утилиты для работы с временными (provisional) сущностями.

Этот модуль содержит функции для решения проблемы "Парадокса первичности" 
через механизм временных сущностей и их последующего связывания с постоянными.
"""

import os
import logging
from typing import Optional, Union, Dict, Any
from sqlalchemy.orm import Session

# Импортируем модели (предполагается, что эти классы существуют)
from ..models.consciousness.experiences import Experience, ExperienceType, ExperienceCategory
from ..models.consciousness.participants import Participant
from ..models.consciousness.contexts import MemoryContext


logger = logging.getLogger(__name__)


def reconcile_provisional_entities(
    session: Session, 
    experience_id: int,
    reconcile_sender: bool = True,
    reconcile_context: bool = True,
    default_participant_type: str = "human",
    default_context_type: str = None
) -> bool:
    """
    Преобразует временные (provisional) данные опыта в полноценные сущности.
    
    Позволяет создать сущности участника и/или контекста на основе временных данных
    в опыте и обновить связи. Решает проблему "Парадокса первичности", когда
    нельзя изначально создать сущность, от которой зависит опыт.
    
    Args:
        session: Сессия базы данных SQLAlchemy
        experience_id: ID опыта для преобразования временных данных
        reconcile_sender: Создавать ли сущность участника из provisional_sender
        reconcile_context: Создавать ли сущность контекста из provisional_context
        default_participant_type: Тип участника по умолчанию, если не определен
        default_context_type: Тип контекста по умолчанию (если None, определяется по типу опыта)
        
    Returns:
        bool: True если хотя бы одна сущность была создана, иначе False
    """
    # Получаем опыт по ID
    experience = session.query(Experience).get(experience_id)
    if not experience:
        logger.error(f"Опыт с ID {experience_id} не найден")
        return False
    
    created_entities = False
    
    # Обработка отправителя, если запрошено и есть временные данные
    if reconcile_sender and experience.provisional_sender and not experience.sender_participant_id:
        # Определяем тип участника на основе категории информации
        participant_type = _determine_participant_type(experience) or default_participant_type
        
        # Создаем нового участника на основе временных данных
        participant = Participant(
            name=experience.provisional_sender,
            participant_type=participant_type,
            is_ephemeral=False,  # Теперь это постоянная сущность
            description=f"Участник, созданный на основе временных данных из опыта {experience_id}",
            familiarity_level=1,  # Начальный уровень знакомства
            trust_level=0         # Нейтральный уровень доверия
        )
        
        session.add(participant)
        session.flush()  # Чтобы получить ID
        
        # Обновляем опыт, связывая его с новым участником
        experience.sender_participant_id = participant.id
        experience.provisional_sender = None  # Очищаем временные данные
        created_entities = True
        logger.info(f"Создан участник ID={participant.id} на основе временных данных из опыта ID={experience_id}")
    
    # Обработка контекста, если запрошено и есть временные данные
    if reconcile_context and experience.provisional_context and not experience.context_id:
        # Определяем тип контекста на основе типа опыта
        context_type = default_context_type or _determine_context_type(experience)
        
        # Создаем новый контекст на основе временных данных
        context = MemoryContext(
            title=experience.provisional_context,
            context_type=context_type,
            active_status=True,  # По умолчанию активный
            summary=f"Контекст, созданный на основе временных данных из опыта {experience_id}"
        )
        
        session.add(context)
        session.flush()  # Чтобы получить ID
        
        # Обновляем опыт, связывая его с новым контекстом
        experience.context_id = context.id
        experience.provisional_context = None  # Очищаем временные данные
        created_entities = True
        logger.info(f"Создан контекст ID={context.id} на основе временных данных из опыта ID={experience_id}")
    
    # Если были созданы сущности, обновляем тип происхождения опыта
    if created_entities:
        # Меняем тип только если все временные данные преобразованы
        if (not experience.provisional_sender or not reconcile_sender) and \
           (not experience.provisional_context or not reconcile_context):
            experience.provenance_type = ExperienceType.IDENTIFIED
            logger.info(f"Опыт ID={experience_id} преобразован из временного в идентифицированный")
    
        # Фиксируем изменения
        session.commit()
    
    return created_entities


def _determine_participant_type(experience: Experience) -> str:
    """
    Определяет тип участника на основе категории информации и типа опыта.
    
    Args:
        experience: Объект опыта
        
    Returns:
        str: Тип участника ('human', 'ami', 'system', 'resource', 'other')
    """
    # Используем информационную категорию для предположения типа
    category_to_type = {
        "agent": "human",   # Категория "Ты" обычно означает человека
        "object": "resource",  # Категория "Оно" обычно означает ресурс
        "self": "ami"       # Категория "Я" - это сам АМИ
    }
    
    # Получаем тип по категории или возвращаем human по умолчанию
    return category_to_type.get(experience.information_category, "human")


def _determine_context_type(experience: Experience) -> str:
    """
    Определяет тип контекста на основе типа опыта.
    
    Args:
        experience: Объект опыта
        
    Returns:
        str: Тип контекста ('conversation', 'task', 'research', etc.)
    """
    # Маппинг типов опыта на типы контекстов
    type_to_context = {
        "dialogue_incoming": "conversation",
        "dialogue_outgoing": "conversation",
        "thought": "internal_dialogue",
        "reflection": "reflection",
        "action": "task",
        "resource_access": "resource_interaction",
        "memory_recall": "reflection"
    }
    
    # Получаем тип по типу опыта или возвращаем 'other' по умолчанию
    return type_to_context.get(experience.experience_type, "other")


def create_experience_with_provisional_entities(
    session: Session,
    content: str,
    information_category: str,
    experience_type: str,
    provisional_sender: Optional[str] = None,
    provisional_context: Optional[str] = None,
    auto_reconcile: bool = True,
    **kwargs
) -> Experience:
    """
    Создает опыт с возможностью использования временных данных вместо реальных сущностей.
    
    Args:
        session: Сессия базы данных SQLAlchemy
        content: Содержимое опыта
        information_category: Категория информации ('self', 'agent', 'object')
        experience_type: Тип опыта ('dialogue_incoming', 'thought', etc.)
        provisional_sender: Временное описание отправителя
        provisional_context: Временное описание контекста
        auto_reconcile: Автоматически преобразовать временные данные в сущности
        **kwargs: Дополнительные параметры для опыта
        
    Returns:
        Experience: Созданный объект опыта
    """
    # Определяем тип происхождения
    has_provisional = bool(provisional_sender or provisional_context)
    provenance_type = ExperienceType.PROVISIONAL if has_provisional else ExperienceType.IDENTIFIED
    
    # Создаем опыт
    experience = Experience(
        content=content,
        information_category=information_category,
        experience_type=experience_type,
        provenance_type=provenance_type,
        provisional_sender=provisional_sender,
        provisional_context=provisional_context,
        **kwargs
    )
    
    session.add(experience)
    session.flush()  # Чтобы получить ID
    
    # Если запрошено автоматическое преобразование временных данных в сущности
    if auto_reconcile and has_provisional:
        reconcile_provisional_entities(
            session=session,
            experience_id=experience.id,
            reconcile_sender=bool(provisional_sender),
            reconcile_context=bool(provisional_context)
        )
    else:
        session.commit()
    
    return experience


def batch_reconcile_provisional_entities(
    session: Session,
    limit: int = 100,
    reconcile_sender: bool = True,
    reconcile_context: bool = True
) -> int:
    """
    Пакетное преобразование временных данных в сущности для всех подходящих опытов.
    
    Args:
        session: Сессия базы данных SQLAlchemy
        limit: Максимальное количество опытов для обработки за раз
        reconcile_sender: Создавать ли сущности участников
        reconcile_context: Создавать ли сущности контекстов
        
    Returns:
        int: Количество успешно обработанных опытов
    """
    # Находим опыты с временными данными
    query = session.query(Experience).filter(Experience.provenance_type == ExperienceType.PROVISIONAL)
    
    if reconcile_sender and not reconcile_context:
        query = query.filter(Experience.provisional_sender != None)
    elif not reconcile_sender and reconcile_context:
        query = query.filter(Experience.provisional_context != None)
    else:
        # Если обе опции включены, ищем опыты с любыми временными данными
        query = query.filter((Experience.provisional_sender != None) | (Experience.provisional_context != None))
    
    # Ограничиваем количество опытов для пакетной обработки
    experiences = query.limit(limit).all()
    
    processed_count = 0
    for exp in experiences:
        if reconcile_provisional_entities(
            session=session,
            experience_id=exp.id,
            reconcile_sender=reconcile_sender,
            reconcile_context=reconcile_context
        ):
            processed_count += 1
    
    return processed_count