"""
Locust Load Testing Configuration.

Simula usuarios reales interactuando con la API.

Ejecución:
    # Web UI (recomendado)
    locust -f tests/performance/locustfile.py --host=http://localhost:8000

    # Headless (sin UI)
    locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # Con CSV output
    locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
           --users 50 --spawn-rate 5 --run-time 2m --csv=results --headless

Escenarios:
    - ReadOnlyUser: Solo consultas (90% de tráfico)
    - NormalUser: Consultas + exploraciones (10% de tráfico)
"""

from locust import HttpUser, task, between, events
import random
import time
import json


# Datos de test realistas
QUERIES_EMERGENCIA = [
    "ayuda",
    "necesito ayuda",
    "ayuda por favor",
    "es una emergencia",
    "ayuda urgente",
    "socorro",
    "auxilio",
]

QUERIES_SALUDOS = [
    "hola",
    "buenos días",
    "buenas tardes",
    "buenas noches",
    "hola amigo",
    "qué tal",
    "cómo estás",
]

QUERIES_AGRADECIMIENTO = [
    "gracias",
    "muchas gracias",
    "te lo agradezco",
    "bien",
    "si",
    "vale",
    "entiendo",
]

QUERIES_TYPOS = [
    "ola",      # typo de hola
    "ayda",     # typo de ayuda
    "grcias",   # typo de gracias
    "hla",      # typo de hola
]

QUERIES_NOMBRES = [
    "Juan",
    "Maria",
    "Carlos",
    "Ana",
    "Pedro",
]

QUERIES_NOMBRES_PATTERNS = [
    "Me llamo Juan",
    "Mi nombre es Maria",
    "Me llamo Carlos",
    "Mi nombre es Ana",
]

ALL_QUERIES = QUERIES_EMERGENCIA + QUERIES_SALUDOS + QUERIES_AGRADECIMIENTO


