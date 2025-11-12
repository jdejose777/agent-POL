"""
🧪 SCRIPT INTERACTIVO PARA PROBAR REDIS
Herramienta de pruebas visual para el caché de artículos
"""
import sys
sys.path.insert(0, 'backend-api')

import time
from main import (
    REDIS_CLIENT, 
    get_cached_articulo, 
    set_cached_articulo, 
    get_cache_stats,
    ARTICULOS_CACHE
)

def print_header(text):
    """Imprimir encabezado bonito"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_section(text):
    """Imprimir sección"""
    print(f"\n{'─'*60}")
    print(f"  {text}")
    print(f"{'─'*60}")

def test_1_conexion():
    """Test 1: Verificar conexión a Redis"""
    print_header("TEST 1: CONEXIÓN A REDIS")
    
    if not REDIS_CLIENT:
        print("❌ Redis no está conectado")
        return False
    
    try:
        response = REDIS_CLIENT.ping()
        if response:
            print("✅ Redis responde correctamente")
            print(f"   Comando: PING")
            print(f"   Respuesta: PONG")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_2_estadisticas():
    """Test 2: Ver estadísticas de Redis"""
    print_header("TEST 2: ESTADÍSTICAS DE REDIS")
    
    stats = get_cache_stats()
    
    print(f"\n📊 Información del servidor Redis:")
    print(f"   • Estado: {stats.get('status', 'unknown')}")
    print(f"   • Versión: {stats.get('redis_version', 'unknown')}")
    print(f"   • Uptime: {stats.get('uptime_seconds', 0)} segundos")
    print(f"   • Memoria usada: {stats.get('memory_used', 'N/A')}")
    print(f"   • Total de claves: {stats.get('total_keys', 0)}")

def test_3_guardar_articulo():
    """Test 3: Guardar un artículo en Redis"""
    print_header("TEST 3: GUARDAR ARTÍCULO EN REDIS")
    
    # Seleccionar un artículo de prueba
    articulo_num = "138"
    
    # Obtener texto del caché en memoria (si existe)
    texto = ARTICULOS_CACHE.get(articulo_num, f"Artículo {articulo_num} - Contenido de prueba para testing de Redis...")
    
    print(f"\n📝 Guardando Artículo {articulo_num}...")
    print(f"   Tamaño del texto: {len(texto)} caracteres")
    
    # Medir tiempo de escritura
    start = time.time()
    success = set_cached_articulo(articulo_num, texto, {"test": True, "timestamp": str(time.time())})
    elapsed = (time.time() - start) * 1000
    
    if success:
        print(f"✅ Guardado exitoso en {elapsed:.2f}ms")
        print(f"   Clave: articulo:{articulo_num}")
        print(f"   TTL: 86400 segundos (24 horas)")
    else:
        print("❌ Error al guardar")

def test_4_recuperar_articulo():
    """Test 4: Recuperar un artículo de Redis"""
    print_header("TEST 4: RECUPERAR ARTÍCULO DE REDIS")
    
    articulo_num = "138"
    
    print(f"\n🔍 Buscando Artículo {articulo_num} en Redis...")
    
    # Medir tiempo de lectura
    start = time.time()
    cached = get_cached_articulo(articulo_num)
    elapsed = (time.time() - start) * 1000
    
    if cached:
        print(f"✅ Encontrado en {elapsed:.2f}ms")
        print(f"\n📄 Contenido:")
        print(f"   • Número: {cached.get('numero', 'N/A')}")
        print(f"   • Texto (primeros 150 chars):")
        print(f"     {cached.get('texto', '')[:150]}...")
        print(f"   • Metadata: {cached.get('metadata', {})}")
    else:
        print("❌ No encontrado en caché")

def test_5_performance():
    """Test 5: Medir performance de escritura/lectura"""
    print_header("TEST 5: TEST DE PERFORMANCE")
    
    num_operaciones = 20
    
    # Test de escritura
    print(f"\n⚡ Escribiendo {num_operaciones} artículos...")
    start = time.time()
    for i in range(200, 200 + num_operaciones):
        texto = f"Artículo {i} - Contenido de prueba número {i} para medir performance de Redis"
        set_cached_articulo(str(i), texto, {"test": True, "batch": True})
    write_time = time.time() - start
    
    print(f"✅ Escritura completada:")
    print(f"   • Tiempo total: {write_time*1000:.2f}ms")
    print(f"   • Tiempo por artículo: {(write_time/num_operaciones)*1000:.2f}ms")
    print(f"   • Throughput: {num_operaciones/write_time:.2f} ops/seg")
    
    # Test de lectura
    print(f"\n⚡ Leyendo {num_operaciones} artículos...")
    start = time.time()
    for i in range(200, 200 + num_operaciones):
        get_cached_articulo(str(i))
    read_time = time.time() - start
    
    print(f"✅ Lectura completada:")
    print(f"   • Tiempo total: {read_time*1000:.2f}ms")
    print(f"   • Tiempo por artículo: {(read_time/num_operaciones)*1000:.2f}ms")
    print(f"   • Throughput: {num_operaciones/read_time:.2f} ops/seg")
    
    # Comparación
    print(f"\n📊 Comparación:")
    if write_time > read_time:
        ratio = write_time / read_time
        print(f"   • Lectura es {ratio:.2f}x más rápida que escritura")
    else:
        ratio = read_time / write_time
        print(f"   • Escritura es {ratio:.2f}x más rápida que lectura")
    
    # Limpiar
    print(f"\n🧹 Limpiando artículos de prueba...")
    for i in range(200, 200 + num_operaciones):
        REDIS_CLIENT.delete(f"articulo:{i}")
    print("✅ Limpieza completada")

def test_6_ttl():
    """Test 6: Probar expiración automática (TTL)"""
    print_header("TEST 6: TTL (TIME TO LIVE)")
    
    test_key = "articulo:999"
    
    print("\n⏰ Creando artículo con TTL de 5 segundos...")
    REDIS_CLIENT.setex(test_key, 5, '{"numero": "999", "texto": "Test de TTL"}')
    print("✅ Artículo creado")
    
    # Verificar que existe
    print("\n🔍 Verificando existencia...")
    if REDIS_CLIENT.exists(test_key):
        ttl = REDIS_CLIENT.ttl(test_key)
        print(f"✅ Artículo existe (TTL: {ttl}s restantes)")
    
    print("\n⏳ Esperando 6 segundos para que expire...")
    for i in range(6):
        time.sleep(1)
        ttl = REDIS_CLIENT.ttl(test_key)
        if ttl > 0:
            print(f"   {i+1}s - TTL restante: {ttl}s")
        else:
            print(f"   {i+1}s - Artículo ha expirado")
            break
    
    # Verificar que ya no existe
    print("\n🔍 Verificando después de expiración...")
    if not REDIS_CLIENT.exists(test_key):
        print("✅ Artículo expiró correctamente")
    else:
        print("⚠️ Artículo aún existe (no debería)")

def test_7_multiples_articulos():
    """Test 7: Cachear múltiples artículos y listarlos"""
    print_header("TEST 7: MÚLTIPLES ARTÍCULOS")
    
    articulos_test = ["100", "150", "200", "250", "300"]
    
    print(f"\n📦 Cacheando {len(articulos_test)} artículos...")
    for num in articulos_test:
        texto = ARTICULOS_CACHE.get(num, f"Artículo {num} de prueba")
        set_cached_articulo(num, texto[:200], {"categoria": "test"})  # Solo primeros 200 chars
    print("✅ Artículos cacheados")
    
    print("\n🔍 Listando artículos en Redis:")
    keys = REDIS_CLIENT.keys("articulo:*")
    print(f"   Total de artículos en caché: {len(keys)}")
    
    if len(keys) <= 10:
        print("\n   📋 Artículos encontrados:")
        for key in sorted(keys):
            numero = key.replace("articulo:", "")
            print(f"      • Artículo {numero}")
    else:
        print(f"\n   📋 Mostrando primeros 10 artículos:")
        for key in sorted(keys)[:10]:
            numero = key.replace("articulo:", "")
            print(f"      • Artículo {numero}")
        print(f"      ... y {len(keys) - 10} más")

def test_8_limpiar_cache():
    """Test 8: Limpiar todo el caché"""
    print_header("TEST 8: LIMPIAR CACHÉ")
    
    # Contar claves antes
    keys_before = len(REDIS_CLIENT.keys("articulo:*"))
    print(f"\n📊 Artículos en caché antes: {keys_before}")
    
    if keys_before > 0:
        respuesta = input("\n⚠️  ¿Quieres limpiar TODOS los artículos del caché? (s/n): ")
        
        if respuesta.lower() == 's':
            print("\n🧹 Limpiando caché...")
            keys = REDIS_CLIENT.keys("articulo:*")
            for key in keys:
                REDIS_CLIENT.delete(key)
            
            keys_after = len(REDIS_CLIENT.keys("articulo:*"))
            print(f"✅ Caché limpiado")
            print(f"   • Artículos eliminados: {keys_before - keys_after}")
            print(f"   • Artículos restantes: {keys_after}")
        else:
            print("❌ Limpieza cancelada")
    else:
        print("ℹ️  No hay artículos en el caché")

def menu_principal():
    """Menú principal interactivo"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║          🧪 REDIS CACHE - HERRAMIENTA DE PRUEBAS         ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    tests = {
        "1": ("Verificar conexión a Redis", test_1_conexion),
        "2": ("Ver estadísticas de Redis", test_2_estadisticas),
        "3": ("Guardar artículo en Redis", test_3_guardar_articulo),
        "4": ("Recuperar artículo de Redis", test_4_recuperar_articulo),
        "5": ("Test de performance (20 artículos)", test_5_performance),
        "6": ("Test de TTL (expiración)", test_6_ttl),
        "7": ("Cachear múltiples artículos", test_7_multiples_articulos),
        "8": ("Limpiar caché", test_8_limpiar_cache),
        "9": ("Ejecutar TODOS los tests", None),
        "0": ("Salir", None)
    }
    
    while True:
        print("\n┌───────────────────────────────────────────────────────┐")
        print("│  MENÚ DE TESTS:                                       │")
        print("└───────────────────────────────────────────────────────┘")
        
        for key, (description, _) in tests.items():
            print(f"  {key}. {description}")
        
        print()
        opcion = input("Selecciona una opción: ").strip()
        
        if opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        elif opcion == "9":
            # Ejecutar todos los tests
            for key in ["1", "2", "3", "4", "5", "7"]:  # Skip TTL y limpiar
                tests[key][1]()
                time.sleep(1)
            print_header("✅ TODOS LOS TESTS COMPLETADOS")
        elif opcion in tests and tests[opcion][1]:
            tests[opcion][1]()
        else:
            print("❌ Opción no válida")
        
        if opcion != "0":
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    try:
        # Verificar que Redis está disponible
        if not REDIS_CLIENT:
            print("❌ Redis no está conectado")
            print("   Por favor, inicia Redis primero:")
            print("   docker run -d -p 6379:6379 --name redis-cache redis:latest")
            sys.exit(1)
        
        menu_principal()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
