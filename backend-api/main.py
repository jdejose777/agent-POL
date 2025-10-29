# main.py
# Backend API para el sistema RAG de consultas legales
# Versión con sentence-transformers LOCAL y Gemini API

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Cargar las variables de entorno desde .env
load_dotenv()

# --- 1. CONFIGURACIÓN Y CLAVES SECRETAS ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# URLs de APIs
PINECONE_HOST = "https://developer-quickstart-py-3oyi1w3.svc.aped-4627-b74a.pinecone.io/query"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


# --- CARGAR MODELO DE EMBEDDINGS LOCAL ---
print("🤖 Cargando modelo sentence-transformers...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Modelo cargado correctamente")


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


# --- 4. ENDPOINT PRINCIPAL ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat_request(request: ChatRequest):
    """
    Endpoint principal que procesa la pregunta del usuario y devuelve una respuesta
    basada en el contexto del Código Penal.
    """
    pregunta_usuario = request.pregunta
    print(f"📝 Recibida pregunta: {pregunta_usuario}")

    # --- PASO 1: Generar Embedding LOCAL con sentence-transformers ---
    try:
        print("🔢 Generando embedding con sentence-transformers local...")
        
        # Generar embedding usando el modelo local
        embedding_array = embedding_model.encode([pregunta_usuario])[0]
        
        # Convertir a lista de Python para JSON
        embedding = embedding_array.tolist()
        
        print(f"✅ Embedding generado: {len(embedding)} dimensiones")

    except Exception as e:
        print(f"❌ Error al generar embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar el embedding: {str(e)}")


    # --- PASO 2: Buscar en Pinecone ---
    try:
        print("🔍 Buscando contexto en Pinecone...")
        pinecone_headers = {
            "Api-Key": PINECONE_API_KEY,
            "Content-Type": "application/json"
        }
        pinecone_payload = {
            "vector": embedding,
            "topK": 5,
            "includeMetadata": True,
            "includeValues": False
        }

        response_pinecone = requests.post(PINECONE_HOST, headers=pinecone_headers, json=pinecone_payload, timeout=30)
        response_pinecone.raise_for_status()

        pinecone_data = response_pinecone.json()
        matches = pinecone_data.get("matches", [])
        
        # Mostrar scores para debugging
        if matches:
            print(f"🔍 Scores encontrados: {[match.get('score', 0) for match in matches[:3]]}")
        
        # Filtrar solo matches con score alto (bajado a 0.3 para ser más permisivo)
        contexto_parts = []
        metadata_info = []
        for match in matches:
            score = match.get("score", 0)
            if score > 0.3:  # Umbral más bajo para capturar más resultados
                text = match.get("metadata", {}).get("text", "")
                articulo = match.get("metadata", {}).get("articulo", "N/A")
                titulo = match.get("metadata", {}).get("titulo", "")
                if text:
                    # Agregar información del artículo y score
                    contexto_parts.append(f"[Artículo {articulo} - Relevancia: {score:.2f}]\n{text}")
                    metadata_info.append(f"Artículo {articulo}")
                    print(f"  ✓ Match con score {score:.3f} - Artículo {articulo}")
        
        contexto = "\n\n---\n\n".join(contexto_parts)
        num_matches = len(contexto_parts)
        
        print(f"📋 Contexto encontrado: {num_matches} fragmentos relevantes ({len(contexto)} caracteres)")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al contactar con Pinecone: {e}")
        raise HTTPException(status_code=500, detail=f"Error al buscar en la base de datos: {str(e)}")


    # --- PASO 3: Generar Respuesta con Gemini (LLM) ---
    if contexto:
        articulos_encontrados = ", ".join(metadata_info) if metadata_info else "varios"
        prompt = f"""Eres un asistente jurídico especializado en el Código Penal español. Responde basándote únicamente en el contexto proporcionado.

PREGUNTA DEL USUARIO:
{pregunta_usuario}

CONTEXTO RELEVANTE DEL CÓDIGO PENAL:
Se encontraron {num_matches} fragmentos relevantes del Código Penal relacionados con tu pregunta ({articulos_encontrados}).

{contexto}

INSTRUCCIONES IMPORTANTES:
- Responde ÚNICAMENTE basándote en el contexto proporcionado arriba
- Cita SIEMPRE los artículos específicos mencionados en el contexto
- Si la información no está completa en el contexto, indícalo claramente
- Usa un lenguaje claro, profesional y preciso
- Menciona las penas asociadas si están en el contexto
- Estructura tu respuesta de forma clara con párrafos separados
- NO inventes información que no esté en el contexto

RESPUESTA:"""
    else:
        prompt = f"""Eres un asistente jurídico especializado en el Código Penal español.

PREGUNTA:
{pregunta_usuario}

No se encontró información específica en el Código Penal para responder a esta pregunta.

Responde educadamente explicando que:
1. No se encontró información relevante en el Código Penal procesado
2. Sugiere reformular la pregunta usando términos jurídicos más específicos
3. Recuerda que solo puedes consultar sobre el Código Penal español

RESPUESTA:"""
    
    # --- PASO 3: Generar Respuesta con Gemini API ---
    try:
        print("⚖️ Llamando a Gemini API para generar respuesta...")
        
        if not GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY no está configurada en el .env")
        
        # Preparar headers y payload para Gemini API
        gemini_headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        gemini_payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        # Hacer petición a Gemini API
        response_gemini = requests.post(GEMINI_URL, headers=gemini_headers, json=gemini_payload, timeout=30)
        response_gemini.raise_for_status()
        
        gemini_data = response_gemini.json()
        respuesta_final = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        
        print("✅ Respuesta generada con éxito")

    except Exception as e:
        print(f"⚠️ Error al contactar con Gemini: {e}")
        print("🔄 Generando respuesta basada en el contexto disponible...")
        
        # Respuesta de fallback con el contexto encontrado
        if contexto:
            respuesta_final = f"""**[MODO DEMOSTRACIÓN - API Gemini no disponible]**

**Contexto encontrado en el Código Penal sobre tu pregunta:**

{contexto[:1500]}...

---
*Nota: Se encontraron {num_matches} fragmentos relevantes en la base de datos. Para obtener respuestas generadas por IA, verifica la API key de Gemini.*"""
        else:
            respuesta_final = "**[MODO DEMOSTRACIÓN]** No se encontró información relevante en la base de datos. Verifica la configuración de la API de Gemini para obtener respuestas generadas por IA."
        
        print("✅ Respuesta de demostración generada")
        
    except (KeyError, IndexError) as e:
        print(f"❌ Error al procesar respuesta de Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar respuesta de Gemini: {str(e)}")


    # --- PASO 4: Devolver la Respuesta Final ---
    return ChatResponse(
        respuesta=respuesta_final,
        metadata={
            "pregunta": pregunta_usuario,
            "tieneContexto": bool(contexto),
            "numeroResultados": num_matches,
            "modelo": "gemini-1.5-flash",
            "dominio": "codigo-penal-espanol"
        }
    )


# --- 5. ENDPOINT DE SALUD ---
@app.get("/health")
async def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return {
        "status": "healthy",
        "service": "RAG API - Código Penal",
        "version": "1.0.0"
    }


# --- 6. ENDPOINT DE INFORMACIÓN ---
@app.get("/")
async def root():
    """Información básica de la API"""
    return {
        "message": "API RAG - Código Penal Español",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)",
            "docs": "/docs (Documentación interactiva)"
        }
    }
