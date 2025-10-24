# 🚀 Backend API - Sistema RAG para Consultas Legales

## 📋 Descripción

API REST desarrollada con FastAPI que reemplaza completamente el workflow de n8n. Proporciona un endpoint para consultas sobre el Código Penal español usando tecnología RAG (Retrieval-Augmented Generation).

## ⚡ Ventajas sobre n8n

- ✅ **Control Total**: Código transparente y debuggeable línea por línea
- ✅ **Sin Problemas de Tipos**: No más errores de conversión entre nodos
- ✅ **Mayor Rendimiento**: Menos overhead, respuestas más rápidas
- ✅ **Más Simple**: Un solo archivo Python vs múltiples nodos complejos
- ✅ **Fácil de Desplegar**: Compatible con cualquier plataforma (Heroku, Railway, AWS, etc.)
- ✅ **Documentación Automática**: FastAPI genera docs interactivas en `/docs`

## 🛠️ Instalación

### 1. Instalar Dependencias

```bash
cd backend-api
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

El archivo `.env` debe contener:

```env
HUGGING_FACE_TOKEN=tu_token_de_hugging_face_aqui
PINECONE_API_KEY=tu_api_key_de_pinecone_aqui
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
```

### 3. Ejecutar el Servidor

```bash
uvicorn main:app --reload --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

## 📡 Endpoints

### POST /chat

Endpoint principal para enviar consultas.

**Request:**
```json
{
  "pregunta": "¿Qué es la prevaricación?"
}
```

**Response:**
```json
{
  "respuesta": "La prevaricación es un delito...",
  "metadata": {
    "pregunta": "¿Qué es la prevaricación?",
    "tieneContexto": true,
    "numeroResultados": 3,
    "modelo": "gemini-1.5-flash",
    "dominio": "codigo-penal-espanol"
  }
}
```

### GET /health

Verifica el estado del servicio.

**Response:**
```json
{
  "status": "healthy",
  "service": "RAG API - Código Penal",
  "version": "1.0.0"
}
```

### GET /docs

Documentación interactiva generada automáticamente por FastAPI.

## 🔄 Flujo de Procesamiento

1. **Recepción**: La API recibe la pregunta del usuario
2. **Embedding**: Genera el vector de embedding usando Hugging Face
3. **Búsqueda**: Consulta Pinecone con el embedding para obtener contexto relevante
4. **Generación**: Envía el contexto y pregunta a Gemini para generar la respuesta
5. **Respuesta**: Devuelve la respuesta formateada al cliente

## 🧪 Pruebas

### Con curl (PowerShell):

```powershell
$body = @{
    pregunta = "¿Qué es la prevaricación?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -ContentType "application/json" -Body $body
```

### Con el Frontend:

1. Asegúrate de que el backend esté corriendo
2. Abre `frontend/index.html` en tu navegador
3. El frontend ya está configurado para usar `http://localhost:8000/chat`

## 📦 Estructura del Proyecto

```
backend-api/
├── main.py           # API FastAPI principal
├── requirements.txt  # Dependencias de Python
├── .env             # Variables de entorno (API keys)
└── README.md        # Esta documentación
```

## 🚀 Despliegue en Producción

### Opción 1: Railway

```bash
# Instalar Railway CLI
npm install -g railway

# Inicializar proyecto
railway init

# Configurar variables de entorno
railway variables set HUGGING_FACE_TOKEN=tu_token
railway variables set PINECONE_API_KEY=tu_key
railway variables set GEMINI_API_KEY=tu_key

# Desplegar
railway up
```

### Opción 2: Heroku

```bash
# Crear Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Desplegar
heroku create tu-app-rag
heroku config:set HUGGING_FACE_TOKEN=tu_token
heroku config:set PINECONE_API_KEY=tu_key
heroku config:set GEMINI_API_KEY=tu_key
git push heroku main
```

### Opción 3: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t rag-api .
docker run -p 8000:8000 --env-file .env rag-api
```

## 🔧 Configuración del Frontend

El frontend ya está actualizado para usar la nueva API. La URL configurada es:

```javascript
const WEBHOOK_URL = 'http://localhost:8000/chat';
```

Para producción, cámbiala a tu dominio desplegado:

```javascript
const WEBHOOK_URL = 'https://tu-dominio.com/chat';
```

## 📝 Logs y Debugging

La API incluye logging detallado:

```
📝 Recibida pregunta: ¿Qué es la prevaricación?
🤖 Llamando a Hugging Face para obtener embedding...
✅ Embedding generado: 384 dimensiones
🔍 Buscando contexto en Pinecone...
📋 Contexto encontrado: 3 fragmentos relevantes (1245 caracteres)
⚖️ Llamando a Gemini para generar respuesta...
✅ Respuesta generada con éxito
```

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "Port already in use"
```bash
# Usa otro puerto
uvicorn main:app --reload --port 8001
```

### Error: "Invalid API Key"
- Verifica que el archivo `.env` existe
- Comprueba que las claves son correctas
- Reinicia el servidor después de cambiar `.env`

## 📊 Monitoreo

FastAPI incluye endpoints de monitoreo:

- `/health` - Estado del servicio
- `/docs` - Documentación interactiva Swagger
- `/redoc` - Documentación ReDoc alternativa

## 🎯 Próximos Pasos

- [ ] Añadir caché de embeddings para consultas frecuentes
- [ ] Implementar rate limiting
- [ ] Añadir autenticación con JWT
- [ ] Implementar métricas con Prometheus
- [ ] Añadir tests unitarios
- [ ] Configurar CI/CD

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs de la consola
2. Verifica que todas las API keys son válidas
3. Asegúrate de que Pinecone tiene los vectores cargados
4. Comprueba la conectividad a internet

---

**¡Adiós n8n! 👋 Bienvenido control total y simplicidad 🚀**
