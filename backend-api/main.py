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
TOP_K_RESULTS = 3  # Número de fragmentos a recuperar

# --- INICIALIZACIÓN DE SERVICIOS ---
print("🔧 Inicializando Vertex AI y Pinecone...")
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
def generate_rag_response(query: str):
    """
    Realiza la consulta RAG completa usando Vertex AI:
    1. Genera embedding de la pregunta
    2. Busca contexto relevante en Pinecone
    3. Genera respuesta con Gemini via Vertex AI
    """
    try:
        print(f"📝 Procesando pregunta: {query}")
        
        # --- PASO 1: GENERAR EMBEDDING CON VERTEX AI ---
        print("🔢 Generando embedding con Vertex AI...")
        embeddings = EMBEDDING_CLIENT.get_embeddings([query])
        query_vector = embeddings[0].values
        print(f"✅ Embedding generado: {len(query_vector)} dimensiones")
        
        # --- PASO 2: RECUPERACIÓN EN PINECONE ---
        print("🔍 Buscando en Pinecone...")
        results = PINECONE_INDEX.query(
            vector=query_vector, 
            top_k=TOP_K_RESULTS, 
            include_metadata=True
        )
        
        # Filtrar por relevancia y construir contexto
        contexto_parts = []
        for match in results['matches']:
            score = match.get('score', 0)
            print(f"  📊 Match con score: {score:.3f}")
            
            # Filtro de calidad: solo matches con score > 0.5
            if score > 0.5:
                text = match.get('metadata', {}).get('text', '')
                if text:
                    contexto_parts.append(f"[Fragmento del Código Penal - Relevancia: {score:.2f}]\n{text}")
                    print(f"  ✓ Fragmento aceptado (score: {score:.3f})")
        
        # Fallback: si no hay resultados con 0.5, bajar a 0.4
        if len(contexto_parts) == 0 and results['matches']:
            print("⚠️ Sin matches > 0.5, bajando umbral a 0.4")
            for match in results['matches']:
                score = match.get('score', 0)
                if score > 0.4:
                    text = match.get('metadata', {}).get('text', '')
                    if text:
                        contexto_parts.append(f"[Fragmento del Código Penal - Relevancia: {score:.2f}]\n{text}")
        
        contexto = "\n\n---\n\n".join(contexto_parts)
        num_matches = len(contexto_parts)
        
        print(f"📋 Contexto construido: {num_matches} fragmentos ({len(contexto)} caracteres)")
        
        # --- PASO 3: CONSTRUIR PROMPT PROFESIONAL ---
        if contexto:
            prompt = f"""Eres un asistente jurídico especializado en derecho penal español. 
Tienes acceso exclusivamente a un documento fuente: el Código Penal español (PDF). 
Todas tus respuestas deben basarse **únicamente** en el contenido de ese documento, sin añadir información externa o inventada.

PREGUNTA DEL USUARIO:
{query}

CONTEXTO RECUPERADO DEL CÓDIGO PENAL (solo {num_matches} fragmentos más relevantes):
{contexto}

INSTRUCCIONES OBLIGATORIAS:
1. Usa **solo el texto recuperado arriba** como base para tu respuesta. 
2. Si el contexto recuperado no incluye el artículo completo, **indícalo claramente** ("el fragmento no contiene todo el artículo") y **no intentes completarlo**.
3. Cuando cites artículos, usa esta estructura:
   - "**Artículo [número]. [Título, si lo hay]**" seguido del texto literal.
4. Si el usuario pide interpretación o resumen, **responde primero con el texto literal** y **luego** con una breve explicación, dejando claro qué parte es literal y cuál es explicativa.
5. Si el contexto incluye varios artículos, **prioriza el más directamente relacionado** con la consulta.
6. No incluyas artículos no solicitados a menos que el contexto lo justifique legalmente (por ejemplo, remisión explícita entre artículos).
7. Si el artículo no se encuentra en el contexto, responde: 
   > "No se ha encontrado el texto literal del artículo solicitado en el contexto recuperado. Verifique que el documento fuente lo incluya completo."

FORMATO DE SALIDA ESPERADO:
---
**Artículo [número]. [Título]**
"[Texto literal del Código Penal]"

📘 *Explicación:* [Breve aclaración si es necesario]
---

Tu prioridad es la **exactitud literal** del Código Penal, no la fluidez o extensión del texto.

RESPUESTA:"""
        else:
            prompt = f"""Eres un asistente jurídico especializado en el Código Penal español.

PREGUNTA:
{query}

No se encontró información específica en el Código Penal para responder a esta pregunta.

Responde educadamente explicando que:
1. No se encontró información relevante en el Código Penal procesado
2. Sugiere reformular la pregunta usando términos jurídicos más específicos
3. Recuerda que solo puedes consultar sobre el Código Penal español

RESPUESTA:"""
        
        # --- PASO 4: LLAMAR A GEMINI VIA VERTEX AI ---
        print("⚖️ Generando respuesta con Gemini (Vertex AI)...")
        response = LLM_CLIENT.generate_content(prompt)
        respuesta_texto = response.text
        
        print("✅ Respuesta generada exitosamente")
        
        return {
            "respuesta": respuesta_texto,
            "metadata": {
                "num_fragmentos": num_matches,
                "tiene_contexto": bool(contexto),
                "modelo": MODEL_NAME,
                "embedding_model": EMBEDDING_MODEL
            }
        }

    except Exception as e:
        print(f"❌ Error en el proceso RAG: {e}")
        return {
            "respuesta": f"Disculpa, ha ocurrido un error al consultar la base de datos de documentos: {str(e)}",
            "metadata": {
                "error": True,
                "mensaje_error": str(e)
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

