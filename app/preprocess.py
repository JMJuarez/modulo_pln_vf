import re
import unicodedata
from typing import List
from rapidfuzz import fuzz


def remove_repeated_punctuation(text: str) -> str:
    """
    Normaliza puntuación repetida para mejorar matching.

    Ejemplos:
        "hola!!!" -> "hola!"
        "gracias..." -> "gracias."
        "ayuda?????" -> "ayuda?"

    Args:
        text: Texto con puntuación potencialmente repetida

    Returns:
        Texto con puntuación normalizada
    """
    # Normalizar signos de exclamación repetidos
    text = re.sub(r'!{2,}', '!', text)
    # Normalizar signos de interrogación repetidos
    text = re.sub(r'\?{2,}', '?', text)
    # Normalizar puntos repetidos
    text = re.sub(r'\.{2,}', '.', text)
    # Normalizar otros signos de puntuación repetidos
    text = re.sub(r'([,;:]){2,}', r'\1', text)

    return text


def normalize_text(text: str) -> str:
    """
    Normaliza el texto removiendo acentos, convirtiendo a minúsculas,
    y limpiando caracteres especiales.

    Args:
        text: Texto a normalizar

    Returns:
        Texto normalizado
    """
    # Convertir a minúsculas
    text = text.lower()

    # Normalizar puntuación repetida ANTES de removerla
    text = remove_repeated_punctuation(text)

    # Remover acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

    # Limpiar caracteres especiales, mantener solo letras, números y espacios
    text = re.sub(r'[^\w\s]', ' ', text)

    # Normalizar espacios múltiples a uno solo
    text = re.sub(r'\s+', ' ', text)

    # Remover espacios al inicio y final
    text = text.strip()

    return text


def light_spelling_correction(query: str, reference_phrases: List[str], threshold: float = 80.0) -> str:
    """
    Aplica corrección ligera de ortografía usando similitud difusa.
    Si encuentra una frase con alta similitud, sugiere una corrección.

    Args:
        query: Texto de consulta
        reference_phrases: Lista de frases de referencia
        threshold: Umbral de similitud para sugerir corrección

    Returns:
        Texto corregido o el original si no se encuentra corrección
    """
    query_normalized = normalize_text(query)
    best_match = ""
    best_score = 0.0

    for phrase in reference_phrases:
        phrase_normalized = normalize_text(phrase)
        score = fuzz.ratio(query_normalized, phrase_normalized)

        if score > best_score and score >= threshold:
            best_score = score
            best_match = phrase

    # Si encontramos una buena coincidencia y es suficientemente diferente,
    # sugerimos la corrección
    if best_match and best_score >= threshold:
        return best_match

    return query


def preprocess_query(query: str, reference_phrases: List[str] = None) -> str:
    """
    Preprocesa la consulta aplicando normalización y corrección opcional.

    Args:
        query: Texto de consulta
        reference_phrases: Lista opcional de frases de referencia para corrección

    Returns:
        Consulta preprocesada
    """
    # Aplicar corrección ligera si se proporcionan frases de referencia
    if reference_phrases:
        query = light_spelling_correction(query, reference_phrases)

    # Normalizar texto
    query = normalize_text(query)

    return query


def preprocess_phrases(phrases: List[str]) -> List[str]:
    """
    Preprocesa una lista de frases aplicando normalización.

    Args:
        phrases: Lista de frases a preprocesar

    Returns:
        Lista de frases preprocesadas
    """
    return [normalize_text(phrase) for phrase in phrases]


def normalize_leet_speak(text: str) -> str:
    """
    Normaliza caracteres de 'leet speak' y sustituciones comunes a letras normales.

    Ejemplos:
        "Acapulc@" -> "Acapulco"
        "M4ri@" -> "Maria"
        "P3dro" -> "Pedro"
        "4yud@" -> "Ayuda"

    Args:
        text: Texto con posibles caracteres especiales

    Returns:
        Texto normalizado con letras estándar
    """
    # Mapeo de caracteres especiales/números a letras
    leet_map = {
        '@': 'a',
        '4': 'a',
        '3': 'e',
        '1': 'i',
        '!': 'i',
        '0': 'o',
        '5': 's',
        '$': 's',
        '7': 't',
        '+': 't',
        '8': 'b',
        '9': 'g',
        '6': 'g',
    }

    # Normalizar carácter por carácter
    normalized = []
    for i, char in enumerate(text):
        # Intentar normalizar con el mapeo
        char_lower = char.lower()
        if char_lower in leet_map:
            normalized_char = leet_map[char_lower]
            # Mantener mayúscula si es el primer carácter o si el original era mayúscula
            if i == 0 and (char.isupper() or not char.isalpha()):
                normalized_char = normalized_char.upper()
            elif i > 0 and normalized and normalized[0].isupper() and char == char.upper():
                # Si el primer carácter es mayúscula y este también, mantener mayúscula
                if len(normalized) == 1:  # Segundo carácter
                    normalized_char = normalized_char.upper()
            normalized.append(normalized_char)
        else:
            normalized.append(char)

    return ''.join(normalized)


def spell_out_text(text: str, include_spaces: bool = True) -> List[str]:
    """
    Deletrea un texto carácter por carácter.

    Args:
        text: Texto a deletrear
        include_spaces: Si True, incluye espacios en el deletreo

    Returns:
        Lista con cada carácter/palabra deletreada
    """
    if not text:
        return []

    result = []
    i=0
    text_upper = text.upper()
    while i < len(text_upper):
        char = text_upper[i]
        if i + 1 < len(text_upper) and text_upper[i:i+2] == 'LL':
            result.append('LL')
            i += 2
            continue
        
        # 2. Comprobar 'RR'
        if i + 1 < len(text_upper) and text_upper[i:i+2] == 'RR':
            result.append('RR')
            i += 2
            continue
        
        # 3. Comprobar 'CH'
        if i + 1 < len(text_upper) and text_upper[i:i+2] == 'CH':
            result.append('CH')
            i += 2
            continue
        
        if char == ' ':
            if include_spaces:
                result.append("espacio")
        elif char.isalpha():
            result.append(char)
        elif char.isdigit():
            result.append(char)
        else:
            # Para caracteres especiales, usar su nombre
            special_chars = {
                '.': 'punto',
                ',': 'coma',
                ';': 'punto y coma',
                ':': 'dos puntos',
                '!': 'exclamación',
                '?': 'interrogación',
                '-': 'guión',
                '_': 'guión bajo',
                '@': 'arroba',
                '#': 'numeral',
                '$': 'dólar',
                '%': 'porcentaje',
                '&': 'ampersand',
                '/': 'barra',
                '\\': 'barra invertida',
                '(': 'paréntesis abierto',
                ')': 'paréntesis cerrado',
                '[': 'corchete abierto',
                ']': 'corchete cerrado',
                '{': 'llave abierta',
                '}': 'llave cerrada',
                '+': 'más',
                '=': 'igual',
                '*': 'asterisco',
                '"': 'comillas',
                "'": 'comilla simple',
            }
            result.append(special_chars.get(char, f"carácter especial: {char}"))
        i += 1
    return result