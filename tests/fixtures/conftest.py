"""
Fixtures compartidos para todos los tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.matcher_improved import ImprovedPhraseMatcher
from app.main import app


@pytest.fixture(scope="session")
def matcher_session():
    """
    Matcher compartido para toda la sesión de tests.
    Optimiza el rendimiento al inicializar el modelo una sola vez.
    """
    m = ImprovedPhraseMatcher(
        model_type="multilingual_balanced",
        use_reranking=True,
        use_synonym_expansion=True
    )
    m.initialize()
    return m


@pytest.fixture
def matcher():
    """
    Matcher fresco para cada test individual.
    Usar cuando se necesite aislamiento completo.
    """
    m = ImprovedPhraseMatcher(
        model_type="multilingual_balanced",
        use_reranking=True,
        use_synonym_expansion=True
    )
    m.initialize()
    return m


@pytest.fixture
def api_client():
    """
    Cliente de testing para la API FastAPI.
    """
    return TestClient(app)


@pytest.fixture
def sample_queries():
    """
    Queries de ejemplo para pruebas.
    """
    return {
        "emergencia": [
            "ayuda por favor",
            "necesito ayuda urgente",
            "llama a la policía",
            "es una emergencia",
        ],
        "saludos": [
            "hola",
            "buenos días",
            "buenas tardes",
            "cómo estás",
        ],
        "agradecimientos": [
            "gracias",
            "muchas gracias",
            "te lo agradezco",
        ],
        "edge_cases": [
            "Ivan",
            "xyz123",
            "a",
            "",
        ]
    }


def pytest_configure(config):
    """
    Configuración personalizada de pytest.
    """
    config.addinivalue_line("markers", "unit: Tests unitarios")
    config.addinivalue_line("markers", "integration: Tests de integración")
    config.addinivalue_line("markers", "e2e: Tests end-to-end")
    config.addinivalue_line("markers", "semantic: Tests de calidad semántica")
    config.addinivalue_line("markers", "slow: Tests lentos")
