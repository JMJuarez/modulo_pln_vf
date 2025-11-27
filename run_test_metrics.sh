#!/bin/bash
###############################################################################
# Script de Generación de Métricas y Mediciones de Tests
#
# Genera reportes completos de:
# - Cobertura de código
# - Métricas de tests
# - Estadísticas por tipo
# - Reportes HTML
# - Resumen ejecutivo
###############################################################################

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Crear directorio de reportes
REPORTS_DIR="test_reports"
mkdir -p "$REPORTS_DIR"

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           GENERADOR DE MÉTRICAS DE TESTS                      ║"
echo "║                                                                ║"
echo "║  Genera reportes completos de cobertura, métricas y stats     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Función para contar tests
count_tests() {
    local marker=$1
    local description=$2

    echo -e "${CYAN}Contando tests: $description${NC}"

    if [ -z "$marker" ]; then
        # Todos los tests
        count=$(pytest --collect-only -q 2>/dev/null | grep -E "test_" | wc -l)
    else
        # Tests con marker específico
        count=$(pytest --collect-only -q -m "$marker" 2>/dev/null | grep -E "test_" | wc -l)
    fi

    echo -e "  → ${GREEN}$count tests${NC}\n"
    echo "$count"
}

# Función para ejecutar tests y capturar métricas
run_tests_with_metrics() {
    local marker=$1
    local description=$2
    local output_file=$3

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Ejecutando: $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    if [ -z "$marker" ]; then
        # Todos los tests
        pytest tests/ \
            -v \
            --tb=short \
            --cov=app \
            --cov-report=term \
            --cov-report=html:htmlcov \
            --cov-report=json:$REPORTS_DIR/coverage.json \
            --junit-xml=$REPORTS_DIR/junit_$output_file.xml \
            --html=$REPORTS_DIR/report_$output_file.html \
            --self-contained-html \
            2>&1 | tee "$REPORTS_DIR/output_$output_file.txt"
    else
        # Tests con marker específico
        pytest tests/ \
            -v \
            -m "$marker" \
            --tb=short \
            --cov=app \
            --cov-report=term \
            --junit-xml=$REPORTS_DIR/junit_$output_file.xml \
            --html=$REPORTS_DIR/report_$output_file.html \
            --self-contained-html \
            2>&1 | tee "$REPORTS_DIR/output_$output_file.txt"
    fi

    echo -e "\n${GREEN}✅ Reporte guardado en: $REPORTS_DIR/report_$output_file.html${NC}\n"
}

# Función para generar resumen de métricas
generate_metrics_summary() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Generando resumen de métricas...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    # Contar tests por tipo
    echo -e "${CYAN}📊 CONTEO DE TESTS POR TIPO:${NC}\n"

    total_tests=$(count_tests "" "Todos los tests")
    unit_tests=$(count_tests "unit" "Tests unitarios")
    integration_tests=$(count_tests "integration" "Tests de integración")
    e2e_tests=$(count_tests "e2e" "Tests E2E")
    semantic_tests=$(count_tests "semantic" "Tests semánticos")
    performance_tests=$(count_tests "performance" "Tests de performance")
    slow_tests=$(count_tests "slow" "Tests lentos")

    # Crear reporte resumen
    cat > "$REPORTS_DIR/metrics_summary.txt" << EOF
╔═══════════════════════════════════════════════════════════════╗
║                  RESUMEN DE MÉTRICAS DE TESTS                  ║
╚═══════════════════════════════════════════════════════════════╝

