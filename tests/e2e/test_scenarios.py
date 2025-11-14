"""
Tests End-to-End (E2E) - Escenarios completos de usuario.
Simulan interacciones reales con el sistema completo.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Cliente de testing para la API."""
    return TestClient(app)


@pytest.mark.e2e
class TestEmergencyScenarios:
    """Escenarios de emergencia completos."""

    def test_scenario_emergency_basic(self, client):
        """
        Escenario: Usuario necesita ayuda de emergencia
        1. Usuario escribe "necesito ayuda urgente"
        2. Sistema clasifica como emergencia (Grupo A)
        3. Sistema retorna frase apropiada con alta similitud
        """
        response = client.post("/buscar", json={"texto": "necesito ayuda urgente"})

        assert response.status_code == 200
        data = response.json()

        # Validaciones del escenario
        assert data["grupo"] == "A", "Debe clasificarse como emergencia"
        assert data["similitud"] >= 0.65, "Similitud debe ser razonable"
        assert 0.0 <= data["similitud"] <= 1.0, "Similitud en rango válido"
        assert "ayuda" in data["frase_similar"].lower(), "Debe contener palabra clave"
        assert data["deletreo_activado"] is False, "No debe activar deletreo"

    def test_scenario_emergency_variations(self, client):
        """
        Escenario: Usuario prueba diferentes formas de pedir ayuda
        Todas deben clasificarse como emergencia.
        """
        emergency_queries = [
            "ayuda por favor",
            "necesito ayuda",
            "es una emergencia",
            "ayuda urgente",
        ]

        for query in emergency_queries:
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200

            data = response.json()
            assert data["grupo"] == "A", f"'{query}' debe ser emergencia"
            assert 0.0 <= data["similitud"] <= 1.0


@pytest.mark.e2e
class TestGreetingScenarios:
    """Escenarios de saludos completos."""

    def test_scenario_greeting_simple(self, client):
        """
        Escenario: Usuario saluda de manera simple
        1. Usuario escribe "hola"
        2. Sistema clasifica como saludo (Grupo B)
        3. Sistema retorna saludo apropiado
        """
        response = client.post("/buscar", json={"texto": "hola"})

        assert response.status_code == 200
        data = response.json()

        assert data["grupo"] == "B", "Debe clasificarse como saludo"
        assert data["similitud"] >= 0.80, "Similitud debe ser alta"
        assert 0.0 <= data["similitud"] <= 1.0

    def test_scenario_greeting_with_typo(self, client):
        """
        Escenario: Usuario saluda con error ortográfico
        1. Usuario escribe "ola" (debería ser "hola")
        2. Sistema corrige o maneja apropiadamente
        3. Sistema puede clasificar como saludo o activar deletreo
        """
        response = client.post("/buscar", json={"texto": "ola"})

        assert response.status_code == 200
        data = response.json()

        # Puede corregir a saludo o activar deletreo
        assert data["grupo"] in ["B", None]
        assert 0.0 <= data["similitud"] <= 1.0

    def test_scenario_greeting_formal(self, client):
        """
        Escenario: Usuario usa saludo formal
        Sistema debe reconocer "buenos días", "buenas tardes", etc.
        """
        formal_greetings = [
            ("buenos días", "B"),
            ("buenas tardes", "B"),
            ("buenas noches", "B"),
        ]

        for query, expected_grupo in formal_greetings:
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200

            data = response.json()
            assert data["grupo"] == expected_grupo
            assert data["similitud"] >= 0.85  # Debe ser muy alto
            assert 0.0 <= data["similitud"] <= 1.0


@pytest.mark.e2e
class TestEdgeCaseScenarios:
    """Escenarios de casos edge importantes."""

    def test_scenario_ivan_edge_case(self, client):
        """
        Escenario CRÍTICO: Usuario escribe "Ivan"
        1. Usuario escribe "Ivan" (nombre propio)
        2. Sistema NO debe matchear con "Sí" del Grupo C
        3. Sistema debe activar deletreo por baja similitud
        4. Usuario recibe deletreo: I-V-A-N
        """
        response = client.post("/buscar", json={"texto": "Ivan"})

        assert response.status_code == 200
        data = response.json()

        # Validaciones críticas del caso Ivan
        assert data["deletreo_activado"] is True, "Debe activar deletreo"
        assert data["grupo"] is None, "No debe clasificarse en ningún grupo"
        assert data["deletreo"] is not None, "Debe incluir deletreo"
        assert "I" in data["deletreo"], "Debe deletrear I"
        assert "V" in data["deletreo"], "Debe deletrear V"
        assert "A" in data["deletreo"], "Debe deletrear A"
        assert "N" in data["deletreo"], "Debe deletrear N"
        assert 0.0 <= data["similitud"] <= 1.0

    def test_scenario_nonsense_text(self, client):
        """
        Escenario: Usuario escribe texto sin sentido
        Sistema debe activar deletreo.
        """
        nonsense_queries = ["xyz123", "asdfgh", "qwerty"]

        for query in nonsense_queries:
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200

            data = response.json()
            assert data["deletreo_activado"] is True, f"'{query}' debe activar deletreo"
            assert 0.0 <= data["similitud"] <= 1.0

    def test_scenario_single_letter(self, client):
        """
        Escenario: Usuario escribe una sola letra
        Sistema debe manejar apropiadamente.
        """
        response = client.post("/buscar", json={"texto": "a"})

        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["similitud"] <= 1.0


