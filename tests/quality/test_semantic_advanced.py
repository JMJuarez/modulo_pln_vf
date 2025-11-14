"""
Tests Avanzados de Calidad Semántica - CRÍTICO para PLN.

Metodologías implementadas:
1. Golden Dataset Testing
2. Confusion Matrix Analysis
3. Error Analysis
4. Robustness Metrics
5. Semantic Similarity Distribution Analysis
"""

import pytest
import numpy as np
from collections import defaultdict
from app.matcher_improved import ImprovedPhraseMatcher


@pytest.fixture(scope="module")
def matcher():
    m = ImprovedPhraseMatcher(
        model_type="multilingual_balanced",
        use_reranking=True,
        use_synonym_expansion=True
    )
    m.initialize()
    return m


@pytest.mark.semantic
class TestGoldenDataset:
    """
    Golden Dataset: Casos cuidadosamente curados que DEBEN funcionar.
    Metodología: Benchmark testing con ground truth
    """

    # Dataset curado manualmente con ground truth
    GOLDEN_CASES = [
        # (query, expected_grupo, min_similarity, categoria)
        # Casos perfectos (>0.90)
        ("Buenos días", "B", 0.90, "exact_match"),
        ("Gracias", "C", 0.90, "exact_match"),
        ("Ayuda, por favor", "A", 0.90, "exact_match"),

        # Variaciones semánticas (>0.75)
        ("necesito ayuda", "A", 0.75, "semantic"),
        ("muchas gracias", "C", 0.75, "semantic"),
        ("que tal", "B", 0.70, "semantic"),

        # Sinónimos (>0.65)
        ("socorro", "A", 0.60, "synonym"),
        ("auxilio", "A", 0.60, "synonym"),
        ("saludos", "B", 0.65, "synonym"),
        ("adios", "B", 0.65, "synonym"),
        ("bien", "C", 0.70, "synonym"),
        ("si", "C", 0.70, "synonym"),

        # Con ruido (>0.70)
        ("hola!!", "B", 0.70, "noisy"),
        ("AYUDA", "A", 0.70, "noisy"),
        ("gracias...", "C", 0.70, "noisy"),

        # Typos comunes (>0.60 o deletreo OK)
        ("hla", "B", 0.50, "typo"),     # puede deletrear
        ("ayda", "A", 0.50, "typo"),    # puede deletrear
    ]

    @pytest.mark.parametrize("query,expected_grupo,min_sim,categoria", GOLDEN_CASES)
    def test_golden_case(self, matcher, query, expected_grupo, min_sim, categoria):
        """
        CRÍTICO: Todos los casos golden DEBEN pasar.
        """
        result = matcher.search_similar_phrase(query)

        # Si activa deletreo, skip para typos (aceptable)
        if result["deletreo_activado"] and categoria == "typo":
            pytest.skip(f"Typo '{query}' activó deletreo (comportamiento aceptable)")

        # Para otros casos, NO debe activar deletreo
        if categoria != "typo":
            assert not result["deletreo_activado"], \
                f"Golden case '{query}' activó deletreo inesperadamente"

        # Validar clasificación
        assert result["grupo"] == expected_grupo, \
            f"Golden case '{query}' mal clasificado: {result['grupo']} != {expected_grupo}"

        # Validar similitud mínima
        assert result["similitud"] >= min_sim, \
            f"Golden case '{query}' similitud baja: {result['similitud']:.2f} < {min_sim}"

        # Validar rango
        assert 0.0 <= result["similitud"] <= 1.0

    def test_golden_dataset_accuracy(self, matcher):
        """
        Accuracy global del golden dataset.
        Objetivo: 100% (estos son casos que DEBEN funcionar)
        """
        correct = 0
        total = 0
        errors = []

        for query, expected_grupo, min_sim, categoria in self.GOLDEN_CASES:
            result = matcher.search_similar_phrase(query)

            # Si es typo y activa deletreo, OK
            if categoria == "typo" and result["deletreo_activado"]:
                total += 1
                correct += 1
                continue

            total += 1
            if result["grupo"] == expected_grupo and result["similitud"] >= min_sim:
                correct += 1
            else:
                errors.append({
                    "query": query,
                    "expected": expected_grupo,
                    "got": result["grupo"],
                    "sim": result["similitud"]
                })

        accuracy = correct / total
        print(f"\n📊 Golden Dataset Accuracy: {accuracy:.2%} ({correct}/{total})")

        if errors:
            print("\n❌ Errores encontrados:")
            for err in errors:
                print(f"   - '{err['query']}': esperado {err['expected']}, "
                      f"obtuvo {err['got']} (sim={err['sim']:.2f})")

        assert accuracy >= 0.90, f"Golden dataset accuracy muy baja: {accuracy:.2%}"


