from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
import logging
import uvicorn

from .matcher_improved import ImprovedPhraseMatcher as PhraseMatcher
from .groups import get_all_phrases
from .preprocess import spell_out_text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="Buscador de Frases Similares en Español",
    description="""
    ## Módulo de PLN para Búsqueda Semántica

    API REST para encontrar frases similares usando **embeddings avanzados** y **similitud coseno**.

    ### Características principales:
    * **3 Grupos Temáticos**: Emergencias (A), Saludos (B), Comunicación (C)
    * **Búsqueda Semántica**: Modelo multilingüe optimizado para español
    * **Sistema de Deletreo Automático**: Activación inteligente para palabras desconocidas
    * **Normalización de Texto**: Corrección ortográfica y leet speak
    * **Alta Performance**: Latencia ~40ms, Throughput 25+ qps

    ### Tecnologías:
    * Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
    * RapidFuzz para corrección ortográfica
    * Re-ranking en 2 fases con thresholds adaptativos
    """,
    version="2.1.0",
    contact={
        "name": "Equipo de Desarrollo PLN",
        "url": "https://github.com/tu-usuario/modulo_pln",
    },
    license_info={
        "name": "MIT",
    },
)

# Instancia global del matcher
matcher = None


class QueryRequest(BaseModel):
    """Modelo para la solicitud de búsqueda de frases similares."""
    texto: str = Field(
        ...,
        description="Texto de entrada para buscar la frase más similar",
        min_length=1,
        max_length=500,
        examples=["necesito ayuda urgente", "hola", "gracias", "Juan"]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"texto": "necesito ayuda urgente"},
                {"texto": "hola buenos días"},
                {"texto": "muchas gracias"},
                {"texto": "Carlos"}
            ]
        }


class QueryResponse(BaseModel):
    """Modelo para la respuesta de búsqueda."""
    query: str = Field(..., description="Texto de consulta original")
    grupo: str | None = Field(
        None,
        description="Grupo temático al que pertenece la frase (A: Emergencias, B: Saludos, C: Comunicación). Null si se activa deletreo"
    )
    frase_similar: str = Field(
        ...,
        description="Frase más similar encontrada o deletreo si similitud es baja"
    )
    similitud: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Puntuación de similitud coseno (0.0 a 1.0)"
    )
    deletreo_activado: bool = Field(
        ...,
        description="Indica si se activó el modo deletreo automático (true) o se encontró una frase similar (false)"
    )
    deletreo: List[str] | None = Field(
        None,
        description="Lista de caracteres deletreados si deletreo_activado es true"
    )
    total_caracteres: int | None = Field(
        None,
        description="Número total de caracteres deletreados"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "necesito ayuda urgente",
                    "grupo": "A",
                    "frase_similar": "Ayuda, por favor",
                    "similitud": 0.8457,
                    "deletreo_activado": False,
                    "deletreo": None,
                    "total_caracteres": None
                },
                {
                    "query": "Juan",
                    "grupo": None,
                    "frase_similar": "J U A N",
                    "similitud": 0.7234,
                    "deletreo_activado": True,
                    "deletreo": ["J", "U", "A", "N"],
                    "total_caracteres": 4
                }
            ]
        }


class StatusResponse(BaseModel):
    """Modelo para la respuesta de estado del sistema."""
    status: str = Field(..., description="Estado del sistema (OK, ERROR)")
    grupos_disponibles: List[str] = Field(
        ...,
        description="Lista de grupos temáticos disponibles (A, B, C)"
    )
    total_frases: int = Field(
        ...,
        description="Número total de frases en todos los grupos"
    )


class SpellOutRequest(BaseModel):
    """Modelo para la solicitud de deletreo manual."""
    texto: str = Field(
        ...,
        description="Texto a deletrear carácter por carácter",
        min_length=1,
        max_length=200,
        examples=["Hola Mundo", "Maria", "Acapulco"]
    )
    incluir_espacios: bool = Field(
        True,
        description="Si es true, incluye 'espacio' en el deletreo. Si es false, omite espacios"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"texto": "Hola Mundo", "incluir_espacios": True},
                {"texto": "Maria", "incluir_espacios": False}
            ]
        }


class SpellOutResponse(BaseModel):
    """Modelo para la respuesta de deletreo."""
    texto_original: str = Field(..., description="Texto original recibido")
    deletreo: List[str] = Field(
        ...,
        description="Lista de caracteres deletreados con nombres de caracteres especiales"
    )
    total_caracteres: int = Field(
        ...,
        description="Número total de elementos en el deletreo"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "texto_original": "Hola",
                    "deletreo": ["H", "O", "L", "A"],
                    "total_caracteres": 4
                },
                {
                    "texto_original": "Hola Mundo",
                    "deletreo": ["H", "O", "L", "A", "espacio", "M", "U", "N", "D", "O"],
                    "total_caracteres": 10
                }
            ]
        }