@pytest.mark.e2e
class TestMultiQueryScenarios:
    """Escenarios con múltiples queries en secuencia."""

    def test_scenario_conversation_flow(self, client):
        """
        Escenario: Usuario tiene conversación completa
        1. Saludo inicial
        2. Consulta de emergencia
        3. Agradecimiento final
        """
        conversation = [
            ("hola", "B", "Saludo inicial"),
            ("necesito ayuda", "A", "Emergencia"),
            ("gracias", "C", "Agradecimiento"),
        ]

        for query, expected_grupo, description in conversation:
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200, f"Falló en: {description}"

            data = response.json()
            assert data["grupo"] == expected_grupo, f"Clasificación incorrecta en: {description}"
            assert 0.0 <= data["similitud"] <= 1.0

    def test_scenario_rapid_fire_queries(self, client):
        """
        Escenario: Usuario hace múltiples queries rápidas
        Sistema debe mantener rendimiento estable.
        """
        queries = ["hola"] * 5 + ["ayuda"] * 5 + ["gracias"] * 5

        for i, query in enumerate(queries):
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200, f"Falló en query {i+1}"

            data = response.json()
            assert 0.0 <= data["similitud"] <= 1.0

    @pytest.mark.slow
    def test_scenario_throughput_simulation(self, client):
        """
        Escenario: Simular carga de múltiples usuarios
        50 queries consecutivas deben procesarse correctamente.
        """
        queries = ["hola", "ayuda", "gracias"] * 17  # ~50 queries

        success_count = 0
        for query in queries:
            response = client.post("/buscar", json={"texto": query})
            if response.status_code == 200:
                data = response.json()
                if 0.0 <= data["similitud"] <= 1.0:
                    success_count += 1

        # Al menos 95% deben ser exitosas
        success_rate = success_count / len(queries)
        assert success_rate >= 0.95, f"Tasa de éxito: {success_rate:.2%}"


@pytest.mark.e2e
class TestCaseSensitivityScenarios:
    """Escenarios de sensibilidad a mayúsculas/minúsculas."""

    def test_scenario_different_cases(self, client):
        """
        Escenario: Usuario usa diferentes combinaciones de mayúsculas
        Sistema debe tratar todas igual (normalización).
        """
        variations = [
            "hola",
            "HOLA",
            "Hola",
            "HoLa",
        ]

        results = []
        for query in variations:
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200

            data = response.json()
            results.append(data["grupo"])
            assert 0.0 <= data["similitud"] <= 1.0

        # Todas deben dar el mismo grupo
        assert len(set(results)) == 1, "Diferentes mayúsculas deben dar mismo resultado"
        assert results[0] == "B", "Todas deben clasificarse como saludo"


@pytest.mark.e2e
class TestSystemHealthScenarios:
    """Escenarios de salud del sistema."""

    def test_scenario_health_before_query(self, client):
        """
        Escenario: Usuario verifica salud antes de usar el sistema
        """
        # 1. Verificar health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # 2. Hacer query
        query_response = client.post("/buscar", json={"texto": "hola"})
        assert query_response.status_code == 200
        assert 0.0 <= query_response.json()["similitud"] <= 1.0

    def test_scenario_explore_then_query(self, client):
        """
        Escenario: Usuario explora grupos disponibles antes de hacer query
        """
        # 1. Ver todos los grupos
        grupos_response = client.get("/grupos")
        assert grupos_response.status_code == 200
        grupos = grupos_response.json()["grupos"]
        assert len(grupos) == 3

        # 2. Explorar grupo específico
        grupo_response = client.get("/grupos/A")
        assert grupo_response.status_code == 200
        assert len(grupo_response.json()["frases"]) > 0

        # 3. Hacer query relacionada
        query_response = client.post("/buscar", json={"texto": "ayuda"})
        assert query_response.status_code == 200
        assert query_response.json()["grupo"] == "A"
