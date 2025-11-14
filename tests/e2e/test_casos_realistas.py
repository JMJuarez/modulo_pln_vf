"""
Tests E2E de casos realistas de usuario final.

Incluye:
- Errores de tipeo comunes
- Leet speak y caracteres especiales
- Nombres propios
- Capitalizaciones variadas
- Puntuación incorrecta
- Casos de deletreo
"""
import pytest
from app.matcher_improved import ImprovedPhraseMatcher


@pytest.fixture
def matcher():
    """Fixture del matcher inicializado."""
    m = ImprovedPhraseMatcher()
    m.initialize()
    return m


class TestErroresTipeoComunes:
    """Tests de errores de tipeo que usuarios reales cometen."""

    def test_ola_devuelve_hola(self, matcher):
        """El typo 'ola' debe devolver 'Hola' canónico, no 'ola'."""
        result = matcher.search_similar_phrase("ola")
        assert result['deletreo_activado'] is False
        assert 'hola' in result['frase_similar'].lower()

    def test_ayda_reconoce_ayuda(self, matcher):
        """El typo 'ayda' debe reconocerse como ayuda."""
        result = matcher.search_similar_phrase("ayda")
        assert result['deletreo_activado'] is False
        assert result['grupo'] in ['A', 'C']  # Ayuda o palabra similar

    def test_graias_reconoce_gracias(self, matcher):
        """El typo 'graias' debe reconocerse como gracias."""
        result = matcher.search_similar_phrase("graias")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'C'

    def test_hla_reconoce_hola(self, matcher):
        """El typo 'hla' debe reconocerse como hola."""
        result = matcher.search_similar_phrase("hla")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'B'

    def test_auxilo_reconoce_auxilio(self, matcher):
        """El typo 'auxilo' debe reconocerse como auxilio."""
        result = matcher.search_similar_phrase("auxilo")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'A'


class TestLeetSpeakYCaracteresEspeciales:
    """Tests de leet speak y caracteres especiales en deletreo."""

    def test_acapulco_con_arroba_normaliza(self, matcher):
        """'Acapulc@' debe deletrearse como 'A C A P U L C O' no 'arroba'."""
        result = matcher.search_similar_phrase("Acapulc@")
        if result['deletreo_activado']:
            deletreo = ' '.join(result['deletreo'])
            # No debe contener 'arroba'
            assert 'arroba' not in deletreo.lower()
            # Debe contener las letras normalizadas
            assert 'A' in deletreo and 'C' in deletreo

    def test_maria_con_4_y_arroba_normaliza(self, matcher):
        """'M4ri@' debe deletrearse como 'M A R I A'."""
        result = matcher.search_similar_phrase("M4ri@")
        if result['deletreo_activado']:
            deletreo_str = ''.join(result['deletreo']).replace(' ', '')
            # Debe ser MARIA sin números ni símbolos
            assert deletreo_str == 'MARIA'

    def test_pedro_con_3_normaliza(self, matcher):
        """'P3dro' debe deletrearse como 'P E D R O'."""
        result = matcher.search_similar_phrase("P3dro")
        if result['deletreo_activado']:
            deletreo_str = ''.join(result['deletreo']).replace(' ', '')
            assert deletreo_str == 'PEDRO'
            # No debe contener el número 3
            assert '3' not in deletreo_str

    def test_carlos_con_arroba_normaliza(self, matcher):
        """'C@rlos' debe deletrearse como 'C A R L O S'."""
        result = matcher.search_similar_phrase("C@rlos")
        if result['deletreo_activado']:
            deletreo = ' '.join(result['deletreo'])
            assert 'arroba' not in deletreo.lower()
            assert 'CARLOS' in deletreo.replace(' ', '')

    def test_ayuda_con_4_y_arroba_normaliza(self, matcher):
        """'4yud@' debe deletrearse como 'A Y U D A'."""
        result = matcher.search_similar_phrase("4yud@")
        if result['deletreo_activado']:
            deletreo_str = ''.join(result['deletreo']).replace(' ', '')
            assert deletreo_str == 'AYUDA'