Fecha de generación: $(date '+%Y-%m-%d %H:%M:%S')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CONTEO DE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total de tests:                 $total_tests
├─ Unitarios:                   $unit_tests ($(echo "scale=1; $unit_tests*100/$total_tests" | bc)%)
├─ Integración:                 $integration_tests ($(echo "scale=1; $integration_tests*100/$total_tests" | bc)%)
├─ End-to-End:                  $e2e_tests ($(echo "scale=1; $e2e_tests*100/$total_tests" | bc)%)
├─ Semánticos:                  $semantic_tests ($(echo "scale=1; $semantic_tests*100/$total_tests" | bc)%)
├─ Performance:                 $performance_tests ($(echo "scale=1; $performance_tests*100/$total_tests" | bc)%)
└─ Lentos (>5s):                $slow_tests ($(echo "scale=1; $slow_tests*100/$total_tests" | bc)%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 ESTRUCTURA DE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Directorio tests/:
$(tree -L 2 tests/ 2>/dev/null || find tests/ -type f -name "*.py" | head -20)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 LÍNEAS DE CÓDIGO DE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$(wc -l tests/**/*.py 2>/dev/null | tail -1)

Por tipo:
  Unit:         $(find tests/unit -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}') líneas
  Integration:  $(find tests/integration -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}') líneas
  E2E:          $(find tests/e2e -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}') líneas
  Quality:      $(find tests/quality -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}') líneas
  Performance:  $(find tests/performance -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}') líneas

EOF

    # Mostrar resumen en consola
    cat "$REPORTS_DIR/metrics_summary.txt"

    echo -e "\n${GREEN}✅ Resumen guardado en: $REPORTS_DIR/metrics_summary.txt${NC}\n"
}

# Función para analizar cobertura
analyze_coverage() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Analizando cobertura de código...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    if [ -f ".coverage" ]; then
        echo -e "${CYAN}Generando reporte de cobertura detallado...${NC}\n"

        # Reporte de cobertura en terminal
        coverage report -m > "$REPORTS_DIR/coverage_report.txt"

        # Extraer métricas principales
        total_coverage=$(coverage report | tail -1 | awk '{print $NF}')

        echo -e "${GREEN}Cobertura total: $total_coverage${NC}\n"

        # Agregar a resumen
        cat >> "$REPORTS_DIR/metrics_summary.txt" << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 COBERTURA DE CÓDIGO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cobertura total: $total_coverage

Reportes disponibles:
  - HTML:  htmlcov/index.html
  - JSON:  $REPORTS_DIR/coverage.json
  - Texto: $REPORTS_DIR/coverage_report.txt

EOF

        echo -e "${GREEN}✅ Reporte HTML de cobertura: htmlcov/index.html${NC}"
        echo -e "${GREEN}✅ Reporte JSON de cobertura: $REPORTS_DIR/coverage.json${NC}\n"
    else
        echo -e "${YELLOW}⚠️  No se encontró archivo .coverage${NC}"
        echo -e "${YELLOW}   Ejecuta primero: pytest --cov=app${NC}\n"
    fi
}

# Función para generar métricas de calidad
generate_quality_metrics() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Generando métricas de calidad...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    cat >> "$REPORTS_DIR/metrics_summary.txt" << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 MÉTRICAS DE CALIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ratio de tests:
  - Tests por 1000 líneas de código: $(echo "scale=1; $total_tests*1000/$(find app -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')" | bc)
  - Líneas de tests / Líneas de código: $(echo "scale=2; $(find tests -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')/$(find app -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')" | bc)

Pirámide de tests (ideal: 70% unit, 20% integration, 10% e2e):
  - Unitarios:    $(echo "scale=1; $unit_tests*100/$total_tests" | bc)%
  - Integración:  $(echo "scale=1; $integration_tests*100/$total_tests" | bc)%
  - E2E:          $(echo "scale=1; $e2e_tests*100/$total_tests" | bc)%

Tests especializados:
  - Semánticos (PLN):  $semantic_tests tests
  - Performance:       $performance_tests tests
  - Robustez:          $(grep -r "class.*Robustness" tests/ | wc -l) clases

EOF

    echo -e "${GREEN}✅ Métricas de calidad generadas${NC}\n"
}

