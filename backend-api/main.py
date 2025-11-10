# main.py
# Backend API para el sistema RAG de consultas legales
# Versión con Vertex AI (Google Cloud)

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# --- IMPORTS ADICIONALES PARA RAG CON VERTEX AI ---
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel
from pinecone import Pinecone
import vertexai

# Cargar las variables de entorno desde .env
load_dotenv()

# --- 1. CONFIGURACIÓN DE VERTEX AI Y PINECONE ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "resolute-return-476416-g5")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = "gemini-2.0-flash-001"  # Modelo de generación
EMBEDDING_MODEL = "text-embedding-004"  # Modelo de embeddings de Google

# Configuración de Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "codigo-penal-vertex-ai")
TOP_K_RESULTS = 20  # Aumentado a 20 para mayor cobertura de artículos largos partidos
TOP_K_MIN = 10  # Mínimo para consultas simples
TOP_K_MAX = 30  # Máximo para consultas complejas

# --- INICIALIZACIÓN DE SERVICIOS ---
print("🔧 Inicializando Vertex AI y Pinecone...")

# Variables globales para búsqueda exacta y cache
TEXTO_COMPLETO_PDF = None
ARTICULOS_CACHE = {}  # Cache: {numero_articulo: texto_completo_articulo}

try:
    # A. Inicializar Vertex AI
    vertexai.init(project=PROJECT_ID, location=REGION)
    print(f"✅ Vertex AI inicializado - Proyecto: {PROJECT_ID}, Región: {REGION}")
    
    # B. Inicializar Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    PINECONE_INDEX = pc.Index(PINECONE_INDEX_NAME)
    print(f"✅ Pinecone conectado - Índice: {PINECONE_INDEX_NAME}")

    # C. Cargar Modelos de Vertex AI
    EMBEDDING_CLIENT = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
    LLM_CLIENT = GenerativeModel(MODEL_NAME)
    print(f"✅ Modelos cargados - Embeddings: {EMBEDDING_MODEL}, LLM: {MODEL_NAME}")
    
    # D. Cargar texto completo del PDF para búsqueda exacta
    try:
        import PyPDF2
        import re
        pdf_path = "../documentos/codigo_penal.pdf"
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            texto_paginas = []
            for page in pdf_reader.pages:
                texto_paginas.append(page.extract_text())
            TEXTO_COMPLETO_PDF = "\n".join(texto_paginas)
            print(f"✅ PDF cargado para búsqueda exacta ({len(TEXTO_COMPLETO_PDF)} caracteres)")
            
        # E. Construir cache de artículos para búsqueda ultra-rápida (⚡ Mejora #1)
        print("🔄 Construyendo cache de artículos...")
        
        # Estrategia robusta: encontrar todos los inicios de artículos
        # Patrón que acepta múltiples variantes: "Artículo", "Articulo", "ARTÍCULO", etc.
        patron_inicio = r'Art[ií\xed]culo\s+(\d+(?:\s+(?:bis|ter|quater))?)\s*\.?'
        matches = list(re.finditer(patron_inicio, TEXTO_COMPLETO_PDF, re.IGNORECASE))
        
        print(f"   📋 Detectados {len(matches)} inicios de artículos en el PDF")
        
        for i, match in enumerate(matches):
            numero_articulo = match.group(1).strip()
            inicio = match.start()
            
            # Encontrar el final: siguiente artículo o fin del texto
            if i < len(matches) - 1:
                fin = matches[i + 1].start()
            else:
                fin = len(TEXTO_COMPLETO_PDF)
            
            # Extraer texto completo del artículo
            texto_articulo = TEXTO_COMPLETO_PDF[inicio:fin].strip()
            
            # Limpiar saltos de línea excesivos pero mantener estructura
            texto_articulo = re.sub(r'\n{3,}', '\n\n', texto_articulo)
            
            ARTICULOS_CACHE[numero_articulo] = texto_articulo
        
        print(f"✅ Cache construido: {len(ARTICULOS_CACHE)} artículos indexados para búsqueda instantánea")
        
        if len(ARTICULOS_CACHE) < 500:
            print(f"⚠️  ADVERTENCIA: Solo se cachearon {len(ARTICULOS_CACHE)} artículos (esperado ~600+)")
            print(f"   Primeros 10 artículos cacheados: {list(ARTICULOS_CACHE.keys())[:10]}")
            # Mostrar muestra del PDF para debug
            muestra = TEXTO_COMPLETO_PDF[10000:10500]
            print(f"   Muestra del PDF (chars 10000-10500):")
            print(f"   {repr(muestra[:200])}")
        else:
            print(f"✅ Calidad del cache verificada")
            # Verificar algunos artículos clave
            articulos_prueba = ['138', '237', '244', '142']
            encontrados = [art for art in articulos_prueba if art in ARTICULOS_CACHE]
            print(f"   Artículos de prueba ({len(encontrados)}/4): {encontrados}")
        
    except Exception as e:
        print(f"⚠️ No se pudo cargar PDF completo: {e} (búsqueda exacta deshabilitada)")
    
    print("✅ ¡Inicialización completada con éxito!")

except Exception as e:
    print(f"❌ ERROR DE INICIALIZACIÓN: {e}")
    raise


# --- 2. MODELOS DE DATOS ---
class ChatMessage(BaseModel):
    """Modelo para un mensaje en el historial de conversación"""
    role: str  # "user" o "assistant"
    content: str


class ChatRequest(BaseModel):
    pregunta: str
    historial: list[ChatMessage] = []  # ⚡ MEJORA #3: Historial conversacional


class ChatResponse(BaseModel):
    respuesta: str
    metadata: dict = None


