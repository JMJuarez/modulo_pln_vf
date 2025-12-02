import numpy as np
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import logging

from .groups import get_all_phrases
from .preprocess import preprocess_query, preprocess_phrases, normalize_text


def clip_similarity(similarity: float) -> float:
    """
    Asegura que el valor de similitud esté en el rango [0.0, 1.0].

    Esto previene errores numéricos de precisión flotante y ajustes
    (como boosts) que puedan generar valores fuera de rango.

    Args:
        similarity: Valor de similitud a normalizar

    Returns:
        Valor de similitud en el rango [0.0, 1.0]
    """
    return np.clip(similarity, 0.0, 1.0)


class ImprovedPhraseMatcher:
    """
    Versión mejorada del matcher con:
    1. Modelo optimizado para español
    2. Re-ranking en dos fases
    3. Expansión de sinónimos
    4. Ajuste de threshold por grupo
    """

    # Modelos disponibles ordenados por calidad para español
    MODELS = {
        "spanish_optimized": "hiiamsid/sentence_similarity_spanish_es",  # Mejor para español
        "multilingual_advanced": "paraphrase-multilingual-mpnet-base-v2",  # Más potente
        "multilingual_balanced": "paraphrase-multilingual-MiniLM-L12-v2",  # Balanceado
        "current": "all-MiniLM-L6-v2"  # Actual
    }

    # Threshold adaptativo por grupo
    GROUP_THRESHOLDS = {
        "A": 0.60,  # Emergencias: más flexible
        "B": 0.63,  # Saludos: flexible
        "C": 0.78   # Comunicación: más estricto para evitar atraer typos
    }

    # Threshold para activar deletreo automático
    # Umbrales ajustados por grupo (más estrictos para mejor detección de nombres)
    SPELL_OUT_THRESHOLDS = {
        "A": 0.75,  # Emergencias: estricto
        "B": 0.80,  # Saludos: más estricto
        "C": 0.85   # Comunicación: muy estricto (máxima precisión)
    }

    # Sinónimos para expansión de query
    SYNONYMS = {
        "ayuda": ["asistencia", "soporte", "apoyo"],
        "problema": ["error", "fallo", "inconveniente", "issue"],
        "quiero": ["deseo", "necesito", "requiero"],
        "cambiar": ["modificar", "actualizar", "editar"],
        "cancelar": ["eliminar", "borrar", "anular"],
        "hola": ["saludos", "buenos días", "buenas"],
        "gracias": ["agradecimiento", "muchas gracias", "te agradezco"],
    }

    def __init__(
        self,
        model_type: str = "multilingual_balanced",  # Mejor que el actual
        cache_path: str = "data/embeddings_improved.npz",
        use_reranking: bool = True,
        use_synonym_expansion: bool = True
    ):
        """
        Inicializa el matcher mejorado.

        Args:
            model_type: Tipo de modelo a usar (ver MODELS)
            cache_path: Ruta para cachear los embeddings
            use_reranking: Activar re-ranking en dos fases
            use_synonym_expansion: Expandir query con sinónimos
        """
        self.model_name = self.MODELS.get(model_type, self.MODELS["current"])
        self.cache_path = cache_path
        self.use_reranking = use_reranking
        self.use_synonym_expansion = use_synonym_expansion
        self.model = None
        self.grupos_embeddings = {}
        self.grupos_frases = {}
        self.grupos_centroids = {}
        self.logger = logging.getLogger(__name__)

        # Lista de nombres comunes en español para detección de nombres propios
        self.COMMON_SPANISH_NAMES = {
            # Nombres masculinos comunes
            'juan', 'jose', 'antonio', 'manuel', 'francisco', 'david', 'carlos',
            'miguel', 'pedro', 'luis', 'jesus', 'pablo', 'javier', 'sergio',
            'rafael', 'daniel', 'jorge', 'alberto', 'fernando', 'ricardo',
            'alejandro', 'adrian', 'andres', 'raul', 'enrique', 'ivan',
            # Nombres femeninos comunes
            'maria', 'carmen', 'ana', 'isabel', 'pilar', 'teresa', 'rosa',
            'laura', 'marta', 'elena', 'sara', 'lucia', 'paula', 'sofia',
            'cristina', 'andrea', 'julia', 'raquel', 'beatriz', 'patricia'
        }

        self.logger.info(f"Matcher mejorado usando modelo: {self.model_name}")

    def _load_model(self):
        """Carga el modelo de embeddings si no está cargado."""
        if self.model is None:
            self.logger.info(f"Cargando modelo mejorado: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)

    def _expand_with_synonyms(self, query: str) -> List[str]:
        """
        Expande la query con sinónimos relevantes.

        Args:
            query: Query original

        Returns:
            Lista de queries expandidas
        """
        if not self.use_synonym_expansion:
            return [query]

        queries = [query]
        words = query.lower().split()

        for word in words:
            if word in self.SYNONYMS:
                for synonym in self.SYNONYMS[word]:
                    expanded = query.lower().replace(word, synonym)
                    queries.append(expanded)

        return queries[:5]  # Limitar a 5 variaciones

    def _load_or_compute_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Carga embeddings desde cache o los computa si no existen.

        Returns:
            Diccionario con embeddings por grupo
        """
        cache_file = Path(self.cache_path)

        # Intentar cargar desde cache
        if cache_file.exists():
            try:
                self.logger.info("Cargando embeddings mejorados desde cache")
                data = np.load(cache_file, allow_pickle=True)
                embeddings_dict = {}
                for key in data.files:
                    embeddings_dict[key] = data[key]
                return embeddings_dict
            except Exception as e:
                self.logger.warning(f"Error al cargar cache: {e}. Recomputando embeddings.")

        # Computar embeddings
        return self._compute_embeddings()

    def _compute_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Computa los embeddings para todas las frases.

        Returns:
            Diccionario con embeddings por grupo
        """
        self.logger.info("Computando embeddings mejorados para todas las frases")
        self._load_model()

        grupos = get_all_phrases()
        embeddings_dict = {}

        for grupo, frases in grupos.items():
            frases_procesadas = preprocess_phrases(frases)
            embeddings = self.model.encode(
                frases_procesadas,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalizar para mejor similitud
            )
            embeddings_dict[grupo] = embeddings

        # Guardar en cache
        self._save_embeddings_cache(embeddings_dict)

        return embeddings_dict

    def _save_embeddings_cache(self, embeddings_dict: Dict[str, np.ndarray]):
        """
        Guarda los embeddings en cache.

        Args:
            embeddings_dict: Diccionario con embeddings por grupo
        """
        try:
            cache_file = Path(self.cache_path)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache_file, **embeddings_dict)
            self.logger.info(f"Embeddings mejorados guardados en cache: {cache_file}")
        except Exception as e:
            self.logger.error(f"Error al guardar cache: {e}")

    def _compute_centroids(self):
        """Computa los centroides para cada grupo."""
        self.grupos_centroids = {}
        for grupo, embeddings in self.grupos_embeddings.items():
            centroid = np.mean(embeddings, axis=0)
            # Normalizar centroide
            centroid = centroid / np.linalg.norm(centroid)
            self.grupos_centroids[grupo] = centroid

    def initialize(self):
        """Inicializa el matcher cargando embeddings y computando centroides."""
        self.logger.info("Inicializando PhraseMatcher mejorado")

        # Cargar frases
        self.grupos_frases = get_all_phrases()

        # Cargar o computar embeddings
        self.grupos_embeddings = self._load_or_compute_embeddings()

        # Computar centroides
        self._compute_centroids()

        self.logger.info("PhraseMatcher mejorado inicializado correctamente")

    def find_best_groups(self, query: str, top_k: int = 2) -> List[Tuple[str, float]]:
        """
        Encuentra los top-k grupos más similares usando centroides.

        Args:
            query: Consulta de entrada
            top_k: Número de grupos a retornar

        Returns:
            Lista de tuplas (grupo, similitud)
        """
        if not self.grupos_centroids:
            raise ValueError("Matcher no inicializado. Llama a initialize() primero.")

        self._load_model()

        # Obtener todas las frases para corrección
        all_phrases = []
        for frases in self.grupos_frases.values():
            all_phrases.extend(frases)

        # Preprocesar query
        query_processed = preprocess_query(query, all_phrases)

        # Expandir con sinónimos
        queries = self._expand_with_synonyms(query_processed)

        # Obtener embeddings de todas las variaciones
        query_embeddings = self.model.encode(
            queries,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Promediar embeddings de variaciones
        query_embedding = np.mean(query_embeddings, axis=0)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Calcular similitud con cada centroide
        group_scores = []
        for grupo, centroid in self.grupos_centroids.items():
            similarity = cosine_similarity([query_embedding], [centroid])[0][0]
            similarity = clip_similarity(similarity)  # Asegurar rango [0.0, 1.0]
            group_scores.append((grupo, similarity))

        # Ordenar por similitud descendente
        group_scores.sort(key=lambda x: x[1], reverse=True)

        return group_scores[:top_k]

    def find_most_similar_phrase_reranked(self, query: str) -> Tuple[str, str, float]:
        """
        Encuentra la frase más similar usando re-ranking en dos fases.

        Args:
            query: Consulta de entrada

        Returns:
            Tupla con (grupo, frase_más_similar, score_similitud)
        """
        # Fase 1: Encontrar top grupos candidatos
        # Buscar en top-3 para aumentar cobertura (en lugar de top-2)
        # Esto ayuda cuando palabras como "alto" no tienen fuerte señal semántica de grupo
        top_groups = self.find_best_groups(query, top_k=3)

        self._load_model()

        # Obtener todas las frases para corrección
        all_phrases = []
        for frases in self.grupos_frases.values():
            all_phrases.extend(frases)

        # Preprocesar query
        query_processed = preprocess_query(query, all_phrases)

        # Obtener embedding del query
        query_embedding = self.model.encode(
            [query_processed],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        best_group = None
        best_phrase = None
        best_similarity = -1.0

        # Fase 2: Búsqueda fina en grupos candidatos
        self.logger.debug(f"Top grupos candidatos para '{query}': {top_groups}")

        for grupo, group_score in top_groups:
            embeddings = self.grupos_embeddings[grupo]
            frases = self.grupos_frases[grupo]

            # Calcular similitud con todas las frases del grupo
            similarities = cosine_similarity([query_embedding], embeddings)[0]

            # MEJORA: Aplicar boost a frases largas (más contexto = más confiable)
            # Esto ayuda a priorizar frases originales completas sobre palabras sueltas
            boosted_similarities = similarities.copy()
            # Asegurar que no excedemos el tamaño del array
            num_frases = min(len(frases), len(boosted_similarities))
            for idx in range(num_frases):
                frase = frases[idx]
                frase_len = len(frase.split())  # Número de palabras
                # Boost progresivo: frases de 2+ palabras reciben bonus fuerte
                if frase_len >= 3:
                    boosted_similarities[idx] += 0.15  # Frases largas: +15% (aumentado de 10%)
                elif frase_len == 2:
                    boosted_similarities[idx] += 0.08  # Frases medianas: +8% (aumentado de 5%)
                # Palabras sueltas no reciben boost (penalizadas relativamente)

            # Encontrar la mejor similitud en este grupo (con boost aplicado)
            max_idx = np.argmax(boosted_similarities)
            max_similarity = boosted_similarities[max_idx]
            max_similarity = clip_similarity(max_similarity)  # Asegurar rango [0.0, 1.0]

            # Aplicar threshold adaptativo
            threshold = self.GROUP_THRESHOLDS.get(grupo, 0.70)

            # Bonus por ser el grupo más probable
            if grupo == top_groups[0][0]:
                max_similarity += 0.05  # Boost al grupo más probable
                max_similarity = clip_similarity(max_similarity)  # Asegurar que no supere 1.0

            self.logger.debug(f"Grupo {grupo}: mejor='{frases[max_idx]}' sim={max_similarity:.1f} threshold={threshold}")

            if max_similarity > best_similarity and max_similarity >= threshold:
                best_similarity = max_similarity
                best_group = grupo
                best_phrase = frases[max_idx]

        # Si no se encontró nada por threshold, retornar el mejor absoluto
        if best_group is None:
            grupo = top_groups[0][0]
            embeddings = self.grupos_embeddings[grupo]
            frases = self.grupos_frases[grupo]
            similarities = cosine_similarity([query_embedding], embeddings)[0]
            max_idx = np.argmax(similarities)
            best_similarity = similarities[max_idx]
            best_similarity = clip_similarity(best_similarity)  # Asegurar rango [0.0, 1.0]
            best_group = grupo
            best_phrase = frases[max_idx]

        return best_group, best_phrase, best_similarity

    def search_similar_phrase(self, query: str) -> Dict:
        """
        Busca la frase más similar usando estrategia mejorada.
        Si la similitud está por debajo del umbral de deletreo, activa el modo deletreo.

        Args:
            query: Consulta de entrada

        Returns:
            Diccionario con resultado de la búsqueda y deletreo si aplica
        """
        if self.use_reranking:
            grupo, frase, similarity = self.find_most_similar_phrase_reranked(query)
        else:
            # Fallback a método básico
            best_group = self.find_best_groups(query, top_k=1)[0][0]
            grupo, frase, similarity = self.find_most_similar_phrase(query, best_group)

        # Verificar si se debe activar el modo deletreo
        spell_out_threshold = self.SPELL_OUT_THRESHOLDS.get(grupo, 0.60)
        should_spell_out = similarity < spell_out_threshold

        self.logger.debug(f"Antes de validaciones: grupo={grupo}, frase='{frase}', sim={similarity:.1f}, spell_threshold={spell_out_threshold}")

        # VALIDACIÓN ESPECIAL: Detectar posibles nombres propios
        # Palabras cortas (4-6 chars) que no están en el dataset con similitud media
        query_normalized = query.strip().lower()
        query_words = query_normalized.split()

        # Si es una palabra sola corta (posible nombre)
        if len(query_words) == 1:
            query_len = len(query_words[0])
            # Nombres típicos: 3-8 caracteres
            if 3 <= query_len <= 8:
                # Construir lista dinámica de palabras conocidas del dataset
                palabras_conocidas = set()
                for frases in self.grupos_frases.values():
                    for frase_item in frases:
                        # Normalizar y extraer palabras del dataset
                        frase_normalized = normalize_text(frase_item)
                        palabras_conocidas.update(frase_normalized.split())

                # Agregar palabras comunes adicionales
                palabras_conocidas.update([
                    'ayuda', 'hola', 'gracias', 'bien', 'mal', 'si', 'no',
                    'vale', 'ok', 'perdon', 'espera', 'entiendo', 'auxilio',
                    'socorro', 'doctor', 'hospital', 'salida', 'fuego', 'urgente',
                    'alto', 'ayda', 'ola', 'hla', 'grcias'  # Incluir variantes y typos del dataset
                ])

                self.logger.debug(f"Query normalizado: '{query_normalized}', en palabras_conocidas: {query_normalized in palabras_conocidas}")

                # VALIDACIÓN 1: Detectar nombres comunes en español
                if query_normalized in self.COMMON_SPANISH_NAMES:
                    should_spell_out = True
                    self.logger.info(f"Nombre común español detectado: '{query}' (similitud={similarity:.2f}), activando deletreo")
                # VALIDACIÓN 2: Palabra no está en el dataset
                elif query_normalized not in palabras_conocidas:
                    # Si la similitud es media pero no alta (posible nombre)
                    # Ajustar rango: solo activar para similitudes medias-bajas
                    if 0.50 <= similarity < 0.85:
                        # Activar deletreo para posibles nombres
                        should_spell_out = True
                        self.logger.info(f"Posible nombre detectado: '{query}' (similitud={similarity:.2f}), activando deletreo")

        # VALIDACIÓN 3: Detectar nombres por capitalización (Primera letra mayúscula)
        # Esto detecta nombres propios por su formato: "Carlos", "Juan", "Maria"
        if len(query) > 2 and query[0].isupper() and len(query) > 1 and query[1:].islower():
            # Verificar que no sea una frase del dataset que empiece con mayúscula
            if similarity < 0.98:  # No es match exacto
                should_spell_out = True
                self.logger.info(f"Nombre propio detectado por capitalización: '{query}' (similitud={similarity:.2f}), activando deletreo")

        # VALIDACIÓN ADICIONAL: Penalizar matches con gran diferencia de longitud
        # Esto previene que palabras como "Ivan" hagan match con "Sí"
        query_words = query.strip().split()
        frase_words = frase.strip().split()

        # Si la query es de una sola palabra y la frase también
        if len(query_words) == 1 and len(frase_words) == 1:
            query_len = len(query_words[0])
            frase_len = len(frase_words[0])

            # Si la diferencia de longitud es > 1 carácter, penalizar
            length_diff = abs(query_len - frase_len)
            if length_diff > 1:
                # Reducir similitud significativamente
                # Penalización muy suave: 5% por cada carácter de diferencia (antes era 25%, luego 10%)
                similarity_penalty = 0.05 * length_diff
                similarity = similarity - similarity_penalty
                similarity = clip_similarity(similarity)  # Asegurar rango [0.0, 1.0]
                self.logger.info(f"Penalización por longitud aplicada: query='{query}' ({query_len}) vs frase='{frase}' ({frase_len}), diff={length_diff}, penalty={similarity_penalty:.2f}, nueva_similitud={similarity:.2f}")

                # Recalcular si se debe activar deletreo con la nueva similitud
                should_spell_out = similarity < spell_out_threshold

        # Si se activa el deletreo, solo retornar el deletreo
        if should_spell_out:
            from .preprocess import spell_out_text, normalize_leet_speak

            # Normalizar leet speak antes de deletrear
            # Convierte: "Acapulc@" -> "Acapulco", "M4ri@" -> "Maria", etc.
            normalized_query = normalize_leet_speak(query)
            self.logger.debug(f"Normalizando para deletreo: '{query}' → '{normalized_query}'")

            deletreo_list = spell_out_text(normalized_query, include_spaces=True)
            # Formatear deletreo como string para mostrar en frase_similar
            deletreo_str = " ".join(deletreo_list)
            return {
                "query": query,
                "grupo": None,
                "frase_similar": deletreo_str,  # Ahora muestra el deletreo en lugar de "frase no reconocida"
                "similitud": round(similarity, 4),
                "deletreo_activado": True,
                "deletreo": deletreo_list,
                "total_caracteres": len(deletreo_list)
            }

        # Si no se activa deletreo, retornar respuesta normal
        return {
            "query": query,
            "grupo": grupo,
            "frase_similar": frase,
            "similitud": round(similarity, 4),
            "deletreo_activado": False,
            "deletreo": None,
            "total_caracteres": None
        }

    def find_most_similar_phrase(self, query: str, group: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Encuentra la frase más similar (método básico para compatibilidad).

        Args:
            query: Consulta de entrada
            group: Grupo específico donde buscar (opcional)

        Returns:
            Tupla con (grupo, frase_más_similar, score_similitud)
        """
        if not self.grupos_embeddings:
            raise ValueError("Matcher no inicializado. Llama a initialize() primero.")

        self._load_model()

        # Obtener todas las frases para corrección
        all_phrases = []
        for frases in self.grupos_frases.values():
            all_phrases.extend(frases)

        # Preprocesar query
        query_processed = preprocess_query(query, all_phrases)

        # Obtener embedding del query
        query_embedding = self.model.encode(
            [query_processed],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        best_group = None
        best_phrase = None
        best_similarity = -1.0

        # Determinar grupos donde buscar
        groups_to_search = [group] if group else list(self.grupos_frases.keys())

        for grupo in groups_to_search:
            if grupo not in self.grupos_embeddings:
                continue

            embeddings = self.grupos_embeddings[grupo]
            frases = self.grupos_frases[grupo]

            # Calcular similitud con todas las frases del grupo
            similarities = cosine_similarity([query_embedding], embeddings)[0]

            # Encontrar la mejor similitud en este grupo
            max_idx = np.argmax(similarities)
            max_similarity = similarities[max_idx]
            max_similarity = clip_similarity(max_similarity)  # Asegurar rango [0.0, 1.0]

            if max_similarity > best_similarity:
                best_similarity = max_similarity
                best_group = grupo
                best_phrase = frases[max_idx]

        return best_group, best_phrase, best_similarity