# Función para generar índice HTML
generate_html_index() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Generando índice HTML de reportes...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    cat > "$REPORTS_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reportes de Tests - Módulo PLN</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .content {
            padding: 2rem;
        }
        .section {
            margin-bottom: 2rem;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.8rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }
        .card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 4px solid #667eea;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h3 {
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 1.3rem;
        }
        .card p {
            color: #666;
            margin-bottom: 1rem;
            line-height: 1.6;
        }
        .card a {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.7rem 1.5rem;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            transition: opacity 0.3s;
        }
        .card a:hover {
            opacity: 0.9;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        footer {
            background: #f8f9fa;
            padding: 1.5rem;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
        }
        .timestamp {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Reportes de Tests</h1>
            <p class="subtitle">Módulo de Procesamiento de Lenguaje Natural</p>
        </header>

        <div class="content">
            <div class="timestamp">
                <strong>⏰ Última actualización:</strong> TIMESTAMP_PLACEHOLDER
            </div>

            <div class="section">
                <h2>📈 Métricas Generales</h2>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">TOTAL_TESTS</div>
                        <div class="stat-label">Total de Tests</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">COVERAGE</div>
                        <div class="stat-label">Cobertura de Código</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">UNIT_TESTS</div>
                        <div class="stat-label">Tests Unitarios</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">E2E_TESTS</div>
                        <div class="stat-label">Tests E2E</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📑 Reportes Principales</h2>
                <div class="card-grid">
                    <div class="card">
                        <h3>🎯 Reporte Completo</h3>
                        <p>Resultados de todos los tests ejecutados con detalles de éxitos y fallos.</p>
                        <a href="report_all.html" target="_blank">Ver Reporte</a>
                    </div>

                    <div class="card">
                        <h3>📊 Cobertura de Código</h3>
                        <p>Análisis detallado de líneas de código cubiertas por tests.</p>
                        <a href="../htmlcov/index.html" target="_blank">Ver Cobertura</a>
                    </div>

                    <div class="card">
                        <h3>📝 Resumen de Métricas</h3>
                        <p>Estadísticas y métricas consolidadas de todos los tests.</p>
                        <a href="metrics_summary.txt" target="_blank">Ver Resumen</a>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔍 Reportes por Tipo</h2>
                <div class="card-grid">
                    <div class="card">
                        <h3>⚡ Tests Unitarios</h3>
                        <p>Tests de funciones y componentes individuales.</p>
                        <a href="report_unit.html" target="_blank">Ver Tests</a>
                    </div>

                    <div class="card">
                        <h3>🔗 Tests de Integración</h3>
                        <p>Tests de interacción entre componentes.</p>
                        <a href="report_integration.html" target="_blank">Ver Tests</a>
                    </div>

                    <div class="card">
                        <h3>🌐 Tests End-to-End</h3>
                        <p>Tests de escenarios completos de usuario.</p>
                        <a href="report_e2e.html" target="_blank">Ver Tests</a>
                    </div>

                    <div class="card">
                        <h3>🧠 Tests Semánticos</h3>
                        <p>Tests de calidad semántica y PLN.</p>
                        <a href="report_semantic.html" target="_blank">Ver Tests</a>
                    </div>

                    <div class="card">
                        <h3>⚡ Tests de Performance</h3>
                        <p>Benchmarks y tests de rendimiento.</p>
                        <a href="report_performance.html" target="_blank">Ver Tests</a>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📄 Archivos XML/JSON</h2>
                <div class="card-grid">
                    <div class="card">
                        <h3>📋 JUnit XML (Todos)</h3>
                        <p>Formato estándar para CI/CD.</p>
                        <a href="junit_all.xml" download>Descargar</a>
                    </div>

                    <div class="card">
                        <h3>📊 Coverage JSON</h3>
                        <p>Datos de cobertura en formato JSON.</p>
                        <a href="coverage.json" download>Descargar</a>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p>Generado automáticamente por <strong>run_test_metrics.sh</strong></p>
            <p>Módulo PLN - Tests Suite</p>
        </footer>
    </div>
</body>
</html>
EOF

    # Reemplazar placeholders
    sed -i "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S')/g" "$REPORTS_DIR/index.html"
    sed -i "s/TOTAL_TESTS/$total_tests/g" "$REPORTS_DIR/index.html"
    sed -i "s/UNIT_TESTS/$unit_tests/g" "$REPORTS_DIR/index.html"
    sed -i "s/E2E_TESTS/$e2e_tests/g" "$REPORTS_DIR/index.html"

    if [ -f ".coverage" ]; then
        coverage_pct=$(coverage report | tail -1 | awk '{print $NF}')
        sed -i "s/COVERAGE/$coverage_pct/g" "$REPORTS_DIR/index.html"
    else
        sed -i "s/COVERAGE/N\/A/g" "$REPORTS_DIR/index.html"
    fi

    echo -e "${GREEN}✅ Índice HTML generado: $REPORTS_DIR/index.html${NC}\n"
}

# Menú principal
show_menu() {
    echo -e "${YELLOW}Selecciona el tipo de reporte a generar:${NC}\n"
    echo "  1) Resumen Rápido       - Solo conteo y estadísticas"
    echo "  2) Todos los Tests      - Ejecutar todos y generar reportes completos"
    echo "  3) Por Tipo             - Ejecutar y reportar por tipo (unit, integration, e2e)"
    echo "  4) Solo Cobertura       - Analizar cobertura existente"
    echo "  5) Métricas Avanzadas   - Generar métricas de calidad detalladas"
    echo "  6) Reportes HTML        - Generar índice HTML con todos los reportes"
    echo "  7) Todo (Suite Completa) - Ejecutar todo y generar todos los reportes"
    echo "  0) Salir"
    echo ""
}

# Procesar selección
process_selection() {
    local choice=$1

    case $choice in
        1)
            echo -e "${GREEN}Generando resumen rápido...${NC}\n"
            generate_metrics_summary
            ;;
        2)
            echo -e "${GREEN}Ejecutando todos los tests...${NC}\n"
            run_tests_with_metrics "" "Todos los tests" "all"
            analyze_coverage
            ;;
        3)
            echo -e "${GREEN}Ejecutando tests por tipo...${NC}\n"
            run_tests_with_metrics "unit" "Tests Unitarios" "unit"
            run_tests_with_metrics "integration" "Tests de Integración" "integration"
            run_tests_with_metrics "e2e" "Tests End-to-End" "e2e"
            run_tests_with_metrics "semantic" "Tests Semánticos" "semantic"
            run_tests_with_metrics "performance and not slow" "Tests de Performance (rápidos)" "performance"
            ;;
        4)
            echo -e "${GREEN}Analizando cobertura...${NC}\n"
            analyze_coverage
            ;;
        5)
            echo -e "${GREEN}Generando métricas avanzadas...${NC}\n"
            generate_metrics_summary
            generate_quality_metrics
            ;;
        6)
            echo -e "${GREEN}Generando índice HTML...${NC}\n"
            generate_html_index
            echo -e "${CYAN}Para abrir el índice:${NC}"
            echo -e "  ${YELLOW}xdg-open $REPORTS_DIR/index.html${NC}"
            ;;
        7)
            echo -e "${GREEN}Generando suite completa...${NC}\n"
            echo -e "${YELLOW}⚠️  ADVERTENCIA: Esto puede tomar varios minutos${NC}\n"
            read -p "¿Continuar? (y/n): " confirm

            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                # Ejecutar todos los tests
                run_tests_with_metrics "" "Todos los tests" "all"

                # Ejecutar por tipo
                run_tests_with_metrics "unit" "Tests Unitarios" "unit"
                run_tests_with_metrics "integration" "Tests de Integración" "integration"
                run_tests_with_metrics "e2e" "Tests End-to-End" "e2e"
                run_tests_with_metrics "semantic" "Tests Semánticos" "semantic"
                run_tests_with_metrics "performance and not slow" "Tests de Performance" "performance"

                # Generar todos los reportes
                generate_metrics_summary
                generate_quality_metrics
                analyze_coverage
                generate_html_index

                echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
                echo -e "${GREEN}║         ✅ SUITE COMPLETA GENERADA CON ÉXITO              ║${NC}"
                echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}\n"

                echo -e "${CYAN}📁 Reportes disponibles en: $REPORTS_DIR/${NC}\n"
                echo -e "${YELLOW}Para ver el índice HTML:${NC}"
                echo -e "  ${MAGENTA}xdg-open $REPORTS_DIR/index.html${NC}\n"
                echo -e "${YELLOW}Para ver cobertura:${NC}"
                echo -e "  ${MAGENTA}xdg-open htmlcov/index.html${NC}\n"
            else
                echo -e "${YELLOW}Operación cancelada${NC}\n"
            fi
            ;;
        0)
            echo -e "${YELLOW}Saliendo...${NC}\n"
            exit 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}\n"
            ;;
    esac
}

# Main
main() {
    # Modo interactivo si no hay argumentos
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Selecciona una opción: " choice
            echo ""
            process_selection $choice

            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
            read -p "Presiona Enter para continuar..."
            clear
        done
    else
        # Modo no interactivo (con argumentos)
        process_selection $1
    fi
}

# Ejecutar
main "$@"