# --- 3. INICIALIZAR LA APLICACIÓN ---
app = FastAPI(
    title="API RAG - Código Penal Español",
    description="API para consultas sobre el Código Penal usando RAG",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 4. FUNCIÓN CENTRAL DE RAG CON VERTEX AI ---

def buscar_articulo_exacto(texto_completo: str, numero_articulo: str) -> str:
    """
    Busca un artículo específico usando cache O(1) o fallback a regex O(n).
    Soporta artículos simples (142) y con sufijos (142 bis, 127 ter, etc.)
    
    ⚡ MEJORA #1: Búsqueda instantánea desde cache construido al inicio
    """
    import re
    
    # Normalizar el número de artículo
    numero_articulo = numero_articulo.strip()
    
    # ⚡ PASO 1: Buscar en cache primero (O(1) - instantáneo)
    if numero_articulo in ARTICULOS_CACHE:
        print(f"⚡ Artículo {numero_articulo} encontrado en cache (búsqueda instantánea)")
        return ARTICULOS_CACHE[numero_articulo]
    
    # PASO 2: Si no está en cache, buscar con regex (O(n) - lento)
    print(f"🔍 Artículo {numero_articulo} no en cache, buscando con regex...")
    
    # Si tiene bis/ter/quater, buscar exactamente ese artículo
    if re.search(r'\b(bis|ter|quater)\b', numero_articulo, re.IGNORECASE):
        # Buscar "Artículo 127 bis" específicamente
        pattern = rf"(?i)(art[íi]culo\s+{re.escape(numero_articulo)})[\.\s]+(.+?)(?=\n\s*Art[íi]culo\s+\d+|\Z)"
    else:
        # Buscar "Artículo N" pero NO "Artículo N bis/ter/quater"
        pattern = rf"(?i)(art[íi]culo\s+{numero_articulo})\s+(?!bis|ter|quater)(.+?)(?=\n\s*Art[íi]culo\s+\d+\s|\Z)"
    
    match = re.search(pattern, texto_completo, re.DOTALL | re.IGNORECASE)
    
    if match:
        # Incluir el encabezado completo "Artículo N"
        texto_articulo = match.group(0).strip()
        
        # Guardar en cache para futuras búsquedas
        ARTICULOS_CACHE[numero_articulo] = texto_articulo
        print(f"💾 Artículo {numero_articulo} guardado en cache")
        
        # NO truncar - devolver el artículo completo
        return texto_articulo
    
    return None


def corregir_encoding(texto: str) -> str:
    """
    Corrige problemas de encoding usando ftfy (automático y robusto).
    
    ⚡ MEJORA #2: Corrección automática con ftfy en lugar de reemplazos manuales
    """
    try:
        import ftfy
        # ftfy detecta y corrige automáticamente problemas de encoding
        texto_corregido = ftfy.fix_text(texto)
        return texto_corregido
    except ImportError:
        # Fallback a reemplazos manuales si ftfy no está disponible
        texto = texto.replace('Ã­', 'í')
        texto = texto.replace('Ã³', 'ó')
        texto = texto.replace('Ã±', 'ñ')
        texto = texto.replace('Ã¡', 'á')
        texto = texto.replace('Ã©', 'é')
        texto = texto.replace('Ãº', 'ú')
        texto = texto.replace('Ã¼', 'ü')
        texto = texto.replace('Ã¶', 'ö')
        
        # Mayúsculas
        texto = texto.replace('Ã', 'Á')
        texto = texto.replace('Ã‰', 'É')
        texto = texto.replace('Ã"', 'Ó')
        texto = texto.replace('Ãš', 'Ú')
        
        # Eliminar caracteres basura
        texto = texto.replace('Â', '')
        
        return texto


def detectar_articulos_en_chunks(chunks: list) -> dict:
    """
    Analiza chunks recuperados y detecta qué artículos aparecen y cuántas partes tienen.
    Retorna: {numero_articulo: [lista de chunks con ese artículo]}
    """
    import re
    articulos_encontrados = {}
    
    for idx, chunk in enumerate(chunks):
        texto = chunk.get('metadata', {}).get('text', '')
        
        # Buscar todos los artículos mencionados en este chunk
        matches = re.finditer(r'Art[íi]culo\s+(\d+(?:\s+bis|\s+ter|\s+quater)?)', texto, re.IGNORECASE)
        
        for match in matches:
            num_articulo = match.group(1).strip()
            
            if num_articulo not in articulos_encontrados:
                articulos_encontrados[num_articulo] = []
            
            articulos_encontrados[num_articulo].append({
                'chunk_index': idx,
                'score': chunk.get('score', 0),
                'texto': texto,
                'posicion_articulo': match.start()
            })
    
    return articulos_encontrados


def es_articulo_incompleto(texto: str) -> bool:
    """
    Detecta si un chunk contiene un artículo incompleto.
    Heurísticas:
    - Termina abruptamente (no termina en punto)
    - Contiene "..." o texto cortado
    - Tiene numeración incompleta (1., 2., pero no cierra)
    """
    import re
    
    texto_limpio = texto.strip()
    
    # Heurística 1: No termina en punto ni en paréntesis de cierre
    if not texto_limpio.endswith(('.', ')', '»', '"')):
        return True
    
    # Heurística 2: Contiene indicadores de truncado
    if '...' in texto_limpio or '[truncado]' in texto_limpio.lower():
        return True
    
    # Heurística 3: Tiene numeración sin cerrar (ej: "1. xxx 2. xxx 3." pero sin texto después del 3)
    numeros = re.findall(r'\n\s*(\d+)\.\s+', texto_limpio)
    if len(numeros) >= 2:
        ultimo_numero = numeros[-1]
        # Verificar si después del último número hay texto sustancial
        patron = rf'{ultimo_numero}\.\s+(.+)$'
        match = re.search(patron, texto_limpio, re.DOTALL)
        if match and len(match.group(1).strip()) < 20:
            return True
    
    return False


def reconstruir_articulos_completos(articulos_detectados: dict, chunks_originales: list) -> dict:
    """
    Para artículos que aparecen partidos, intenta reconstruirlos usando:
    1. Combinación de múltiples chunks si están disponibles
    2. Búsqueda instantánea en ARTICULOS_CACHE (O(1))
    
    Retorna: {numero_articulo: texto_completo_reconstruido}
    """
    articulos_reconstruidos = {}
    
    for num_articulo, partes in articulos_detectados.items():
        # Ordenar partes por posición en el texto (usando chunk_index como proxy)
        partes_ordenadas = sorted(partes, key=lambda x: x['chunk_index'])
        
        # CASO 1: Solo hay 1 parte
        if len(partes_ordenadas) == 1:
            texto = partes_ordenadas[0]['texto']
            
            # Verificar si parece incompleto
            if es_articulo_incompleto(texto):
                print(f"  ⚠️ Art. {num_articulo} parece incompleto (1 chunk) - buscando en cache...")
                
                # ⚡ MEJORA #1: Búsqueda instantánea en cache O(1)
                if num_articulo in ARTICULOS_CACHE:
                    articulo_completo = ARTICULOS_CACHE[num_articulo]
                    articulos_reconstruidos[num_articulo] = {
                        'texto': corregir_encoding(articulo_completo),
                        'metodo': 'cache_instantaneo',
                        'completo': True
                    }
                    print(f"  ✅ Art. {num_articulo} reconstruido desde cache (O(1))")
                    continue
                
                # Si no se pudo reconstruir, usar lo que hay pero marcarlo como incompleto
                articulos_reconstruidos[num_articulo] = {
                    'texto': corregir_encoding(texto),
                    'metodo': 'chunk_unico',
                    'completo': False
                }
            else:
                # Parece completo
                articulos_reconstruidos[num_articulo] = {
                    'texto': corregir_encoding(texto),
                    'metodo': 'chunk_unico',
                    'completo': True
                }
        
        # CASO 2: Múltiples partes - intentar combinarlas
        else:
            print(f"  🔄 Art. {num_articulo} encontrado en {len(partes_ordenadas)} chunks - combinando...")
            
            # Combinar textos evitando duplicados
            textos_combinados = []
            texto_previo = ""
            
            for parte in partes_ordenadas:
                texto_actual = parte['texto']
                
                # Evitar duplicar texto si hay overlap
                if texto_previo:
                    # Buscar overlap entre final de texto_previo y inicio de texto_actual
                    overlap_length = min(200, len(texto_previo), len(texto_actual))
                    for i in range(overlap_length, 0, -1):
                        if texto_previo[-i:] == texto_actual[:i]:
                            texto_actual = texto_actual[i:]
                            break
                
                textos_combinados.append(texto_actual)
                texto_previo = texto_actual
            
            texto_combinado = "".join(textos_combinados)
            
            # Verificar si la combinación parece completa
            if es_articulo_incompleto(texto_combinado):
                print(f"  ⚠️ Art. {num_articulo} combinado aún parece incompleto - buscando en cache...")
                
                # ⚡ MEJORA #1: Fallback a búsqueda instantánea en cache
                if num_articulo in ARTICULOS_CACHE:
                    articulo_completo = ARTICULOS_CACHE[num_articulo]
                    articulos_reconstruidos[num_articulo] = {
                        'texto': corregir_encoding(articulo_completo),
                        'metodo': 'cache_instantaneo_fallback',
                        'completo': True
                    }
                    print(f"  ✅ Art. {num_articulo} reconstruido desde cache (O(1) fallback)")
                    continue
            
            articulos_reconstruidos[num_articulo] = {
                'texto': corregir_encoding(texto_combinado),
                'metodo': f'combinacion_{len(partes_ordenadas)}_chunks',
                'completo': not es_articulo_incompleto(texto_combinado)
            }
    
    return articulos_reconstruidos


def decidir_estrategia_busqueda(query: str, numero_articulo: str = None) -> dict:
    """
    Decide dinámicamente qué estrategia de búsqueda usar basándose en la consulta.
    
    Retorna:
    {
        'top_k': int,  # Cuántos resultados recuperar
        'usar_reconstruccion': bool,  # Si aplicar post-procesamiento
        'razon': str  # Explicación de la decisión
    }
    """
    import re
    
    # ESTRATEGIA 1: Consulta de artículo específico simple
    if numero_articulo and not re.search(r'\b(y|o|con|sin|además|también)\b', query, re.IGNORECASE):
        return {
            'top_k': TOP_K_MIN,  # 10 suficiente, irá a búsqueda exacta
            'usar_reconstruccion': False,
            'razon': 'Consulta de artículo específico - búsqueda exacta'
        }
    
    # ESTRATEGIA 2: Consulta compleja con múltiples conceptos
    palabras = query.split()
    tiene_conectores = bool(re.search(r'\b(y|o|además|también|con|más)\b', query, re.IGNORECASE))
    
    if len(palabras) > 8 or tiene_conectores:
        return {
            'top_k': TOP_K_MAX,  # 30 para capturar más contexto
            'usar_reconstruccion': True,
            'razon': 'Consulta compleja multi-concepto - máxima cobertura + reconstrucción'
        }
    
    # ESTRATEGIA 3: Consulta conceptual media (default)
    return {
        'top_k': TOP_K_RESULTS,  # 20 (balance)
        'usar_reconstruccion': True,
        'razon': 'Consulta conceptual estándar - cobertura media + reconstrucción'
    }


def generate_rag_response(query: str, historial: list = None):
    """
    Sistema RAG híbrido con búsqueda exacta + vector search + memoria conversacional.
    
    ⚡ MEJORA #3: Soporte para historial conversacional
    
    1. Enriquece la consulta con contexto del historial (si aplica)
    2. Detecta si es consulta de artículo específico
    3. Intenta búsqueda exacta con regex primero
    4. Si no encuentra, usa RAG con embeddings
    5. Corrige encoding en todos los resultados
    """
    import re  # Importar al principio para usar en todo el scope
    import time  # Para medir tiempo de respuesta
    
    start_time = time.time()  # Iniciar contador de tiempo
    
    try:
        print(f"\n{'='*80}")
        print(f"📨 CONSULTA: {query}")
        if historial:
            print(f"💬 Historial: {len(historial)} mensajes previos")
        print(f"{'='*80}")

        # --- PASO 0.5: ENRIQUECER CONSULTA CON CONTEXTO CONVERSACIONAL ---
        query_enriquecida = query
        nota_correccion = ""  # Variable para almacenar instrucciones de corrección
        
        if historial and len(historial) > 0:
            print(f"🔍 DEBUG: Analizando si es consulta de seguimiento...")
            
            # Detectar si es una consulta de seguimiento
            palabras_seguimiento = ['y', 'también', 'además', 'qué más', 'otra', 'ese', 'esa', 'esos', 'esas', 'cuál', 'pena', 'entonces', 'pero']
            
            # Palabras que indican nuevo caso (resetear contexto)
            palabras_nuevo_caso = ['nuevo caso', 'otra consulta', 'ahora sobre', 'pregunta nueva', 'cambio de tema']
            
            # Palabras que indican corrección/refinamiento
            palabras_correccion = ['no', 'mejor', 'prefiero', 'creo que', 'en realidad', 'debería ser', 
                                  'en vez de', 'en lugar de', 'más bien', 'corrección', 'correción',
                                  'no es', 'sería mejor', 'más apropiado', 'en su lugar']
            
            query_lower = query.lower().strip()
            print(f"   Query lowercase: '{query_lower}'")
            print(f"   Número de palabras: {len(query.split())}")
            
            # Si menciona explícitamente nuevo caso, no enriquecer
            es_nuevo_caso = any(palabra in query_lower for palabra in palabras_nuevo_caso)
            print(f"   Es nuevo caso: {es_nuevo_caso}")
            
            # Detectar si menciona artículo
            menciona_articulo = bool(re.search(r'\b(?:art[íi]culo|art\.?)\s*\d+', query, re.IGNORECASE))
            print(f"   Menciona artículo: {menciona_articulo}")
            
            # PRIORIDAD 1: Detectar si es corrección/refinamiento
            es_correccion = any(palabra in query_lower for palabra in palabras_correccion) and menciona_articulo
            print(f"   Es corrección: {es_correccion}")
            
            if es_correccion:
                print(f"🔄 CORRECCIÓN DETECTADA - Usuario propone artículo alternativo")
                
                # Extraer el artículo propuesto
                match_articulo_propuesto = re.search(r'art[íi]culo\s*(\d+(?:\s+(?:bis|ter|quater))?)', query, re.IGNORECASE)
                if match_articulo_propuesto:
                    articulo_propuesto = match_articulo_propuesto.group(1).strip()
                    print(f"   📌 Artículo propuesto por usuario: {articulo_propuesto}")
                    
                    # Obtener contexto de qué artículos se mencionaron antes
                    articulos_previos = []
                    for msg in reversed(historial):
                        if msg.role == "assistant":
                            # Buscar artículos mencionados en la respuesta anterior
                            matches_previos = re.finditer(r'Art[íi]culo\s*(\d+)', msg.content, re.IGNORECASE)
                            articulos_previos = [m.group(1) for m in matches_previos]
                            if articulos_previos:
                                print(f"   📋 Artículos en respuesta anterior: {articulos_previos[:3]}")
                                break
                    
                    # Crear nota de corrección para Gemini
                    nota_correccion = f"""
**🔄 CORRECCIÓN/REFINAMIENTO DEL USUARIO:**
El usuario está sugiriendo que el **artículo {articulo_propuesto}** sería más apropiado.

**⚠️ IMPORTANTE - NO ACEPTES AUTOMÁTICAMENTE:**
El usuario puede estar equivocado. Debes EVALUAR primero si su sugerencia es correcta.

**PASO 1 - EVALUAR OBLIGATORIAMENTE:**
Antes de responder, analiza críticamente:

1. **Hechos del caso original:** {historial[0].content if historial else "N/A"}
2. **Artículos previamente identificados como correctos:** {articulos_previos[:3] if articulos_previos else "N/A"}
3. **Artículo propuesto por el usuario:** {articulo_propuesto}

**PREGÚNTATE:**
- ¿El artículo {articulo_propuesto} realmente encaja con los HECHOS descritos en el caso?
- ¿Los requisitos legales del artículo {articulo_propuesto} se cumplen en este caso?
- ¿O el usuario está confundiendo conceptos? (ejemplo: doloso vs imprudente, fuerza vs intimidación)

**PASO 2 - RESPONDER SEGÚN TU EVALUACIÓN:**

**OPCIÓN A - SI EL ARTÍCULO {articulo_propuesto} ES CORRECTO:**
✅ El usuario tiene razón → Responde:
"Tienes razón, el artículo {articulo_propuesto} [nombre del delito] es el más apropiado porque [breve razón]."
Luego proporciona ficha legal completa del artículo {articulo_propuesto}.

**OPCIÓN B - SI EL ARTÍCULO {articulo_propuesto} NO ES CORRECTO:**
❌ El usuario se equivoca → Responde:
"Entiendo que sugieres el artículo {articulo_propuesto} ([nombre del delito que propone]), sin embargo, este artículo no sería el más apropiado para este caso porque [razón específica: qué requisito NO se cumple].

Según los hechos descritos [mencionar hechos relevantes], el artículo correcto sería el **artículo [X]** ([nombre del delito correcto]) porque [razón específica: qué requisito SÍ se cumple].

A continuación te muestro ambos artículos para que puedas comparar:

[Muestra AMBOS artículos con sus diferencias clave resaltadas]"

**EJEMPLOS DE CORRECCIÓN:**

✅ **Ejemplo cuando usuario ACIERTA:**
Usuario sugiere: art. 237 en caso de robo con fuerza
Respuesta: "Tienes razón, el artículo 237 sobre robo con fuerza en las cosas es el apropiado porque los hechos indican escalamiento..."

❌ **Ejemplo cuando usuario SE EQUIVOCA:**
Usuario sugiere: art. 138 (homicidio doloso) en caso de atropello imprudente
Respuesta: "Entiendo que sugieres el artículo 138 (homicidio doloso), sin embargo, este artículo requiere que la muerte se cause con **intención deliberada**, lo cual no se cumple en un atropello por imprudencia.

Según los hechos descritos (atropello por imprudencia grave), el artículo correcto sería el **artículo 142** (homicidio imprudente) porque..."

**NO ASUMAS QUE EL USUARIO SIEMPRE TIENE RAZÓN. EVALÚA CRÍTICAMENTE.**
"""
                    
                    # No enriquecer con contexto previo en correcciones - el usuario ya sabe qué quiere
                    query_enriquecida = query
                    print(f"   ✅ Corrección procesada - enfocándose en artículo {articulo_propuesto}")
                
            elif es_nuevo_caso:
                print(f"🆕 Nuevo caso detectado - no se enriquece con historial")
            else:
                # Criterios para considerar seguimiento:
                # 1. Empieza con palabra de seguimiento (muy común)
                # 2. Es una consulta corta (< 10 palabras) con palabra de seguimiento
                # 3. No menciona explícitamente un artículo nuevo
                
                empieza_con_seguimiento = any(query_lower.startswith(palabra) for palabra in palabras_seguimiento)
                contiene_seguimiento = any(palabra in query_lower for palabra in palabras_seguimiento)
                es_corta = len(query.split()) < 10
                
                print(f"   Empieza con seguimiento: {empieza_con_seguimiento}")
                print(f"   Contiene seguimiento: {contiene_seguimiento}")
                print(f"   Es corta (<10 palabras): {es_corta}")
                
                # No es seguimiento si menciona explícitamente un artículo
                menciona_articulo = bool(re.search(r'\b(?:art[íi]culo|art\.?)\s*\d+', query, re.IGNORECASE))
                print(f"   Menciona artículo: {menciona_articulo}")
                
                es_seguimiento = (empieza_con_seguimiento or (contiene_seguimiento and es_corta)) and not menciona_articulo
                print(f"   ✅ RESULTADO: Es seguimiento = {es_seguimiento}")
                
                if es_seguimiento:
                    # Tomar el último contexto del usuario para entender el tema
                    contexto_previo = ""
                    
                    print(f"   🔍 Buscando contexto previo en historial ({len(historial)} mensajes)...")
                    # Buscar en historial la última pregunta del usuario (no la respuesta del bot)
                    for i, msg in enumerate(reversed(historial)):
                        print(f"      Mensaje {i}: role='{msg.role}', content='{msg.content[:50]}...'")
                        if msg.role == "user":
                            contexto_previo = msg.content
                            print(f"      ✓ Contexto encontrado!")
                            break
                    
                    if contexto_previo:
                        query_enriquecida = f"{contexto_previo} {query}"
                        print(f"🔗 Consulta detectada como seguimiento")
                        print(f"📝 Contexto previo: {contexto_previo[:80]}...")
                        print(f"🔍 Consulta enriquecida: {query_enriquecida[:150]}...")
                    else:
                        print(f"⚠️ Seguimiento detectado pero sin contexto previo")
                else:
                    print(f"   ℹ️  No se detectó como seguimiento - usando consulta original")

        # --- PASO 1: DETECTAR NÚMERO DE ARTÍCULO O RANGO ---
        articulo_pattern = r'\b(?:art[íi]culo|art\.?)\s*(\d+(?:\s+bis|\s+ter|\s+quater)?)\b'
        solo_numero_pattern = r'^\s*(\d+(?:\s+bis|\s+ter|\s+quater)?)\s*$'
        
        # 🆕 MEJORA #4: Detectar rangos de artículos (ej: "artículos 138 a 142", "del 237 al 244")
        rango_pattern_1 = r'\b(?:art[íi]culos?|arts?\.?)\s*(\d+)\s*(?:a|al|hasta|-)\s*(?:art[íi]culo|art\.?)?\s*(\d+)\b'
        rango_pattern_2 = r'\b(?:del|desde)\s*(?:art[íi]culo|art\.?)?\s*(\d+)\s*(?:a|al|hasta)\s*(?:art[íi]culo|art\.?)?\s*(\d+)\b'
        rango_pattern_3 = r'\b(\d+)\s*(?:a|al|-)\s*(\d+)\s*$'  # Solo números al final
        
        numero_articulo = None
        rango_articulos = None
        
        # Primero verificar si es un rango
        match_rango = (re.search(rango_pattern_1, query_enriquecida, re.IGNORECASE) or 
                       re.search(rango_pattern_2, query_enriquecida, re.IGNORECASE) or
                       re.search(rango_pattern_3, query_enriquecida, re.IGNORECASE))
        
        if match_rango:
            inicio = int(match_rango.group(1))
            fin = int(match_rango.group(2))
            
            # Validar que el rango sea razonable (máximo 20 artículos)
            if inicio < fin and (fin - inicio) <= 20:
                rango_articulos = (inicio, fin)
                print(f"📚 Rango de artículos detectado: {inicio} a {fin} ({fin - inicio + 1} artículos)")
            else:
                print(f"⚠️ Rango inválido o demasiado amplio: {inicio} a {fin}")
        
        # Si no hay rango, buscar artículo individual
        if not rango_articulos:
            match_articulo = re.search(articulo_pattern, query_enriquecida, re.IGNORECASE)
            match_numero = re.match(solo_numero_pattern, query_enriquecida)
            
            if match_articulo:
                numero_articulo = match_articulo.group(1)
                print(f"🎯 Artículo detectado (patrón completo): {numero_articulo}")
            elif match_numero:
                numero_articulo = match_numero.group(1)
                print(f"🎯 Artículo detectado (solo número): {numero_articulo}")
            else:
                print(f"ℹ️  No se detectó número de artículo en la query")
        
        # --- PASO 2: BÚSQUEDA EXACTA INSTANTÁNEA ---
        # ⚡ MEJORA #1: Usar cache O(1) para artículos individuales
        # 📚 MEJORA #4: Usar cache para rangos de artículos
        # EXCEPCIÓN: Si es una corrección, NO usar cache directo - pasar por Gemini con contexto
        
        # 📚 Caso 1: RANGO DE ARTÍCULOS
        if rango_articulos:
            inicio, fin = rango_articulos
            articulos_encontrados = []
            articulos_faltantes = []
            articulos_incompletos = []
            
            print(f"📚 Buscando rango de artículos {inicio} a {fin} en cache...")
            
            for num in range(inicio, fin + 1):
                num_str = str(num)
                if num_str in ARTICULOS_CACHE:
                    texto = ARTICULOS_CACHE[num_str]
                    
                    # 🔍 Verificar si el artículo está completo
                    if es_articulo_incompleto(texto):
                        print(f"   ⚠️ Art. {num_str} está incompleto en cache")
                        articulos_incompletos.append(num_str)
                    else:
                        articulos_encontrados.append((num_str, texto))
                else:
                    articulos_faltantes.append(num_str)
            
            print(f"✅ Completos: {len(articulos_encontrados)}/{fin - inicio + 1} artículos")
            if articulos_faltantes:
                print(f"⚠️ No encontrados: {articulos_faltantes}")
            if articulos_incompletos:
                print(f"⚠️ Incompletos (pasarán por RAG): {articulos_incompletos}")
            
            # Si hay artículos incompletos, NO usar cache directo - pasar por RAG
            if articulos_incompletos:
                print(f"🔄 Rango contiene {len(articulos_incompletos)} artículo(s) incompleto(s) - usando RAG para reconstruir")
                # NO retornar aquí - dejar que caiga en el flujo de RAG normal
            elif articulos_encontrados:
                # Solo si TODOS los artículos están completos, responder desde cache
                respuesta_rango = f"**Artículos {inicio} a {fin} del Código Penal**\n\n"
                
                for num, texto in articulos_encontrados:
                    texto_corregido = corregir_encoding(texto)
                    respuesta_rango += f"**Artículo {num}**\n\n{texto_corregido}\n\n{'='*70}\n\n"
                
                if articulos_faltantes:
                    respuesta_rango += f"\n⚠️ **Nota:** Los siguientes artículos no se encontraron en la base de datos: {', '.join(articulos_faltantes)}"
                
                print(f"⚡ Respuesta de rango generada ({len(respuesta_rango)} caracteres)")
                return {
                    "respuesta": respuesta_rango,
                    "metadata": {
                        "num_fragmentos": len(articulos_encontrados),
                        "tiene_contexto": True,
                        "modelo": "Cache instantáneo - Rango",
                        "embedding_model": "N/A",
                        "metodo": "cache_rango",
                        "fuentes": [f"Artículo {num}" for num, _ in articulos_encontrados],
                        "tiempo_respuesta": time.time() - start_time
                    }
                }
        
        # 🎯 Caso 2: ARTÍCULO INDIVIDUAL
        if numero_articulo:
            print(f"🔑 Buscando '{numero_articulo}' en cache...")
            print(f"📋 Cache tiene {len(ARTICULOS_CACHE)} artículos")
            print(f"🔍 Artículo en cache: {numero_articulo in ARTICULOS_CACHE}")
            
        # Solo usar cache directo si NO es corrección
        if numero_articulo and numero_articulo in ARTICULOS_CACHE and not nota_correccion:
            print(f"⚡ Búsqueda instantánea en cache para artículo {numero_articulo}...")
            texto_exacto = ARTICULOS_CACHE[numero_articulo]
            
            if texto_exacto:
                print(f"✅ ¡Artículo {numero_articulo} encontrado en cache (O(1))!")
                
                # 🔍 Verificar si el artículo en cache está completo
                if es_articulo_incompleto(texto_exacto):
                    print(f"⚠️  Artículo {numero_articulo} en cache parece INCOMPLETO - pasando por RAG para reconstrucción...")
                    # NO retornar aquí - dejar que caiga en el flujo de RAG normal
                else:
                    texto_corregido = corregir_encoding(texto_exacto)
                    
                    # Responder directamente sin pasar por Gemini si es texto razonable
                    # Aumentado a 4000 caracteres (la mayoría de artículos caben)
                    if len(texto_corregido) < 4000:
                        respuesta_final = f"**Artículo {numero_articulo}**\n\n{texto_corregido}"
                        return {
                            "respuesta": respuesta_final,
                            "metadata": {
                                "num_fragmentos": 1,
                                "tiene_contexto": True,
                                "modelo": "Cache instantáneo (sin LLM)",
                                "embedding_model": "N/A",
                                "metodo": "cache_O(1)"
                            }
                        }
                    else:
                        # Si es muy largo (>4000 chars), pasar por Gemini para formatear mejor
                        prompt = f"""Eres un asistente legal especializado en el Código Penal español.

El usuario preguntó: "{query}"

Aquí está el texto LITERAL y COMPLETO del artículo encontrado:

{texto_corregido}

INSTRUCCIONES:
1. Responde con el texto COMPLETO del artículo tal como aparece
2. NO resumas ni parafrasees - cita el texto literal
3. Organiza el contenido de forma clara usando formato Markdown
4. Mantén TODOS los apartados, números y subapartados
5. Usa el formato: **Artículo [número].** seguido del texto completo

Responde ahora:"""

                        response = LLM_CLIENT.generate_content(prompt)
                        return {
                            "respuesta": response.text,
                            "metadata": {
                                "num_fragmentos": 1,
                                "tiene_contexto": True,
                                "modelo": MODEL_NAME,
                                "embedding_model": "N/A",
                                "metodo": "exact_match_formatted"
                            }
                        }

        # --- PASO 3: DECIDIR ESTRATEGIA INTELIGENTE ---
        estrategia = decidir_estrategia_busqueda(query, numero_articulo)
        print(f"🧠 Estrategia seleccionada: {estrategia['razon']}")
        print(f"   - Top K: {estrategia['top_k']}")
        print(f"   - Reconstrucción: {estrategia['usar_reconstruccion']}")
        
        # --- PASO 4: ENRIQUECER QUERY (si no hubo match exacto) ---
        if numero_articulo:
            query_enriquecida_embedding = (
                f"Contenido literal del Código Penal español "
                f"Artículo {numero_articulo} delito pena castigo texto completo"
            )
            print(f"🔄 Query para embedding: {query_enriquecida_embedding}")
        else:
            # IMPORTANTE: Mantener la query enriquecida con contexto conversacional
            # que se creó en PASO 0.5 (no sobrescribir)
            query_enriquecida_embedding = query_enriquecida
            if query_enriquecida != query:
                print(f"🔄 Usando query enriquecida con contexto conversacional")

        # --- PASO 5: GENERAR EMBEDDING ---
        print("🔢 Generando embedding con Vertex AI...")
        embeddings = EMBEDDING_CLIENT.get_embeddings([query_enriquecida_embedding])
        query_vector = embeddings[0].values
        print(f"✅ Embedding generado: {len(query_vector)} dimensiones")

        # --- PASO 6: BÚSQUEDA VECTORIAL EN PINECONE (con Top K dinámico) ---
        top_k_dinamico = estrategia['top_k']
        print(f"🔍 Buscando en Pinecone (TOP_K={top_k_dinamico})...")
        results = PINECONE_INDEX.query(
            vector=query_vector,
            top_k=top_k_dinamico,
            include_metadata=True
        )
        # --- PASO 6: BÚSQUEDA VECTORIAL EN PINECONE (con Top K dinámico) ---
        top_k_dinamico = estrategia['top_k']
        print(f"🔍 Buscando en Pinecone (TOP_K={top_k_dinamico})...")
        results = PINECONE_INDEX.query(
            vector=query_vector,
            top_k=top_k_dinamico,
            include_metadata=True
        )

        # --- PASO 7: FILTRADO ADAPTATIVO ---
        umbral = 0.35 if numero_articulo else 0.45
        print(f"📊 Aplicando umbral adaptativo: {umbral}")
        
        chunks_relevantes = []
        for match in results['matches']:
            score = match.get('score', 0)
            print(f"  📊 Match con score: {score:.3f}")
            
            if score > umbral:
                chunks_relevantes.append(match)
                print(f"  ✓ Chunk aceptado (score: {score:.3f})")

        if not chunks_relevantes:
            print("⚠️ No hay resultados relevantes después del filtrado")
            return {
                "respuesta": "Lo siento, no encontré información relevante en el Código Penal sobre tu consulta. ¿Podrías reformularla o ser más específico?",
                "metadata": {
                    "num_fragmentos": 0,
                    "tiene_contexto": False,
                    "modelo": MODEL_NAME,
                    "embedding_model": EMBEDDING_MODEL,
                    "metodo": "rag_vector_search"
                }
            }

        # --- PASO 8: POST-PROCESAMIENTO INTELIGENTE (si está habilitado) ---
        if estrategia['usar_reconstruccion']:
            print(f"\n🔧 Aplicando reconstrucción inteligente de artículos...")
            
            # Detectar artículos en los chunks
            articulos_detectados = detectar_articulos_en_chunks(chunks_relevantes)
            print(f"📋 Artículos detectados: {list(articulos_detectados.keys())}")
            
            # Reconstruir artículos completos
            articulos_reconstruidos = reconstruir_articulos_completos(articulos_detectados, chunks_relevantes)
            
            # Construir contexto usando artículos reconstruidos + chunks originales
            contexto_parts = []
            articulos_ya_incluidos = set()
            
            # Primero, agregar artículos reconstruidos
            for num_art, info in articulos_reconstruidos.items():
                if info['completo'] or info['metodo'].startswith('busqueda_exacta'):
                    contexto_parts.append(
                        f"[Artículo {num_art} - Reconstruido ({info['metodo']})]"
                        f"\n{info['texto']}"
                    )
                    articulos_ya_incluidos.add(num_art)
                    print(f"  ✅ Art. {num_art} agregado como reconstruido ({info['metodo']})")
            
            # Luego, agregar chunks que no sean de artículos ya reconstruidos
            for match in chunks_relevantes:
                texto = match.get('metadata', {}).get('text', '')
                score = match.get('score', 0)
                
                # Verificar si este chunk es de un artículo ya incluido
                es_duplicado = False
                for num_art in articulos_ya_incluidos:
                    if f"Artículo {num_art}" in texto or f"Art. {num_art}" in texto:
                        es_duplicado = True
                        break
                
                if not es_duplicado:
                    texto_corregido = corregir_encoding(texto)
                    contexto_parts.append(
                        f"[Fragmento del Código Penal - Relevancia: {score:.2f}]"
                        f"\n{texto_corregido}"
                    )
            
            contexto = "\n\n---\n\n".join(contexto_parts)
            num_matches = len(contexto_parts)
            articulos_completos = sum(1 for info in articulos_reconstruidos.values() if info['completo'])
            articulos_incompletos = len(articulos_reconstruidos) - articulos_completos
            
            print(f"📋 Contexto final: {num_matches} fragmentos")
            print(f"   - {articulos_completos} artículos completos reconstruidos")
            print(f"   - {articulos_incompletos} artículos parciales")
            print(f"   - Total: {len(contexto)} caracteres")
        
        else:
            # Sin reconstrucción - método original
            print(f"\n📋 Construcción de contexto sin reconstrucción...")
            contexto_parts = []
            for match in chunks_relevantes:
                text = match.get('metadata', {}).get('text', '')
                score = match.get('score', 0)
                if text:
                    texto_corregido = corregir_encoding(text)
                    contexto_parts.append(f"[Fragmento del Código Penal - Relevancia: {score:.2f}]\n{texto_corregido}")
            
            contexto = "\n\n---\n\n".join(contexto_parts)
            num_matches = len(contexto_parts)
            print(f"📋 Contexto construido: {num_matches} fragmentos ({len(contexto)} caracteres)")

        # --- PASO 9: GENERAR RESPUESTA CON GEMINI ---
        
        # Ajustar límites de concisión según si es consulta de seguimiento
        es_seguimiento = query_enriquecida != query  # Si se enriqueció, es seguimiento
        
        # Si hay nota de corrección, usarla (tiene prioridad sobre seguimiento)
        if nota_correccion:
            nota_contextual = nota_correccion
            # En correcciones, mantener límites normales (el usuario sabe qué quiere)
            limite_articulos = "1-3 artículos"
            limite_max_articulos = "5 artículos"
            limite_penas = "2-5 penas"
            limite_max_penas = "8 penas"
        elif es_seguimiento:
            limite_articulos = "4-8 artículos"
            limite_max_articulos = "12 artículos"
            limite_penas = "4-12 penas"
            limite_max_penas = "12 penas"
            
            # Extraer la última consulta del usuario del historial
            ultima_consulta_usuario = ""
            for msg in reversed(historial):
                if msg.role == "user":
                    ultima_consulta_usuario = msg.content
                    break
            
            nota_seguimiento = f"""
**⚠️ CONTEXTO CONVERSACIONAL - CONSULTA DE SEGUIMIENTO:**
El usuario está continuando una conversación previa. Esta consulta hace referencia a múltiples aspectos:

- **Consulta anterior:** "{ultima_consulta_usuario}"
- **Consulta actual:** "{query}"
- **CONSULTA COMPLETA INTERPRETADA:** "{query_enriquecida}"

**INSTRUCCIÓN CRÍTICA:** 
Debes analizar y responder sobre TODOS los delitos/aspectos mencionados en la "CONSULTA COMPLETA INTERPRETADA" con IGUAL importancia y detalle. No priorices solo el último tema mencionado - dedica espacio y artículos similares a CADA aspecto del caso.

Ejemplo: Si la consulta completa es "robo de coche y además atropello mortal", debes explicar AMBOS delitos (robo + atropello) con similar nivel de detalle, artículos y penas.
"""
            nota_contextual = nota_seguimiento
        else:
            limite_articulos = "3-5 artículos"
            limite_max_articulos = "6 artículos"
            limite_penas = "3-6 penas"
            limite_max_penas = "6 penas"
            nota_contextual = ""
        
        prompt = f"""Actúa como un asistente jurídico especializado en Derecho Penal español. Tu conocimiento se basa exclusivamente en el texto oficial del Código Penal.

{nota_contextual}

CONSULTA DEL USUARIO:
{query_enriquecida}

CONTEXTO RECUPERADO ({num_matches} fragmentos del Código Penal):
{contexto}

═══════════════════════════════════════════════════════════════

PROTOCOLO DE RESPUESTA:

**1. Si el usuario pregunta por un artículo específico** (ej: "142", "artículo 138"):
   - Muestra el texto COMPLETO y LITERAL del artículo
   - Formato: **Artículo [número].** seguido del texto completo
   - NO resumas, cita el texto tal como aparece en el Código Penal
   - NO apliques el formato de ficha estructurada

**2. Si es una consulta conceptual sobre un delito o situación** (ej: "violación a menor", "robo de coche con accidente"):
   Genera una ficha legal completa, clara y visualmente ordenada con este formato:

---
## **[TÍTULO DEL DELITO]**

### **Artículos relevantes:**
- **Art. [número]** – [nombre o resumen breve del tipo penal]
- **Art. [número]** – [nombre o resumen breve del tipo penal]

**LÍMITES DE CONCISIÓN:**
- **Recomendado: {limite_articulos}** (los más directamente relevantes)
- **Máximo: {limite_max_articulos}** (solo si el caso es muy complejo con múltiples delitos en concurso)
- Prioriza CALIDAD sobre CANTIDAD: mejor 3 artículos bien explicados que 6 superficiales

### **Penas aplicables:**
- **Art. [número]:** [pena concreta: prisión de X a Y años, multa de X a Y meses, inhabilitación, etc.]
- **Art. [número]:** [pena concreta con todas las condiciones aplicables]
- **Agravantes/Atenuantes:** [factores que modifican la pena si aplican]

**LÍMITES DE CONCISIÓN:**
- **Recomendado: {limite_penas}** (las principales para cada artículo relevante)
- **Máximo: {limite_max_penas}** (si hay varios delitos acumulables o múltiples agravantes)
- Si hay muchos artículos, agrupa las penas similares en lugar de listarlas todas

**IMPORTANTE:** Usa SIEMPRE números para expresar las penas (ej: "de 1 a 6 meses", "de 2 a 5 años"), NUNCA escribas los números en letra (NO "de uno a seis meses").

### **Explicación legal:**
Redacta un párrafo claro y conciso explicando:
- Cómo encaja el delito en el Código Penal
- Cuándo se aplicaría cada artículo según el contexto (violencia, imprudencia, dolo, etc.)
- Qué factores agravan o atenúan la pena
- Si hay dolo (intención) o imprudencia
- Si el delito no aparece directamente, qué artículos lo cubren por analogía

### **Resumen final:**
**→** [Resumen corto tipo fórmula: delito + agravantes + artículos principales]  
**→** [Rango de penas aproximado: prisión de X a Y años + multa + inhabilitación + otras consecuencias]

**IMPORTANTE:** En el resumen también usa números para las penas (ej: "de 2 a 5 años"), no los escribas en letra.

---

**3. Reglas de estilo y contenido:**
   - Mantén un tono profesional, directo y visualmente limpio
   - Prioriza la claridad: cada punto debe poder leerse en 10-15 segundos
   - Usa terminología legal precisa (NO uses "aproximadamente", "más o menos")
   - Diferencia claramente entre dolo (intención) e imprudencia
   - SIEMPRE menciona las penas exactas (prisión, multa, inhabilitación)
   - Basa tu respuesta EXCLUSIVAMENTE en el contexto proporcionado
   - No incluyas notas doctrinales, jurisprudencia ni referencias externas
   - Si falta información clave, indícalo claramente

═══════════════════════════════════════════════════════════════

EJEMPLO DE FICHA BIEN ESTRUCTURADA (respetando límites de concisión):

---
## **Agresión con cuchillo sin causar la muerte**

### **Artículos relevantes:**
- **Art. 147** – Lesiones dolosas con instrumento peligroso
- **Art. 148** – Agravantes por uso de armas o medios peligrosos
- **Art. 20** – Eximentes (legítima defensa, estado de necesidad)

(Nota: Solo 3 artículos - los más relevantes. NO agregues más a menos que sea estrictamente necesario)

### **Penas aplicables:**
- **Art. 147.1:** Prisión de 3 a 6 meses o multa de 6 a 12 meses (lesiones que requieren tratamiento médico)
- **Art. 148.1:** Prisión de 2 a 5 años (si se usan armas, instrumentos peligrosos o hay ensañamiento)
- **Agravantes:** Si hay alevosía, premeditación o la víctima es vulnerable, la pena puede elevarse al tipo superior

(Nota: Solo 3 penas principales. Si hubiera más artículos, agrúpalas en lugar de listar todas)

### **Explicación legal:**
El uso de un cuchillo en una agresión se considera empleo de instrumento peligroso, lo que agrava automáticamente las lesiones según el Art. 148. Si las lesiones requieren tratamiento médico o quirúrgico (más allá de primera asistencia), se aplica el Art. 147. La intención dolosa es clave: si hubo premeditación, la pena es más severa. Si no se causó la muerte, no aplican los tipos de homicidio (Arts. 138-140), pero si hubo intención de matar y esta no se consumó, podría configurarse tentativa de homicidio (Arts. 62 + 138).

### **Resumen final:**
**→** Agresión con cuchillo + lesiones = Arts. 147 + 148 = delito doloso contra la integridad física  
**→** Penas: Prisión de 2 a 5 años + posible indemnización a la víctima + antecedentes penales

(Nota: Fíjate que las penas se escriben con NÚMEROS: "2 a 5 años", no "dos a cinco años")

---

RESPONDE AHORA:"""

        print("⚖️ Generando respuesta con Gemini (Vertex AI)...")
        response = LLM_CLIENT.generate_content(prompt)
        
        print("✅ Respuesta generada exitosamente")
        return {
            "respuesta": response.text,
            "metadata": {
                "num_fragmentos": num_matches,
                "tiene_contexto": True,
                "modelo": MODEL_NAME,
                "embedding_model": EMBEDDING_MODEL,
                "metodo": "rag_vector_search"
            }
        }

    except Exception as e:
        print(f"❌ Error en el proceso RAG: {e}")
        import traceback
        traceback.print_exc()
        return {
            "respuesta": f"Disculpa, ha ocurrido un error al consultar la base de datos de documentos: {str(e)}",
            "metadata": {
                "error": True,
                "mensaje_error": str(e),
                "num_fragmentos": 0,
                "tiene_contexto": False
            }
        }
# --- 5. ENDPOINT PRINCIPAL DE CHAT ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat_request(request: ChatRequest):
    """
    Endpoint principal que procesa la pregunta del usuario y devuelve una respuesta
    basada en el contexto del Código Penal usando Vertex AI.
    
    ⚡ MEJORA #3: Soporte para historial conversacional
    """
    pregunta_usuario = request.pregunta
    historial = request.historial if hasattr(request, 'historial') else []
    
    print(f"\n{'='*60}")
    print(f"📨 Nueva petición recibida")
    if historial:
        print(f"💬 Con historial de {len(historial)} mensajes")
    print(f"{'='*60}")
    
    # Llamar a la función RAG con Vertex AI, pasando el historial
    resultado = generate_rag_response(pregunta_usuario, historial)
    
    return ChatResponse(
        respuesta=resultado["respuesta"],
        metadata={
            "pregunta": pregunta_usuario,
            "tieneContexto": resultado["metadata"].get("tiene_contexto", False),
            "numeroResultados": resultado["metadata"].get("num_fragmentos", 0),
            "modelo": resultado["metadata"].get("modelo", MODEL_NAME),
            "dominio": "codigo-penal-espanol",
            "proveedor": "Vertex AI (Google Cloud)"
        }
    )


# --- 6. ENDPOINT DE SALUD ---
@app.get("/health")
async def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return {
        "status": "healthy",
        "service": "RAG API - Código Penal (Vertex AI)",
        "version": "2.0.0",
        "provider": "Google Cloud Vertex AI",
        "models": {
            "llm": MODEL_NAME,
            "embeddings": EMBEDDING_MODEL
        }
    }


# --- 7. ENDPOINT DE INFORMACIÓN ---
@app.get("/")
async def root():
    """Información básica de la API"""
    return {
        "message": "API RAG - Código Penal Español (Vertex AI)",
        "version": "2.0.0",
        "provider": "Google Cloud Platform",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)",
            "docs": "/docs (Documentación interactiva)"
        },
        "models": {
            "generacion": MODEL_NAME,
            "embeddings": EMBEDDING_MODEL
        }
    }

