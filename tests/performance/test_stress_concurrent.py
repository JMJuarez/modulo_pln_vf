"""
Tests de Estrés con Concurrencia.

Metodologías:
1. Concurrent Load Testing - Múltiples usuarios simultáneos
2. Spike Testing - Picos súbitos de carga
3. Soak Testing - Carga prolongada
4. Stress Testing - Encontrar punto de quiebre
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, stdev
from fastapi.testclient import TestClient
from app.main import app
from app.matcher_improved import ImprovedPhraseMatcher


@pytest.fixture(scope="module")
def matcher():
    """Matcher para tests de estrés."""
    m = ImprovedPhraseMatcher(
        model_type="multilingual_balanced",
        use_reranking=True,
        use_synonym_expansion=True
    )
    m.initialize()
    return m


@pytest.fixture
def client():
    """Cliente de testing para la API."""
    return TestClient(app)


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentLoad:
    """
    Tests de carga concurrente - múltiples usuarios simultáneos.
    Metodología: Concurrent Load Testing
    """

    def test_concurrent_10_users(self, client):
        """
        10 usuarios concurrentes haciendo queries simultáneas.
        Objetivo: Sistema debe mantener latencia <200ms con 10 usuarios.
        """
        num_users = 10
        queries_per_user = 10

        queries = ["hola", "ayuda", "gracias", "buenos días", "muchas gracias"]

        def user_session(user_id):
            """Simula una sesión de usuario."""
            results = []
            for i in range(queries_per_user):
                query = queries[i % len(queries)]
                start = time.time()
                response = client.post("/buscar", json={"texto": query})
                latency = time.time() - start

                results.append({
                    "user_id": user_id,
                    "query": query,
                    "status": response.status_code,
                    "latency": latency,
                    "valid": 0.0 <= response.json().get("similitud", -1) <= 1.0 if response.status_code == 200 else False
                })
            return results

        # Ejecutar usuarios concurrentemente
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_session, user_id) for user_id in range(num_users)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        total_time = time.time() - start_time

        # Análisis de resultados
        total_queries = len(all_results)
        successful = sum(1 for r in all_results if r["status"] == 200)
        valid_responses = sum(1 for r in all_results if r["valid"])
        latencies = [r["latency"] for r in all_results if r["status"] == 200]

        avg_latency = mean(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        throughput = total_queries / total_time

        print(f"\n📊 CONCURRENT LOAD TEST (10 usuarios):")
        print(f"   Total queries:     {total_queries}")
        print(f"   Exitosas:          {successful}/{total_queries} ({successful/total_queries*100:.1f}%)")
        print(f"   Respuestas válidas: {valid_responses}/{total_queries} ({valid_responses/total_queries*100:.1f}%)")
        print(f"   Latencia promedio: {avg_latency*1000:.2f}ms")
        print(f"   Latencia mínima:   {min_latency*1000:.2f}ms")
        print(f"   Latencia máxima:   {max_latency*1000:.2f}ms")
        print(f"   Latencia P95:      {p95_latency*1000:.2f}ms")
        print(f"   Throughput:        {throughput:.1f} queries/s")
        print(f"   Tiempo total:      {total_time:.2f}s")

        # Validaciones
        assert successful / total_queries >= 0.95, f"Tasa de éxito baja: {successful/total_queries*100:.1f}%"
        assert valid_responses / total_queries >= 0.95, "Muchas respuestas inválidas"
        assert avg_latency < 0.2, f"Latencia promedio alta: {avg_latency*1000:.0f}ms"
        assert p95_latency < 0.5, f"P95 muy alto: {p95_latency*1000:.0f}ms"

    def test_concurrent_50_users(self, client):
        """
        50 usuarios concurrentes - Test de estrés moderado.
        Objetivo: Sistema debe mantener >90% éxito con 50 usuarios.
        """
        num_users = 50
        queries_per_user = 5

        queries = ["hola", "ayuda", "gracias", "buenos días", "emergencia"]

        def user_session(user_id):
            results = []
            for i in range(queries_per_user):
                query = queries[i % len(queries)]
                try:
                    start = time.time()
                    response = client.post("/buscar", json={"texto": query})
                    latency = time.time() - start

                    results.append({
                        "status": response.status_code,
                        "latency": latency,
                        "valid": 0.0 <= response.json().get("similitud", -1) <= 1.0 if response.status_code == 200 else False
                    })
                except Exception as e:
                    results.append({
                        "status": 500,
                        "latency": 0,
                        "valid": False,
                        "error": str(e)
                    })
            return results

        # Ejecutar
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_session, uid) for uid in range(num_users)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        total_time = time.time() - start_time

        # Análisis
        total = len(all_results)
        successful = sum(1 for r in all_results if r["status"] == 200)
        valid = sum(1 for r in all_results if r["valid"])
        success_rate = successful / total

        print(f"\n📊 STRESS TEST (50 usuarios):")
        print(f"   Total queries:  {total}")
        print(f"   Exitosas:       {successful} ({success_rate*100:.1f}%)")
        print(f"   Válidas:        {valid} ({valid/total*100:.1f}%)")
        print(f"   Tiempo total:   {total_time:.2f}s")
        print(f"   Throughput:     {total/total_time:.1f} q/s")

        # El sistema debe mantener >90% bajo carga moderada
        assert success_rate >= 0.90, f"Tasa de éxito muy baja: {success_rate*100:.1f}%"

    @pytest.mark.slow
    def test_concurrent_100_users_breaking_point(self, client):
        """
        100 usuarios concurrentes - Encontrar punto de quiebre.
        Objetivo: Documentar comportamiento bajo estrés extremo.
        """
        num_users = 100
        queries_per_user = 3

        queries = ["hola", "ayuda", "gracias"]

        def user_session(user_id):
            results = []
            for i in range(queries_per_user):
                try:
                    start = time.time()
                    response = client.post("/buscar", json={"texto": queries[i]})
                    latency = time.time() - start
                    results.append({"status": response.status_code, "latency": latency})
                except Exception as e:
                    results.append({"status": 500, "latency": 0, "error": str(e)})
            return results

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_session, uid) for uid in range(num_users)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        total_time = time.time() - start_time

        total = len(all_results)
        successful = sum(1 for r in all_results if r["status"] == 200)
        success_rate = successful / total

        print(f"\n⚠️  BREAKING POINT TEST (100 usuarios):")
        print(f"   Total queries:  {total}")
        print(f"   Exitosas:       {successful} ({success_rate*100:.1f}%)")
        print(f"   Tiempo total:   {total_time:.2f}s")
        print(f"   Throughput:     {total/total_time:.1f} q/s")

        # Solo documentar, no fallar
        print(f"\n   ℹ️  Test informativo - sistema bajo estrés extremo")
        print(f"   ℹ️  Éxito rate: {success_rate*100:.1f}%")

        # Validación suave - al menos 50% debe funcionar incluso bajo estrés extremo
        assert success_rate >= 0.50, f"Sistema colapsó: solo {success_rate*100:.1f}% exitosas"


@pytest.mark.performance
@pytest.mark.slow
class TestSpikeLoad:
    """
    Tests de picos de carga súbitos.
    Metodología: Spike Testing
    """

    def test_sudden_spike_0_to_20_users(self, client):
        """
        Spike súbito: 0 → 20 usuarios en 1 segundo.
        Objetivo: Sistema debe adaptarse sin fallos.
        """
        num_users = 20
        queries = ["hola", "ayuda", "gracias"] * 10

        def rapid_queries():
            results = []
            for query in queries[:10]:  # 10 queries por usuario
                try:
                    response = client.post("/buscar", json={"texto": query})
                    results.append(response.status_code == 200)
                except:
                    results.append(False)
            return results

        # Spike súbito - todos empiezan al mismo tiempo
        start = time.time()
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(rapid_queries) for _ in range(num_users)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        elapsed = time.time() - start

        total = len(all_results)
        successful = sum(all_results)
        success_rate = successful / total

        print(f"\n⚡ SPIKE TEST (0→20 usuarios):")
        print(f"   Tiempo de spike: {elapsed:.2f}s")
        print(f"   Total queries:   {total}")
        print(f"   Exitosas:        {successful} ({success_rate*100:.1f}%)")

        # Bajo spike, al menos 80% debe funcionar
        assert success_rate >= 0.80, f"Sistema no manejó spike: {success_rate*100:.1f}%"


@pytest.mark.performance
@pytest.mark.slow
class TestSoakTesting:
    """
    Tests de carga prolongada (Soak Testing).
    Metodología: Detectar memory leaks y degradación gradual.
    """

    def test_sustained_load_5_minutes(self, client):
        """
        Carga sostenida: 5 usuarios durante 5 minutos.
        Objetivo: Detectar degradación, memory leaks, etc.
        """
        duration_seconds = 300  # 5 minutos
        num_users = 5

        queries = ["hola", "ayuda", "gracias", "buenos días"]

        def continuous_user(user_id, stop_time):
            """Usuario que hace queries continuamente hasta stop_time."""
            results = []
            query_count = 0
            while time.time() < stop_time:
                query = queries[query_count % len(queries)]
                try:
                    start = time.time()
                    response = client.post("/buscar", json={"texto": query})
                    latency = time.time() - start

                    results.append({
                        "timestamp": start,
                        "latency": latency,
                        "status": response.status_code,
                        "query_num": query_count
                    })
                    query_count += 1
                    time.sleep(0.1)  # Pequeña pausa entre queries
                except Exception as e:
                    results.append({
                        "timestamp": time.time(),
                        "latency": 0,
                        "status": 500,
                        "error": str(e)
                    })
            return results

        print(f"\n⏱️  SOAK TEST - Iniciando carga sostenida de 5 minutos...")
        print(f"   {num_users} usuarios haciendo queries continuas...")

        start_time = time.time()
        stop_time = start_time + duration_seconds

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(continuous_user, uid, stop_time) for uid in range(num_users)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        actual_duration = time.time() - start_time

        # Análisis de degradación temporal
        total = len(all_results)
        successful = sum(1 for r in all_results if r["status"] == 200)

        # Dividir en ventanas de 1 minuto
        window_size = 60  # segundos
        windows = {}
        for r in all_results:
            if r["status"] == 200:
                window = int((r["timestamp"] - start_time) / window_size)
                if window not in windows:
                    windows[window] = []
                windows[window].append(r["latency"])

        print(f"\n📊 SOAK TEST RESULTS:")
        print(f"   Duración real:     {actual_duration:.1f}s")
        print(f"   Total queries:     {total}")
        print(f"   Exitosas:          {successful} ({successful/total*100:.1f}%)")
        print(f"   Queries/segundo:   {total/actual_duration:.1f}")

        print(f"\n   Análisis temporal (ventanas de 1 minuto):")
        for window, latencies in sorted(windows.items()):
            avg_lat = mean(latencies)
            print(f"     Minuto {window+1}: avg latency = {avg_lat*1000:.2f}ms, queries = {len(latencies)}")

        # Validar que no hay degradación significativa
        if len(windows) >= 2:
            first_window_avg = mean(windows[0])
            last_window_avg = mean(windows[max(windows.keys())])
            degradation = (last_window_avg - first_window_avg) / first_window_avg

            print(f"\n   Degradación: {degradation*100:.1f}%")

            # La latencia no debe aumentar más de 50% con el tiempo
            assert degradation < 0.50, f"Degradación significativa detectada: {degradation*100:.1f}%"

        # Tasa de éxito debe mantenerse alta
        assert successful / total >= 0.95, f"Tasa de éxito baja en soak test: {successful/total*100:.1f}%"


@pytest.mark.performance
class TestResourceExhaustion:
    """
    Tests de agotamiento de recursos.
    Metodología: Resource Exhaustion Testing
    """

    def test_memory_stability_under_load(self, matcher):
        """
        Test de estabilidad de memoria bajo carga.
        1000 queries para verificar que no hay memory leaks.
        """
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Memoria inicial
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        queries = ["hola", "ayuda", "gracias", "buenos días"] * 250  # 1000 queries

        for query in queries:
            result = matcher.search_similar_phrase(query)
            assert 0.0 <= result["similitud"] <= 1.0

        # Memoria final
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory
        memory_increase_pct = (memory_increase / initial_memory) * 100

        print(f"\n💾 MEMORY STABILITY TEST:")
        print(f"   Memoria inicial:  {initial_memory:.2f} MB")
        print(f"   Memoria final:    {final_memory:.2f} MB")
        print(f"   Incremento:       {memory_increase:.2f} MB ({memory_increase_pct:.1f}%)")

        # El incremento de memoria no debe ser mayor a 20%
        assert memory_increase_pct < 20, f"Posible memory leak: {memory_increase_pct:.1f}% incremento"

    def test_error_recovery(self, client):
        """
        Test de recuperación después de errores.
        Sistema debe recuperarse después de queries inválidas.
        """
        # Fase 1: Queries válidas
        valid_queries = ["hola", "ayuda", "gracias"]
        valid_results = []
        for q in valid_queries:
            response = client.post("/buscar", json={"texto": q})
            valid_results.append(response.status_code == 200)

        # Fase 2: Queries inválidas (stress)
        invalid_queries = ["", "   ", None, "x" * 10000]
        for q in invalid_queries:
            try:
                client.post("/buscar", json={"texto": q})
            except:
                pass  # Esperamos errores

        # Fase 3: Queries válidas de nuevo (recovery)
        recovery_results = []
        for q in valid_queries:
            response = client.post("/buscar", json={"texto": q})
            recovery_results.append(response.status_code == 200)

        valid_success = sum(valid_results) / len(valid_results)
        recovery_success = sum(recovery_results) / len(recovery_results)

        print(f"\n🔄 ERROR RECOVERY TEST:")
        print(f"   Pre-error success:  {valid_success*100:.1f}%")
        print(f"   Post-error success: {recovery_success*100:.1f}%")

        # Sistema debe recuperarse completamente
        assert recovery_success >= 0.90, f"Sistema no se recuperó: {recovery_success*100:.1f}%"
        assert recovery_success >= valid_success * 0.90, "Degradación después de errores"


@pytest.mark.performance
class TestGradualDegradation:
    """
    Tests de degradación gradual.
    Metodología: Gradual Degradation Testing
    """

    def test_increasing_load_degradation_curve(self, client):
        """
        Curva de degradación con carga incremental.
        1 → 5 → 10 → 20 → 50 usuarios.
        """
        load_levels = [1, 5, 10, 20, 50]
        results_by_load = {}

        for num_users in load_levels:
            queries_per_user = 10

            def user_queries():
                successful = 0
                for i in range(queries_per_user):
                    try:
                        response = client.post("/buscar", json={"texto": "hola"})
                        if response.status_code == 200:
                            successful += 1
                    except:
                        pass
                return successful

            with ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [executor.submit(user_queries) for _ in range(num_users)]
                total_successful = sum(f.result() for f in as_completed(futures))

            total_queries = num_users * queries_per_user
            success_rate = total_successful / total_queries
            results_by_load[num_users] = success_rate

        print(f"\n📈 DEGRADATION CURVE:")
        for load, success in results_by_load.items():
            print(f"   {load:3d} usuarios: {success*100:.1f}% éxito")

        # Validar que la degradación es gradual, no abrupta
        rates = list(results_by_load.values())
        for i in range(len(rates) - 1):
            drop = rates[i] - rates[i+1]
            assert drop < 0.30, f"Degradación abrupta detectada: {drop*100:.1f}%"
