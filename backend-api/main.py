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
TOP_K_RESULTS = 10  # Aumentado para capturar más contexto y encontrar artículos específicos

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

        # --- PASO 3: ENRIQUECER QUERY (si no hubo match exacto) ---
        if numero_articulo:
            query_enriquecida = (
                f"Contenido literal del Código Penal español "
                f"Artículo {numero_articulo} delito pena castigo texto completo"
            )
            print(f"🔄 Query enriquecida: {query_enriquecida}")
        else:
            query_enriquecida = query

        # --- PASO 4: GENERAR EMBEDDING ---
        print("🔢 Generando embedding con Vertex AI...")
        embeddings = EMBEDDING_CLIENT.get_embeddings([query_enriquecida])
        query_vector = embeddings[0].values
        print(f"✅ Embedding generado: {len(query_vector)} dimensiones")

        # --- PASO 5: BÚSQUEDA VECTORIAL EN PINECONE ---
        print(f"🔍 Buscando en Pinecone (TOP_K={TOP_K_RESULTS})...")
        results = PINECONE_INDEX.query(
            vector=query_vector,
            top_k=TOP_K_RESULTS,
            include_metadata=True
        )

        # --- PASO 6: FILTRADO ADAPTATIVO ---
        umbral = 0.35 if numero_articulo else 0.45
        print(f"📊 Aplicando umbral adaptativo: {umbral}")
        
        contexto_parts = []
        for match in results['matches']:
            score = match.get('score', 0)
            print(f"  📊 Match con score: {score:.3f}")
            
            if score > umbral:
                text = match.get('metadata', {}).get('text', '')
                if text:
                    # Corregir encoding del texto recuperado
                    texto_corregido = corregir_encoding(text)
                    contexto_parts.append(f"[Fragmento del Código Penal - Relevancia: {score:.2f}]\n{texto_corregido}")
                    print(f"  ✓ Fragmento aceptado (score: {score:.3f})")

        if not contexto_parts:
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

        contexto = "\n\n---\n\n".join(contexto_parts)
        num_matches = len(contexto_parts)
        print(f"📋 Contexto construido: {num_matches} fragmentos ({len(contexto)} caracteres)")

        # --- PASO 7: GENERAR RESPUESTA CON GEMINI ---
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
(máximo 5 artículos, los más relacionados con la consulta)

### **Penas aplicables:**
- **Art. [número]:** [pena concreta: prisión de X a Y años, multa de X a Y meses, inhabilitación, etc.]
- **Art. [número]:** [pena concreta con todas las condiciones aplicables]
- **Agravantes/Atenuantes:** [factores que modifican la pena si aplican]

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

EJEMPLO DE FICHA BIEN ESTRUCTURADA:

---
## **Agresión con cuchillo sin causar la muerte**

### **Artículos relevantes:**
- **Art. 147** – Lesiones dolosas con instrumento peligroso
- **Art. 148** – Agravantes por uso de armas o medios peligrosos
- **Art. 20** – Eximentes (legítima defensa, estado de necesidad)

### **Penas aplicables:**
- **Art. 147.1:** Prisión de 3 a 6 meses o multa de 6 a 12 meses (lesiones que requieren tratamiento médico)
- **Art. 148.1:** Prisión de 2 a 5 años (si se usan armas, instrumentos peligrosos o hay ensañamiento)
- **Agravantes:** Si hay alevosía, premeditación o la víctima es vulnerable, la pena puede elevarse al tipo superior

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