class TestNombresPropios:
    """Tests de detección correcta de nombres propios."""

    def test_juan_activa_deletreo(self, matcher):
        """'Juan' debe activar deletreo, no devolver 'vale'."""
        result = matcher.search_similar_phrase("Juan")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['J', 'U', 'A', 'N']

    def test_carlos_activa_deletreo(self, matcher):
        """'Carlos' debe activar deletreo, no devolver palabra similar."""
        result = matcher.search_similar_phrase("Carlos")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['C', 'A', 'R', 'L', 'O', 'S']

    def test_maria_activa_deletreo(self, matcher):
        """'Maria' debe activar deletreo."""
        result = matcher.search_similar_phrase("Maria")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['M', 'A', 'R', 'I', 'A']

    def test_pedro_activa_deletreo(self, matcher):
        """'Pedro' debe activar deletreo."""
        result = matcher.search_similar_phrase("Pedro")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['P', 'E', 'D', 'R', 'O']

    def test_luis_activa_deletreo(self, matcher):
        """'Luis' debe activar deletreo, no devolver 'vale'."""
        result = matcher.search_similar_phrase("Luis")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['L', 'U', 'I', 'S']

    def test_ana_activa_deletreo(self, matcher):
        """'Ana' debe activar deletreo."""
        result = matcher.search_similar_phrase("Ana")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['A', 'N', 'A']

    def test_sofia_activa_deletreo(self, matcher):
        """'Sofia' debe activar deletreo."""
        result = matcher.search_similar_phrase("Sofia")
        assert result['deletreo_activado'] is True
        assert result['deletreo'] == ['S', 'O', 'F', 'I', 'A']


class TestCapitalizacionVariada:
    """Tests de consistencia con diferentes capitalizaciones."""

    def test_hola_variaciones_consistentes(self, matcher):
        """Todas las variaciones de 'hola' deben dar resultado consistente."""
        variaciones = ['hola', 'Hola', 'HOLA', 'HoLa', 'hOLa']
        resultados = [matcher.search_similar_phrase(v) for v in variaciones]

        # Todos deben tener el mismo grupo
        grupos = [r['grupo'] for r in resultados]
        assert len(set(grupos)) == 1, f"Grupos inconsistentes: {grupos}"

        # Todos deben tener el mismo estado de deletreo
        deletreos = [r['deletreo_activado'] for r in resultados]
        assert len(set(deletreos)) == 1, f"Deletreos inconsistentes: {deletreos}"

    def test_ola_variaciones_devuelven_hola(self, matcher):
        """Todas las variaciones de 'ola' deben devolver 'Hola'."""
        variaciones = ['ola', 'Ola', 'OLA', 'oLa']
        for var in variaciones:
            result = matcher.search_similar_phrase(var)
            assert result['deletreo_activado'] is False
            assert 'hola' in result['frase_similar'].lower()

    def test_ayuda_variaciones_consistentes(self, matcher):
        """Todas las variaciones de 'ayuda' deben ser consistentes."""
        variaciones = ['ayuda', 'Ayuda', 'AYUDA', 'AyUdA']
        resultados = [matcher.search_similar_phrase(v) for v in variaciones]

        grupos = [r['grupo'] for r in resultados]
        assert len(set(grupos)) == 1
        assert grupos[0] == 'A'


class TestPuntuacionIncorrecta:
    """Tests de manejo de puntuación incorrecta."""

    def test_alto_sin_puntuacion_no_deletreo(self, matcher):
        """'Alto' sin puntuación debe hacer match con '¡Alto!'."""
        result = matcher.search_similar_phrase("Alto")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'A'
        assert 'alto' in result['frase_similar'].lower()

    def test_alto_con_dobles_signos(self, matcher):
        """'¡¡ALTO!!' debe reconocerse como '¡Alto!'."""
        result = matcher.search_similar_phrase("¡¡ALTO!!")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'A'

    def test_hola_con_exclamaciones_multiples(self, matcher):
        """'hola!!!' debe reconocerse como 'Hola'."""
        result = matcher.search_similar_phrase("hola!!!")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'B'

    def test_gracias_con_puntos_multiples(self, matcher):
        """'gracias...' debe reconocerse como 'Gracias'."""
        result = matcher.search_similar_phrase("gracias...")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'C'


