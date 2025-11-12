# 🚀 Sistema RAG con Vertex AI - Código Penal Español

## 📋 Resumen del Sistema

Sistema completo de consultas sobre el Código Penal español usando **Retrieval-Augmented Generation (RAG)** con:

- ✅ **Vertex AI** (Google Cloud) para embeddings y generación
- ✅ **Pinecone** para búsqueda vectorial
- ✅ **FastAPI** como backend
- ✅ **Frontend HTML/CSS/JS** simple y funcional

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│   FRONTEND      │  HTML/CSS/JS (Puerto 3000)
│   index.html    │
└────────┬────────┘
         │ HTTP POST /chat
         ▼
┌─────────────────┐
│   BACKEND       │  FastAPI (Puerto 8000)
│   main.py       │  + Vertex AI
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Pinecone│ │  Vertex AI   │
│768 dims│ │  - Embeddings│
│1146 vec│ │  - Gemini LLM│
└────────┘ └──────────────┘
```

---

## ⚙️ Configuración Técnica

### Modelos de IA

**Embeddings:**
- Modelo: `text-embedding-004` (Google Vertex AI)
- Dimensiones: 768
- Región: `us-central1`

**Generación (LLM):**
- Modelo: `gemini-2.0-flash-001`
- Región: `us-central1`

### Base de Datos Vectorial

**Pinecone:**
- Índice: `codigo-penal-vertex-ai`
- Dimensiones: 768
- Región: `us-east-1`
- Vectores almacenados: **1,146 chunks**
- Fuente: Código Penal español (429 páginas)

### Parámetros RAG

- **TOP_K**: 3 fragmentos recuperados
- **Threshold primario**: 0.5
- **Threshold fallback**: 0.4
- **Chunk size**: 800 caracteres
- **Overlap**: 100 caracteres

---

## 🚀 Instrucciones de Uso

### 1️⃣ Instalar Dependencias

```powershell
cd C:\agent-POL\backend-api
C:\agent-POL\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Paquetes principales:**
- `fastapi>=0.115.0`
- `uvicorn[standard]`
- `google-cloud-aiplatform>=1.38.0`
- `vertexai>=1.0.0`
- `pinecone>=5.0.0`
- `PyPDF2`

### 2️⃣ Configurar Variables de Entorno

Archivo: `backend-api/.env`

```env
PINECONE_API_KEY=pcsk_7SfBoG_9FeU7etGnzFAQX9wLEhoeY1uWJYw92gYNWBAkArVuFVKX2xQu4gEaUtxyAfCLPW
PINECONE_INDEX_NAME=codigo-penal-vertex-ai
GOOGLE_APPLICATION_CREDENTIALS=C:/agent-POL/resolute-return-476416-g5-d74c75925421.json
GCP_PROJECT_ID=resolute-return-476416-g5
GCP_REGION=us-central1
```

### 3️⃣ Iniciar Backend

```powershell
cd C:\agent-POL\backend-api
C:\agent-POL\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Backend disponible en:** `http://localhost:8000`

**Endpoints:**
- `GET /` - Información de la API
- `GET /health` - Estado del servicio
- `POST /chat` - Consulta RAG
- `GET /docs` - Documentación Swagger

### 4️⃣ Iniciar Frontend

**Opción 1:** Abrir directamente
```powershell
start C:\agent-POL\frontend\index.html
```

**Opción 2:** Servidor HTTP
```powershell
cd C:\agent-POL\frontend
python -m http.server 3000
```

**Frontend disponible en:** `http://localhost:3000`

---

## 🧪 Pruebas del Sistema

### Prueba desde PowerShell

```powershell
$body = @{ pregunta = "¿Qué dice el artículo 138?" } | ConvertTo-Json -Compress
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -Body $body -ContentType "application/json; charset=utf-8"
Write-Host $response.respuesta
```

### Ejemplos de Consultas

✓ "¿Qué es el homicidio?"  
✓ "¿Cuál es la pena por robo con violencia?"  
✓ "Artículo 138 del Código Penal"  
✓ "¿Qué dice sobre la prevaricación?"  

### Ejemplo de Respuesta

