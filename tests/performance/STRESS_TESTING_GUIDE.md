# Guía de Tests de Estrés

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Tipos de Tests Implementados](#tipos-de-tests-implementados)
3. [Herramientas Utilizadas](#herramientas-utilizadas)
4. [Ejecución de Tests](#ejecución-de-tests)
5. [Interpretación de Resultados](#interpretación-de-resultados)
6. [Métricas y Objetivos](#métricas-y-objetivos)
7. [Troubleshooting](#troubleshooting)

---

## Introducción

Este proyecto implementa una **suite completa de tests de estrés** para validar el rendimiento, escalabilidad y robustez del módulo de PLN bajo diferentes condiciones de carga.

### ¿Por qué tests de estrés?

- **Prevenir caídas en producción**: Identificar límites antes de deployment
- **Optimizar rendimiento**: Encontrar cuellos de botella
- **Validar SLAs**: Asegurar que se cumplen objetivos de latencia/throughput
- **Detectar memory leaks**: Validar estabilidad en carga sostenida
- **Planear escalabilidad**: Determinar capacidad de usuarios concurrentes

---

## Tipos de Tests Implementados

### 1. **Concurrent Load Testing** 🔀

**Archivo**: `test_stress_concurrent.py::TestConcurrentLoad`

Simula múltiples usuarios concurrentes haciendo requests simultáneos.

| Test | Usuarios | Queries/Usuario | Objetivo |
|------|----------|-----------------|----------|
| `test_concurrent_10_users` | 10 | 10 | Latencia <200ms |
| `test_concurrent_50_users` | 50 | 5 | Success rate >90% |
| `test_concurrent_100_users_breaking_point` | 100 | 3 | Encontrar límite |

**Propósito**: Validar que el sistema maneja múltiples usuarios simultáneos sin degradación significativa.

**Ejecución**:
```bash
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad -v -s
```

**Métricas clave**:
- ✅ Success rate (% de requests exitosos)
- ✅ Latencia promedio, mínima, máxima, P95
- ✅ Throughput (queries/segundo)

---

### 2. **Spike Testing** ⚡

**Archivo**: `test_stress_concurrent.py::TestSpikeLoad`

Simula picos súbitos de tráfico (0 → N usuarios en 1 segundo).

| Test | Spike | Objetivo |
|------|-------|----------|
| `test_sudden_spike_0_to_20_users` | 0→20 | Success rate >80% |

**Propósito**: Validar que el sistema se adapta a picos súbitos sin colapsar.

**Escenario real**: Black Friday, viral marketing, eventos especiales.

**Ejecución**:
```bash
pytest tests/performance/test_stress_concurrent.py::TestSpikeLoad -v -s
```

---

### 3. **Soak Testing (Endurance)** ⏱️

**Archivo**: `test_stress_concurrent.py::TestSoakTesting`

Carga sostenida durante períodos prolongados (5+ minutos).

| Test | Duración | Usuarios | Objetivo |
|------|----------|----------|----------|
| `test_sustained_load_5_minutes` | 5 min | 5 | Detectar degradación |

**Propósito**:
- Detectar **memory leaks**
- Validar que no hay **degradación temporal**
- Asegurar estabilidad a largo plazo

**Ejecución**:
```bash
pytest tests/performance/test_stress_concurrent.py::TestSoakTesting -v -s -m slow
```

**Análisis**: El test divide el tiempo en ventanas de 1 minuto y compara la latencia inicial vs final.

---

### 4. **Resource Exhaustion Testing** 💾

**Archivo**: `test_stress_concurrent.py::TestResourceExhaustion`

Valida uso de recursos (memoria, CPU, file descriptors).

| Test | Propósito |
|------|-----------|
| `test_memory_stability_under_load` | Memory leaks |
| `test_error_recovery` | Recuperación post-error |

**Ejecución**:
```bash
pytest tests/performance/test_stress_concurrent.py::TestResourceExhaustion -v -s
```

**Validaciones**:
- ✅ Incremento de memoria <20% después de 1000 queries
- ✅ Sistema se recupera después de errores

---

### 5. **Gradual Degradation Testing** 📉

**Archivo**: `test_stress_concurrent.py::TestGradualDegradation`

Curva de degradación con carga incremental (1 → 5 → 10 → 20 → 50 usuarios).

**Propósito**: Entender cómo el sistema degrada gradualmente al aumentar la carga.

**Ejecución**:
```bash
pytest tests/performance/test_stress_concurrent.py::TestGradualDegradation -v -s
```

---

### 6. **Locust Load Testing** 🦗

**Archivo**: `locustfile.py`

Tests de carga realistas con simulación de comportamiento de usuario.

#### **User Classes Disponibles**:

1. **ReadOnlyUser** (90% del tráfico)
   - Búsquedas normales
   - Búsquedas con typos
   - Búsquedas de nombres
   - Health checks

2. **NormalUser** (10% del tráfico)
   - Exploración de grupos
   - Deletreo directo
   - Info del sistema

3. **StressUser** (desactivado por defecto)
   - Queries muy rápidas (50ms entre requests)
   - Para encontrar límites absolutos

#### **Ejecución con Locust**:

**Opción 1: Web UI (Recomendado)**
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
# Luego abre: http://localhost:8089
```

**Opción 2: Headless (sin UI)**
```bash
# Light load (10 usuarios, 2 minutos)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 10 --spawn-rate 2 --run-time 2m --headless

# Moderate load (50 usuarios, 5 minutos)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless

# Heavy load (100 usuarios, 5 minutos)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless
```

**Opción 3: Con reportes**
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless \
       --csv=results --html=report.html
```

---

## Herramientas Utilizadas

### 1. **Pytest** + **ThreadPoolExecutor**
- Tests de concurrencia con control fino
- Análisis detallado de métricas
- Integración con CI/CD

### 2. **Locust**
- Simulación realista de usuarios
- Web UI para monitoreo en tiempo real
- Reportes HTML y CSV
- Distribución de carga

### 3. **psutil**
- Monitoreo de memoria
- Detección de memory leaks

---

## Ejecución de Tests

### **Opción 1: Script Automatizado** (Recomendado)

```bash
./run_stress_tests.sh
```

Menú interactivo con opciones:
1. Quick Test (30s)
2. Light Load (10 usuarios, 2 min)
3. Moderate Load (50 usuarios, 5 min)
4. Heavy Load (100 usuarios, 5 min)
5. Stress Test (200 usuarios, 5 min)
6. Concurrent Tests (pytest)
7. Soak Test (10 min)
8. Full Suite (>30 min)
9. Custom Test

### **Opción 2: Pytest Directo**

```bash
# Todos los tests de performance
pytest tests/performance/ -v -s -m performance

# Solo tests rápidos
pytest tests/performance/ -v -s -m "performance and not slow"

# Solo concurrencia
pytest tests/performance/test_stress_concurrent.py::TestConcurrentLoad -v -s

# Solo soak testing
pytest tests/performance/test_stress_concurrent.py::TestSoakTesting -v -s
```

### **Opción 3: Locust Directo**

Ver sección anterior.

---

## Interpretación de Resultados

### Métricas Clave

| Métrica | Bueno | Aceptable | Malo |
|---------|-------|-----------|------|
| **Latencia promedio** | <100ms | <200ms | >200ms |
| **Latencia P95** | <200ms | <500ms | >500ms |
| **Success rate** | >95% | >90% | <90% |
| **Throughput** | >50 q/s | >30 q/s | <30 q/s |
| **Memory increase (1000q)** | <10% | <20% | >20% |

### Análisis de Locust Reports

**Archivo**: `stress_results/*_report.html`

#### **Secciones importantes**:

1. **Request Statistics**
   - Total requests
   - Failures (%)
   - Average response time
   - Min/Max response time

2. **Response Time Percentiles**
   - 50th percentile (mediana)
   - 95th percentile
   - 99th percentile

3. **Charts**
   - Total Requests per Second
   - Response Times (ms)
   - Number of Users

#### **Qué buscar**:

✅ **Buenas señales**:
- Response time estable a lo largo del test
- Failure rate <1%
- RPS (requests/s) constante
- Sin picos anormales de latencia

⚠️ **Señales de alerta**:
- Response time creciente
- Failure rate >5%
- RPS decreciente con usuarios constantes
- Picos de latencia >1s

🚨 **Señales críticas**:
- Failure rate >20%
- Response time >5s
- Sistema no responde
- Errores 500/502/503

---

## Métricas y Objetivos

### SLAs Definidos

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Latencia P50 | <100ms | >200ms |
| Latencia P95 | <200ms | >500ms |
| Latencia P99 | <500ms | >1s |
| Availability | >99.5% | <99% |
| Throughput | >50 q/s | <30 q/s |
| Max concurrent users | 100 | 50 |
| Memory growth rate | <1% per hour | >5% per hour |

### Alertas Configuradas

El script `run_stress_tests.sh` genera alertas cuando:
- ❌ Success rate <90%
- ❌ Latencia promedio >200ms
- ❌ P95 latency >500ms
- ❌ Memory increase >20%

---

## Troubleshooting

### Problema: "Connection refused" o "Connection timeout"

**Causa**: Servidor no está corriendo o no acepta conexiones.

**Solución**:
```bash
# Verificar que el servidor está corriendo
curl http://localhost:8000/health

# Si no está corriendo:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### Problema: Tests fallan con "Too many open files"

**Causa**: Límite de file descriptors alcanzado.

**Solución**:
```bash
# Ver límite actual
ulimit -n

# Aumentar límite (temporal)
ulimit -n 4096

# Aumentar límite (permanente) - agregar a ~/.bashrc
echo "ulimit -n 4096" >> ~/.bashrc
```

---

### Problema: Latencias muy altas en tests locales

**Causa**: Modelo no está cargado en cache, CPU limitado.

**Solución**:
1. Hacer warm-up antes de tests:
```bash
pytest tests/performance/test_benchmarks.py::TestInitializationPerformance::test_initialization_with_cache -v
```

2. Reducir número de usuarios:
```bash
./run_stress_tests.sh
# Seleccionar opción 2 (Light Load) en vez de 3 o 4
```

---

### Problema: Memory leaks detectados

**Causa**: Objetos no se liberan correctamente.

**Diagnóstico**:
```bash
# Ejecutar con memory profiler
pytest tests/performance/test_stress_concurrent.py::TestResourceExhaustion::test_memory_stability_under_load -v -s

# Ver output detallado
```

**Solución**: Revisar código para:
- Cerrar conexiones explícitamente
- Liberar recursos después de uso
- Evitar referencias circulares

---

### Problema: Tests de Locust no encuentran el archivo

**Causa**: Path incorrecto.

**Solución**:
```bash
# Ejecutar desde el directorio raíz del proyecto
cd /path/to/modulo_pln
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

### Problema: Results directory no existe

**Causa**: Script no creó el directorio.

**Solución**:
```bash
mkdir -p stress_results
```

---

## Mejores Prácticas

### 1. **Antes de ejecutar tests de estrés**:

✅ Asegurar que el servidor está en modo producción (no debug)
✅ Warm-up: Ejecutar algunas queries primero
✅ Cerrar otras aplicaciones pesadas
✅ Verificar que hay suficiente memoria/CPU disponible

### 2. **Durante los tests**:

✅ Monitorear logs del servidor
✅ Usar `htop` o similar para ver uso de recursos
✅ No interferir con el sistema (no ejecutar otras tareas pesadas)

### 3. **Después de los tests**:

✅ Revisar reportes generados
✅ Comparar con tests anteriores (regresión?)
✅ Documentar hallazgos
✅ Crear tickets para issues encontrados

---

## Roadmap de Tests de Estrés

### ✅ Implementado

- [x] Tests de concurrencia (10, 50, 100 usuarios)
- [x] Tests de spike (0→20 usuarios)
- [x] Soak testing (5 minutos)
- [x] Resource exhaustion testing
- [x] Locust load testing
- [x] Script automatizado de ejecución
- [x] Reportes HTML y CSV

### 🚧 En Progreso

- [ ] Tests distribuidos con Locust (múltiples workers)
- [ ] Integración con CI/CD (GitHub Actions)
- [ ] Dashboards en tiempo real (Grafana + Prometheus)

### 📋 Futuro

- [ ] Chaos engineering (kill random services)
- [ ] Network latency simulation
- [ ] Tests de failover y recovery
- [ ] Load testing en staging environment
- [ ] Benchmarking vs competidores

---

## Recursos Adicionales

- **Locust Documentation**: https://docs.locust.io
- **Pytest Documentation**: https://docs.pytest.org
- **Load Testing Best Practices**: https://www.blazemeter.com/blog/performance-testing-best-practices

---

## Contacto y Soporte

Para preguntas o issues relacionados con tests de estrés:

1. Revisar esta guía
2. Revisar los comentarios en el código
3. Crear issue en el repositorio

---

**Última actualización**: 2025-11-26
