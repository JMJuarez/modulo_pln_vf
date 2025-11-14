import json
from typing import Dict, List
from pathlib import Path


def load_groups(file_path: str = "data/grupos.json") -> Dict[str, List[str]]:
    """
    Carga los grupos de frases desde el archivo JSON.

    Args:
        file_path: Ruta al archivo JSON con los grupos

    Returns:
        Diccionario con los grupos de frases
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("grupos", {})


def get_all_phrases() -> Dict[str, List[str]]:
    """
    Obtiene todas las frases organizadas por grupo.

    Returns:
        Diccionario con las frases por grupo
    """
    return load_groups()


def get_phrases_by_group(group_name: str) -> List[str]:
    """
    Obtiene las frases de un grupo específico.

    Args:
        group_name: Nombre del grupo (A, B, C)

    Returns:
        Lista de frases del grupo especificado
    """
    grupos = load_groups()
    return grupos.get(group_name, [])


def get_all_phrases_flat() -> List[tuple[str, str]]:
    """
    Obtiene todas las frases en formato plano con su grupo.

    Returns:
        Lista de tuplas (grupo, frase)
    """
    grupos = load_groups()
    phrases_flat = []

    for group_name, phrases in grupos.items():
        for phrase in phrases:
            phrases_flat.append((group_name, phrase))

    return phrases_flat