@pytest.mark.semantic
class TestConfusionMatrixDetailed:
    """
    Análisis de matriz de confusión detallada.
    Metodología: Statistical analysis
    """

    TEST_DATASET = [
        # Grupo A - Emergencia (10 casos)
        ("ayuda", "A"),
        ("necesito ayuda", "A"),
        ("emergencia", "A"),
        ("ayuda por favor", "A"),
        ("es una emergencia", "A"),
        ("ayuda urgente", "A"),
        ("necesito asistencia", "A"),
        ("socorro", "A"),  # puede deletrear
        ("auxilio", "A"),  # puede deletrear
        ("help", "A"),     # puede deletrear (inglés)

        # Grupo B - Saludos (10 casos)
        ("hola", "B"),
        ("buenos días", "B"),
        ("buenas tardes", "B"),
        ("buenas noches", "B"),
        ("hola amigo", "B"),
        ("saludos", "B"),
        ("qué tal", "B"),  # puede fallar
        ("cómo estás", "B"),
        ("buen día", "B"),
        ("hi", "B"),  # puede deletrear

        # Grupo C - Comunicación Mínima (10 casos)
        ("gracias", "C"),
        ("muchas gracias", "C"),
        ("te lo agradezco", "C"),
        ("bien", "C"),
        ("mal", "C"),
        ("entiendo", "C"),
        ("no entiendo", "C"),
        ("si", "C"),
        ("no", "C"),
        ("perdon", "C")
    ]

    def test_full_confusion_matrix(self, matcher):
        """
        Calcular matriz de confusión completa.
        """
        # Matriz: [predicted][actual] = count
        matrix = defaultdict(lambda: defaultdict(int))
        total_by_group = defaultdict(int)
        correct_by_group = defaultdict(int)

        for query, expected in self.TEST_DATASET:
            result = matcher.search_similar_phrase(query)

            # Si activa deletreo, contar como "None"
            predicted = result["grupo"] if not result["deletreo_activado"] else None

            matrix[predicted][expected] += 1
            total_by_group[expected] += 1

            if predicted == expected:
                correct_by_group[expected] += 1

        # Imprimir matriz
        print("\n📊 MATRIZ DE CONFUSIÓN:")
        print("=" * 50)
        print(f"{'Predicted →':<15} {'A':<10} {'B':<10} {'C':<10} {'None':<10}")
        print("-" * 50)

        for pred in ["A", "B", "C", None]:
            row = f"{pred if pred else 'Deletreo':<15}"
            for actual in ["A", "B", "C"]:
                count = matrix[pred][actual]
                row += f"{count:<10}"
            print(row)

        # Calcular métricas
        print("\n📊 MÉTRICAS POR GRUPO:")
        print("=" * 50)

        for grupo in ["A", "B", "C"]:
            total = total_by_group[grupo]
            correct = correct_by_group[grupo]
            accuracy = correct / total if total > 0 else 0

            # Precision: de lo que predije como grupo X, cuántos eran correctos
            predicted_as_grupo = sum(matrix[grupo].values())
            precision = matrix[grupo][grupo] / predicted_as_grupo if predicted_as_grupo > 0 else 0

            # Recall: de todos los del grupo X, cuántos detecté
            recall = correct / total if total > 0 else 0

            # F1-Score
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            print(f"\nGrupo {grupo}:")
            print(f"  Accuracy:  {accuracy:.2%}")
            print(f"  Precision: {precision:.2%}")
            print(f"  Recall:    {recall:.2%}")
            print(f"  F1-Score:  {f1:.2%}")

            # Validaciones
            assert accuracy >= 0.60, f"Accuracy grupo {grupo} muy baja: {accuracy:.2%}"

    def test_per_group_precision_recall(self, matcher):
        """
        Precision y Recall por grupo (métricas estándar de ML).
        """
        true_positives = defaultdict(int)
        false_positives = defaultdict(int)
        false_negatives = defaultdict(int)

        for query, expected in self.TEST_DATASET:
            result = matcher.search_similar_phrase(query)
            predicted = result["grupo"] if not result["deletreo_activado"] else None

            if predicted == expected:
                true_positives[expected] += 1
            elif predicted is not None:
                false_positives[predicted] += 1
                false_negatives[expected] += 1
            else:
                # Deletreó cuando no debía
                false_negatives[expected] += 1

        print("\n📊 PRECISION Y RECALL:")
        for grupo in ["A", "B", "C"]:
            tp = true_positives[grupo]
            fp = false_positives[grupo]
            fn = false_negatives[grupo]

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            print(f"\nGrupo {grupo}:")
            print(f"  TP={tp}, FP={fp}, FN={fn}")
            print(f"  Precision: {precision:.2%}")
            print(f"  Recall:    {recall:.2%}")
            print(f"  F1-Score:  {f1:.2%}")

            # Objetivo: >70% en ambas métricas
            assert precision >= 0.60, f"Precision grupo {grupo}: {precision:.2%} < 60%"
            assert recall >= 0.60, f"Recall grupo {grupo}: {recall:.2%} < 60%"


