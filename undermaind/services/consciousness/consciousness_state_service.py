"""
Сервис управления состоянием сознания АМИ (ConsciousnessStateService).

Этот модуль реализует управление текущим состоянием сознания АМИ,
включая фокус внимания, активные процессы мышления и мониторинг контекстов.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple, Union, Set
from datetime import datetime, timedelta
from sqlalchemy import func, desc, asc, and_, or_, not_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from undermaind.models.consciousness.experience import Experience
from undermaind.models.consciousness.experience_contexts import ExperienceContext
from undermaind.models.consciousness.thinking_process import ThinkingProcess
from undermaind.models.consciousness.thinking_phase import ThinkingPhase
from undermaind.services.base import BaseService
from undermaind.core.session import SessionManager

logger = logging.getLogger(__name__)


class ThinkingProcessNotFoundError(Exception):
    """Исключение, вызываемое когда процесс мышления не найден."""
    pass


class InvalidStateTransitionError(Exception):
    """Исключение, вызываемое при попытке недопустимого перехода состояния."""
    pass


class ConsciousnessStateService(BaseService):
    """
    Сервис для управления состоянием сознания АМИ.
    
    Этот сервис отвечает за управление фокусом внимания, отслеживание активных 
    процессов мышления, координацию переключения контекстов и мониторинг состояния сознания.
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Инициализация сервиса управления состоянием сознания.
        
        Args:
            session_manager: Менеджер сессий для работы с БД
        """
        super().__init__(session_manager)
    
    # === Методы для работы с фокусом внимания ===
    
    def set_focus_on_experience(self, 
                               experience_id: int, 
                               focus_intensity: int = 100,
                               meta_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Установка фокуса внимания на конкретный опыт.
        
        Args:
            experience_id: ID опыта для фокусировки
            focus_intensity: Интенсивность фокуса (от 1 до 100)
            meta_data: Дополнительные метаданные для сохранения
            
        Returns:
            Dict[str, Any]: Информация о текущем фокусе
            
        Raises:
            ValueError: Если опыт не найден или параметры некорректны
        """
        # Проверяем корректность параметров
        if not 1 <= focus_intensity <= 100:
            raise ValueError("Интенсивность фокуса должна быть от 1 до 100")
        
        def _set_focus(session: Session) -> Dict[str, Any]:
            # Проверяем существование опыта
            experience = session.query(Experience).filter(Experience.id == experience_id).first()
            if not experience:
                raise ValueError(f"Опыт с ID {experience_id} не найден")
            
            # Создаем запись о фокусе внимания
            now = datetime.now()
            focus_data = {
                "experience_id": experience_id,
                "focus_intensity": focus_intensity,
                "timestamp": now.isoformat(),
                "context_id": experience.context_id,
                "experience_type": experience.experience_type,
                "meta_data": meta_data or {}
            }
            
            # В реальной системе здесь будет сохранение в отдельную таблицу,
            # но для прототипа можно использовать сессионный кеш или временную таблицу
            # Временное решение - сохраняем последний фокус в атрибуты сессии
            session.info["current_focus"] = focus_data
            
            # Обновляем опыт, увеличивая счётчик обращений
            experience.access_count = (experience.access_count or 0) + 1
            experience.last_accessed = now
            
            # Если у опыта есть контекст, активируем его
            if experience.context_id:
                context = session.query(ExperienceContext).filter(
                    ExperienceContext.id == experience.context_id
                ).first()
                
                if context and not context.active_status:
                    context.active_status = True
            
            return focus_data
        
        return self._execute_in_transaction(_set_focus)
    
    def get_current_focus(self) -> Optional[Dict[str, Any]]:
        """
        Получение информации о текущем фокусе внимания.
        
        Returns:
            Optional[Dict[str, Any]]: Информация о текущем фокусе или None, если фокус не установлен
        """
        def _get_focus(session: Session) -> Optional[Dict[str, Any]]:
            # В реальной системе здесь будет запрос к таблице фокусов внимания
            # Временное решение - получаем последний фокус из атрибутов сессии
            return session.info.get("current_focus")
        
        return self._execute_in_transaction(_get_focus)
    
    def clear_focus(self) -> bool:
        """
        Сброс текущего фокуса внимания.
        
        Returns:
            bool: True, если фокус был успешно сброшен
        """
        def _clear_focus(session: Session) -> bool:
            # В реальной системе здесь будет обновление таблицы фокусов внимания
            # Временное решение - удаляем последний фокус из атрибутов сессии
            if "current_focus" in session.info:
                del session.info["current_focus"]
                return True
            return False
        
        return self._execute_in_transaction(_clear_focus)
    
    # === Методы для работы с мыслительными процессами ===
    
    def create_thinking_process(self,
                              title: str,
                              process_type: str,
                              description: Optional[str] = None,
                              context_id: Optional[int] = None,
                              initial_phase_title: Optional[str] = None,
                              meta_data: Optional[Dict[str, Any]] = None) -> ThinkingProcess:
        """
        Создание нового процесса мышления.
        
        Args:
            title: Название процесса мышления
            process_type: Тип процесса (reasoning, problem_solving, reflection и т.д.)
            description: Описание процесса
            context_id: ID связанного контекста
            initial_phase_title: Название начальной фазы (если нужно создать)
            meta_data: Дополнительные метаданные
            
        Returns:
            ThinkingProcess: Созданный процесс мышления
            
        Raises:
            ValueError: Если параметры некорректны
        """
        if not title or not title.strip():
            raise ValueError("Название процесса мышления не может быть пустым")
        
        if not process_type or not process_type.strip():
            raise ValueError("Тип процесса мышления должен быть указан")
        
        def _create_process(session: Session) -> ThinkingProcess:
            # Если указан контекст, проверяем его существование
            if context_id:
                context = session.query(ExperienceContext).filter(
                    ExperienceContext.id == context_id
                ).first()
                
                if not context:
                    raise ValueError(f"Контекст с ID {context_id} не найден")
            
            # Создаем новый процесс мышления
            process = ThinkingProcess(
                title=title,
                process_type=process_type,
                description=description,
                context_id=context_id,
                start_time=datetime.now(),
                status="active",
                progress_percentage=0,
                meta_data=meta_data or {}
            )
            
            session.add(process)
            session.flush()  # Получаем ID процесса
            
            # Если указано название начальной фазы, создаем её
            if initial_phase_title:
                phase = ThinkingPhase(
                    thinking_process_id=process.id,
                    title=initial_phase_title,
                    phase_order=1,
                    start_time=datetime.now(),
                    status="active"
                )
                
                session.add(phase)
                
                # Связываем с процессом
                process.current_phase_id = phase.id
            
            return process
        
        return self._execute_in_transaction(_create_process)
    
    def get_thinking_process(self, process_id: int) -> ThinkingProcess:
        """
        Получение процесса мышления по ID.
        
        Args:
            process_id: ID процесса мышления
            
        Returns:
            ThinkingProcess: Объект процесса мышления
            
        Raises:
            ThinkingProcessNotFoundError: Если процесс не найден
        """
        def _get_process(session: Session) -> ThinkingProcess:
            process = session.query(ThinkingProcess).filter(ThinkingProcess.id == process_id).first()
            
            if not process:
                raise ThinkingProcessNotFoundError(f"Процесс мышления с ID {process_id} не найден")
                
            return process
        
        return self._execute_in_transaction(_get_process)
    
    def update_thinking_process(self, 
                              process_id: int,
                              progress_percentage: Optional[int] = None,
                              status: Optional[str] = None,
                              meta_data: Optional[Dict[str, Any]] = None) -> ThinkingProcess:
        """
        Обновление параметров процесса мышления.
        
        Args:
            process_id: ID процесса мышления
            progress_percentage: Процент выполнения (от 0 до 100)
            status: Статус процесса (active, paused, completed, failed)
            meta_data: Дополнительные метаданные для обновления
            
        Returns:
            ThinkingProcess: Обновленный процесс мышления
            
        Raises:
            ThinkingProcessNotFoundError: Если процесс не найден
            ValueError: Если параметры некорректны
        """
        # Проверяем корректность параметров
        if progress_percentage is not None and not 0 <= progress_percentage <= 100:
            raise ValueError("Процент выполнения должен быть от 0 до 100")
        
        valid_statuses = ["active", "paused", "completed", "failed"]
        if status is not None and status not in valid_statuses:
            raise ValueError(f"Недопустимый статус. Допустимые значения: {', '.join(valid_statuses)}")
        
        def _update_process(session: Session) -> ThinkingProcess:
            process = session.query(ThinkingProcess).filter(ThinkingProcess.id == process_id).first()
            
            if not process:
                raise ThinkingProcessNotFoundError(f"Процесс мышления с ID {process_id} не найден")
            
            # Обновляем поля процесса
            if progress_percentage is not None:
                process.progress_percentage = progress_percentage
            
            if status is not None:
                process.status = status
                
                # Если процесс завершен, устанавливаем время завершения
                if status in ["completed", "failed"]:
                    process.end_time = datetime.now()
            
            # Обновляем метаданные
            if meta_data:
                if not process.meta_data:
                    process.meta_data = {}
                process.meta_data.update(meta_data)
            
            # Всегда обновляем время последнего изменения
            process.last_updated = datetime.now()
            
            return process
        
        return self._execute_in_transaction(_update_process)
    
    def add_thinking_phase(self,
                          process_id: int,
                          title: str,
                          description: Optional[str] = None,
                          make_active: bool = True) -> ThinkingPhase:
        """
        Добавление новой фазы в процесс мышления.
        
        Args:
            process_id: ID процесса мышления
            title: Название фазы
            description: Описание фазы
            make_active: Сделать ли фазу активной
            
        Returns:
            ThinkingPhase: Созданная фаза мышления
            
        Raises:
            ThinkingProcessNotFoundError: Если процесс не найден
            ValueError: Если параметры некорректны
        """
        if not title or not title.strip():
            raise ValueError("Название фазы не может быть пустым")
        
        def _add_phase(session: Session) -> ThinkingPhase:
            # Проверяем существование процесса
            process = session.query(ThinkingProcess).filter(ThinkingProcess.id == process_id).first()
            
            if not process:
                raise ThinkingProcessNotFoundError(f"Процесс мышления с ID {process_id} не найден")
            
            # Определяем порядковый номер новой фазы
            max_order = session.query(func.max(ThinkingPhase.phase_order)).filter(
                ThinkingPhase.thinking_process_id == process_id
            ).scalar() or 0
            
            # Создаем новую фазу
            phase = ThinkingPhase(
                thinking_process_id=process_id,
                title=title,
                description=description,
                phase_order=max_order + 1,
                start_time=datetime.now(),
                status="active"
            )
            
            session.add(phase)
            session.flush()  # Получаем ID фазы
            
            # Если нужно активировать эту фазу
            if make_active:
                # Деактивируем текущую активную фазу, если она есть
                if process.current_phase_id:
                    current_phase = session.query(ThinkingPhase).filter(
                        ThinkingPhase.id == process.current_phase_id
                    ).first()
                    
                    if current_phase:
                        current_phase.status = "completed"
                        current_phase.end_time = datetime.now()
                
                # Устанавливаем новую активную фазу
                process.current_phase_id = phase.id
                process.last_updated = datetime.now()
            
            return phase
        
        return self._execute_in_transaction(_add_phase)
    
    def complete_thinking_phase(self,
                               phase_id: int,
                               conclusion: Optional[str] = None,
                               outcome: Optional[Dict[str, Any]] = None) -> ThinkingPhase:
        """
        Завершение фазы процесса мышления.
        
        Args:
            phase_id: ID фазы процесса мышления
            conclusion: Заключение по результатам фазы
            outcome: Результаты фазы
            
        Returns:
            ThinkingPhase: Обновленная фаза мышления
            
        Raises:
            ValueError: Если фаза не найдена
        """
        def _complete_phase(session: Session) -> ThinkingPhase:
            # Получаем фазу
            phase = session.query(ThinkingPhase).filter(ThinkingPhase.id == phase_id).first()
            
            if not phase:
                raise ValueError(f"Фаза мышления с ID {phase_id} не найдена")
            
            # Проверяем, что фаза активна
            if phase.status != "active":
                raise InvalidStateTransitionError(
                    f"Нельзя завершить фазу в статусе '{phase.status}'"
                )
            
            # Обновляем статус фазы
            phase.status = "completed"
            phase.end_time = datetime.now()
            phase.conclusion = conclusion
            
            # Сохраняем результаты
            if outcome:
                phase.outcome = outcome
            
            # Обновляем процесс мышления
            process = session.query(ThinkingProcess).filter(
                ThinkingProcess.id == phase.thinking_process_id
            ).first()
            
            if process:
                # Если это была активная фаза, обнуляем current_phase_id
                if process.current_phase_id == phase_id:
                    process.current_phase_id = None
                
                process.last_updated = datetime.now()
                
                # Проверяем, есть ли ещё активные фазы
                active_phases = session.query(func.count(ThinkingPhase.id)).filter(
                    ThinkingPhase.thinking_process_id == process.id,
                    ThinkingPhase.status == "active"
                ).scalar()
                
                # Если активных фаз больше нет, возможно процесс завершен
                if active_phases == 0:
                    # Получаем общее количество фаз
                    total_phases = session.query(func.count(ThinkingPhase.id)).filter(
                        ThinkingPhase.thinking_process_id == process.id
                    ).scalar()
                    
                    # Получаем количество завершенных фаз
                    completed_phases = session.query(func.count(ThinkingPhase.id)).filter(
                        ThinkingPhase.thinking_process_id == process.id,
                        ThinkingPhase.status == "completed"
                    ).scalar()
                    
                    # Обновляем прогресс выполнения
                    if total_phases > 0:
                        process.progress_percentage = int((completed_phases / total_phases) * 100)
                    
                    # Если все фазы завершены, завершаем процесс
                    if completed_phases == total_phases:
                        process.status = "completed"
                        process.end_time = datetime.now()
            
            return phase
        
        return self._execute_in_transaction(_complete_phase)
    
    def get_active_thinking_processes(self) -> List[ThinkingProcess]:
        """
        Получение списка активных процессов мышления.
        
        Returns:
            List[ThinkingProcess]: Список активных процессов мышления
        """
        def _get_active_processes(session: Session) -> List[ThinkingProcess]:
            return session.query(ThinkingProcess).filter(
                ThinkingProcess.status == "active"
            ).all()
        
        return self._execute_in_transaction(_get_active_processes)
    
    # === Методы для работы с контекстами сознания ===
    
    def get_active_contexts(self) -> List[ExperienceContext]:
        """
        Получение списка активных контекстов.
        
        Returns:
            List[ExperienceContext]: Список активных контекстов
        """
        def _get_active_contexts(session: Session) -> List[ExperienceContext]:
            return session.query(ExperienceContext).filter(
                ExperienceContext.active_status == True
            ).all()
        
        return self._execute_in_transaction(_get_active_contexts)
    
    def activate_context(self, context_id: int) -> ExperienceContext:
        """
        Активация контекста.
        
        Args:
            context_id: ID контекста для активации
            
        Returns:
            ExperienceContext: Активированный контекст
            
        Raises:
            ValueError: Если контекст не найден
        """
        def _activate_context(session: Session) -> ExperienceContext:
            context = session.query(ExperienceContext).filter(
                ExperienceContext.id == context_id
            ).first()
            
            if not context:
                raise ValueError(f"Контекст с ID {context_id} не найден")
            
            # Активируем контекст, если он не активен
            if not context.active_status:
                context.active_status = True
                context.last_activated = datetime.now()
            
            return context
        
        return self._execute_in_transaction(_activate_context)
    
    def deactivate_context(self, context_id: int) -> ExperienceContext:
        """
        Деактивация контекста.
        
        Args:
            context_id: ID контекста для деактивации
            
        Returns:
            ExperienceContext: Деактивированный контекст
            
        Raises:
            ValueError: Если контекст не найден
        """
        def _deactivate_context(session: Session) -> ExperienceContext:
            context = session.query(ExperienceContext).filter(
                ExperienceContext.id == context_id
            ).first()
            
            if not context:
                raise ValueError(f"Контекст с ID {context_id} не найден")
            
            # Деактивируем контекст, если он активен
            if context.active_status:
                context.active_status = False
            
            return context
        
        return self._execute_in_transaction(_deactivate_context)
    
    def switch_active_context(self, new_context_id: int) -> Tuple[ExperienceContext, List[ExperienceContext]]:
        """
        Переключение активного контекста.
        
        Деактивирует все активные контексты, кроме родительских для нового,
        и активирует новый контекст и все его родительские контексты.
        
        Args:
            new_context_id: ID нового активного контекста
            
        Returns:
            Tuple[ExperienceContext, List[ExperienceContext]]: Новый активный контекст и список деактивированных
            
        Raises:
            ValueError: Если контекст не найден
        """
        def _switch_context(session: Session) -> Tuple[ExperienceContext, List[ExperienceContext]]:
            # Получаем новый контекст
            new_context = session.query(ExperienceContext).filter(
                ExperienceContext.id == new_context_id
            ).first()
            
            if not new_context:
                raise ValueError(f"Контекст с ID {new_context_id} не найден")
            
            # Получаем цепочку родительских контекстов
            parent_ids = []
            current_id = new_context.parent_context_id
            
            while current_id:
                parent_ids.append(current_id)
                parent = session.query(ExperienceContext.parent_context_id).filter(
                    ExperienceContext.id == current_id
                ).first()
                current_id = parent[0] if parent else None
            
            # Деактивируем все активные контексты, кроме родительских
            deactivated = []
            active_contexts = session.query(ExperienceContext).filter(
                ExperienceContext.active_status == True,
                ~ExperienceContext.id.in_([new_context_id] + parent_ids)
            ).all()
            
            for context in active_contexts:
                context.active_status = False
                deactivated.append(context)
            
            # Активируем новый контекст
            if not new_context.active_status:
                new_context.active_status = True
                new_context.last_activated = datetime.now()
            
            # Активируем все родительские контексты
            if parent_ids:
                session.query(ExperienceContext).filter(
                    ExperienceContext.id.in_(parent_ids),
                    ExperienceContext.active_status == False
                ).update(
                    {ExperienceContext.active_status: True, 
                     ExperienceContext.last_activated: datetime.now()},
                    synchronize_session=False
                )
            
            return new_context, deactivated
        
        return self._execute_in_transaction(_switch_context)
    
    # === Методы мониторинга состояния сознания ===
    
    def get_consciousness_state(self) -> Dict[str, Any]:
        """
        Получение текущего состояния сознания АМИ.
        
        Returns:
            Dict[str, Any]: Информация о текущем состоянии сознания
        """
        def _get_state(session: Session) -> Dict[str, Any]:
            # Получаем текущий фокус
            current_focus = session.info.get("current_focus")
            
            # Получаем активные контексты
            active_contexts = session.query(ExperienceContext).filter(
                ExperienceContext.active_status == True
            ).all()
            
            # Получаем активные процессы мышления
            active_processes = session.query(ThinkingProcess).filter(
                ThinkingProcess.status == "active"
            ).all()
            
            # Собираем информацию о недавнем опыте (последние 5 доступов)
            recent_experiences = session.query(Experience).order_by(
                desc(Experience.last_accessed)
            ).limit(5).all()
            
            # Формируем результат
            state = {
                "timestamp": datetime.now().isoformat(),
                "focus": current_focus,
                "active_contexts": [
                    {
                        "id": ctx.id,
                        "title": ctx.title,
                        "context_type": ctx.context_type,
                        "last_activated": ctx.last_activated.isoformat() if ctx.last_activated else None
                    } for ctx in active_contexts
                ],
                "active_thinking_processes": [
                    {
                        "id": proc.id,
                        "title": proc.title,
                        "process_type": proc.process_type,
                        "progress_percentage": proc.progress_percentage,
                        "current_phase_id": proc.current_phase_id
                    } for proc in active_processes
                ],
                "recent_experiences": [
                    {
                        "id": exp.id,
                        "content": exp.content[:100] + "..." if len(exp.content) > 100 else exp.content,
                        "experience_type": exp.experience_type,
                        "last_accessed": exp.last_accessed.isoformat() if exp.last_accessed else None
                    } for exp in recent_experiences
                ]
            }
            
            return state
        
        return self._execute_in_transaction(_get_state)