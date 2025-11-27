# 📊 Guía de Métricas e Indicadores de Tests

## 🎯 Introducción

Esta guía explica cómo obtener, interpretar y utilizar las métricas e indicadores de todos los tests del proyecto.

---

## 📋 Tabla de Contenidos

1. [Métricas Disponibles](#métricas-disponibles)
2. [Cómo Obtener las Métricas](#cómo-obtener-las-métricas)
3. [Interpretación de Resultados](#interpretación-de-resultados)
4. [Indicadores Clave (KPIs)](#indicadores-clave-kpis)
5. [Dashboards y Reportes](#dashboards-y-reportes)
6. [CI/CD Integration](#cicd-integration)

---

## 📊 Métricas Disponibles

### 1. **Métricas de Cobertura de Código**

| Métrica | Descripción | Fuente |
|---------|-------------|--------|
| **Coverage %** | Porcentaje de líneas cubiertas | `coverage report` |
| **Lines Covered** | Número de líneas cubiertas | `.coverage` |
| **Branches Covered** | Cobertura de ramas (if/else) | `coverage report --branch` |
| **Missing Lines** | Líneas no cubiertas | `coverage report -m` |

**Archivos generados**:
- `htmlcov/index.html` - Reporte HTML visual
- `.coverage` - Base de datos de cobertura
- `test_reports/coverage.json` - Datos en JSON
- `test_reports/coverage_report.txt` - Reporte en texto

---

### 2. **Métricas de Tests**

| Métrica | Descripción | Cómo Obtenerla |
|---------|-------------|----------------|
| **Total Tests** | Número total de tests | `pytest --collect-only` |
| **Passed Tests** | Tests exitosos | `pytest -v` |
| **Failed Tests** | Tests fallidos | `pytest -v` |
| **Skipped Tests** | Tests omitidos | `pytest -v` |
| **Duration** | Tiempo de ejecución | `pytest --durations=0` |
| **Tests por Tipo** | Conteo por marker | `pytest -m <marker> --collect-only` |

---

### 3. **Métricas de Calidad**

| Métrica | Fórmula | Objetivo |
|---------|---------|----------|
| **Test Density** | Tests / 1000 líneas código | >10 |
| **Test Ratio** | Líneas tests / Líneas código | >0.5 |
| **Mutation Score** | Mutaciones detectadas / Total | >80% |
| **Code Complexity** | Complejidad ciclomática | <10 |

---

### 4. **Métricas de Rendimiento** (Performance)

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| **Avg Latency** | Latencia promedio | <100ms |
| **P95 Latency** | Percentil 95 | <200ms |
| **P99 Latency** | Percentil 99 | <500ms |
| **Throughput** | Queries por segundo | >50 q/s |
| **Max Concurrent Users** | Usuarios simultáneos | >100 |

---

### 5. **Métricas Semánticas** (PLN Specific)

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| **Accuracy** | % clasificaciones correctas | >95% |
| **Precision** | True Positives / (TP + FP) | >90% |
| **Recall** | True Positives / (TP + FN) | >90% |
| **F1-Score** | Media armónica P y R | >90% |
| **Confusion Matrix** | Matriz de confusión | Análisis |

---

## 🚀 Cómo Obtener las Métricas

### Opción 1: Script Automatizado (MÁS FÁCIL)

```bash
# Ejecutar script interactivo
./run_test_metrics.sh

# Opciones disponibles:
# 1) Resumen Rápido       - Solo conteo y estadísticas
# 2) Todos los Tests      - Ejecutar todos y generar reportes
# 3) Por Tipo             - Reportes separados por tipo
# 4) Solo Cobertura       - Análisis de cobertura
# 5) Métricas Avanzadas   - Métricas de calidad
# 6) Reportes HTML        - Índice HTML visual
# 7) Todo (Suite Completa) - Todos los reportes
```

**Output**:
- `test_reports/` - Todos los reportes
- `test_reports/index.html` - Dashboard HTML
- `htmlcov/index.html` - Cobertura visual

---

### Opción 2: Comandos Manuales

#### A. **Cobertura de Código**

```bash
# Ejecutar tests con cobertura
pytest --cov=app --cov-report=html --cov-report=term

# Ver reporte en terminal
coverage report

# Ver reporte detallado (con líneas faltantes)
coverage report -m

# Generar reporte JSON
coverage json -o test_reports/coverage.json

# Abrir reporte HTML
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # macOS
```

---

#### B. **Conteo de Tests**

```bash
# Contar todos los tests
pytest --collect-only -q | grep "test_" | wc -l

# Por tipo (markers)
pytest --collect-only -q -m unit | grep "test_" | wc -l
pytest --collect-only -q -m integration | grep "test_" | wc -l
pytest --collect-only -q -m e2e | grep "test_" | wc -l
pytest --collect-only -q -m semantic | grep "test_" | wc -l
pytest --collect-only -q -m performance | grep "test_" | wc -l
```

---

#### C. **Ejecutar Tests con Reportes**

```bash
# Reporte HTML con pytest-html
pytest --html=test_reports/report.html --self-contained-html

# Reporte JUnit XML (para CI/CD)
pytest --junit-xml=test_reports/junit.xml

# Con cobertura y reportes
pytest \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --html=test_reports/report.html \
    --junit-xml=test_reports/junit.xml \
    -v
```

---

#### D. **Métricas de Performance**

```bash
# Duración de tests más lentos
pytest --durations=10

# Todos los durations
pytest --durations=0

# Solo tests de performance
pytest tests/performance/ -v --durations=0

# Benchmarks con pytest-benchmark
pytest tests/performance/test_benchmarks.py --benchmark-only
```

---

#### E. **Métricas Semánticas**

```bash
# Tests semánticos con métricas
pytest tests/quality/ -v -s

# Ver confusion matrix
pytest tests/quality/test_semantic_advanced.py::TestConfusionMatrixDetailed -v -s

# Ver distribución de similitudes
pytest tests/quality/test_semantic_advanced.py::TestSimilarityDistribution -v -s
```

---

## 📈 Interpretación de Resultados

### 1. **Reporte de Cobertura**

```
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
app/__init__.py              0      0   100%
app/main.py                145     12    92%   45-47, 67-69
app/matcher_improved.py    256     23    91%   234-245
app/preprocess.py           89      5    94%   78-82
------------------------------------------------------
TOTAL                      490     40    92%
```

**Interpretación**:
- ✅ **>90%**: Excelente cobertura
- ⚠️ **70-90%**: Buena, pero mejorable
- ❌ **<70%**: Necesita más tests

**Qué buscar**:
- Líneas críticas sin cubrir (`Missing`)
- Funciones de error handling sin tests
- Código nuevo sin tests

---

### 2. **Reporte de Tests**

```
tests/unit/test_matcher.py::TestClipSimilarity::test_clip_normal_value PASSED [ 10%]
tests/unit/test_matcher.py::TestClipSimilarity::test_clip_above_one PASSED [ 20%]
tests/integration/test_api.py::TestBuscarEndpoint::test_buscar_valid_query PASSED [ 30%]
...
======================== 150 passed, 2 failed, 3 skipped in 45.23s ========================
```

**Métricas clave**:
- **Passed**: Tests exitosos
- **Failed**: Tests fallidos (INVESTIGAR)
- **Skipped**: Tests omitidos (normal si están marcados)
- **Duration**: Tiempo total

**Análisis**:
- ✅ **0 failed**: Perfecto
- ⚠️ **1-3 failed**: Investigar y corregir
- ❌ **>3 failed**: Problema serio

---

### 3. **Métricas de Performance**

```
📊 CONCURRENT LOAD TEST (10 usuarios):
   Total queries:     100
   Exitosas:          98/100 (98.0%)
   Latencia promedio: 45.23ms      ✅ Bueno
   Latencia P95:      89.12ms      ✅ Bueno
   Throughput:        52.3 q/s     ✅ Bueno
```

**Indicadores**:
- ✅ Latencia promedio <100ms
- ✅ P95 <200ms
- ✅ Throughput >50 q/s
- ✅ Success rate >95%

---

### 4. **Matriz de Confusión (Semántica)**

```
📊 MATRIZ DE CONFUSIÓN:
Predicted →     A         B         C         None
------------------------------------------------------
A              8         1         0         1        ← 80% accuracy
B              0        10         0         0        ← 100% accuracy
C              1         0         9         0        ← 90% accuracy
Deletreo       1         0         0         0        ← Falso negativo

Grupo A:
  Accuracy:  80.0%
  Precision: 88.9%
  Recall:    80.0%
  F1-Score:  84.2%
```

**Interpretación**:
- **Diagonal**: Clasificaciones correctas
- **Fuera de diagonal**: Errores (analizar)
- **Precision**: De lo que predije como A, cuántos eran realmente A
- **Recall**: De todos los A reales, cuántos detecté

---

## 🎯 Indicadores Clave (KPIs)

### KPIs de Cobertura

| KPI | Fórmula | Objetivo | Estado Actual |
|-----|---------|----------|---------------|
| **Code Coverage** | Líneas cubiertas / Total líneas × 100 | >90% | Ver reporte |
| **Branch Coverage** | Ramas cubiertas / Total ramas × 100 | >80% | Ver reporte |
| **Function Coverage** | Funciones con tests / Total funciones × 100 | >95% | Ver reporte |

---

### KPIs de Calidad

| KPI | Objetivo | Cómo Medir |
|-----|----------|------------|
| **Test Pass Rate** | >99% | `pytest -v` |
| **Test Execution Time** | <5 min | `pytest --durations=0` |
| **Flaky Tests** | 0 | Ejecutar 3 veces |
| **Test Maintenance Ratio** | <20% | Tiempo de fix / Tiempo total |

---

### KPIs de Rendimiento

| KPI | Objetivo | Cómo Medir |
|-----|----------|------------|
| **Average Latency** | <100ms | `pytest tests/performance/` |
| **P95 Latency** | <200ms | Ver reportes de performance |
| **Throughput** | >50 q/s | Ver reportes de Locust |
| **Max Concurrent Users** | >100 | Tests de estrés |
| **Error Rate** | <1% | Success rate en load tests |

---

### KPIs Semánticos (PLN)

| KPI | Objetivo | Cómo Medir |
|-----|----------|------------|
| **Classification Accuracy** | >95% | Tests semánticos |
| **Precision (promedio)** | >90% | Confusion matrix |
| **Recall (promedio)** | >90% | Confusion matrix |
| **F1-Score (promedio)** | >90% | Tests de calidad |
| **Robustez ante Typos** | >70% | Tests de robustez |

---

## 📱 Dashboards y Reportes

### 1. **Dashboard HTML Principal**

```bash
# Generar dashboard
./run_test_metrics.sh
# Seleccionar opción 6 o 7

# Abrir dashboard
xdg-open test_reports/index.html
```

**Contiene**:
- 📊 Métricas generales
- 📑 Enlaces a reportes HTML
- 📈 Estadísticas por tipo
- 📄 Archivos descargables (XML, JSON)

---

### 2. **Reporte de Cobertura Visual**

```bash
xdg-open htmlcov/index.html
```

**Características**:
- Vista por archivo
- Líneas cubiertas en verde
- Líneas no cubiertas en rojo
- Navegación interactiva

---

### 3. **Reportes por Tipo**

Generados en `test_reports/`:
- `report_all.html` - Todos los tests
- `report_unit.html` - Solo unitarios
- `report_integration.html` - Solo integración
- `report_e2e.html` - Solo E2E
- `report_semantic.html` - Solo semánticos
- `report_performance.html` - Solo performance

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests & Metrics

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests with coverage
        run: |
          pytest \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            --junit-xml=junit.xml \
            --html=report.html \
            --self-contained-html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage.xml

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: junit.xml

      - name: Upload HTML reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: |
            htmlcov/
            report.html
```

---

### Badges para README

```markdown
![Tests](https://github.com/user/repo/workflows/Tests/badge.svg)
![Coverage](https://codecov.io/gh/user/repo/branch/main/graph/badge.svg)
```

---

## 📊 Ejemplo de Resumen Completo

Después de ejecutar `./run_test_metrics.sh` (opción 7), obtendrás:

```
╔═══════════════════════════════════════════════════════════════╗
║                  RESUMEN DE MÉTRICAS DE TESTS                  ║
╚═══════════════════════════════════════════════════════════════╝

Fecha de generación: 2025-11-26 20:45:32

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CONTEO DE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total de tests:                 150
├─ Unitarios:                   45 (30.0%)
├─ Integración:                 25 (16.7%)
├─ End-to-End:                  40 (26.7%)
├─ Semánticos:                  30 (20.0%)
├─ Performance:                 10 (6.7%)
└─ Lentos (>5s):                8 (5.3%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 COBERTURA DE CÓDIGO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cobertura total: 92%

Reportes disponibles:
  - HTML:  htmlcov/index.html
  - JSON:  test_reports/coverage.json
  - Texto: test_reports/coverage_report.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 MÉTRICAS DE CALIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ratio de tests:
  - Tests por 1000 líneas de código: 12.5
  - Líneas de tests / Líneas de código: 1.8

Pirámide de tests (ideal: 70% unit, 20% integration, 10% e2e):
  - Unitarios:    30.0%  ⚠️  (objetivo: 70%)
  - Integración:  16.7%
  - E2E:          26.7%  ⚠️  (objetivo: 10%)

Tests especializados:
  - Semánticos (PLN):  30 tests
  - Performance:       10 tests
  - Robustez:          5 clases
```

---

## 🎓 Mejores Prácticas

### 1. **Frecuencia de Ejecución**

| Tests | Frecuencia |
|-------|------------|
| Unit | Cada commit (pre-commit hook) |
| Integration | Cada push |
| E2E | Cada merge a main |
| Performance | Semanal |
| Stress | Mensual |

---

### 2. **Umbrales Recomendados**

```yaml
coverage:
  min: 90%
  target: 95%

performance:
  avg_latency: 100ms
  p95_latency: 200ms
  throughput: 50qps

quality:
  test_pass_rate: 99%
  accuracy: 95%
  precision: 90%
  recall: 90%
```

---

### 3. **Alertas y Notificaciones**

Configurar alertas cuando:
- ❌ Cobertura cae <90%
- ❌ Tests fallan >1%
- ❌ Latencia promedio >100ms
- ❌ Accuracy <95%

---

## 📞 Soporte

Para preguntas sobre métricas:
1. Revisar esta guía
2. Ejecutar `./run_test_metrics.sh` opción 1 (resumen rápido)
3. Abrir dashboard HTML: `xdg-open test_reports/index.html`
4. Crear issue en el repositorio

---

**Última actualización**: 2025-11-26