```
---
**Artículo 138.**
"1. El que matare a otro será castigado, como reo de homicidio, con la pena de prisión de diez a quince años."

📘 *Explicación:* Este artículo define el delito de homicidio y establece la pena correspondiente.
---
```

---

## 🔄 Reprocesar PDF (Si es necesario)

Si necesitas actualizar el índice de Pinecone con una nueva versión del PDF:

```powershell
cd C:\agent-POL\backend-api
C:\agent-POL\.venv\Scripts\python.exe procesar-pdf-vertex.py
```

**El script:**
1. Extrae texto del PDF (429 páginas)
2. Divide en 1,146 chunks de 800 caracteres
3. Genera embeddings con Vertex AI (768 dims)
4. Sube a Pinecone

**Tiempo estimado:** 10-15 minutos

---

## 🔍 Solución de Problemas

### 1. Error "Vector dimension mismatch"
- **Causa:** El índice de Pinecone tiene dimensiones incorrectas
- **Solución:** Recrear índice con 768 dimensiones y reprocesar PDF

### 2. Warning "ALTS creds ignored"
- **Causa:** No estás ejecutando en infraestructura GCP
- **Solución:** Es normal, no afecta el funcionamiento

### 3. Error de autenticación Google Cloud
```powershell
# Verificar credenciales
gcloud auth application-default login
```

### 4. Error de conexión Pinecone
- Verificar `PINECONE_API_KEY` en `.env`
- Comprobar nombre del índice: `codigo-penal-vertex-ai`

### 5. Respuestas vacías o incorrectas
- Revisar logs del backend
- Verificar que Pinecone tenga 1,146 vectores
- Ajustar threshold si es necesario

---

## 📊 Información de Costos

### Google Cloud (Vertex AI)

**Embeddings (text-embedding-004):**
- Costo: ~$0.00002 por 1,000 caracteres
- Procesamiento inicial: ~$0.015 (767,608 caracteres)
- Por consulta: ~$0.000001

**Generación (Gemini 2.0 Flash):**
- Input: ~$0.075 por 1M tokens
- Output: ~$0.30 por 1M tokens
- Costo promedio por consulta: ~$0.001-0.003

**Estimación mensual (100 consultas/día):**
- Embeddings: ~$0.03
- Generación: ~$3-9
- **Total:** ~$3-10/mes

### Pinecone

**Plan Serverless:**
- Storage: Gratis hasta 10GB
- Lecturas: $0.40 por millón de unidades
- **Estimación:** ~$1-2/mes para uso moderado

---

## 📝 Características del Prompt

El sistema usa un **prompt profesional** optimizado para:

✅ **Respuestas literales** del Código Penal  
✅ **Citación exacta** de artículos con formato  
✅ **Sin invención** de información  
✅ **Formato estructurado** con explicaciones opcionales  
✅ **Prioridad en exactitud** sobre fluidez  

---

## 🚨 Seguridad

**NO subir a Git:**
- `backend-api/.env` (contiene API keys)
- `*.json` (credenciales Google Cloud)
- `__pycache__/`

**Archivo `.gitignore` actualizado** para proteger credenciales.

---

## ✅ Estado del Proyecto

- [x] Migración completa a Vertex AI
- [x] Eliminación de dependencias de n8n
- [x] Embeddings locales reemplazados por Vertex AI
- [x] 1,146 chunks del Código Penal procesados
- [x] Prompt optimizado para respuestas literales
- [x] Sistema probado y funcional
- [x] Documentación completa
- [x] Código subido a GitHub

---

## 📚 Recursos

- **Dashboard Pinecone:** https://app.pinecone.io/
- **Google Cloud Console:** https://console.cloud.google.com/
- **Documentación Vertex AI:** https://cloud.google.com/vertex-ai/docs
- **Repositorio GitHub:** https://github.com/jdejose777/agent-POL

---

## 👨‍💻 Comandos Rápidos

```powershell
# Iniciar sistema completo
cd C:\agent-POL\backend-api
C:\agent-POL\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Consulta de prueba
$body = @{ pregunta = "artículo 138" } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -Body $body -ContentType "application/json"

# Ver logs en tiempo real
# (Los logs aparecen en la terminal donde corre uvicorn)
```

---

**🎉 Sistema listo para producción con Vertex AI**
