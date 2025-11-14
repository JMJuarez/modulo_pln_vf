#!/usr/bin/env python3
"""
Script de configuración para el módulo de PLN.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def setup_environment():
    """Configura el entorno de desarrollo."""
    print("🚀 Configurando entorno de desarrollo...")
    print("=" * 50)

    # Verificar Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 10):
        print("❌ Se requiere Python 3.10 o superior")
        return False

    print(f"✅ Python {python_version.major}.{python_version.minor} detectado")

    # Crear entorno virtual si no existe
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("📦 Creando entorno virtual...")
        if not run_command("python3 -m venv .venv", "Crear entorno virtual"):
            return False

    # Activar entorno e instalar dependencias
    activate_cmd = "source .venv/bin/activate"
    install_cmd = f"{activate_cmd} && pip install --upgrade pip && pip install -r requirements.txt"

    if not run_command(install_cmd, "Instalar dependencias"):
        print("⚠️  La instalación de dependencias puede tomar varios minutos debido a PyTorch...")
        return False

    print("🎉 ¡Entorno configurado correctamente!")
    return True


def test_installation():
    """Prueba la instalación básica."""
    print("\n🧪 Probando instalación...")
    print("-" * 30)

    # Ejecutar test básico
    test_cmd = "source .venv/bin/activate && python test_basic.py"
    return run_command(test_cmd, "Ejecutar tests básicos")


def show_usage():
    """Muestra instrucciones de uso."""
    print("\n" + "=" * 50)
    print("📖 INSTRUCCIONES DE USO")
    print("=" * 50)

    print("""
Para ejecutar el servidor:

1. Activar el entorno virtual:
   source .venv/bin/activate

2. Ejecutar el servidor:
   uvicorn app.main:app --reload --port 8000

3. La API estará disponible en:
   http://localhost:8000

4. Documentación automática:
   http://localhost:8000/docs

Endpoints principales:
- GET  /          - Estado del sistema
- POST /buscar    - Buscar frase similar
- GET  /grupos    - Obtener todos los grupos
- GET  /health    - Verificación de salud

Ejemplo de uso con curl:
curl -X POST "http://localhost:8000/buscar" \\
     -H "Content-Type: application/json" \\
     -d '{"texto": "como creo una cuenta"}'

Para ejecutar con Docker:
docker build -t frase-similar .
docker run -p 8000:8000 frase-similar
""")


def main():
    """Función principal."""
    print("🔧 Setup del Módulo de Procesamiento de Lenguaje Natural")
    print("=" * 60)

    # Configurar entorno
    if not setup_environment():
        print("❌ Error en la configuración del entorno")
        sys.exit(1)

    # Probar instalación
    if not test_installation():
        print("⚠️  Los tests básicos no pasaron completamente")
        print("   Esto puede deberse a dependencias aún instalándose")

    # Mostrar instrucciones
    show_usage()


if __name__ == "__main__":
    main()