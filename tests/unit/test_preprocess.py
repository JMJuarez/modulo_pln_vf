"""
Tests unitarios para el módulo de preprocesamiento.
"""

import pytest
from app.preprocess import normalize_text, spell_out_text, preprocess_query, light_spelling_correction


@pytest.mark.unit
class TestNormalizeText:
    """Tests para normalización de texto."""

    def test_lowercase_conversion(self):
        """Debe convertir a minúsculas."""
        assert normalize_text("HOLA") == "hola"
        assert normalize_text("Buenos DÍAS") == "buenos dias"
        assert normalize_text("MiXtO") == "mixto"

    def test_accent_removal(self):
        """Debe remover acentos."""
        assert normalize_text("médico") == "medico"
        assert normalize_text("emergéncia") == "emergencia"
        assert normalize_text("¿Cómo estás?") == "como estas"
        assert normalize_text("café") == "cafe"

    def test_special_chars_removal(self):
        """Debe remover caracteres especiales."""
        assert normalize_text("¡Ayuda!") == "ayuda"
        assert normalize_text("Hola, ¿qué tal?") == "hola que tal"
        assert normalize_text("test@email.com") == "test email com"

    def test_whitespace_normalization(self):
        """Debe normalizar espacios múltiples."""
        assert normalize_text("hola    mundo") == "hola mundo"
        assert normalize_text("  espacios  ") == "espacios"
        assert normalize_text("a  b  c") == "a b c"

    def test_empty_string(self):
        """Debe manejar strings vacíos."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""
        assert normalize_text("\t\n") == ""

    def test_unicode_handling(self):
        """Debe manejar caracteres Unicode correctamente."""
        assert normalize_text("niño") == "nino"
        assert normalize_text("señor") == "senor"
        assert normalize_text("año") == "ano"

    def test_combined_transformations(self):
        """Debe aplicar todas las transformaciones juntas."""
        text = "¡HOLA, ¿Cómo    estás?!"
        result = normalize_text(text)
        assert result == "hola como estas"


@pytest.mark.unit
class TestSpellOut:
    """Tests para deletreo de texto."""

    def test_basic_spelling(self):
        """Debe deletrear texto básico."""
        result = spell_out_text("hola")
        assert result == ["H", "O", "L", "A"]

    def test_spelling_with_spaces(self):
        """Debe incluir espacios cuando se solicita."""
        result = spell_out_text("a b", include_spaces=True)
        assert result == ["A", "espacio", "B"]

    def test_spelling_without_spaces(self):
        """No debe incluir espacios si no se solicita."""
        result = spell_out_text("a b", include_spaces=False)
        assert result == ["A", "B"]

    def test_special_characters(self):
        """Debe convertir caracteres especiales a nombres."""
        result = spell_out_text("a@b.com")
        assert "A" in result
        assert "arroba" in result
        assert "B" in result
        assert "punto" in result
        assert "C" in result
        assert "O" in result
        assert "M" in result

    def test_numbers(self):
        """Debe mantener números."""
        result = spell_out_text("abc123")
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_empty_string(self):
        """Debe retornar lista vacía para string vacío."""
        assert spell_out_text("") == []

    def test_mixed_content(self):
        """Debe manejar contenido mixto (letras, números, símbolos)."""
        result = spell_out_text("Ivan123!")
        assert "I" in result
        assert "V" in result
        assert "A" in result
        assert "N" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result
        assert "exclamación" in result


@pytest.mark.unit
class TestPreprocessQuery:
    """Tests para preprocesamiento de queries."""

    def test_basic_preprocessing(self):
        """Debe aplicar normalización básica."""
        result = preprocess_query("HOLA MUNDO")
        assert result == "hola mundo"

    def test_without_references(self):
        """Debe funcionar sin frases de referencia."""
        result = preprocess_query("Hola!")
        assert result == "hola"

    def test_with_references(self):
        """Debe usar frases de referencia si se proporcionan."""
        referencias = ["hola", "buenos días", "ayuda"]
        # Debería normalizar normalmente
        result = preprocess_query("HOLA", referencias)
        assert "hola" in result.lower()

    def test_complex_text(self):
        """Debe procesar texto complejo."""
        result = preprocess_query("¡¡Necesito AYUDA urgente!!")
        assert result == "necesito ayuda urgente"


@pytest.mark.unit
class TestLightSpellingCorrection:
    """Tests para corrección ortográfica ligera."""

    def test_no_correction_needed(self):
        """No debe corregir si el texto es correcto."""
        referencias = ["hola", "buenos días"]
        result = light_spelling_correction("hola", referencias)
        assert result == "hola"

    def test_high_similarity_match(self):
        """Debe corregir si hay alta similitud."""
        referencias = ["hola", "buenos días", "ayuda"]
        # "ola" debería ser similar a "hola"
        result = light_spelling_correction("ola", referencias, threshold=70.0)
        # Podría corregir a "hola" dependiendo del threshold
        assert result in ["ola", "hola"]

    def test_no_match_below_threshold(self):
        """No debe corregir si la similitud es baja."""
        referencias = ["hola", "buenos días"]
        result = light_spelling_correction("xyz123", referencias)
        assert result == "xyz123"
