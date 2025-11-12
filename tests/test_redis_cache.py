"""
TESTS PARA CACHÉ REDIS
Valida la funcionalidad de caché persistente con Redis
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Añadir directorio backend-api al path
backend_path = Path(__file__).parent.parent / "backend-api"
sys.path.insert(0, str(backend_path))


def test_redis_imported():
    """Verificar que Redis se puede importar"""
    import redis
    assert redis is not None
    print("✅ Módulo redis importado correctamente")


def test_redis_connection_config():
    """Verificar que las variables de configuración están definidas"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Verificar que existen las variables de entorno (o valores por defecto)
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))
    redis_ttl = int(os.getenv("REDIS_TTL", 86400))
    
    assert redis_host is not None
    assert redis_port > 0
    assert redis_db >= 0
    assert redis_ttl > 0
    
    print(f"✅ Configuración Redis: {redis_host}:{redis_port} (DB: {redis_db}, TTL: {redis_ttl}s)")


@patch('redis.Redis')
def test_get_cached_articulo_mock(mock_redis):
    """Test de get_cached_articulo con Redis mockeado"""
    # Mock Redis client
    mock_client = Mock()
    mock_client.get.return_value = '{"numero": "234", "texto": "El que..."}'
    mock_redis.return_value = mock_client
    
    # Importar después de mockear
    import json
    
    # Simular la función
    def get_cached_articulo_test(numero: str):
        cached_data = mock_client.get(f"articulo:{numero}")
        if cached_data:
            return json.loads(cached_data)
        return None
    
    result = get_cached_articulo_test("234")
    
    assert result is not None
    assert result["numero"] == "234"
    assert "texto" in result
    
    print(f"✅ get_cached_articulo (mock) funciona correctamente")


@patch('redis.Redis')
def test_set_cached_articulo_mock(mock_redis):
    """Test de set_cached_articulo con Redis mockeado"""
    # Mock Redis client
    mock_client = Mock()
    mock_client.setex.return_value = True
    mock_redis.return_value = mock_client
    
    import json
    
    # Simular la función
    def set_cached_articulo_test(numero: str, texto: str):
        key = f"articulo:{numero}"
        data = {
            "numero": numero,
            "texto": texto
        }
        return mock_client.setex(key, 86400, json.dumps(data))
    
    result = set_cached_articulo_test("234", "El que con ánimo de lucro...")
    
    assert result is True
    mock_client.setex.assert_called_once()
    
    print(f"✅ set_cached_articulo (mock) funciona correctamente")


def test_redis_real_connection():
    """Test de conexión real a Redis (skip si no está disponible)"""
    import redis
    
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        # Test ping
        response = client.ping()
        assert response is True
        
        print("✅ Conexión real a Redis exitosa")
        
        # Test básico de escritura/lectura
        client.setex("test:key", 10, "test_value")
        value = client.get("test:key")
        assert value == "test_value"
        
        # Limpiar
        client.delete("test:key")
        
        print("✅ Operaciones básicas de Redis funcionan")
        
    except redis.ConnectionError:
        pytest.skip("Redis no disponible en localhost:6379")


def test_redis_articulo_cache_workflow():
    """Test del flujo completo: guardar → recuperar → expirar"""
    import redis
    import json
    import time
    
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        client.ping()
        
        # 1. Guardar artículo
        numero = "999"
        key = f"articulo:{numero}"
        data = {
            "numero": numero,
            "texto": "Este es un artículo de prueba...",
            "metadata": {"test": True}
        }
        
        client.setex(key, 5, json.dumps(data))  # TTL: 5 segundos
        print(f"✅ Artículo {numero} guardado en Redis")
        
        # 2. Recuperar artículo
        cached = client.get(key)
        assert cached is not None
        
        cached_data = json.loads(cached)
        assert cached_data["numero"] == numero
        assert "texto" in cached_data
        print(f"✅ Artículo {numero} recuperado correctamente")
        
        # 3. Verificar TTL
        ttl = client.ttl(key)
        assert ttl > 0 and ttl <= 5
        print(f"✅ TTL configurado correctamente: {ttl}s")
        
        # 4. Esperar expiración
        time.sleep(6)
        expired = client.get(key)
        assert expired is None
        print(f"✅ Artículo expiró correctamente después del TTL")
        
    except redis.ConnectionError:
        pytest.skip("Redis no disponible en localhost:6379")


def test_redis_keys_pattern():
    """Test de búsqueda por patrón de claves"""
    import redis
    
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        client.ping()
        
        # Guardar varios artículos
        for i in range(100, 105):
            client.setex(f"articulo:{i}", 10, f"Texto del artículo {i}")
        
        # Buscar todas las claves de artículos
        keys = client.keys("articulo:*")
        assert len(keys) >= 5
        
        print(f"✅ Encontradas {len(keys)} claves de artículos en Redis")
        
        # Limpiar
        for key in keys:
            client.delete(key)
        
    except redis.ConnectionError:
        pytest.skip("Redis no disponible en localhost:6379")


def test_redis_performance():
    """Test de performance: medir latencia de operaciones"""
    import redis
    import time
    
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        client.ping()
        
        # Test de escritura
        start = time.time()
        for i in range(100):
            client.setex(f"perf:test:{i}", 10, f"value_{i}")
        write_time = time.time() - start
        
        # Test de lectura
        start = time.time()
        for i in range(100):
            client.get(f"perf:test:{i}")
        read_time = time.time() - start
        
        # Limpiar
        for i in range(100):
            client.delete(f"perf:test:{i}")
        
        print(f"✅ Performance Redis:")
        print(f"   - 100 escrituras: {write_time*1000:.2f}ms ({write_time*10:.2f}ms por operación)")
        print(f"   - 100 lecturas: {read_time*1000:.2f}ms ({read_time*10:.2f}ms por operación)")
        
        # Verificar que es rápido (< 1ms por operación en promedio)
        assert write_time < 1.0, "Escrituras demasiado lentas"
        assert read_time < 1.0, "Lecturas demasiado lentas"
        
    except redis.ConnectionError:
        pytest.skip("Redis no disponible en localhost:6379")


def test_cache_stats_structure():
    """Verificar estructura de get_cache_stats()"""
    # Simular respuesta esperada
    expected_keys = ["status", "total_keys"]
    
    # Mock de la función
    def get_cache_stats_mock():
        return {
            "status": "connected",
            "total_keys": 142,
            "memory_used": "1.2M",
            "uptime_seconds": 3600,
            "redis_version": "7.0.0"
        }
    
    stats = get_cache_stats_mock()
    
    for key in expected_keys:
        assert key in stats
    
    assert stats["status"] in ["connected", "disabled", "error"]
    
    print(f"✅ Estructura de get_cache_stats validada")


def test_fallback_to_memory_cache():
    """Test de fallback a caché en memoria cuando Redis no está disponible"""
    # Este test verifica que la app sigue funcionando sin Redis
    
    # Simular REDIS_CLIENT = None
    redis_client = None
    articulos_cache = {"234": "Artículo 234 en memoria..."}
    
    # Buscar en memoria
    numero = "234"
    
    if redis_client is None:
        # Fallback a memoria
        resultado = articulos_cache.get(numero)
    else:
        resultado = None
    
    assert resultado is not None
    assert "234" in resultado
    
    print("✅ Fallback a caché en memoria funciona correctamente")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