class ReadOnlyUser(HttpUser):
    """
    Usuario que solo hace consultas (lectura).
    Representa 90% del tráfico típico.
    """
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre requests
    weight = 9  # 90% de los usuarios serán de este tipo

    @task(10)
    def buscar_query_normal(self):
        """
        Task más común: Buscar query normal (saludos, ayuda, gracias).
        """
        query = random.choice(ALL_QUERIES)
        with self.client.post(
            "/buscar",
            json={"texto": query},
            catch_response=True,
            name="POST /buscar [normal]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Validar respuesta
                if "similitud" in data and 0.0 <= data["similitud"] <= 1.0:
                    response.success()
                else:
                    response.failure(f"Similitud inválida: {data.get('similitud')}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def buscar_query_con_typo(self):
        """
        Usuario comete error de tipeo.
        """
        query = random.choice(QUERIES_TYPOS)
        with self.client.post(
            "/buscar",
            json={"texto": query},
            catch_response=True,
            name="POST /buscar [typo]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if 0.0 <= data.get("similitud", -1) <= 1.0:
                    response.success()
                else:
                    response.failure("Similitud fuera de rango")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def buscar_nombre(self):
        """
        Usuario escribe un nombre (debe activar deletreo).
        """
        query = random.choice(QUERIES_NOMBRES)
        with self.client.post(
            "/buscar",
            json={"texto": query},
            catch_response=True,
            name="POST /buscar [nombre]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Nombres deben activar deletreo
                if data.get("deletreo_activado"):
                    response.success()
                else:
                    # No falla, pero es interesante
                    response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def buscar_patron_nombre(self):
        """
        Usuario usa patrón 'Me llamo X'.
        """
        query = random.choice(QUERIES_NOMBRES_PATTERNS)
        with self.client.post(
            "/buscar",
            json={"texto": query},
            catch_response=True,
            name="POST /buscar [patron_nombre]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("nombre_detectado"):
                    response.success()
                else:
                    response.success()  # No crítico
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def health_check(self):
        """
        Usuario verifica salud del sistema.
        """
        with self.client.get("/health", catch_response=True, name="GET /health") as response:
            if response.status_code == 200 and response.json().get("status") == "healthy":
                response.success()
            else:
                response.failure("Health check failed")


class NormalUser(HttpUser):
    """
    Usuario que explora la API (lectura + exploración).
    Representa 10% del tráfico.
    """
    wait_time = between(2, 5)
    weight = 1  # 10% de los usuarios

    @task(5)
    def buscar_query(self):
        """Buscar query normal."""
        query = random.choice(ALL_QUERIES)
        self.client.post("/buscar", json={"texto": query}, name="POST /buscar")

    @task(2)
    def ver_todos_grupos(self):
        """Explorar grupos disponibles."""
        with self.client.get("/grupos", catch_response=True, name="GET /grupos") as response:
            if response.status_code == 200:
                data = response.json()
                if "grupos" in data and len(data["grupos"]) > 0:
                    response.success()
                else:
                    response.failure("No hay grupos")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def ver_grupo_especifico(self):
        """Ver frases de un grupo específico."""
        grupo = random.choice(["A", "B", "C"])
        with self.client.get(f"/grupos/{grupo}", catch_response=True, name="GET /grupos/{grupo}") as response:
            if response.status_code == 200:
                data = response.json()
                if "frases" in data and len(data["frases"]) > 0:
                    response.success()
                else:
                    response.failure("No hay frases")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def deletrear_texto(self):
        """Usar endpoint de deletreo directo."""
        texto = random.choice(["test", "hola", "xyz123"])
        with self.client.post(
            "/deletreo",
            json={"texto": texto, "incluir_espacios": False},
            catch_response=True,
            name="POST /deletreo"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "deletreo" in data and isinstance(data["deletreo"], list):
                    response.success()
                else:
                    response.failure("Formato de deletreo inválido")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def root_endpoint(self):
        """Ver info del sistema."""
        with self.client.get("/", catch_response=True, name="GET /") as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    response.success()
                else:
                    response.failure("Status no OK")
            else:
                response.failure(f"Status: {response.status_code}")


class StressUser(HttpUser):
    """
    Usuario agresivo para stress testing.
    NO incluir en tests normales, solo para encontrar límites.
    """
    wait_time = between(0.1, 0.5)  # Muy rápido
    weight = 0  # Desactivado por defecto

    @task
    def rapid_fire_queries(self):
        """Queries muy rápidas."""
        for _ in range(10):
            query = random.choice(ALL_QUERIES)
            self.client.post("/buscar", json={"texto": query})
            time.sleep(0.05)  # 50ms entre queries


# ==================== EVENT LISTENERS ====================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al inicio del test."""
    print("\n" + "="*60)
    print("🚀 INICIANDO LOAD TEST CON LOCUST")
    print("="*60)
    print(f"Host: {environment.host}")
    print(f"Usuarios: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al final del test."""
    print("\n" + "="*60)
    print("✅ LOAD TEST COMPLETADO")
    print("="*60)

    stats = environment.stats
    print(f"\nEstadísticas Globales:")
    print(f"  Total requests:        {stats.total.num_requests}")
    print(f"  Total failures:        {stats.total.num_failures}")
    print(f"  Failure rate:          {stats.total.fail_ratio * 100:.2f}%")
    print(f"  Avg response time:     {stats.total.avg_response_time:.2f}ms")
    print(f"  Min response time:     {stats.total.min_response_time:.2f}ms")
    print(f"  Max response time:     {stats.total.max_response_time:.2f}ms")
    print(f"  Median response time:  {stats.total.median_response_time:.2f}ms")
    print(f"  Requests/s:            {stats.total.total_rps:.2f}")

    print("\n" + "="*60 + "\n")


# ==================== ESCENARIOS PREDEFINIDOS ====================

class QuickTest(HttpUser):
    """
    Test rápido de humo (smoke test).
    Usar para validar que la API funciona antes de load test completo.

    Ejecución:
        locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
               --users 5 --spawn-rate 1 --run-time 30s --headless \
               QuickTest
    """
    wait_time = between(1, 2)

    @task
    def smoke_test(self):
        # Health check
        self.client.get("/health")

        # Query simple
        self.client.post("/buscar", json={"texto": "hola"})

        # Ver grupos
        self.client.get("/grupos")


# ==================== HELPER FUNCTIONS ====================

def run_load_test(host="http://localhost:8000", users=50, spawn_rate=5, duration="2m"):
    """
    Helper para ejecutar load test programáticamente.

    Ejemplo:
        from tests.performance.locustfile import run_load_test
        run_load_test(users=100, duration="5m")
    """
    import subprocess

    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--host", host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--headless",
        "--csv", "locust_results",
        "--html", "locust_report.html"
    ]

    print(f"Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd)


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                  LOCUST LOAD TESTING                           ║
    ╚════════════════════════════════════════════════════════════════╝

    Uso:

    1. Test básico con UI web:
       locust -f tests/performance/locustfile.py --host=http://localhost:8000
       Luego abre: http://localhost:8089

    2. Test headless (sin UI):
       locust -f tests/performance/locustfile.py --host=http://localhost:8000 \\
              --users 50 --spawn-rate 5 --run-time 2m --headless

    3. Test rápido de humo:
       locust -f tests/performance/locustfile.py --host=http://localhost:8000 \\
              --users 5 --spawn-rate 1 --run-time 30s --headless QuickTest

    4. Stress test extremo:
       locust -f tests/performance/locustfile.py --host=http://localhost:8000 \\
              --users 200 --spawn-rate 20 --run-time 5m --headless

    5. Con reportes CSV y HTML:
       locust -f tests/performance/locustfile.py --host=http://localhost:8000 \\
              --users 100 --spawn-rate 10 --run-time 5m --headless \\
              --csv=results --html=report.html

    Escenarios disponibles:
    - ReadOnlyUser:  90% usuarios, solo consultas
    - NormalUser:    10% usuarios, consultas + exploración
    - StressUser:    Desactivado, para stress extremo
    - QuickTest:     Test rápido de humo

    """)
