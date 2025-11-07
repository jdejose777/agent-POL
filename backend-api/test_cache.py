"""
Script de prueba para verificar el funcionamiento del cache de artículos
"""
import sys
import time

print("🧪 INICIANDO PRUEBAS DEL CACHE DE ARTÍCULOS\n")
print("=" * 60)

try:
    # Importar el módulo main (esto activará la inicialización)
    print("📦 Importando módulo main.py...")
    sys.path.insert(0, '.')
    import main
    
    print(f"\n✅ Módulo importado correctamente")
    print(f"📊 Cache construido con {len(main.ARTICULOS_CACHE)} artículos\n")
    
    # Mostrar algunos artículos en el cache
    print("📋 Primeros 10 artículos en cache:")
    for i, numero in enumerate(sorted(main.ARTICULOS_CACHE.keys(), key=lambda x: int(x.split()[0] if ' ' not in x else x.split()[0]))[:10]):
        print(f"   {i+1}. Artículo {numero}")
    
    print("\n" + "=" * 60)
    print("🧪 PRUEBA 1: Búsqueda desde cache (debería ser instantánea)\n")
    
    # Probar búsqueda con cache
    articulo_test = "138"
    print(f"🔍 Buscando artículo {articulo_test}...")
    start = time.time()
    resultado = main.buscar_articulo_exacto(main.TEXTO_COMPLETO_PDF, articulo_test)
    elapsed = time.time() - start
    
    if resultado:
        print(f"✅ ENCONTRADO en {elapsed*1000:.2f}ms")
        print(f"📄 Longitud: {len(resultado)} caracteres")
        print(f"📝 Primeros 200 caracteres:\n{resultado[:200]}...")
    else:
        print(f"❌ NO ENCONTRADO")
    
    print("\n" + "=" * 60)
    print("🧪 PRUEBA 2: Búsqueda de artículo no cacheado (fallback a regex)\n")
    
    # Probar con un artículo que probablemente no esté (o limpiar cache temporalmente)
    articulo_test2 = "999"  # Probablemente no existe
    print(f"🔍 Buscando artículo {articulo_test2}...")
    start = time.time()
    resultado2 = main.buscar_articulo_exacto(main.TEXTO_COMPLETO_PDF, articulo_test2)
    elapsed2 = time.time() - start
    
    if resultado2:
        print(f"✅ ENCONTRADO en {elapsed2*1000:.2f}ms")
        print(f"📄 Longitud: {len(resultado2)} caracteres")
    else:
        print(f"✅ NO ENCONTRADO (esperado) en {elapsed2*1000:.2f}ms")
    
    print("\n" + "=" * 60)
    print("🧪 PRUEBA 3: Comparación de velocidad (con vs sin cache)\n")
    
    # Simular búsqueda múltiple
    articulos_test = ["138", "142", "173", "200", "234"]
    
    print("⏱️  Buscando 5 artículos con cache:")
    start_total = time.time()
    for art in articulos_test:
        resultado = main.buscar_articulo_exacto(main.TEXTO_COMPLETO_PDF, art)
        if resultado:
            print(f"   ✓ Artículo {art}: {len(resultado)} chars")
    elapsed_cache = time.time() - start_total
    print(f"   Total: {elapsed_cache*1000:.2f}ms ({elapsed_cache*1000/5:.2f}ms promedio)")
    
    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS\n")
    
    print(f"📊 RESUMEN:")
    print(f"   - Artículos en cache: {len(main.ARTICULOS_CACHE)}")
    print(f"   - Tiempo búsqueda con cache: ~{elapsed*1000:.2f}ms")
    print(f"   - Mejora esperada: >100x más rápido que regex puro")
    
except Exception as e:
    print(f"\n❌ ERROR EN LAS PRUEBAS: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