class TestCasosDeletreo:
    """Tests específicos de activación de deletreo."""

    def test_palabra_desconocida_activa_deletreo(self, matcher):
        """Una palabra totalmente desconocida debe activar deletreo."""
        result = matcher.search_similar_phrase("xyzabc")
        assert result['deletreo_activado'] is True

    def test_nombre_ciudad_activa_deletreo(self, matcher):
        """Nombres de ciudades deben activar deletreo."""
        ciudades = ["Acapulco", "Guadalajara", "Monterrey"]
        for ciudad in ciudades:
            result = matcher.search_similar_phrase(ciudad)
            assert result['deletreo_activado'] is True

    def test_deletreo_incluye_espacios(self, matcher):
        """El deletreo de frase con espacios debe incluir 'espacio'."""
        result = matcher.search_similar_phrase("Hola Mundo")
        if result['deletreo_activado']:
            assert 'espacio' in result['deletreo']

    def test_deletreo_conserva_mayusculas(self, matcher):
        """El deletreo debe usar mayúsculas para las letras."""
        result = matcher.search_similar_phrase("Test")
        if result['deletreo_activado']:
            # Todas las letras deben estar en mayúsculas
            letras = [c for c in result['deletreo'] if c.isalpha()]
            assert all(c.isupper() for c in letras)


class TestCasosComplexos:
    """Tests de casos complejos o combinados."""

    def test_typo_con_puntuacion_extra(self, matcher):
        """Typo + puntuación extra debe manejarse correctamente."""
        result = matcher.search_similar_phrase("ola!!")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'B'

    def test_caps_lock_con_typo(self, matcher):
        """CAPS LOCK + typo debe manejarse."""
        result = matcher.search_similar_phrase("HLA")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'B'

    def test_espacios_extras(self, matcher):
        """Espacios extras no deben afectar el matching."""
        result = matcher.search_similar_phrase("  hola  ")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'B'

    def test_mezcla_acentos(self, matcher):
        """Mezcla de acentos debe normalizarse."""
        result = matcher.search_similar_phrase("grácias")
        assert result['deletreo_activado'] is False
        assert result['grupo'] == 'C'


class TestRendimientoDeletreo:
    """Tests de rendimiento del deletreo."""

    def test_deletreo_texto_largo(self, matcher):
        """Deletreo de texto largo debe completarse rápidamente."""
        texto_largo = "A" * 50
        result = matcher.search_similar_phrase(texto_largo)
        # Debe completarse sin error
        assert 'deletreo' in result

    def test_deletreo_con_caracteres_especiales_mixtos(self, matcher):
        """Deletreo con mix de caracteres debe manejarse."""
        result = matcher.search_similar_phrase("T3st@123")
        if result['deletreo_activado']:
            assert len(result['deletreo']) > 0


class TestConsistenciaRespuestas:
    """Tests de consistencia de respuestas."""

    def test_misma_query_multiples_veces(self, matcher):
        """La misma query debe dar siempre el mismo resultado."""
        query = "hola"
        resultados = [matcher.search_similar_phrase(query) for _ in range(5)]

        # Todos los grupos deben ser iguales
        grupos = [r['grupo'] for r in resultados]
        assert len(set(grupos)) == 1

        # Todas las similitudes deben ser iguales
        similitudes = [r['similitud'] for r in resultados]
        assert len(set(similitudes)) == 1

    def test_orden_no_afecta_resultado(self, matcher):
        """El orden de las queries no debe afectar el resultado."""
        queries = ["hola", "ayuda", "gracias"]

        # Primera ronda
        resultados1 = [matcher.search_similar_phrase(q) for q in queries]

        # Segunda ronda en orden inverso
        resultados2 = [matcher.search_similar_phrase(q) for q in reversed(queries)]
        resultados2.reverse()

        # Deben ser iguales
        for r1, r2 in zip(resultados1, resultados2):
            assert r1['grupo'] == r2['grupo']
            assert r1['similitud'] == r2['similitud']
