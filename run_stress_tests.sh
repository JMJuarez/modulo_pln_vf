#!/bin/bash
###############################################################################
# Script de Ejecución de Tests de Estrés
#
# Ejecuta diferentes niveles de tests de estrés y genera reportes.
###############################################################################

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  STRESS TESTING SUITE                          ║"
echo "║                                                                ║"
echo "║  Tests de carga, concurrencia y estrés para módulo PLN        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Verificar que el servidor está corriendo
check_server() {
    echo -e "${YELLOW}🔍 Verificando servidor...${NC}"

    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Servidor está corriendo${NC}\n"
        return 0
    else
        echo -e "${RED}❌ Servidor no está corriendo en http://localhost:8000${NC}"
        echo -e "${YELLOW}Por favor, inicia el servidor con: uvicorn app.main:app --reload${NC}\n"
        return 1
    fi
}

# Función para ejecutar tests con pytest
run_pytest_stress() {
    local test_level=$1
    local marker=$2
    local description=$3

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    pytest tests/performance/test_stress_concurrent.py::$test_level \
        -v \
        -s \
        --tb=short \
        --color=yes \
        || true  # No fallar el script completo si un test falla

    echo -e "\n"
}

# Función para ejecutar Locust
run_locust_test() {
    local users=$1
    local spawn_rate=$2
    local duration=$3
    local description=$4
    local output_prefix=$5

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🚀 $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}Usuarios: $users | Spawn rate: $spawn_rate/s | Duración: $duration${NC}\n"

    locust -f tests/performance/locustfile.py \
        --host=http://localhost:8000 \
        --users $users \
        --spawn-rate $spawn_rate \
        --run-time $duration \
        --headless \
        --csv="stress_results/${output_prefix}" \
        --html="stress_results/${output_prefix}_report.html" \
        || true

    echo -e "\n${GREEN}✅ Reporte guardado en: stress_results/${output_prefix}_report.html${NC}\n"
}

# Crear directorio de resultados
mkdir -p stress_results

# Mostrar menú
show_menu() {
    echo -e "${YELLOW}Selecciona el tipo de test:${NC}\n"
    echo "  1) Quick Test         - Test rápido de verificación (30s)"
    echo "  2) Light Load         - Carga ligera: 10 usuarios (2 min)"
    echo "  3) Moderate Load      - Carga moderada: 50 usuarios (5 min)"
    echo "  4) Heavy Load         - Carga pesada: 100 usuarios (5 min)"
    echo "  5) Stress Test        - Test de estrés: 200 usuarios (5 min)"
    echo "  6) Concurrent Tests   - Tests de concurrencia con pytest"
    echo "  7) Soak Test          - Test prolongado: 5 usuarios durante 10 min"
    echo "  8) Full Suite         - Suite completa (todos los tests)"
    echo "  9) Custom Test        - Configuración personalizada"
    echo "  0) Salir"
    echo ""
}

# Procesar selección
process_selection() {
    local choice=$1

    case $choice in
        1)
            echo -e "${GREEN}Ejecutando Quick Test...${NC}\n"
            run_locust_test 5 1 "30s" "QUICK TEST - Verificación Rápida" "quick_test"
            ;;
        2)
            echo -e "${GREEN}Ejecutando Light Load Test...${NC}\n"
            run_locust_test 10 2 "2m" "LIGHT LOAD - 10 Usuarios" "light_load"
            ;;
        3)
            echo -e "${GREEN}Ejecutando Moderate Load Test...${NC}\n"
            run_locust_test 50 5 "5m" "MODERATE LOAD - 50 Usuarios" "moderate_load"
            ;;
        4)
            echo -e "${GREEN}Ejecutando Heavy Load Test...${NC}\n"
            run_locust_test 100 10 "5m" "HEAVY LOAD - 100 Usuarios" "heavy_load"
            ;;
        5)
            echo -e "${GREEN}Ejecutando Stress Test...${NC}\n"
            run_locust_test 200 20 "5m" "STRESS TEST - 200 Usuarios" "stress_test"
            ;;
        6)
            echo -e "${GREEN}Ejecutando Concurrent Tests con pytest...${NC}\n"

            run_pytest_stress "TestConcurrentLoad::test_concurrent_10_users" \
                "performance" \
                "Test de Concurrencia - 10 Usuarios"

            run_pytest_stress "TestConcurrentLoad::test_concurrent_50_users" \
                "performance" \
                "Test de Concurrencia - 50 Usuarios"

            run_pytest_stress "TestSpikeLoad::test_sudden_spike_0_to_20_users" \
                "performance" \
                "Test de Spike - 20 Usuarios Súbitos"

            echo -e "${GREEN}✅ Tests de concurrencia completados${NC}\n"
            ;;
        7)
            echo -e "${GREEN}Ejecutando Soak Test...${NC}\n"
            echo -e "${YELLOW}⚠️  ADVERTENCIA: Este test durará 10 minutos${NC}\n"
            read -p "¿Continuar? (y/n): " confirm

            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                run_locust_test 5 1 "10m" "SOAK TEST - Carga Prolongada" "soak_test"
            else
                echo -e "${YELLOW}Test cancelado${NC}\n"
            fi
            ;;
        8)
            echo -e "${GREEN}Ejecutando Full Test Suite...${NC}\n"
            echo -e "${YELLOW}⚠️  ADVERTENCIA: Esto puede tomar más de 30 minutos${NC}\n"
            read -p "¿Continuar? (y/n): " confirm

            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                # Tests con Locust
                run_locust_test 10 2 "2m" "1/5 - Light Load" "full_1_light"
                run_locust_test 50 5 "3m" "2/5 - Moderate Load" "full_2_moderate"
                run_locust_test 100 10 "3m" "3/5 - Heavy Load" "full_3_heavy"
                run_locust_test 200 20 "3m" "4/5 - Stress Test" "full_4_stress"

                # Tests con pytest
                echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${BLUE}5/5 - Concurrent & Specialized Tests${NC}"
                echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

                pytest tests/performance/test_stress_concurrent.py \
                    -v \
                    -s \
                    --tb=short \
                    --color=yes \
                    -m "performance and not slow" \
                    || true

                echo -e "\n${GREEN}✅ Full Test Suite completado${NC}\n"
                echo -e "${YELLOW}📁 Reportes guardados en: stress_results/${NC}\n"
            else
                echo -e "${YELLOW}Test cancelado${NC}\n"
            fi
            ;;
        9)
            echo -e "${GREEN}Configuración personalizada:${NC}\n"
            read -p "Número de usuarios: " users
            read -p "Spawn rate (usuarios/segundo): " spawn_rate
            read -p "Duración (ej: 1m, 30s, 5m): " duration
            read -p "Nombre del reporte: " report_name

            run_locust_test $users $spawn_rate $duration \
                "CUSTOM TEST - $users usuarios" \
                "custom_${report_name}"
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
    # Verificar servidor
    if ! check_server; then
        exit 1
    fi

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

# Trap para cleanup
cleanup() {
    echo -e "\n${YELLOW}Limpiando...${NC}"
    # Matar procesos de locust si existen
    pkill -f "locust" 2>/dev/null || true
}

trap cleanup EXIT

# Ejecutar
main "$@"
