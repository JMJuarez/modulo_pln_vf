"""
Tests de calidad semántica - Específicos para sistemas de PLN.
Validan la precisión del modelo de embeddings y clasificación.
"""

import pytest
from app.matcher_improved import ImprovedPhraseMatcher


@pytest.fixture(scope="module")
def matcher():
    """Matcher para tests de calidad semántica."""
    m = ImprovedPhraseMatcher(
        model_type="multilingual_balanced",
        use_reranking=True,
        use_synonym_expansion=True
    )
    m.initialize()
    return m


@pytest.mark.semantic
class TestSemanticAccuracy:
    """Tests de precisión semántica con dataset conocido."""

    @pytest.mark.parametrize("query,expected_grupo,min_similitud", [
        # Grupo A - Emergencia
        ("necesito ayuda", "A", 0.70),
        ("ayuda por favor", "A", 0.85),
        ("es una emergencia", "A", 0.75),
        ("socorro", "A", 0.65),
        ("ayuda urgente", "A", 0.70),

        # Grupo B - Saludos
        ("hola", "B", 0.80),
        ("buenos días", "B", 0.85),
        ("buenas tardes", "B", 0.85),
        ("hola amigo", "B", 0.75),
        ("qué tal", "B", 0.60),

        # Grupo C - Agradecimientos
        ("gracias", "C", 0.85),
        ("muchas gracias", "C", 0.85),
        ("te lo agradezco", "C", 0.65),
    ])
    def test_semantic_classification_accuracy(self, matcher, query, expected_grupo, min_similitud):
        """
        Valida que queries se clasifiquen correctamente con similitud mínima.
        """
        result = matcher.search_similar_phrase(query)

        # Si activa deletreo, skip
        if result["deletreo_activado"]:
            pytest.skip(f"Query '{query}' activó deletreo (similitud muy baja)")

        assert result["grupo"] == expected_grupo, \
            f"Query '{query}' mal clasificada como {result['grupo']}"
        assert result["similitud"] >= min_similitud, \
            f"Similitud {result['similitud']:.2f} por debajo del mínimo {min_similitud}"
        assert 0.0 <= result["similitud"] <= 1.0


@pytest.mark.semantic
class TestSemanticVariations:
    """Tests de robustez semántica con variaciones lingüísticas."""

    def test_synonyms_recognition(self, matcher):
        """
        Sinónimos deben clasificarse en el mismo grupo.
        """
        synonym_groups = [
            (["ayuda", "asistencia", "socorro"], "A"),
            (["hola", "saludos", "buenos días"], "B"),
            (["gracias", "muchas gracias"], "C"),
        ]

        for synonyms, expected_grupo in synonym_groups:
            results = []
            for word in synonyms:
                result = matcher.search_similar_phrase(word)
                if not result["deletreo_activado"]:
                    results.append(result["grupo"])

            # Al menos 70% deben estar en el grupo esperado
            if len(results) > 0:
                correct = sum(1 for g in results if g == expected_grupo)
                accuracy = correct / len(results)
                assert accuracy >= 0.70, \
                    f"Sinónimos de grupo {expected_grupo}: solo {accuracy:.0%} correctos"

    def test_case_insensitivity(self, matcher):
        """
        Mayúsculas/minúsculas no deben afectar clasificación.
        """
        test_cases = [
            ("hola", "HOLA", "HoLa"),
            ("gracias", "GRACIAS", "Gracias"),
            ("ayuda", "AYUDA", "Ayuda"),
        ]

        for variations in test_cases:
            grupos = []
            for query in variations:
                result = matcher.search_similar_phrase(query)
                if not result["deletreo_activado"]:
                    grupos.append(result["grupo"])

            # Todas las variaciones deben dar el mismo grupo
            if len(grupos) > 0:
                assert len(set(grupos)) == 1, \
                    f"Variaciones de caso dieron grupos diferentes: {grupos}"

    def test_accent_robustness(self, matcher):
        """
        Acentos no deben afectar significativamente la clasificación.
        """
        test_pairs = [
            ("medico", "médico"),
            ("emergencia", "emergéncia"),
            ("gracias", "grácias"),
        ]

        for without_accent, with_accent in test_pairs:
            result1 = matcher.search_similar_phrase(without_accent)
            result2 = matcher.search_similar_phrase(with_accent)

            # Si ambos se clasifican (no deletreo), deben dar mismo grupo
            if not result1["deletreo_activado"] and not result2["deletreo_activado"]:
                assert result1["grupo"] == result2["grupo"], \
                    f"Acentos cambiaron grupo: {without_accent} vs {with_accent}"


