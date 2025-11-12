"""
TESTS UNITARIOS PARA EXPANSIÓN SEMÁNTICA
Valida la funcionalidad de expansión de queries con sinónimos legales
"""

import pytest
import sys
from pathlib import Path

# Añadir directorio padre para importar semantic_utils.py
backend_path = Path(__file__).parent.parent / "backend-api"
sys.path.insert(0, str(backend_path))


def test_import_sinonimos_legales():
    """Verificar que el diccionario SINONIMOS_LEGALES existe"""
    from semantic_utils import SINONIMOS_LEGALES
    
    assert SINONIMOS_LEGALES is not None
    assert isinstance(SINONIMOS_LEGALES, dict)
    assert len(SINONIMOS_LEGALES) > 0
    print(f"✅ SINONIMOS_LEGALES cargado con {len(SINONIMOS_LEGALES)} términos")


def test_sinonimos_contains_key_terms():
    """Verificar que contiene términos clave esperados"""
    from semantic_utils import SINONIMOS_LEGALES
    
    # Términos que deben estar
    expected_terms = ["matar", "robar", "violar", "drogas", "herir"]
    
    for term in expected_terms:
        assert term in SINONIMOS_LEGALES, f"Término '{term}' debería estar en SINONIMOS_LEGALES"
        assert isinstance(SINONIMOS_LEGALES[term], list)
        assert len(SINONIMOS_LEGALES[term]) > 0
    
    print(f"✅ Todos los términos clave encontrados: {expected_terms}")


def test_sinonimos_values_are_lists():
    """Verificar que todos los valores son listas de strings"""
    from semantic_utils import SINONIMOS_LEGALES
    
    for key, value in SINONIMOS_LEGALES.items():
        assert isinstance(value, list), f"Valor de '{key}' debe ser lista"
        assert len(value) > 0, f"Valor de '{key}' no debe estar vacío"
        
        for sinonimo in value:
            assert isinstance(sinonimo, str), f"Sinónimo en '{key}' debe ser string"
            assert len(sinonimo) > 0, f"Sinónimo en '{key}' no debe estar vacío"
    
    print("✅ Todos los valores son listas de strings válidas")


def test_import_expandir_query_function():
    """Verificar que la función expandir_query_con_sinonimos existe"""
    from semantic_utils import expandir_query_con_sinonimos
    
    assert callable(expandir_query_con_sinonimos)
    print("✅ Función expandir_query_con_sinonimos importada correctamente")


def test_expandir_query_simple():
    """Test de expansión con un término simple"""
    from semantic_utils import expandir_query_con_sinonimos
    
    query = "quiero saber sobre matar"
    resultado = expandir_query_con_sinonimos(query)
    
    # La query expandida debe contener el original
    assert "matar" in resultado
    
    # Debe contener al menos algunos sinónimos
    assert any(word in resultado for word in ["homicidio", "asesinato", "muerte"])
    
    print(f"✅ Query simple expandida correctamente:")
    print(f"   Original: {query}")
    print(f"   Expandida: {resultado}")


def test_expandir_query_multiple_terms():
    """Test de expansión con múltiples términos"""
    from semantic_utils import expandir_query_con_sinonimos
    
    query = "robar un coche es lo mismo que matar"
    resultado = expandir_query_con_sinonimos(query)
    
    # Debe contener el original
    assert "robar" in resultado
    assert "matar" in resultado
    assert "coche" in resultado
    
    # Debe contener sinónimos de ambos términos
    assert any(word in resultado for word in ["hurto", "apropiación", "sustracción"])
    assert any(word in resultado for word in ["homicidio", "asesinato"])
    
    print(f"✅ Query múltiple expandida correctamente:")
    print(f"   Original: {query}")
    print(f"   Expandida: {resultado}")


def test_expandir_query_no_match():
    """Test con query que no tiene términos a expandir"""
    from semantic_utils import expandir_query_con_sinonimos
    
    query = "artículo 234 código penal"
    resultado = expandir_query_con_sinonimos(query)
    
    # Si no hay términos a expandir, debería devolver la query original
    assert "artículo" in resultado
    assert "234" in resultado
    assert "código" in resultado
    assert "penal" in resultado
    
    print(f"✅ Query sin términos expandibles:")
    print(f"   Original: {query}")
    print(f"   Resultado: {resultado}")