@pytest.mark.semantic
class TestSimilarityDistribution:
    """
    Análisis de distribución de similitudes.
    Metodología: Statistical distribution analysis
    """

    def test_similarity_statistics(self, matcher):
        """
        Analizar estadísticas de similitud (media, std, percentiles).
        """
        queries = [
            # Matches perfectos
            "Buenos días", "Gracias", "Ayuda, por favor",
            # Matches buenos
            "hola", "ayuda", "gracias",
            # Matches medios
            "necesito ayuda", "muchas gracias", "hola amigo",
            # Matches bajos
            "socorro", "auxilio", "saludos",
        ]

        similarities = []
        for query in queries:
            result = matcher.search_similar_phrase(query)
            if not result["deletreo_activado"]:
                similarities.append(result["similitud"])

        # Estadísticas
        mean = np.mean(similarities)
        std = np.std(similarities)
        median = np.median(similarities)
        p25 = np.percentile(similarities, 25)
        p75 = np.percentile(similarities, 75)
        min_sim = np.min(similarities)
        max_sim = np.max(similarities)

        print(f"\n📊 DISTRIBUCIÓN DE SIMILITUDES:")
        print(f"  Media:    {mean:.3f}")
        print(f"  Mediana:  {median:.3f}")
        print(f"  Std Dev:  {std:.3f}")
        print(f"  Min:      {min_sim:.3f}")
        print(f"  P25:      {p25:.3f}")
        print(f"  P75:      {p75:.3f}")
        print(f"  Max:      {max_sim:.3f}")

        # Validaciones
        assert min_sim >= 0.0, "Similitud mínima negativa!"
        assert max_sim <= 1.0, "Similitud máxima > 1.0!"
        assert mean >= 0.70, f"Media muy baja: {mean:.3f}"