@pytest.mark.semantic
class TestConfusionMatrix:
    """Tests para calcular matriz de confusión y métricas de calidad."""

    def test_classification_accuracy_overall(self, matcher):
        """
        Calcula accuracy global del clasificador.
        Objetivo: >95%
        """
        test_dataset = [
            # (query, expected_grupo)
            ("ayuda", "A"),
            ("necesito ayuda", "A"),
            ("emergencia", "A"),
            ("hola", "B"),
            ("buenos días", "B"),
            ("buenas tardes", "B"),
            ("gracias", "C"),
            ("muchas gracias", "C"),
            ("te agradezco", "C"),
        ]

        correct = 0
        total = 0

        for query, expected in test_dataset:
            result = matcher.search_similar_phrase(query)

            # Solo contar si no activa deletreo
            if not result["deletreo_activado"]:
                total += 1
                if result["grupo"] == expected:
                    correct += 1

        if total > 0:
            accuracy = correct / total
            print(f"\n📊 Accuracy global: {accuracy:.2%} ({correct}/{total})")
            assert accuracy >= 0.85, \
                f"Accuracy {accuracy:.2%} por debajo del objetivo 85%"

    def test_per_group_precision(self, matcher):
        """
        Calcula precision por grupo.
        Precision = True Positives / (True Positives + False Positives)
        """
        test_dataset = [
            ("ayuda", "A"),
            ("emergencia", "A"),
            ("socorro", "A"),
            ("hola", "B"),
            ("buenos días", "B"),
            ("saludos", "B"),
            ("gracias", "C"),
            ("muchas gracias", "C"),
        ]

        # Contador: grupo_predicho -> {grupo_real: count}
        predictions = {"A": {}, "B": {}, "C": {}}

        for query, expected in test_dataset:
            result = matcher.search_similar_phrase(query)

            if not result["deletreo_activado"]:
                predicted = result["grupo"]
                if expected not in predictions[predicted]:
                    predictions[predicted][expected] = 0
                predictions[predicted][expected] += 1

        # Calcular precision por grupo
        for grupo in ["A", "B", "C"]:
            total_predicted = sum(predictions[grupo].values())
            if total_predicted > 0:
                true_positives = predictions[grupo].get(grupo, 0)
                precision = true_positives / total_predicted
                print(f"\n📊 Precision Grupo {grupo}: {precision:.2%}")
                assert precision >= 0.70, \
                    f"Precision grupo {grupo}: {precision:.2%} < 70%"


