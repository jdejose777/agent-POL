# main.py
# Backend API para el sistema RAG de consultas legales
# Versión con sentence-transformers LOCAL (sin API de Hugging Face)

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
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
        print("🤖 Generando embedding con sentence-transformers local...")
        
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
        
        # Filtrar solo matches con score alto
        contexto_parts = []
        for match in matches:
            if match.get("score", 0) > 0.7:  # Solo alta similitud
                text = match.get("metadata", {}).get("text", "")
                if text:
                    contexto_parts.append(text)
        
        contexto = "\n\n".join(contexto_parts)
        num_matches = len(contexto_parts)
        
        print(f"📋 Contexto encontrado: {num_matches} fragmentos relevantes ({len(contexto)} caracteres)")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al contactar con Pinecone: {e}")
        raise HTTPException(status_code=500, detail=f"Error al buscar en la base de datos: {str(e)}")


    # --- PASO 3: Generar Respuesta con Gemini (LLM) ---
    if contexto:
        prompt = f"""Eres un asistente jurídico especializado en el Código Penal español. Responde basándote únicamente en el contexto proporcionado.

CONTEXTO DEL CÓDIGO PENAL:
{contexto}

PREGUNTA:
{pregunta_usuario}

INSTRUCCIONES:
- Responde basándote únicamente en el contexto del Código Penal proporcionado
- Si la información no está en el contexto, indícalo claramente
- Cita los artículos específicos cuando sea posible
- Usa un lenguaje claro y profesional
- Si es relevante, menciona las penas asociadas

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
    
    try:
        print("⚖️ Llamando a Gemini para generar respuesta...")
        gemini_payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 20,
                "topP": 0.8,
                "maxOutputTokens": 800
            }
        }
        
        response_gemini = requests.post(GEMINI_URL, json=gemini_payload, timeout=30)
        response_gemini.raise_for_status()

        gemini_data = response_gemini.json()
        respuesta_final = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        
        print("✅ Respuesta generada con éxito")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al contactar con Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar la respuesta final: {str(e)}")
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
