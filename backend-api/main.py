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
    Evita confusiones entre art. X y art. X bis/ter/quater.
    """
    import re
    
    # Patrón mejorado: el PDF usa "Artículo N \n" (espacio + salto), no punto
    # Busca "Artículo 142 " (con espacio) pero NO "Artículo 142 bis"
    pattern = rf"(?i)(art[íi]culo\s+{numero_articulo})\s+(?!bis|ter|quater)(.+?)(?=\n\s*Art[íi]culo\s+\d+\s|\Z)"
    
    match = re.search(pattern, texto_completo, re.DOTALL | re.IGNORECASE)
    
    if match:
        # Incluir el encabezado completo "Artículo N"
        texto_articulo = match.group(0).strip()
        
        # Limitar a 2000 caracteres
        if len(texto_articulo) > 2000:
            texto_articulo = texto_articulo[:2000] + "\n\n[...texto truncado...]"
        
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
        articulo_pattern = r'\b(?:art[íi]culo|art\.?)\s*(\d+)\b'
        solo_numero_pattern = r'^\s*(\d+)\s*$'
        
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
                
                # Responder directamente sin pasar por Gemini si es texto literal
                if len(texto_corregido) < 2000:  # Si es razonablemente corto
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
                    # Si es muy largo, pasar por Gemini para formatear
                    prompt = f"""Eres un asistente legal especializado en el Código Penal español.

El usuario preguntó: "{query}"

Aquí está el texto LITERAL del artículo encontrado:

{texto_corregido}

Instrucciones:
1. Responde con el texto COMPLETO del artículo tal como aparece
2. NO resumas ni parafrasees - cita el texto literal
3. Si el artículo es largo, preséntalo de forma organizada pero completa
4. Usa formato Markdown para mejor legibilidad

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
        prompt = f"""Eres un asistente jurídico especializado en derecho penal español. 
Tu tarea es proporcionar información del Código Penal español basándote EXCLUSIVAMENTE en el contexto que te proporcionan.

PREGUNTA DEL USUARIO:
{query}

CONTEXTO RECUPERADO ({num_matches} fragmentos del Código Penal):
{contexto}

INSTRUCCIONES CRÍTICAS:
1. **Si el usuario menciona un número de artículo** (como "138", "artículo 138", "art. 138"):
   - Busca ESE número de artículo en el contexto recuperado
   - Si lo encuentras, muéstralo COMPLETO con su texto literal
   - Usa el formato: **Artículo [número].** seguido del texto
   
2. **Si el contexto contiene el artículo solicitado**: Muéstralo aunque sea parcial, indicando si está incompleto

3. **Si no encuentras el artículo en el contexto**: Di claramente "El artículo X no se encuentra en los fragmentos recuperados"

4. Para preguntas conceptuales (ej: "¿Qué es el homicidio?"):
   - Identifica el artículo relevante en el contexto
   - Cita su contenido literal
   - Añade una explicación breve

FORMATO DE RESPUESTA:
---
**Artículo [número].**
[Texto literal del Código Penal tal como aparece en el contexto]

📘 [Explicación breve solo si es necesario]
---

RESPONDE AHORA basándote únicamente en el contexto proporcionado:"""

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