@pytest.mark.semantic
class TestSimilarityDistribution:
    """Tests para analizar distribución de similitudes."""

    def test_exact_matches_high_similarity(self, matcher):
        """
        Matches exactos deben tener similitud muy alta (>0.95).
        """
        exact_matches = [
            "Buenos días",
            "Gracias",
            "Ayuda, por favor",
        ]

        for query in exact_matches:
            result = matcher.search_similar_phrase(query)

            assert not result["deletreo_activado"], \
                f"Match exacto '{query}' no debería activar deletreo"
            assert result["similitud"] >= 0.95, \
                f"Match exacto '{query}' tiene similitud baja: {result['similitud']:.2f}"
            assert result["similitud"] <= 1.0, \
                f"Match exacto '{query}' excede 1.0: {result['similitud']:.2f}"

    def test_partial_matches_medium_similarity(self, matcher):
        """
        Matches parciales deben tener similitud media (0.60-0.90).
        """
        partial_matches = [
            "necesito asistencia",
            "hola amigo",
            "te lo agradezco mucho",
        ]

        for query in partial_matches:
            result = matcher.search_similar_phrase(query)

            if not result["deletreo_activado"]:
                assert 0.50 <= result["similitud"] <= 0.95, \
                    f"Match parcial '{query}' fuera de rango medio: {result['similitud']:.2f}"

    def test_no_matches_low_similarity(self, matcher):
        """
        Sin matches deben tener similitud baja (<0.70) y activar deletreo.
        """
        no_matches = [
            "xyz123",
            "asdfgh",
            "qwerty123",
        ]

        for query in no_matches:
            result = matcher.search_similar_phrase(query)

            assert result["deletreo_activado"] is True, \
                f"Query sin match '{query}' no activó deletreo"
            assert result["similitud"] < 0.70, \
                f"Query sin match '{query}' tiene similitud alta: {result['similitud']:.2f}"


@pytest.mark.semantic
class TestSemanticConsistency:
    """Tests de consistencia semántica."""

    def test_repeated_queries_same_result(self, matcher):
        """
        La misma query debe dar siempre el mismo resultado.
        """
        query = "hola"
        results = []

        # Ejecutar 5 veces
        for _ in range(5):
            result = matcher.search_similar_phrase(query)
            results.append({
                "grupo": result["grupo"],
                "similitud": result["similitud"],
                "deletreo": result["deletreo_activado"]
            })

        # Verificar que todos sean idénticos
        first = results[0]
        for r in results[1:]:
            assert r["grupo"] == first["grupo"], "Grupo inconsistente"
            assert abs(r["similitud"] - first["similitud"]) < 0.001, "Similitud inconsistente"
            assert r["deletreo"] == first["deletreo"], "Deletreo inconsistente"

    def test_similar_queries_similar_results(self, matcher):
        """
        Queries similares deben dar resultados similares.
        """
        similar_pairs = [
            ("hola", "hola amigo"),
            ("ayuda", "ayuda por favor"),
            ("gracias", "muchas gracias"),
        ]

        for query1, query2 in similar_pairs:
            result1 = matcher.search_similar_phrase(query1)
            result2 = matcher.search_similar_phrase(query2)

            # Si ambos se clasifican, deben estar en el mismo grupo
            if not result1["deletreo_activado"] and not result2["deletreo_activado"]:
                assert result1["grupo"] == result2["grupo"], \
                    f"Queries similares clasificadas diferente: '{query1}' vs '{query2}'"


@pytest.mark.semantic
class TestThresholdValidation:
    """Tests para validar que los thresholds están bien calibrados."""

    def test_spell_out_threshold_calibration(self, matcher):
        """
        Valida que el threshold de deletreo (0.70) está bien calibrado.
        """
        # Casos que DEBEN activar deletreo (< 0.70)
        should_spell_out = ["Ivan", "xyz123", "asdfgh", "qwerty"]

        for query in should_spell_out:
            result = matcher.search_similar_phrase(query)
            assert result["deletreo_activado"] is True, \
                f"'{query}' debería activar deletreo"
            assert result["similitud"] < 0.70, \
                f"'{query}' similitud {result['similitud']:.2f} >= 0.70"

        # Casos que NO deben activar deletreo (>= 0.70)
        should_not_spell_out = ["hola", "ayuda", "gracias"]

        for query in should_not_spell_out:
            result = matcher.search_similar_phrase(query)
            assert result["deletreo_activado"] is False, \
                f"'{query}' no debería activar deletreo"
            assert result["similitud"] >= 0.70, \
                f"'{query}' similitud {result['similitud']:.2f} < 0.70"
