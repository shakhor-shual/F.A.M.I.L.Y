"""
Интеграционные тесты для MemoryNetworkService.

Проверяет функциональность сервиса управления сетью связей,
включая создание и укрепление связей, поиск путей между опытами,
анализ сети связей и контекстную группировку опытов.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from undermaind.services.consciousness.memory_network_service import (
    MemoryNetworkService,
    ConnectionNotFoundError,
    NetworkAnalysisError
)
from undermaind.models.consciousness import (
    Experience,
    ExperienceConnection,
    ExperienceContext
)


@pytest.mark.integration
class TestMemoryNetworkService:
    """Тесты для сервиса управления сетью связей."""
    
    @pytest.fixture
    def service(self):
        """Фикстура, создающая экземпляр сервиса для тестов."""
        return MemoryNetworkService()
    
    @pytest.fixture
    def context(self, db_session_postgres):
        """Фикстура, создающая тестовый контекст."""
        context = ExperienceContext(
            title="Тестовый контекст для сети связей",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION
        )
        db_session_postgres.add(context)
        db_session_postgres.commit()
        return context
    
    @pytest.fixture
    def experiences(self, db_session_postgres, context):
        """Фикстура, создающая набор тестовых опытов для тестирования сети связей."""
        exp1 = Experience(
            content="Первый опыт в сети",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            context_id=context.id
        )
        exp2 = Experience(
            content="Второй опыт в сети",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            context_id=context.id
        )
        exp3 = Experience(
            content="Третий опыт в сети",
            experience_type=Experience.TYPE_PERCEPTION,
            information_category=Experience.CATEGORY_SUBJECT
        )
        exp4 = Experience(
            content="Четвертый опыт в сети",
            experience_type=Experience.TYPE_COMMUNICATION,
            information_category=Experience.CATEGORY_SUBJECT
        )
        exp5 = Experience(
            content="Пятый опыт в сети",
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF
        )
        
        db_session_postgres.add_all([exp1, exp2, exp3, exp4, exp5])
        db_session_postgres.commit()
        
        return [exp1, exp2, exp3, exp4, exp5]
    
    def test_create_connection(self, service, experiences):
        """Проверка создания связи между опытами."""
        # Создаем связь между опытами
        connection = service.create_connection(
            source_id=experiences[0].id,
            target_id=experiences[1].id,
            connection_type=ExperienceConnection.TYPE_SEMANTIC,
            strength=8,
            description="Тестовая семантическая связь"
        )
        
        # Проверяем параметры созданной связи
        assert connection is not None, "Связь должна быть создана"
        assert connection.id is not None, "Связь должна иметь ID"
        assert connection.source_experience_id == experiences[0].id, "ID источника должен соответствовать"
        assert connection.target_experience_id == experiences[1].id, "ID цели должен соответствовать"
        assert connection.connection_type == ExperienceConnection.TYPE_SEMANTIC, "Тип связи должен соответствовать"
        assert connection.strength == 8, "Сила связи должна соответствовать"
        assert connection.description == "Тестовая семантическая связь", "Описание должно соответствовать"
        assert connection.direction == ExperienceConnection.DIRECTION_UNI, "По умолчанию связь должна быть однонаправленной"
        assert connection.conscious_status is True, "По умолчанию связь должна быть осознаваемой"
    
    def test_create_bidirectional_connection(self, service, experiences):
        """Проверка создания двунаправленной связи между опытами."""
        # Создаем двунаправленную связь
        connection = service.create_connection(
            source_id=experiences[1].id,
            target_id=experiences[2].id,
            connection_type=ExperienceConnection.TYPE_CAUSAL,
            bidirectional=True,
            strength=7
        )
        
        # Проверяем, что связь двунаправленная
        assert connection.direction == ExperienceConnection.DIRECTION_BI, "Связь должна быть двунаправленной"
    
    def test_update_existing_connection(self, service, experiences, db_session_postgres):
        """Проверка обновления существующей связи."""
        # Сначала создаем связь
        connection = service.create_connection(
            source_id=experiences[2].id,
            target_id=experiences[3].id,
            connection_type=ExperienceConnection.TYPE_TEMPORAL,
            strength=5
        )
        
        # Запоминаем ID и количество активаций
        connection_id = connection.id
        initial_activations = connection.activation_count
        
        # Обновляем существующую связь
        updated_connection = service.create_connection(
            source_id=experiences[2].id,
            target_id=experiences[3].id,
            connection_type=ExperienceConnection.TYPE_TEMPORAL,
            strength=8,
            description="Обновленная связь"
        )
        
        # Проверяем, что это та же связь, но обновленная
        assert updated_connection.id == connection_id, "ID связи должен остаться тем же"
        assert updated_connection.strength == 8, "Сила связи должна быть обновлена"
        assert updated_connection.description == "Обновленная связь", "Описание должно быть обновлено"
        assert updated_connection.activation_count > initial_activations, "Счетчик активаций должен быть увеличен"
        
        # Проверяем состояние в БД
        db_connection = db_session_postgres.query(ExperienceConnection).filter_by(id=connection_id).first()
        assert db_connection.strength == 8, "Сила связи должна быть обновлена в БД"
    
    def test_get_connection(self, service, experiences, db_session_postgres):
        """Проверка получения связи по ID."""
        # Создаем связь
        connection = ExperienceConnection(
            source_experience_id=experiences[3].id,
            target_experience_id=experiences[4].id,
            connection_type=ExperienceConnection.TYPE_ASSOCIATIVE,
            strength=6
        )
        db_session_postgres.add(connection)
        db_session_postgres.commit()
        
        # Получаем связь по ID
        retrieved_connection = service.get_connection(connection.id)
        
        # Проверяем, что получили ту же связь
        assert retrieved_connection.id == connection.id, "ID должны совпадать"
        assert retrieved_connection.source_experience_id == experiences[3].id, "ID источника должен соответствовать"
        assert retrieved_connection.target_experience_id == experiences[4].id, "ID цели должен соответствовать"
        
        # Проверяем поведение с несуществующим ID
        with pytest.raises(ConnectionNotFoundError):
            service.get_connection(99999)
    
    def test_update_connection_strength(self, service, experiences, db_session_postgres):
        """Проверка обновления силы существующей связи."""
        # Создаем связь
        connection = ExperienceConnection(
            source_experience_id=experiences[0].id,
            target_experience_id=experiences[4].id,
            connection_type=ExperienceConnection.TYPE_SEMANTIC,
            strength=4
        )
        db_session_postgres.add(connection)
        db_session_postgres.commit()
        
        initial_activations = connection.activation_count
        
        # Обновляем силу связи
        updated = service.update_connection_strength(connection.id, 9)
        
        # Проверяем, что сила связи обновлена
        assert updated.strength == 9, "Сила связи должна быть обновлена"
        assert updated.activation_count > initial_activations, "Счетчик активаций должен быть увеличен"
        
        # Проверяем состояние в БД
        db_connection = db_session_postgres.query(ExperienceConnection).filter_by(id=connection.id).first()
        assert db_connection.strength == 9, "Сила связи должна быть обновлена в БД"
        
        # Проверяем валидацию значения
        with pytest.raises(ValueError):
            service.update_connection_strength(connection.id, 11)  # Сила связи > 10
            
        with pytest.raises(ValueError):
            service.update_connection_strength(connection.id, 0)   # Сила связи < 1
            
        # Проверяем поведение с несуществующим ID
        with pytest.raises(ConnectionNotFoundError):
            service.update_connection_strength(99999, 5)
    
    def test_activate_connection(self, service, experiences, db_session_postgres):
        """Проверка активации связи (увеличение счетчика активаций)."""
        # Создаем связь
        connection = ExperienceConnection(
            source_experience_id=experiences[1].id,
            target_experience_id=experiences[3].id,
            connection_type=ExperienceConnection.TYPE_CAUSAL,
            strength=5
        )
        db_session_postgres.add(connection)
        db_session_postgres.commit()
        
        initial_activations = connection.activation_count
        initial_timestamp = connection.last_activated
        
        # Делаем небольшую паузу для гарантии отличия timestamp
        import time
        time.sleep(0.1)
        
        # Активируем связь
        activated = service.activate_connection(connection.id)
        
        # Проверяем, что счетчик активаций увеличен
        assert activated.activation_count > initial_activations, "Счетчик активаций должен быть увеличен"
        assert activated.last_activated > initial_timestamp, "Время последней активации должно быть обновлено"
        
        # Проверяем состояние в БД
        db_connection = db_session_postgres.query(ExperienceConnection).filter_by(id=connection.id).first()
        assert db_connection.activation_count > initial_activations, "Счетчик активаций должен быть увеличен в БД"
    
    def test_find_connected_experiences(self, service, experiences, db_session_postgres):
        """Проверка поиска связанных опытов."""
        # Создаем центральный опыт и набор связей с ним
        central = experiences[0]
        
        # Создаем разные типы связей
        connections = [
            ExperienceConnection(
                source_experience_id=central.id,
                target_experience_id=experiences[1].id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=9,
                conscious_status=True
            ),
            ExperienceConnection(
                source_experience_id=central.id,
                target_experience_id=experiences[2].id,
                connection_type=ExperienceConnection.TYPE_TEMPORAL,
                strength=3,
                conscious_status=False
            ),
            ExperienceConnection(
                source_experience_id=experiences[3].id,
                target_experience_id=central.id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=7,
                conscious_status=True
            ),
            ExperienceConnection(
                source_experience_id=experiences[4].id,
                target_experience_id=central.id,
                connection_type=ExperienceConnection.TYPE_ASSOCIATIVE,
                strength=4,
                conscious_status=False
            )
        ]
        
        db_session_postgres.add_all(connections)
        db_session_postgres.commit()
        
        # Ищем все связанные опыты
        all_connected = service.find_connected_experiences(central.id)
        assert len(all_connected) == 4, "Должны быть найдены все 4 связанных опыта"
        
        # Проверяем фильтрацию по типу связи
        semantic_connected = service.find_connected_experiences(
            central.id,
            connection_types=[ExperienceConnection.TYPE_SEMANTIC]
        )
        assert len(semantic_connected) == 1, "Должен быть найден 1 семантически связанный опыт"
        
        # Проверяем фильтрацию по минимальной силе
        strong_connected = service.find_connected_experiences(
            central.id,
            min_strength=7
        )
        assert len(strong_connected) == 2, "Должны быть найдены 2 сильно связанных опыта"
        
        # Проверяем фильтрацию по осознаваемым связям
        conscious_connected = service.find_connected_experiences(
            central.id,
            only_conscious=True
        )
        assert len(conscious_connected) == 2, "Должны быть найдены 2 осознаваемо связанных опыта"
        
        # Проверяем комбинированную фильтрацию
        combined_filter = service.find_connected_experiences(
            central.id,
            min_strength=7,
            only_conscious=True
        )
        assert len(combined_filter) == 2, "Должны быть найдены 2 опыта"
    
    def test_find_path_between_experiences(self, service, experiences, db_session_postgres):
        """Проверка поиска путей между опытами."""
        # Создаем цепочку связей
        connections = [
            # Прямой путь: 0 -> 1 -> 2 -> 4
            ExperienceConnection(
                source_experience_id=experiences[0].id,
                target_experience_id=experiences[1].id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=8
            ),
            ExperienceConnection(
                source_experience_id=experiences[1].id,
                target_experience_id=experiences[2].id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=7
            ),
            ExperienceConnection(
                source_experience_id=experiences[2].id,
                target_experience_id=experiences[4].id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=6
            ),
            
            # Альтернативный путь: 0 -> 3 -> 4
            ExperienceConnection(
                source_experience_id=experiences[0].id,
                target_experience_id=experiences[3].id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=5
            ),
            ExperienceConnection(
                source_experience_id=experiences[3].id,
                target_experience_id=experiences[4].id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=4
            )
        ]
        
        db_session_postgres.add_all(connections)
        db_session_postgres.commit()
        
        # Ищем пути между начальным и конечным опытом
        paths = service.find_path_between_experiences(
            experiences[0].id,
            experiences[4].id,
            max_depth=3
        )
        
        # Проверяем, что найдены оба пути
        assert len(paths) == 2, "Должны быть найдены оба пути между опытами"
        
        # Проверяем пути с учетом минимальной силы связей
        strong_paths = service.find_path_between_experiences(
            experiences[0].id,
            experiences[4].id,
            min_strength=6
        )
        assert len(strong_paths) == 1, "Должен быть найден только один путь с сильными связями"
        
        # Проверяем обработку ошибок
        with pytest.raises(ValueError):
            service.find_path_between_experiences(99999, experiences[4].id)
            
        with pytest.raises(ValueError):
            service.find_path_between_experiences(experiences[0].id, 99999)
    
    def test_find_experiences_by_context_proximity(self, service, db_session_postgres):
        """Проверка поиска опытов, близких по контексту."""
        # Создаем иерархию контекстов
        parent_ctx = ExperienceContext(
            title="Родительский контекст",
            context_type=ExperienceContext.CONTEXT_TYPE_PROJECT
        )
        db_session_postgres.add(parent_ctx)
        db_session_postgres.flush()
        
        child_ctx1 = ExperienceContext(
            title="Дочерний контекст 1",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION,
            parent_context_id=parent_ctx.id
        )
        
        child_ctx2 = ExperienceContext(
            title="Дочерний контекст 2",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION,
            parent_context_id=parent_ctx.id
        )
        
        db_session_postgres.add_all([child_ctx1, child_ctx2])
        db_session_postgres.flush()
        
        grandchild_ctx = ExperienceContext(
            title="Контекст-внук",
            context_type=ExperienceContext.CONTEXT_TYPE_CONVERSATION,
            parent_context_id=child_ctx1.id
        )
        db_session_postgres.add(grandchild_ctx)
        db_session_postgres.commit()
        
        # Создаем опыты в разных контекстах
        exp1 = Experience(
            content="Опыт в родительском контексте",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=parent_ctx.id
        )
        
        exp2 = Experience(
            content="Опыт в дочернем контексте 1",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=child_ctx1.id
        )
        
        exp3 = Experience(
            content="Опыт в дочернем контексте 2",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=child_ctx2.id
        )
        
        exp4 = Experience(
            content="Опыт в контексте-внуке",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=grandchild_ctx.id
        )
        
        exp5 = Experience(
            content="Опыт без контекста",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=None
        )
        
        db_session_postgres.add_all([exp1, exp2, exp3, exp4, exp5])
        db_session_postgres.commit()
        
        # Ищем опыты, близкие по контексту к опыту в дочернем контексте 1
        similar_to_child1 = service.find_experiences_by_context_proximity(exp2.id, max_distance=1)
        
        # Должны найти опыт из родительского контекста и опыт из контекста-внука
        assert len(similar_to_child1) == 2, "Должны быть найдены 2 контекстно-близких опыта"
        found_ids = [e.id for e in similar_to_child1]
        assert exp1.id in found_ids, "Должен быть найден опыт из родительского контекста"
        assert exp4.id in found_ids, "Должен быть найден опыт из контекста-внука"
        
        # Ищем с большей глубиной
        similar_to_parent = service.find_experiences_by_context_proximity(exp1.id, max_distance=2)
        assert len(similar_to_parent) >= 3, "Должны быть найдены все связанные контекстно опыты"
    
    def test_calculate_experience_centrality(self, service, experiences, db_session_postgres):
        """Проверка расчета центральности опыта в сети связей."""
        # Создаем сеть связей с центральным узлом
        central = experiences[2]
        
        # Создаем направленные связи от центрального узла
        outgoing = [
            ExperienceConnection(
                source_experience_id=central.id,
                target_experience_id=experiences[0].id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=8
            ),
            ExperienceConnection(
                source_experience_id=central.id,
                target_experience_id=experiences[1].id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=7
            )
        ]
        
        # Создаем направленные связи к центральному узлу
        incoming = [
            ExperienceConnection(
                source_experience_id=experiences[3].id,
                target_experience_id=central.id,
                connection_type=ExperienceConnection.TYPE_TEMPORAL,
                strength=6
            ),
            ExperienceConnection(
                source_experience_id=experiences[4].id,
                target_experience_id=central.id,
                connection_type=ExperienceConnection.TYPE_ASSOCIATIVE,
                strength=5
            )
        ]
        
        db_session_postgres.add_all(outgoing + incoming)
        db_session_postgres.commit()
        
        # Вычисляем центральность
        centrality = service.calculate_experience_centrality(central.id)
        
        # Проверяем результат
        assert centrality["degree_centrality"] == 4, "Общая степень должна быть 4"
        assert centrality["in_degree"] == 2, "Входящая степень должна быть 2"
        assert centrality["out_degree"] == 2, "Исходящая степень должна быть 2"
        assert centrality["avg_incoming_strength"] == 5.5, "Средняя сила входящих связей должна быть 5.5"
        assert centrality["avg_outgoing_strength"] == 7.5, "Средняя сила исходящих связей должна быть 7.5"
        assert centrality["weighted_centrality"] == 26.0, "Взвешенная центральность должна быть 26.0"
    
    @patch('undermaind.services.consciousness.memory_network_service.cosine_similarity')
    def test_suggest_new_connections(self, mock_cosine, service, experiences, db_session_postgres):
        """Проверка предложения новых связей для опыта."""
        # Создаем несколько связанных опытов
        connections = [
            ExperienceConnection(
                source_experience_id=experiences[0].id,
                target_experience_id=experiences[1].id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=7
            ),
            ExperienceConnection(
                source_experience_id=experiences[1].id,
                target_experience_id=experiences[2].id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=6
            )
        ]
        
        db_session_postgres.add_all(connections)
        db_session_postgres.commit()
        
        # Делаем заглушку для функции сравнения векторов
        mock_cosine.return_value = 0.8
        
        # Получаем предложения новых связей
        suggestions = service.suggest_new_connections(experiences[0].id, min_similarity=0.7)
        
        # Проверяем формат результата
        assert isinstance(suggestions, list), "Результат должен быть списком"
        
        # Примечание: поскольку функция семантического сравнения заменена заглушкой,
        # мы тестируем только формат результата, а не его точное содержимое.
        # В реальном коде тут можно проверить, что предлагаются ожидаемые связи.
    
    def test_strengthen_connections_by_cooccurrence(self, service, db_session_postgres, context):
        """Проверка укрепления связей между опытами на основе совместного появления."""
        # Создаем несколько опытов с близкими временными метками в одном контексте
        base_time = datetime.now()
        
        exp1 = Experience(
            content="Первый опыт в последовательности",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=context.id,
            timestamp=base_time
        )
        
        exp2 = Experience(
            content="Второй опыт в последовательности",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=context.id,
            timestamp=base_time + timedelta(seconds=30)
        )
        
        exp3 = Experience(
            content="Третий опыт в последовательности",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=context.id,
            timestamp=base_time + timedelta(seconds=90)
        )
        
        exp4 = Experience(
            content="Отдаленный опыт в последовательности",
            experience_type=Experience.TYPE_THOUGHT,
            context_id=context.id,
            timestamp=base_time + timedelta(minutes=15)
        )
        
        db_session_postgres.add_all([exp1, exp2, exp3, exp4])
        db_session_postgres.commit()
        
        # Укрепляем связи между опытами, появившимися в близком временном окне
        updated_count = service.strengthen_connections_by_cooccurrence(
            context.id,
            time_window_seconds=120  # 2 минуты
        )
        
        # Проверяем, что созданы/обновлены связи
        assert updated_count >= 3, "Должно быть создано/обновлено не менее 3 связей"
        
        # Проверяем наличие связей в БД
        # Между exp1 и exp2, exp2 и exp3, exp1 и exp3 должны быть связи
        connections = db_session_postgres.query(ExperienceConnection).filter(
            (ExperienceConnection.source_experience_id.in_([exp1.id, exp2.id, exp3.id])) &
            (ExperienceConnection.target_experience_id.in_([exp1.id, exp2.id, exp3.id])) &
            (ExperienceConnection.source_experience_id != ExperienceConnection.target_experience_id)
        ).all()
        
        assert len(connections) >= 3, "Должно быть создано не менее 3 временных связей"
        
        # Проверяем, что все связи имеют тип TYPE_TEMPORAL
        assert all(c.connection_type == ExperienceConnection.TYPE_TEMPORAL for c in connections), \
            "Все связи должны иметь тип TYPE_TEMPORAL"
    
    def test_find_clusters_in_network(self, service, db_session_postgres):
        """Проверка поиска кластеров в сети связей."""
        # Создаем два набора опытов с внутренними связями
        exp_cluster1 = [
            Experience(content=f"Кластер 1 опыт {i}", experience_type=Experience.TYPE_THOUGHT)
            for i in range(4)
        ]
        
        exp_cluster2 = [
            Experience(content=f"Кластер 2 опыт {i}", experience_type=Experience.TYPE_THOUGHT)
            for i in range(3)
        ]
        
        isolated_exp = Experience(content="Изолированный опыт", experience_type=Experience.TYPE_THOUGHT)
        
        db_session_postgres.add_all(exp_cluster1 + exp_cluster2 + [isolated_exp])
        db_session_postgres.commit()
        
        # Создаем сильные связи внутри первого кластера
        connections_cluster1 = []
        for i in range(len(exp_cluster1)):
            for j in range(i + 1, len(exp_cluster1)):
                connections_cluster1.append(
                    ExperienceConnection(
                        source_experience_id=exp_cluster1[i].id,
                        target_experience_id=exp_cluster1[j].id,
                        connection_type=ExperienceConnection.TYPE_SEMANTIC,
                        strength=8,
                        direction=ExperienceConnection.DIRECTION_BI
                    )
                )
        
        # Создаем сильные связи внутри второго кластера
        connections_cluster2 = []
        for i in range(len(exp_cluster2)):
            for j in range(i + 1, len(exp_cluster2)):
                connections_cluster2.append(
                    ExperienceConnection(
                        source_experience_id=exp_cluster2[i].id,
                        target_experience_id=exp_cluster2[j].id,
                        connection_type=ExperienceConnection.TYPE_TEMPORAL,
                        strength=7,
                        direction=ExperienceConnection.DIRECTION_BI
                    )
                )
        
        # Создаем слабую связь между кластерами
        inter_cluster_connection = ExperienceConnection(
            source_experience_id=exp_cluster1[0].id,
            target_experience_id=exp_cluster2[0].id,
            connection_type=ExperienceConnection.TYPE_ASSOCIATIVE,
            strength=3
        )
        
        db_session_postgres.add_all(connections_cluster1 + connections_cluster2 + [inter_cluster_connection])
        db_session_postgres.commit()
        
        # Находим кластеры в сети
        clusters = service.find_clusters_in_network(min_connections=3)
        
        # Проверяем, что найдены оба кластера
        assert len(clusters) >= 2, "Должны быть найдены минимум 2 кластера"
        
        # Получаем ID опытов в кластерах
        cluster_ids = [[exp_id for exp_id in cluster] for cluster in clusters]
        
        # Проверяем, что опыты из первого кластера попали в один найденный кластер
        cluster1_ids = [exp.id for exp in exp_cluster1]
        found_cluster1 = False
        for cluster in cluster_ids:
            if all(exp_id in cluster for exp_id in cluster1_ids):
                found_cluster1 = True
                break
                
        assert found_cluster1, "Все опыты из первого кластера должны быть в одном найденном кластере"
        
        # Проверяем, что опыты из второго кластера попали в один найденный кластер
        cluster2_ids = [exp.id for exp in exp_cluster2]
        found_cluster2 = False
        for cluster in cluster_ids:
            if all(exp_id in cluster for exp_id in cluster2_ids):
                found_cluster2 = True
                break
                
        assert found_cluster2, "Все опыты из второго кластера должны быть в одном найденном кластере"
        
        # Проверяем, что изолированный опыт не попал ни в один кластер
        isolated_in_cluster = False
        for cluster in cluster_ids:
            if isolated_exp.id in cluster:
                isolated_in_cluster = True
                break
                
        assert not isolated_in_cluster, "Изолированный опыт не должен быть в кластерах"
    
    def test_get_connection_types_distribution(self, service, db_session_postgres):
        """Проверка получения распределения типов связей в сети."""
        # Создаем связи разных типов
        exp1 = Experience(content="Опыт для распределения связей 1", experience_type=Experience.TYPE_THOUGHT)
        exp2 = Experience(content="Опыт для распределения связей 2", experience_type=Experience.TYPE_THOUGHT)
        
        db_session_postgres.add_all([exp1, exp2])
        db_session_postgres.commit()
        
        # Создаем связи разных типов
        connections = [
            ExperienceConnection(
                source_experience_id=exp1.id,
                target_experience_id=exp2.id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=7
            ),
            ExperienceConnection(
                source_experience_id=exp2.id,
                target_experience_id=exp1.id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=6
            ),
            ExperienceConnection(
                source_experience_id=exp1.id,
                target_experience_id=exp2.id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=8
            ),
            ExperienceConnection(
                source_experience_id=exp2.id,
                target_experience_id=exp1.id,
                connection_type=ExperienceConnection.TYPE_TEMPORAL,
                strength=5
            )
        ]
        
        db_session_postgres.add_all(connections)
        db_session_postgres.commit()
        
        # Получаем распределение типов связей
        distribution = service.get_connection_types_distribution()
        
        # Проверяем результат
        assert ExperienceConnection.TYPE_SEMANTIC in distribution, "Семантические связи должны присутствовать в распределении"
        assert ExperienceConnection.TYPE_CAUSAL in distribution, "Причинно-следственные связи должны присутствовать в распределении"
        assert ExperienceConnection.TYPE_TEMPORAL in distribution, "Временные связи должны присутствовать в распределении"
        
        assert distribution[ExperienceConnection.TYPE_SEMANTIC] == 2, "Должны быть 2 семантические связи"
        assert distribution[ExperienceConnection.TYPE_CAUSAL] == 1, "Должна быть 1 причинно-следственная связь"
        assert distribution[ExperienceConnection.TYPE_TEMPORAL] == 1, "Должна быть 1 временная связь"
    
    def test_get_network_statistics(self, service, db_session_postgres, experiences):
        """Проверка получения общей статистики по сети связей."""
        # Создаем несколько связей разных типов
        connections = [
            ExperienceConnection(
                source_experience_id=experiences[0].id,
                target_experience_id=experiences[1].id,
                connection_type=ExperienceConnection.TYPE_SEMANTIC,
                strength=8
            ),
            ExperienceConnection(
                source_experience_id=experiences[1].id,
                target_experience_id=experiences[2].id,
                connection_type=ExperienceConnection.TYPE_CAUSAL,
                strength=7
            ),
            ExperienceConnection(
                source_experience_id=experiences[2].id,
                target_experience_id=experiences[0].id,
                connection_type=ExperienceConnection.TYPE_TEMPORAL,
                strength=6
            )
        ]
        
        db_session_postgres.add_all(connections)
        db_session_postgres.commit()
        
        # Получаем статистику сети
        stats = service.get_network_statistics()
        
        # Проверяем наличие основных метрик
        assert "total_connections" in stats, "Должно присутствовать общее количество связей"
        assert "experiences_with_connections" in stats, "Должно присутствовать количество опытов с связями"
        assert "total_experiences" in stats, "Должно присутствовать общее количество опытов"
        assert "avg_strength" in stats, "Должна присутствовать средняя сила связей"
        assert "avg_degree" in stats, "Должна присутствовать средняя степень узла"
        assert "network_coverage" in stats, "Должно присутствовать покрытие сети"
        assert "connection_types_distribution" in stats, "Должно присутствовать распределение типов связей"
        
        # Проверяем значения метрик
        assert stats["total_connections"] >= 3, "Должно быть минимум 3 связи"
        assert stats["experiences_with_connections"] >= 3, "Должно быть минимум 3 опыта с связями"
        assert stats["total_experiences"] >= len(experiences), "Должно быть учтено общее количество опытов"
        assert 0.0 <= stats["avg_strength"] <= 10.0, "Средняя сила связей должна быть в диапазоне от 0 до 10"
        assert stats["avg_degree"] > 0, "Средняя степень узла должна быть положительной"
        assert 0.0 <= stats["network_coverage"] <= 1.0, "Покрытие сети должно быть в диапазоне от 0 до 1"
        assert isinstance(stats["connection_types_distribution"], dict), "Распределение типов связей должно быть словарем"