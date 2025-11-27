# 🚀 Performance & Stress Testing

Suite completa de tests de rendimiento, carga y estrés para el módulo de PLN.

## 📁 Estructura

```
tests/performance/
├── README.md                      # Este archivo
├── STRESS_TESTING_GUIDE.md        # Guía detallada de tests de estrés
├── test_benchmarks.py             # Benchmarks básicos (latencia, throughput)
├── test_stress_concurrent.py      # Tests de concurrencia y estrés (NUEVO)
├── locustfile.py                  # Configuración de Locust para load testing (NUEVO)
└── stress_results/                # Directorio para resultados (autogenerado)
```

## ⚡ Quick Start

### Opción 1: Script Automatizado (Más Fácil)

```bash
# Ejecutar script interactivo
./run_stress_tests.sh

# Seleccionar opción del menú
# Recomendado para empezar: Opción 1 (Quick Test)
```

### Opción 2: Tests Individuales

```bash
# Tests de benchmarks básicos (rápido)
pytest tests/performance/test_benchmarks.py -v -s

# Tests de concurrencia
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad -v -s

# Locust con UI web
locust -f tests/performance/locustfile.py --host=http://localhost:8000
# Luego abre: http://localhost:8089
```

## 📊 Tipos de Tests

| Tipo | Archivo | Duración | Propósito |
|------|---------|----------|-----------|
| **Benchmarks** | `test_benchmarks.py` | <1 min | Latencia, throughput baseline |
| **Concurrencia** | `test_stress_concurrent.py` | 2-5 min | Múltiples usuarios simultáneos |
| **Spike** | `test_stress_concurrent.py` | <1 min | Picos súbitos de carga |
| **Soak** | `test_stress_concurrent.py` | 5-10 min | Carga sostenida (memory leaks) |
| **Locust** | `locustfile.py` | Variable | Simulación realista de usuarios |

## 🎯 Métricas Objetivo

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Latencia P50 | <100ms | >200ms |
| Latencia P95 | <200ms | >500ms |
| Success Rate | >95% | <90% |
| Throughput | >50 q/s | <30 q/s |
| Max Users | 100+ | <50 |

## 🔥 Tests de Estrés Disponibles

### 1. Concurrent Load Testing

```bash
# 10 usuarios concurrentes
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad::test_concurrent_10_users -v -s

# 50 usuarios concurrentes
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad::test_concurrent_50_users -v -s

# 100 usuarios (breaking point)
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad::test_concurrent_100_users_breaking_point -v -s
```

### 2. Spike Testing

```bash
# Spike súbito: 0 → 20 usuarios
pytest tests/performance/test_stress_concurrent.py::TestSpikeLoad::test_sudden_spike_0_to_20_users -v -s
```

### 3. Soak Testing (Endurance)

```bash
# Carga sostenida 5 minutos
pytest tests/performance/test_stress_concurrent.py::TestSoakTesting::test_sustained_load_5_minutes -v -s -m slow
```

### 4. Locust Load Testing

```bash
# Light load (10 usuarios, 2 min)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 10 --spawn-rate 2 --run-time 2m --headless

# Moderate load (50 usuarios, 5 min)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless

# Heavy load (100 usuarios, 5 min)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless

# Con reportes HTML
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless \
       --csv=results --html=report.html
```

## 📈 Interpretación de Resultados

### Output de pytest

```
📊 CONCURRENT LOAD TEST (10 usuarios):
   Total queries:     100
   Exitosas:          98/100 (98.0%)
   Respuestas válidas: 98/100 (98.0%)
   Latencia promedio: 45.23ms      # ✅ Bueno (<100ms)
   Latencia P95:      89.12ms      # ✅ Bueno (<200ms)
   Throughput:        52.3 q/s     # ✅ Bueno (>50 q/s)
```

### Reportes de Locust

Los reportes HTML se generan en `stress_results/` con:
- Request statistics
- Response time charts
- Failure rate
- Users over time

**Qué buscar**:
- ✅ Failure rate <1%
- ✅ Response time estable
- ✅ RPS constante
- ❌ Picos de latencia >1s
- ❌ Failure rate >5%

## 🔧 Prerequisitos

### 1. Servidor corriendo

```bash
# Verificar
curl http://localhost:8000/health

# Si no está corriendo:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Dependencias instaladas

```bash
pip install -r requirements-test.txt
```

### 3. Recursos suficientes

- RAM: 4GB+ disponible
- CPU: 2+ cores
- File descriptors: ulimit -n >= 1024

## 🐛 Troubleshooting

### "Connection refused"
```bash
# Asegurar que el servidor está corriendo
uvicorn app.main:app --reload
```

### "Too many open files"
```bash
# Aumentar límite
ulimit -n 4096
```

### Latencias muy altas
```bash
# Warm-up del modelo primero
pytest tests/performance/test_benchmarks.py::TestInitializationPerformance::test_initialization_with_cache -v
```

### Locust no encuentra archivo
```bash
# Ejecutar desde directorio raíz del proyecto
cd /path/to/modulo_pln
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 📚 Documentación Detallada

Ver **[STRESS_TESTING_GUIDE.md](STRESS_TESTING_GUIDE.md)** para:
- Explicación detallada de cada tipo de test
- Metodologías utilizadas
- Análisis avanzado de resultados
- Best practices
- Troubleshooting extendido

## 🎓 Ejemplos de Uso

### Escenario 1: Validación rápida antes de deploy

```bash
# Quick test (30 segundos)
./run_stress_tests.sh
# Seleccionar: 1 (Quick Test)
```

### Escenario 2: Validación completa semanal

```bash
# Full suite (30+ minutos)
./run_stress_tests.sh
# Seleccionar: 8 (Full Suite)
```

### Escenario 3: Encontrar límite del sistema

```bash
# Breaking point test
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad::test_concurrent_100_users_breaking_point -v -s
```

### Escenario 4: Simular tráfico real durante 5 minutos

```bash
# Locust con mix realista de usuarios
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless \
       --html=report.html
```

## 📊 CI/CD Integration

### GitHub Actions Example

```yaml
name: Stress Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:      # Manual trigger

jobs:
  stress-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Start server
        run: |
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10
      - name: Run stress tests
        run: |
          pytest tests/performance/test_stress_concurrent.py -v -s -m "performance and not slow"
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: stress-test-results
          path: stress_results/
```

## 🚀 Roadmap

### ✅ Implementado
- [x] Tests de concurrencia básicos
- [x] Tests de spike
- [x] Soak testing
- [x] Locust integration
- [x] Script automatizado
- [x] Reportes HTML/CSV

### 🚧 Próximos pasos
- [ ] Distributed Locust (múltiples workers)
- [ ] Grafana dashboards
- [ ] CI/CD integration
- [ ] Chaos engineering tests

## 📞 Soporte

Para preguntas o problemas:
1. Revisar [STRESS_TESTING_GUIDE.md](STRESS_TESTING_GUIDE.md)
2. Revisar comentarios en el código
3. Crear issue en el repositorio

---

**Última actualización**: 2025-11-26
