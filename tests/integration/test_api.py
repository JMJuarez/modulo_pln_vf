"""
Tests de integración para la API FastAPI.
Prueban los endpoints completos con el servidor de testing.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Cliente de testing para la API."""
    return TestClient(app)


@pytest.mark.integration
class TestBuscarEndpoint:
    """Tests para el endpoint POST /buscar."""

    def test_buscar_valid_query(self, client):
        """Query válida debe retornar resultado exitoso."""
        response = client.post(
            "/buscar",
            json={"texto": "hola"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "grupo" in data
        assert "frase_similar" in data
        assert "similitud" in data
        assert "deletreo_activado" in data

        # VALIDACIÓN CRÍTICA: Similitud en rango
        assert 0.0 <= data["similitud"] <= 1.0, \
            f"Similitud fuera de rango: {data['similitud']}"

    def test_buscar_empty_query(self, client):
        """Query vacía debe retornar error 400."""
        response = client.post(
            "/buscar",
            json={"texto": ""}
        )
        assert response.status_code == 400

    def test_buscar_whitespace_only(self, client):
        """Query solo con espacios debe retornar error 400."""
        response = client.post(
            "/buscar",
            json={"texto": "   "}
        )
        assert response.status_code == 400

    def test_buscar_exact_match(self, client):
        """Match exacto debe tener similitud muy alta."""
        response = client.post(
            "/buscar",
            json={"texto": "Buenos días"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["grupo"] == "B"
        assert data["similitud"] >= 0.95
        assert data["similitud"] <= 1.0  # ✅ NO debe exceder 1.0

    def test_buscar_spell_out_activation(self, client):
        """Queries sin match deben activar deletreo."""
        response = client.post(
            "/buscar",
            json={"texto": "xyz123"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["deletreo_activado"] is True
        assert data["grupo"] is None
        assert data["deletreo"] is not None
        assert len(data["deletreo"]) > 0
        assert 0.0 <= data["similitud"] <= 1.0

    def test_buscar_emergency_query(self, client):
        """Emergencia debe clasificarse correctamente."""
        response = client.post(
            "/buscar",
            json={"texto": "necesito ayuda urgente"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["grupo"] == "A"
        assert 0.0 <= data["similitud"] <= 1.0

    def test_buscar_ivan_edge_case(self, client):
        """Caso edge 'Ivan' debe activar deletreo."""
        response = client.post(
            "/buscar",
            json={"texto": "Ivan"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["deletreo_activado"] is True
        assert 0.0 <= data["similitud"] <= 1.0

    def test_buscar_invalid_json(self, client):
        """JSON inválido debe retornar error 422."""
        response = client.post(
            "/buscar",
            data="invalid json"
        )
        assert response.status_code == 422

    def test_buscar_missing_field(self, client):
        """JSON sin campo 'texto' debe retornar error 422."""
        response = client.post(
            "/buscar",
            json={"wrong_field": "value"}
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("query,expected_grupo", [
        ("hola", "B"),
        ("buenos días", "B"),
        ("ayuda", "A"),
        ("gracias", "C"),
    ])
    def test_buscar_multiple_queries(self, client, query, expected_grupo):
        """Múltiples queries deben clasificarse correctamente."""
        response = client.post(
            "/buscar",
            json={"texto": query}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["grupo"] == expected_grupo
        assert 0.0 <= data["similitud"] <= 1.0


@pytest.mark.integration
class TestGruposEndpoint:
    """Tests para endpoints de grupos."""

    def test_get_all_grupos(self, client):
        """GET /grupos debe retornar todos los grupos."""
        response = client.get("/grupos")
        assert response.status_code == 200

        data = response.json()
        assert "grupos" in data
        assert "A" in data["grupos"]
        assert "B" in data["grupos"]
        assert "C" in data["grupos"]

    def test_get_grupo_especifico(self, client):
        """GET /grupos/{grupo} debe retornar frases del grupo."""
        response = client.get("/grupos/A")
        assert response.status_code == 200

        data = response.json()
        assert "grupo" in data
        assert "frases" in data
        assert data["grupo"] == "A"
        assert isinstance(data["frases"], list)
        assert len(data["frases"]) > 0

    def test_get_grupo_inexistente(self, client):
        """GET /grupos/INEXISTENTE debe retornar 404."""
        response = client.get("/grupos/Z")
        assert response.status_code == 404


@pytest.mark.integration
class TestDeletreoEndpoint:
    """Tests para el endpoint POST /deletreo."""

    def test_deletreo_basic(self, client):
        """Deletreo básico debe funcionar."""
        response = client.post(
            "/deletreo",
            json={"texto": "hola"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "texto_original" in data
        assert "deletreo" in data
        assert "total_caracteres" in data
        assert data["deletreo"] == ["H", "O", "L", "A"]

    def test_deletreo_with_spaces(self, client):
        """Deletreo con espacios."""
        response = client.post(
            "/deletreo",
            json={"texto": "a b", "incluir_espacios": True}
        )
        assert response.status_code == 200

        data = response.json()
        assert "espacio" in data["deletreo"]

    def test_deletreo_empty(self, client):
        """Deletreo de texto vacío debe retornar error 400."""
        response = client.post(
            "/deletreo",
            json={"texto": ""}
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests para el endpoint GET /health."""

    def test_health_check_healthy(self, client):
        """Health check debe retornar estado healthy."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.integration
class TestRootEndpoint:
    """Tests para el endpoint raíz GET /."""

    def test_root_endpoint(self, client):
        """Endpoint raíz debe retornar información del sistema."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "grupos_disponibles" in data
        assert "total_frases" in data
        assert data["status"] == "OK"
        assert len(data["grupos_disponibles"]) == 3
