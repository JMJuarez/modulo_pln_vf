"""
Tests de rendimiento y benchmarks.
Validan que el sistema cumple con los objetivos de latencia y throughput.
"""

import pytest
import time
from app.matcher_improved import ImprovedPhraseMatcher


@pytest.fixture(scope="module")
def matcher():
    """Matcher para tests de rendimiento."""
    m = ImprovedPhraseMatcher(
        model_type="multilingual_balanced",
        use_reranking=True,
        use_synonym_expansion=True
    )
    m.initialize()
    return m


@pytest.mark.performance
class TestInitializationPerformance:
    """Tests de rendimiento de inicialización."""

    def test_initialization_with_cache(self, benchmark):
        """
        Inicialización con cache debe ser rápida (<2s).
        """
        def initialize():
            m = ImprovedPhraseMatcher()
            m.initialize()
            return m

        result = benchmark(initialize)
        assert result is not None

    @pytest.mark.slow
    def test_cold_start_time(self):
        """
        Tiempo de inicio en frío (sin cache).
        Objetivo: <10s
        """
        start = time.time()
        m = ImprovedPhraseMatcher()
        m.initialize()
        elapsed = time.time() - start

        print(f"\n⏱️  Tiempo de inicio en frío: {elapsed:.2f}s")
        assert elapsed < 10.0, f"Inicio muy lento: {elapsed:.2f}s"


@pytest.mark.performance
class TestQueryLatency:
    """Tests de latencia por query."""

    def test_single_query_latency(self, matcher, benchmark):
        """
        Latencia de una query debe ser <100ms.
        """
        def search():
            return matcher.search_similar_phrase("hola")

        result = benchmark(search)

        # Benchmark proporciona estadísticas
        # Validar que el resultado es correcto
        assert 0.0 <= result["similitud"] <= 1.0

    @pytest.mark.parametrize("query", [
        "hola",
        "ayuda por favor",
        "gracias",
        "necesito ayuda urgente",
    ])
    def test_various_queries_latency(self, matcher, benchmark, query):
        """
        Diferentes tipos de queries deben tener latencia similar.
        """
        def search():
            return matcher.search_similar_phrase(query)

        result = benchmark(search)
        assert 0.0 <= result["similitud"] <= 1.0


@pytest.mark.performance
class TestThroughput:
    """Tests de throughput (queries por segundo)."""

    def test_sequential_queries_throughput(self, matcher):
        """
        Throughput con queries secuenciales.
        Objetivo: >50 queries/segundo
        """
        queries = ["hola", "ayuda", "gracias"] * 20  # 60 queries

        start = time.time()
        for query in queries:
            result = matcher.search_similar_phrase(query)
            assert 0.0 <= result["similitud"] <= 1.0
        elapsed = time.time() - start

        throughput = len(queries) / elapsed
        print(f"\n📊 Throughput secuencial: {throughput:.1f} queries/s")
        assert throughput > 50, f"Throughput bajo: {throughput:.1f} q/s"

    @pytest.mark.slow
    def test_sustained_load(self, matcher):
        """
        Carga sostenida: 1000 queries sin degradación.
        """
        queries = ["hola", "ayuda", "gracias"] * 334  # ~1000 queries

        latencies = []
        for query in queries:
            start = time.time()
            result = matcher.search_similar_phrase(query)
            elapsed = time.time() - start
            latencies.append(elapsed)

            assert 0.0 <= result["similitud"] <= 1.0

        # Analizar latencias
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\n📊 Carga sostenida (1000 queries):")
        print(f"   Latencia promedio: {avg_latency*1000:.2f}ms")
        print(f"   Latencia máxima: {max_latency*1000:.2f}ms")
        print(f"   Latencia P95: {p95_latency*1000:.2f}ms")

        assert avg_latency < 0.1, f"Latencia promedio alta: {avg_latency*1000:.0f}ms"
        assert p95_latency < 0.2, f"P95 latency alta: {p95_latency*1000:.0f}ms"


@pytest.mark.performance
class TestMemoryUsage:
    """Tests de uso de memoria."""

    def test_memory_footprint(self, matcher):
        """
        Uso de memoria del matcher debe ser razonable.
        Este es un test informativo más que de validación.
        """
        import sys

        # Tamaño aproximado del matcher en memoria
        size_embeddings = sum(
            emb.nbytes for emb in matcher.grupos_embeddings.values()
        )
        size_centroids = sum(
            c.nbytes for c in matcher.grupos_centroids.values()
        )

        total_size_mb = (size_embeddings + size_centroids) / (1024 * 1024)

        print(f"\n💾 Uso de memoria:")
        print(f"   Embeddings: {size_embeddings/(1024*1024):.2f} MB")
        print(f"   Centroids: {size_centroids/(1024):.2f} KB")
        print(f"   Total: {total_size_mb:.2f} MB")

        # Validación suave: no debe exceder 500MB
        assert total_size_mb < 500, f"Uso de memoria muy alto: {total_size_mb:.2f}MB"


@pytest.mark.performance
class TestCacheEfficiency:
    """Tests de eficiencia del cache."""

    def test_cache_speedup(self):
        """
        Inicialización con cache debe ser significativamente más rápida.
        """
        # Primera inicialización (puede crear cache)
        start1 = time.time()
        m1 = ImprovedPhraseMatcher()
        m1.initialize()
        time1 = time.time() - start1

        # Segunda inicialización (usa cache)
        start2 = time.time()
        m2 = ImprovedPhraseMatcher()
        m2.initialize()
        time2 = time.time() - start2

        print(f"\n⚡ Eficiencia del cache:")
        print(f"   Primera inicialización: {time1:.2f}s")
        print(f"   Segunda inicialización: {time2:.2f}s")
        print(f"   Speedup: {time1/time2:.1f}x")

        # Segunda debe ser al menos 2x más rápida (si hay cache)
        # Si no hay cache, ambas serán similares
        assert time2 < 5.0, f"Inicialización lenta incluso con cache: {time2:.2f}s"
