"""
Шаблон модульного теста для проекта F.A.M.I.L.Y.

Этот шаблон демонстрирует базовую структуру модульного теста,
который проверяет функциональность компонента в изоляции от других
компонентов системы.

Для запуска: pytest -xvs path/to/test_file.py
"""

import pytest
from undermaind.utils.vector_utils import normalize_vector  # Пример импорта тестируемого модуля


class TestVectorUtils:
    """Тесты для утилит работы с векторами."""
    
    def test_normalize_vector(self):
        """
        Проверяет нормализацию вектора.
        
        Этот тест демонстрирует проверку изолированной функциональности
        без необходимости подключения к базе данных.
        """
        # Подготовка тестовых данных
        vector = [3.0, 4.0]
        
        # Вызов тестируемой функции
        normalized = normalize_vector(vector)
        
        # Проверка результатов
        assert len(normalized) == 2
        assert normalized[0] == 0.6
        assert normalized[1] == 0.8
        
        # Проверка граничных случаев
        assert normalize_vector([0, 0]) == [0, 0]  # Нулевой вектор
        
        # Проверка исключений
        with pytest.raises(TypeError):
            normalize_vector("not a vector")


# Если запускается как отдельный скрипт
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])