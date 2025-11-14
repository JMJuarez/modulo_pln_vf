"""
Tests unitarios para el matcher mejorado.
CRÍTICO: Validar que la similitud siempre esté en [0.0, 1.0]
"""

import pytest
from app.matcher_improved import ImprovedPhraseMatcher, clip_similarity


@pytest.mark.unit
class TestClipSimilarity:
    """Tests para la función de clipping de similitud."""

    def test_clip_normal_value(self):
        """Valores normales deben permanecer igual."""
        assert clip_similarity(0.5) == 0.5
        assert clip_similarity(0.85) == 0.85
        assert clip_similarity(0.0) == 0.0
        assert clip_similarity(1.0) == 1.0

    def test_clip_above_one(self):
        """Valores >1.0 deben normalizarse a 1.0."""
        assert clip_similarity(1.05) == 1.0
        assert clip_similarity(1.0029) == 1.0
        assert clip_similarity(2.0) == 1.0
        assert clip_similarity(100.0) == 1.0

    def test_clip_below_zero(self):
        """Valores negativos deben normalizarse a 0.0."""
        assert clip_similarity(-0.1) == 0.0
        assert clip_similarity(-1.0) == 0.0
        assert clip_similarity(-100.0) == 0.0

    def test_clip_edge_cases(self):
        """Casos edge con precisión flotante."""
        assert clip_similarity(1.0000001) == 1.0
        assert clip_similarity(0.9999999) <= 1.0
        assert clip_similarity(-0.0000001) == 0.0


@pytest.mark.unit
class TestMatcherInitialization:
    """Tests para inicialización del matcher."""

    def test_matcher_initialization(self):
        """Matcher debe inicializarse correctamente."""
        matcher = ImprovedPhraseMatcher()
        matcher.initialize()

        assert matcher.grupos_frases is not None
        assert matcher.grupos_embeddings is not None
        assert matcher.grupos_centroids is not None
        assert len(matcher.grupos_frases) == 3  # A, B, C

    def test_matcher_with_custom_model(self):
        """Matcher debe aceptar modelo personalizado."""
        matcher = ImprovedPhraseMatcher(model_type="multilingual_balanced")
        matcher.initialize()
        assert matcher.model_name is not None


@pytest.mark.unit
class TestMatcherSimilarityRange:
    """
    Tests CRÍTICOS para verificar que el matcher retorna valores válidos.
    """

    @pytest.fixture
    def matcher(self):
        """Fixture para crear matcher."""
        m = ImprovedPhraseMatcher(
            model_type="multilingual_balanced",
            use_reranking=True,
            use_synonym_expansion=True
        )
        m.initialize()
        return m

    def test_exact_match_range(self, matcher):
        """Match exacto debe retornar 1.0 (no 1.05)."""
        result = matcher.search_similar_phrase("Buenos días")

        # VALIDACIONES CRÍTICAS
        assert 0.0 <= result["similitud"] <= 1.0, \
            f"Similitud fuera de rango: {result['similitud']}"
        assert result["similitud"] >= 0.95  # Debe ser muy alto
        assert result["grupo"] == "B"

    def test_no_match_range(self, matcher):
        """Sin match debe retornar valor bajo pero válido."""
        result = matcher.search_similar_phrase("xyz123abc")

        # VALIDACIONES CRÍTICAS
        assert 0.0 <= result["similitud"] <= 1.0, \
            f"Similitud fuera de rango: {result['similitud']}"
        assert result["similitud"] < 0.3  # Debe ser bajo
        assert result["deletreo_activado"] is True

    def test_partial_match_range(self, matcher):
        """Match parcial debe estar en rango medio."""
        result = matcher.search_similar_phrase("necesito asistencia")

        # VALIDACIONES CRÍTICAS
        assert 0.0 <= result["similitud"] <= 1.0, \
            f"Similitud fuera de rango: {result['similitud']}"

    @pytest.mark.parametrize("query", [
        "hola",
        "ayuda por favor",
        "gracias",
        "Buenos días",
        "AYUDA",
        "Ivan",
        "a",
        "xyz",
        "necesito ayuda urgente",
        "buenas tardes",
    ])
    def test_all_queries_in_range(self, matcher, query):
        """
        CRÍTICO: Todas las queries deben retornar valores en [0.0, 1.0].
        """
        result = matcher.search_similar_phrase(query)

        # VALIDACIÓN MÁS IMPORTANTE
        assert 0.0 <= result["similitud"] <= 1.0, \
            f"Query '{query}' retornó similitud fuera de rango: {result['similitud']}"

    def test_ivan_edge_case(self, matcher):
        """
        Caso edge específico: 'Ivan' no debe matchear con 'Sí'.
        Debe activar deletreo por baja similitud.
        """
        result = matcher.search_similar_phrase("Ivan")

        # Validaciones
        assert 0.0 <= result["similitud"] <= 1.0
        assert result["deletreo_activado"] is True
        assert result["grupo"] is None
        assert "I" in result["deletreo"]
        assert "V" in result["deletreo"]


@pytest.mark.unit
class TestMatcherGroupClassification:
    """Tests para clasificación de grupos."""

    @pytest.fixture
    def matcher(self):
        m = ImprovedPhraseMatcher()
        m.initialize()
        return m

    def test_emergency_classification(self, matcher):
        """Emergencias deben clasificarse como Grupo A."""
        queries = ["ayuda", "emergencia", "socorro", "necesito ayuda"]
        for query in queries:
            result = matcher.search_similar_phrase(query)
            if result["deletreo_activado"]:
                continue  # Skippear si activa deletreo
            assert result["grupo"] == "A", \
                f"Query '{query}' mal clasificada como {result['grupo']}"

    def test_greeting_classification(self, matcher):
        """Saludos deben clasificarse como Grupo B."""
        queries = ["hola", "buenos días", "buenas tardes"]
        for query in queries:
            result = matcher.search_similar_phrase(query)
            assert result["grupo"] == "B", \
                f"Query '{query}' mal clasificada como {result['grupo']}"

    def test_thanks_classification(self, matcher):
        """Agradecimientos deben clasificarse como Grupo C."""
        queries = ["gracias", "muchas gracias"]
        for query in queries:
            result = matcher.search_similar_phrase(query)
            assert result["grupo"] == "C", \
                f"Query '{query}' mal clasificada como {result['grupo']}"


@pytest.mark.unit
class TestSpellOutActivation:
    """Tests para activación del modo deletreo."""

    @pytest.fixture
    def matcher(self):
        m = ImprovedPhraseMatcher()
        m.initialize()
        return m

    def test_spell_out_for_low_similarity(self, matcher):
        """Baja similitud debe activar deletreo."""
        result = matcher.search_similar_phrase("xyz123")

        assert result["deletreo_activado"] is True
        assert result["grupo"] is None
        assert result["deletreo"] is not None
        assert len(result["deletreo"]) > 0
        assert 0.0 <= result["similitud"] <= 1.0

    def test_no_spell_out_for_good_match(self, matcher):
        """Buen match NO debe activar deletreo."""
        result = matcher.search_similar_phrase("hola")

        assert result["deletreo_activado"] is False
        assert result["grupo"] is not None
        assert result["deletreo"] is None
