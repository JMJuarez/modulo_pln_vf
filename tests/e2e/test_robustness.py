"""
Tests de Robustez Lingüística - CRÍTICO para sistemas PLN.

Metodología: Perturbation Testing
- Simula errores reales de usuarios
- Valida tolerancia a ruido
- Mide degradación gradual
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.e2e
@pytest.mark.semantic
class TestTypoRobustness:
    """
    Tests de robustez ante errores ortográficos.
    Metodología: Character-level perturbations
    """

    def test_single_char_typo_beginning(self, client):
        """
        Error al inicio de palabra (común en usuarios apresurados).
        """
        test_cases = [
            ("hola", "hila", "B"),      # i en lugar de o
            ("ayuda", "yuda", "A"),     # falta a inicial
            ("gracias", "graias", "C"), # c→i
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            assert response.status_code == 200

            data = response.json()
            # Debe clasificar correctamente O activar deletreo (aceptable)
            if not data["deletreo_activado"]:
                assert data["grupo"] == expected_grupo, \
                    f"Typo '{typo}' (correcto: '{correct}') mal clasificado como {data['grupo']}"
            # Si activa deletreo, al menos la similitud debe ser razonable
            assert 0.0 <= data["similitud"] <= 1.0

    def test_single_char_typo_middle(self, client):
        """
        Error en medio de palabra (typo común).
        """
        test_cases = [
            ("ayuda", "auuda", "A"),      # y→u
            ("gracias", "gracias", "C"),  # correcto
            ("buenos", "bueons", "B"),    # n↔o
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            data = response.json()

            if not data["deletreo_activado"]:
                assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_single_char_typo_end(self, client):
        """
        Error al final de palabra.
        """
        test_cases = [
            ("hola", "holq", "B"),
            ("ayuda", "ayuds", "A"),
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            data = response.json()

            if not data["deletreo_activado"]:
                assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_missing_char(self, client):
        """
        Falta un carácter (usuario omite letra).
        """
        test_cases = [
            ("hola", "hla", "B"),        # falta o
            ("ayuda", "ayda", "A"),      # falta u
            ("gracias", "graias", "C"),  # falta c
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            data = response.json()

            # Puede clasificar o deletrear
            if not data["deletreo_activado"]:
                assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_extra_char(self, client):
        """
        Carácter extra (usuario tipea dos veces).
        """
        test_cases = [
            ("hola", "hoola", "B"),
            ("ayuda", "ayyuda", "A"),
            ("gracias", "graciass", "C"),
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            data = response.json()

            if not data["deletreo_activado"]:
                assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_adjacent_char_swap(self, client):
        """
        Caracteres adyacentes intercambiados (error común de tipeo).
        """
        test_cases = [
            ("hola", "hloa", "B"),
            ("ayuda", "ayuad", "A"),
            ("gracias", "gracais", "C"),
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            data = response.json()

            if not data["deletreo_activado"]:
                assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_multiple_typos(self, client):
        """
        Múltiples errores en una palabra (usuario muy apresurado).
        """
        test_cases = [
            ("hola", "hloa", "B"),           # 2 errores
            ("ayuda", "yuda", "A"),          # 1 error grave
            ("buenos días", "buens dias", "B"),  # 2 errores
        ]

        for correct, typo, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": typo})
            data = response.json()

            # Con múltiples errores, puede activar deletreo
            assert 0.0 <= data["similitud"] <= 1.0

    @pytest.mark.parametrize("severity,query,expected", [
        ("leve", "hola", "B"),        # sin error
        ("leve", "hila", "B"),        # 1 char
        ("medio", "hla", "B"),        # falta 1 char
        ("grave", "hkka", None),      # 2+ chars → deletreo
    ])
    def test_typo_severity_levels(self, client, severity, query, expected):
        """
        Validar que el sistema degrada graciosamente.
        Leve → Clasifica correctamente
        Medio → Clasifica o deletrea
        Grave → Deletrea
        """
        response = client.post("/buscar", json={"texto": query})
        data = response.json()

        if severity == "grave":
            # Errores graves deben activar deletreo
            assert data["deletreo_activado"] is True or data["grupo"] == expected
        else:
            # Errores leves/medios deben clasificar
            if not data["deletreo_activado"]:
                assert data["grupo"] == expected

        assert 0.0 <= data["similitud"] <= 1.0


@pytest.mark.e2e
@pytest.mark.semantic
class TestNoiseRobustness:
    """
    Tests de robustez ante ruido en el input.
    Metodología: Input fuzzing
    """

    def test_extra_whitespace(self, client):
        """
        Espacios extra (usuario presiona espacio varias veces).
        """
        test_cases = [
            ("hola", "hola  ", "B"),
            ("ayuda", "  ayuda", "A"),
            ("gracias", "  gracias  ", "C"),
            ("buenos días", "buenos    días", "B"),
        ]

        for correct, noisy, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": noisy})
            data = response.json()

            assert data["grupo"] == expected_grupo, \
                f"Espacios extra afectaron: '{noisy}'"
            assert 0.0 <= data["similitud"] <= 1.0

    def test_mixed_case_noise(self, client):
        """
        Mayúsculas/minúsculas mezcladas aleatoriamente.
        """
        test_cases = [
            ("hola", "HoLa", "B"),
            ("ayuda", "AyUdA", "A"),
            ("gracias", "GrAcIaS", "C"),
        ]

        for correct, noisy, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": noisy})
            data = response.json()

            assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_punctuation_noise(self, client):
        """
        Puntuación extra (usuario enfatiza).
        """
        test_cases = [
            ("ayuda", "ayuda!!", "A"),
            ("ayuda", "¡¡ayuda!!", "A"),
            ("hola", "hola....", "B"),
            ("gracias", "gracias!!!", "C"),
        ]

        for correct, noisy, expected_grupo in test_cases:
            response = client.post("/buscar", json={"texto": noisy})
            data = response.json()

            assert data["grupo"] == expected_grupo
            assert 0.0 <= data["similitud"] <= 1.0

    def test_accent_variations(self, client):
        """
        Variaciones de acentos (teclados sin tildes).
        """
        test_cases = [
            ("médico", "medico", "A"),
            ("emergencia", "emergéncia", "A"),
            ("días", "dias", "B"),
        ]

        for with_accent, without_accent, expected_grupo in test_cases:
            for query in [with_accent, without_accent]:
                response = client.post("/buscar", json={"texto": query})
                data = response.json()

                if not data["deletreo_activado"]:
                    # Ambos deben dar el mismo grupo
                    assert data["grupo"] == expected_grupo


@pytest.mark.e2e
@pytest.mark.semantic
class TestContextualRobustness:
    """
    Tests de comprensión contextual.
    Metodología: Semantic equivalence testing
    """

    def test_synonym_understanding(self, client):
        """
        Sinónimos deben clasificarse igual.
        """
        synonym_groups = [
            (["ayuda", "socorro", "auxilio"], "A"),
            (["hola", "saludos", "adios"], "B"),
            (["gracias", "muchas gracias", "bien", "si"], "C"),
        ]

        for synonyms, expected_grupo in synonym_groups:
            grupos_found = []
            for synonym in synonyms:
                response = client.post("/buscar", json={"texto": synonym})
                data = response.json()

                if not data["deletreo_activado"]:
                    grupos_found.append(data["grupo"])

            # Al menos 70% deben estar en el grupo correcto
            if len(grupos_found) > 0:
                correct = sum(1 for g in grupos_found if g == expected_grupo)
                accuracy = correct / len(grupos_found)
                assert accuracy >= 0.70, \
                    f"Sinónimos {synonyms}: solo {accuracy:.0%} correctos"

    def test_phrase_vs_single_word(self, client):
        """
        Palabra sola vs frase completa (contexto).
        """
        test_pairs = [
            ("ayuda", "necesito ayuda", "A"),
            ("hola", "hola amigo", "B"),
            ("gracias", "muchas gracias", "C"),
        ]

        for single, phrase, expected_grupo in test_pairs:
            # Probar palabra sola
            r1 = client.post("/buscar", json={"texto": single})
            # Probar frase
            r2 = client.post("/buscar", json={"texto": phrase})

            d1, d2 = r1.json(), r2.json()

            # Ambos deben clasificar en el mismo grupo
            if not d1["deletreo_activado"] and not d2["deletreo_activado"]:
                assert d1["grupo"] == d2["grupo"] == expected_grupo


@pytest.mark.e2e
@pytest.mark.slow
class TestStressAndLoad:
    """
    Tests de estrés y carga.
    Metodología: Load testing
    """

    def test_rapid_queries_with_typos(self, client):
        """
        Múltiples queries rápidas con errores (usuario apresurado).
        """
        queries_with_typos = [
            "hla",      # typo de hola
            "ayda",     # typo de ayuda
            "grcias",   # typo de gracias
            "hola",     # correcto
            "ayuda",    # correcto
        ] * 10  # 50 queries

        success = 0
        for query in queries_with_typos:
            response = client.post("/buscar", json={"texto": query})
            if response.status_code == 200:
                data = response.json()
                if 0.0 <= data["similitud"] <= 1.0:
                    success += 1

        success_rate = success / len(queries_with_typos)
        assert success_rate >= 0.95, f"Solo {success_rate:.0%} exitosas bajo estrés"

    def test_mixed_quality_inputs(self, client):
        """
        Mezcla de inputs buenos, malos y aleatorios.
        """
        mixed_inputs = [
            # Buenos
            "hola", "ayuda", "gracias",
            # Typos
            "hla", "ayda", "grcias",
            # Ruido
            "hola!!!", "AYUDA", "gracias...",
            # Aleatorios
            "xyz", "qwerty", "asdf",
        ]

        for query in mixed_inputs:
            response = client.post("/buscar", json={"texto": query})
            assert response.status_code == 200

            data = response.json()
            # Lo crítico: NUNCA debe salir del rango
            assert 0.0 <= data["similitud"] <= 1.0, \
                f"Query '{query}' generó similitud fuera de rango"

    @pytest.mark.parametrize("length", [1, 2, 5, 10, 20, 50])
    def test_varying_input_lengths(self, client, length):
        """
        Inputs de diferentes longitudes (desde 1 char hasta 50).
        """
        # Generar query de longitud variable
        base = "hola ayuda gracias "
        query = (base * (length // len(base) + 1))[:length]

        response = client.post("/buscar", json={"texto": query})
        assert response.status_code == 200

        data = response.json()
        assert 0.0 <= data["similitud"] <= 1.0


@pytest.mark.e2e
@pytest.mark.semantic
class TestEdgeCasesReal:
    """
    Casos edge encontrados en uso real.
    """

    def test_numbers_in_text(self, client):
        """
        Usuario incluye números (e.g., "ayuda 911").
        """
        queries = [
            "ayuda 911",
            "hola 123",
            "gracias 100",
        ]

        for query in queries:
            response = client.post("/buscar", json={"texto": query})
            data = response.json()
            assert 0.0 <= data["similitud"] <= 1.0

    def test_repeated_chars(self, client):
        """
        Usuario repite caracteres para énfasis.
        """
        queries = [
            "holaaaaa",
            "ayudaaa",
            "graciassss",
        ]

        for query in queries:
            response = client.post("/buscar", json={"texto": query})
            data = response.json()
            assert 0.0 <= data["similitud"] <= 1.0

    def test_all_caps_urgent(self, client):
        """
        MAYÚSCULAS indica urgencia (contexto emocional).
        """
        queries = [
            "AYUDA",
            "EMERGENCIA",
            "SOCORRO",
        ]

        for query in queries:
            response = client.post("/buscar", json={"texto": query})
            data = response.json()

            # Debe clasificar como emergencia
            if not data["deletreo_activado"]:
                assert data["grupo"] == "A"
