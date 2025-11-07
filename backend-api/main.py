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

# Variable global para texto completo del PDF (para búsqueda exacta)
TEXTO_COMPLETO_PDF = None

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
        pdf_path = "../documentos/codigo_penal.pdf"
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            texto_paginas = []
            for page in pdf_reader.pages:
                texto_paginas.append(page.extract_text())
            TEXTO_COMPLETO_PDF = "\n".join(texto_paginas)
            print(f"✅ PDF cargado para búsqueda exacta ({len(TEXTO_COMPLETO_PDF)} caracteres)")
    except Exception as e:
        print(f"⚠️ No se pudo cargar PDF completo: {e} (búsqueda exacta deshabilitada)")
    
    print("✅ ¡Inicialización completada con éxito!")

except Exception as e:
    print(f"❌ ERROR DE INICIALIZACIÓN: {e}")
    raise


# --- 2. MODELOS DE DATOS ---
class ChatRequest(BaseModel):
    pregunta: str


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
    Busca un artículo específico en el texto completo del PDF usando regex.
    Soporta artículos simples (142) y con sufijos (142 bis, 127 ter, etc.)
    """
    import re
    
    # Normalizar el número de artículo (puede venir como "127 bis" o "127")
    numero_articulo = numero_articulo.strip()
    
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
        
        # NO truncar - devolver el artículo completo
        # Si es muy largo, el flujo principal decidirá si pasarlo por Gemini
        return texto_articulo
    
    return None


def corregir_encoding(texto: str) -> str:
    """
    Corrige problemas de encoding comunes en el PDF del Código Penal
    """
    # Reemplazos básicos de caracteres corruptos
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
    2. Búsqueda exacta en PDF completo si es necesario
    
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
                print(f"  ⚠️ Art. {num_articulo} parece incompleto (1 chunk) - buscando en PDF completo...")
                
                # Intentar búsqueda exacta en PDF completo
                if TEXTO_COMPLETO_PDF:
                    articulo_completo = buscar_articulo_exacto(TEXTO_COMPLETO_PDF, num_articulo)
                    if articulo_completo:
                        articulos_reconstruidos[num_articulo] = {
                            'texto': corregir_encoding(articulo_completo),
                            'metodo': 'busqueda_exacta_pdf',
                            'completo': True
                        }
                        print(f"  ✅ Art. {num_articulo} reconstruido desde PDF completo")
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
                print(f"  ⚠️ Art. {num_articulo} combinado aún parece incompleto - buscando en PDF...")
                
                # Fallback a búsqueda exacta
                if TEXTO_COMPLETO_PDF:
                    articulo_completo = buscar_articulo_exacto(TEXTO_COMPLETO_PDF, num_articulo)
                    if articulo_completo:
                        articulos_reconstruidos[num_articulo] = {
                            'texto': corregir_encoding(articulo_completo),
                            'metodo': 'busqueda_exacta_pdf_fallback',
                            'completo': True
                        }
                        print(f"  ✅ Art. {num_articulo} reconstruido desde PDF completo (fallback)")
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


def generate_rag_response(query: str):
    """
    Sistema RAG híbrido con búsqueda exacta + vector search.
    
    1. Detecta si es consulta de artículo específico
    2. Intenta búsqueda exacta con regex primero
    3. Si no encuentra, usa RAG con embeddings
    4. Corrige encoding en todos los resultados
    """
    try:
        print(f"\n{'='*80}")
        print(f"📨 CONSULTA: {query}")
        print(f"{'='*80}")

        # --- PASO 1: DETECTAR NÚMERO DE ARTÍCULO ---
        import re
        articulo_pattern = r'\b(?:art[íi]culo|art\.?)\s*(\d+(?:\s+bis|\s+ter|\s+quater)?)\b'
        solo_numero_pattern = r'^\s*(\d+(?:\s+bis|\s+ter|\s+quater)?)\s*$'
        
        numero_articulo = None
        match_articulo = re.search(articulo_pattern, query, re.IGNORECASE)
        match_numero = re.match(solo_numero_pattern, query)
        
        if match_articulo:
            numero_articulo = match_articulo.group(1)
            print(f"🎯 Artículo detectado (patrón completo): {numero_articulo}")
        elif match_numero:
            numero_articulo = match_numero.group(1)
            print(f"🎯 Artículo detectado (solo número): {numero_articulo}")
        
        # DEBUG: Verificar estado del PDF
        if numero_articulo:
            print(f"📄 TEXTO_COMPLETO_PDF disponible: {TEXTO_COMPLETO_PDF is not None}")
            if TEXTO_COMPLETO_PDF:
                print(f"📄 Tamaño del PDF: {len(TEXTO_COMPLETO_PDF)} caracteres")
        
        # --- PASO 2: BÚSQUEDA EXACTA (si hay número de artículo y PDF cargado) ---
        if numero_articulo and TEXTO_COMPLETO_PDF:
            print(f"🔍 Intentando búsqueda exacta para artículo {numero_articulo}...")
            texto_exacto = buscar_articulo_exacto(TEXTO_COMPLETO_PDF, numero_articulo)
            
            if texto_exacto:
                print(f"✅ ¡Artículo {numero_articulo} encontrado con búsqueda exacta!")
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
                            "modelo": "Búsqueda exacta (sin LLM)",
                            "embedding_model": "N/A",
                            "metodo": "exact_match"
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
            query_enriquecida = (
                f"Contenido literal del Código Penal español "
                f"Artículo {numero_articulo} delito pena castigo texto completo"
            )
            print(f"🔄 Query enriquecida: {query_enriquecida}")
        else:
            query_enriquecida = query

        # --- PASO 5: GENERAR EMBEDDING ---
        print("🔢 Generando embedding con Vertex AI...")
        embeddings = EMBEDDING_CLIENT.get_embeddings([query_enriquecida])
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
        prompt = f"""Actúa como un asistente jurídico especializado en Derecho Penal español. Tu conocimiento se basa exclusivamente en el texto oficial del Código Penal.

CONSULTA DEL USUARIO:
{query}

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
- **Recomendado: 3-5 artículos** (los más directamente relevantes)
- **Máximo: 6 artículos** (solo si el caso es muy complejo con múltiples delitos en concurso)
- Prioriza CALIDAD sobre CANTIDAD: mejor 3 artículos bien explicados que 6 superficiales

### **Penas aplicables:**
- **Art. [número]:** [pena concreta: prisión de X a Y años, multa de X a Y meses, inhabilitación, etc.]
- **Art. [número]:** [pena concreta con todas las condiciones aplicables]
- **Agravantes/Atenuantes:** [factores que modifican la pena si aplican]

**LÍMITES DE CONCISIÓN:**
- **Recomendado: 3-6 penas** (las principales para cada artículo relevante)
- **Máximo: 6 penas** (si hay varios delitos acumulables o múltiples agravantes)
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
    """
    pregunta_usuario = request.pregunta
    print(f"\n{'='*60}")
    print(f"� Nueva petición recibida")
    print(f"{'='*60}")
    
    # Llamar a la función RAG con Vertex AI
    resultado = generate_rag_response(pregunta_usuario)
    
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