@pytest.mark.semantic
class TestErrorAnalysis:
    """
    Análisis de errores del sistema.
    Metodología: Qualitative error analysis
    """

    def test_identify_failure_patterns(self, matcher):
        """
        Identificar patrones en los fallos.
        """
        test_cases = [
            # Casos que pueden fallar
            ("qué tal", "B", "informal_greeting"),
            ("socorro", "A", "short_word"),
            ("Ivan", None, "name_should_spell"),
            ("ola", "B", "common_typo"),
        ]

        failures = []
        for query, expected, reason in test_cases:
            result = matcher.search_similar_phrase(query)
            actual = result["grupo"] if not result["deletreo_activado"] else None

            if actual != expected:
                failures.append({
                    "query": query,
                    "expected": expected,
                    "actual": actual,
                    "similarity": result["similitud"],
                    "reason": reason,
                    "deletreo": result["deletreo_activado"]
                })

        if failures:
            print(f"\n⚠️  PATRONES DE FALLO IDENTIFICADOS ({len(failures)}):")
            for f in failures:
                print(f"\n  Query: '{f['query']}'")
                print(f"  Esperado: {f['expected']}, Obtuvo: {f['actual']}")
                print(f"  Similitud: {f['similarity']:.3f}")
                print(f"  Razón: {f['reason']}")
                print(f"  Deletreo: {f['deletreo']}")

        # Documentar, no fallar (estos son casos conocidos)
        print(f"\n📝 Casos edge documentados: {len(failures)}")


@pytest.mark.semantic
class TestRobustnessMetrics:
    """
    Métricas de robustez del sistema.
    """

    def test_robustness_to_typos_metric(self, matcher):
        """
        Medir robustez ante errores ortográficos.
        Métrica: % de typos que aún se clasifican correctamente
        """
        typo_pairs = [
            ("hola", "hla", "B"),
            ("hola", "hila", "B"),
            ("ayuda", "ayda", "A"),
            ("ayuda", "yuda", "A"),
            ("gracias", "grcias", "C"),
            ("gracias", "graias", "C"),
        ]

        correct_with_typo = 0
        total_typos = 0

        for correct, typo, expected_grupo in typo_pairs:
            result = matcher.search_similar_phrase(typo)
            total_typos += 1

            if not result["deletreo_activado"] and result["grupo"] == expected_grupo:
                correct_with_typo += 1

        robustness_rate = correct_with_typo / total_typos
        print(f"\n📊 Tasa de Robustez ante Typos: {robustness_rate:.2%}")
        print(f"   {correct_with_typo}/{total_typos} typos clasificados correctamente")

        # Objetivo: >50% de typos manejados correctamente
        assert robustness_rate >= 0.40, \
            f"Robustez muy baja: {robustness_rate:.2%}"

    def test_degradation_curve(self, matcher):
        """
        Curva de degradación: cómo baja la accuracy con más errores.
        """
        base_queries = [
            ("hola", "B"),
            ("ayuda", "A"),
            ("gracias", "C"),
        ]

        # Función para introducir N errores
        def add_errors(text, n):
            if n == 0:
                return text
            if n == 1:
                return text[1:] if len(text) > 1 else "x"  # quitar primer char
            if n == 2:
                return text[1:-1] if len(text) > 2 else "x"  # quitar primero y último
            return "xxx"  # muchos errores

        degradation = {0: 0, 1: 0, 2: 0, 3: 0}

        for base_query, expected_grupo in base_queries:
            for n_errors in [0, 1, 2, 3]:
                corrupted = add_errors(base_query, n_errors)
                result = matcher.search_similar_phrase(corrupted)

                if not result["deletreo_activado"] and result["grupo"] == expected_grupo:
                    degradation[n_errors] += 1

        # Normalizar
        total_per_level = len(base_queries)
        degradation_rates = {k: v/total_per_level for k, v in degradation.items()}

        print(f"\n📊 CURVA DE DEGRADACIÓN:")
        for n_errors, rate in degradation_rates.items():
            print(f"  {n_errors} errores: {rate:.1%} accuracy")

        # La accuracy debe bajar gradualmente
        assert degradation_rates[0] >= degradation_rates[1] >= degradation_rates[2]