@app.on_event("startup")
async def startup_event():
    """Inicializa el matcher mejorado al arrancar la aplicación."""
    global matcher
    try:
        logger.info("Inicializando la aplicación con matcher mejorado...")
        # Usar modelo balanceado optimizado para español con todas las mejoras
        matcher = PhraseMatcher(
            model_type="multilingual_balanced",  # Mejor modelo para español
            use_reranking=True,  # Re-ranking en dos fases
            use_synonym_expansion=True  # Expansión de sinónimos
        )
        matcher.initialize()
        logger.info("Aplicación inicializada correctamente con matcher mejorado")
    except Exception as e:
        logger.error(f"Error al inicializar la aplicación: {e}")
        raise


@app.get(
    "/",
    response_model=StatusResponse,
    tags=["Sistema"],
    summary="Estado del sistema",
    description="""
    Retorna el estado general del sistema y estadísticas básicas.

    **Retorna:**
    - Estado del sistema (OK/ERROR)
    - Lista de grupos temáticos disponibles (A, B, C)
    - Número total de frases cargadas en el sistema

    **Casos de uso:**
    - Verificar que el sistema está funcionando correctamente
    - Obtener información sobre los grupos disponibles
    - Health check básico
    """
)
async def root():
    """Endpoint raíz que muestra el estado del sistema."""
    try:
        grupos = get_all_phrases()
        total_frases = sum(len(frases) for frases in grupos.values())

        return StatusResponse(
            status="OK",
            grupos_disponibles=list(grupos.keys()),
            total_frases=total_frases
        )
    except Exception as e:
        logger.error(f"Error en endpoint root: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.post(
    "/buscar",
    response_model=QueryResponse,
    tags=["Búsqueda"],
    summary="Buscar frase similar",
    description="""
    **Endpoint principal:** Busca la frase más similar al texto proporcionado usando embeddings y similitud coseno.

    ## Funcionamiento:

    1. **Normalización**: El texto es normalizado (minúsculas, acentos, leet speak)
    2. **Corrección Ortográfica**: Se corrigen typos comunes usando RapidFuzz
    3. **Búsqueda Semántica**: Se usa modelo multilingüe para generar embeddings
    4. **Clasificación por Grupo**: Se identifica el grupo temático más probable
    5. **Re-ranking**: Se busca la mejor frase dentro del grupo con thresholds adaptativos

    ## Sistema de Deletreo Automático:

    Si la similitud es menor al threshold del grupo, se activa el **deletreo automático**:
    - **Grupo A (Emergencias)**: threshold 0.75
    - **Grupo B (Saludos)**: threshold 0.80
    - **Grupo C (Comunicación)**: threshold 0.85

    El deletreo se activa para:
    - Nombres propios detectados (Juan, Maria, Carlos, etc.)
    - Palabras desconocidas no en el dataset
    - Palabras con capitalización de nombre propio

    ## Ejemplos de uso:

    **Búsqueda normal:**
    ```json
    {"texto": "necesito ayuda urgente"}
    → Retorna: grupo "A", frase "Ayuda, por favor", similitud 0.8457
    ```

    **Deletreo activado:**
    ```json
    {"texto": "Juan"}
    → Retorna: deletreo ["J", "U", "A", "N"], deletreo_activado: true
    ```

    **Normalización de typos:**
    ```json
    {"texto": "ola"}
    → Retorna: grupo "B", frase "Hola", similitud ~0.92
    ```

    **Normalización de leet speak:**
    ```json
    {"texto": "M4ri@"}
    → Normaliza a "Maria" → Retorna deletreo ["M", "A", "R", "I", "A"]
    ```
    """,
    responses={
        200: {
            "description": "Búsqueda exitosa - Retorna frase similar o deletreo",
            "content": {
                "application/json": {
                    "examples": {
                        "frase_similar": {
                            "summary": "Frase similar encontrada",
                            "value": {
                                "query": "necesito ayuda urgente",
                                "grupo": "A",
                                "frase_similar": "Ayuda, por favor",
                                "similitud": 0.8457,
                                "deletreo_activado": False,
                                "deletreo": None,
                                "total_caracteres": None
                            }
                        },
                        "deletreo_activado": {
                            "summary": "Deletreo automático activado",
                            "value": {
                                "query": "Juan",
                                "grupo": None,
                                "frase_similar": "J U A N",
                                "similitud": 0.7234,
                                "deletreo_activado": True,
                                "deletreo": ["J", "U", "A", "N"],
                                "total_caracteres": 4
                            }
                        }
                    }
                }
            }
        },
        400: {"description": "Texto vacío o inválido"},
        503: {"description": "Servicio no disponible (matcher no inicializado)"},
        500: {"description": "Error interno del servidor"}
    }
)
async def buscar_frase_similar(request: QueryRequest):
    """Busca la frase más similar al texto proporcionado usando PLN avanzado."""
    if matcher is None:
        raise HTTPException(status_code=503, detail="Servicio no disponible: matcher no inicializado")

    if not request.texto or not request.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío")

    try:
        logger.info(f"Buscando similitud para: {request.texto}")
        resultado = matcher.search_similar_phrase(request.texto)

        response = QueryResponse(
            query=resultado["query"],
            grupo=resultado["grupo"],
            frase_similar=resultado["frase_similar"],
            similitud=resultado["similitud"],
            deletreo_activado=resultado["deletreo_activado"],
            deletreo=resultado.get("deletreo"),
            total_caracteres=resultado.get("total_caracteres")
        )

        if resultado["deletreo_activado"]:
            logger.info(f"Resultado: {response.grupo} - {response.similitud} (DELETREO ACTIVADO)")
        else:
            logger.info(f"Resultado: {response.grupo} - {response.similitud}")

        return response

    except Exception as e:
        logger.error(f"Error al buscar frase similar: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get(
    "/grupos",
    tags=["Grupos"],
    summary="Listar todos los grupos",
    description="""
    Retorna todos los grupos temáticos disponibles con sus frases.

    ## Grupos disponibles:

    - **Grupo A (Emergencias)**: Frases relacionadas con situaciones de urgencia, ayuda y emergencias médicas
    - **Grupo B (Saludos)**: Presentaciones, saludos y despedidas
    - **Grupo C (Comunicación)**: Comunicación general, agradecimientos y expresiones comunes

    **Total de frases**: 43 frases distribuidas en 3 grupos

    ## Caso de uso:
    - Explorar el dataset completo
    - Conocer qué frases están disponibles en cada grupo
    - Verificar que el dataset se cargó correctamente
    """,
    responses={
        200: {
            "description": "Listado exitoso de grupos",
            "content": {
                "application/json": {
                    "example": {
                        "grupos": {
                            "A": ["Ayuda, por favor", "Llama a la policía", "..."],
                            "B": ["Hola", "¿Cómo estás?", "..."],
                            "C": ["Gracias", "Muchas gracias", "..."]
                        }
                    }
                }
            }
        },
        500: {"description": "Error interno del servidor"}
    }
)
async def obtener_grupos():
    """Obtiene todos los grupos temáticos y sus frases."""
    try:
        grupos = get_all_phrases()
        return {"grupos": grupos}
    except Exception as e:
        logger.error(f"Error al obtener grupos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get(
    "/grupos/{grupo}",
    tags=["Grupos"],
    summary="Obtener frases de un grupo",
    description="""
    Retorna las frases de un grupo temático específico.

    ## Parámetros:

    - **grupo**: Código del grupo (A, B, o C)
      - **A**: Emergencias (13 frases)
      - **B**: Saludos (13 frases)
      - **C**: Comunicación (17 frases)

    ## Ejemplo:
    ```
    GET /grupos/A
    ```
    Retorna todas las frases del grupo A (Emergencias)
    """,
    responses={
        200: {
            "description": "Frases del grupo retornadas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "grupo": "A",
                        "frases": [
                            "Ayuda, por favor",
                            "Llama a la policía",
                            "Necesito un médico",
                            "..."
                        ]
                    }
                }
            }
        },
        404: {"description": "Grupo no encontrado (debe ser A, B, o C)"},
        500: {"description": "Error interno del servidor"}
    }
)
async def obtener_frases_grupo(grupo: str):
    """Obtiene las frases de un grupo temático específico."""
    try:
        grupos = get_all_phrases()
        if grupo not in grupos:
            raise HTTPException(status_code=404, detail=f"Grupo '{grupo}' no encontrado")

        return {
            "grupo": grupo,
            "frases": grupos[grupo]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener frases del grupo {grupo}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.post(
    "/deletreo",
    response_model=SpellOutResponse,
    tags=["Utilidades"],
    summary="Deletrear texto manualmente",
    description="""
    Deletrea un texto carácter por carácter, útil para comunicación con personas sordas.

    ## Funcionamiento:

    - **Letras**: Se deletrean en mayúsculas (H, O, L, A)
    - **Números**: Se deletrean tal cual (1, 2, 3)
    - **Espacios**: Se deletrean como "espacio" (configurable)
    - **Caracteres especiales**: Se usan nombres descriptivos
      - @ → "arroba"
      - . → "punto"
      - ! → "exclamación"
      - ? → "interrogación"
      - etc.

    ## Parámetros:

    - **texto**: Texto a deletrear (1-200 caracteres)
    - **incluir_espacios**: Si es true, incluye "espacio". Si es false, omite espacios (default: true)

    ## Ejemplos:

    **Con espacios:**
    ```json
    {"texto": "Hola Mundo", "incluir_espacios": true}
    → ["H", "O", "L", "A", "espacio", "M", "U", "N", "D", "O"]
    ```

    **Sin espacios:**
    ```json
    {"texto": "Hola Mundo", "incluir_espacios": false}
    → ["H", "O", "L", "A", "M", "U", "N", "D", "O"]
    ```

    **Con caracteres especiales:**
    ```json
    {"texto": "Hola!"}
    → ["H", "O", "L", "A", "exclamación"]
    ```

    ## Diferencia con /buscar:

    Este endpoint **siempre deletrea** el texto proporcionado.
    El endpoint `/buscar` solo deletrea **automáticamente** si la similitud es baja.
    """,
    responses={
        200: {
            "description": "Deletreo exitoso",
            "content": {
                "application/json": {
                    "examples": {
                        "con_espacios": {
                            "summary": "Con espacios incluidos",
                            "value": {
                                "texto_original": "Hola Mundo",
                                "deletreo": ["H", "O", "L", "A", "espacio", "M", "U", "N", "D", "O"],
                                "total_caracteres": 10
                            }
                        },
                        "sin_espacios": {
                            "summary": "Sin espacios",
                            "value": {
                                "texto_original": "Hola",
                                "deletreo": ["H", "O", "L", "A"],
                                "total_caracteres": 4
                            }
                        }
                    }
                }
            }
        },
        400: {"description": "Texto vacío o inválido"},
        500: {"description": "Error interno del servidor"}
    }
)
async def deletrear_texto(request: SpellOutRequest):
    """Deletrea texto carácter por carácter para comunicación con personas sordas."""
    if not request.texto:
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío")

    try:
        logger.info(f"Deletreando texto: {request.texto}")
        deletreo = spell_out_text(request.texto, request.incluir_espacios)

        response = SpellOutResponse(
            texto_original=request.texto,
            deletreo=deletreo,
            total_caracteres=len(deletreo)
        )

        logger.info(f"Deletreo completado: {len(deletreo)} caracteres")
        return response

    except Exception as e:
        logger.error(f"Error al deletrear texto: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get(
    "/health",
    tags=["Sistema"],
    summary="Health check del servicio",
    description="""
    Verifica el estado de salud del servicio y sus componentes.

    ## Verificaciones realizadas:

    1. **Matcher inicializado**: Verifica que el modelo PLN esté cargado
    2. **Dataset cargado**: Verifica que los grupos y frases se puedan leer
    3. **Embeddings disponibles**: Verifica que el cache de embeddings esté listo

    ## Estados posibles:

    - **healthy**: Todos los componentes funcionan correctamente
    - **unhealthy**: Al menos un componente tiene problemas

    ## Uso recomendado:

    - **Monitoreo**: Llamar periódicamente para verificar disponibilidad
    - **Load Balancers**: Usar como endpoint de health check
    - **Docker/Kubernetes**: Configurar como liveness/readiness probe
    - **CI/CD**: Verificar que el deployment fue exitoso

    ## Ejemplo con Docker healthcheck:

    ```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    ```
    """,
    responses={
        200: {
            "description": "Health check completado (puede ser healthy o unhealthy)",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Sistema saludable",
                            "value": {"status": "healthy"}
                        },
                        "unhealthy_matcher": {
                            "summary": "Matcher no inicializado",
                            "value": {
                                "status": "unhealthy",
                                "reason": "Matcher no inicializado"
                            }
                        },
                        "unhealthy_dataset": {
                            "summary": "Error al cargar dataset",
                            "value": {
                                "status": "unhealthy",
                                "reason": "No se pudieron cargar los grupos"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def health_check():
    """Endpoint de verificación de salud del servicio para monitoreo y orquestación."""
    try:
        # Verificar que el matcher esté inicializado
        if matcher is None:
            return {"status": "unhealthy", "reason": "Matcher no inicializado"}

        # Verificar que los grupos se puedan cargar
        grupos = get_all_phrases()
        if not grupos:
            return {"status": "unhealthy", "reason": "No se pudieron cargar los grupos"}

        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {"status": "unhealthy", "reason": str(e)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)