def test_expandir_query_case_insensitive():
    """Test de case insensitivity"""
    from semantic_utils import expandir_query_con_sinonimos
    
    queries = [
        "MATAR a alguien",
        "Matar a alguien",
        "matar a alguien",
    ]
    
    resultados = [expandir_query_con_sinonimos(q) for q in queries]
    
    # Todos deberían contener sinónimos (aunque el case del input varíe)
    for resultado in resultados:
        assert any(word in resultado.lower() for word in ["homicidio", "asesinato", "muerte"])
    
    print(f"✅ Expansión funciona sin importar el case:")
    for query, resultado in zip(queries, resultados):
        print(f"   {query} → {resultado}")


def test_expandir_query_preserves_context():
    """Test que verifica que el contexto original se mantiene"""
    from semantic_utils import expandir_query_con_sinonimos
    
    query = "¿Qué pena tiene robar con violencia?"
    resultado = expandir_query_con_sinonimos(query)
    
    # Debe mantener palabras del contexto
    assert "pena" in resultado
    assert "tiene" in resultado or "¿Qué" in resultado
    assert "violencia" in resultado
    
    # Y añadir sinónimos de "robar"
    assert "robar" in resultado
    assert any(word in resultado for word in ["hurto", "apropiación"])
    
    print(f"✅ Contexto preservado correctamente:")
    print(f"   Original: {query}")
    print(f"   Expandida: {resultado}")


def test_expandir_query_with_drogas():
    """Test específico para término 'drogas'"""
    from semantic_utils import expandir_query_con_sinonimos
    
    query = "tráfico de drogas"
    resultado = expandir_query_con_sinonimos(query)
    
    assert "drogas" in resultado
    assert any(word in resultado for word in ["estupefacientes", "sustancias"])
    
    print(f"✅ Término 'drogas' expandido:")
    print(f"   Original: {query}")
    print(f"   Expandida: {resultado}")


def test_expandir_query_with_violar():
    """Test específico para término 'violar'"""
    from semantic_utils import expandir_query_con_sinonimos
    
    query = "violar a una persona"
    resultado = expandir_query_con_sinonimos(query)
    
    assert "violar" in resultado
    assert any(word in resultado for word in ["violación", "agresión sexual", "abuso sexual"])
    
    print(f"✅ Término 'violar' expandido:")
    print(f"   Original: {query}")
    print(f"   Expandida: {resultado}")


def test_expandir_query_returns_string():
    """Verificar que siempre retorna un string"""
    from semantic_utils import expandir_query_con_sinonimos
    
    queries = [
        "matar",
        "robar un coche",
        "",
        "   ",
        "xyz123",
    ]
    
    for query in queries:
        resultado = expandir_query_con_sinonimos(query)
        assert isinstance(resultado, str), f"Resultado debe ser string para query: {query}"
    
    print("✅ Función siempre retorna string")


def test_sinonimos_quality():
    """Test de calidad: verificar que los sinónimos son relevantes"""
    from semantic_utils import SINONIMOS_LEGALES
    
    # Verificar que "matar" no contiene sinónimos de "robar"
    assert "hurto" not in SINONIMOS_LEGALES["matar"]
    assert "apropiación" not in SINONIMOS_LEGALES["matar"]
    
    # Verificar que "robar" no contiene sinónimos de "matar"
    assert "homicidio" not in SINONIMOS_LEGALES["robar"]
    assert "asesinato" not in SINONIMOS_LEGALES["robar"]
    
    print("✅ Calidad de sinónimos verificada (no hay contaminación cruzada)")


def test_expandir_query_performance():
    """Test de performance básico"""
    from semantic_utils import expandir_query_con_sinonimos
    import time
    
    query = "robar matar violar herir drogas"
    
    start = time.time()
    for _ in range(100):
        expandir_query_con_sinonimos(query)
    elapsed = time.time() - start
    
    # Debería procesar 100 queries en menos de 1 segundo
    assert elapsed < 1.0, f"Performance issue: {elapsed:.3f}s para 100 expansiones"
    
    print(f"✅ Performance OK: {elapsed:.3f}s para 100 expansiones ({elapsed*10:.2f}ms por query)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
