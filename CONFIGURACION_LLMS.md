# 🤖 Configuración de LLMs de Código Abierto para n8n

## 🎯 Resumen de Cambios

He reemplazado el nodo de Google Gemini con un **nodo HTTP Request flexible** que te permite usar cualquier API de LLM de código abierto. Esto te da más opciones, mejor costo-beneficio y mayor control.

## 🔧 Configuración del Nodo HTTP Request

### Parámetros Configurados:
- **Method**: `POST`
- **URL**: `URL_DE_LA_API_AQUI` (reemplazar según el proveedor)
- **Authentication**: `Header Auth`
- **Header Name**: `Authorization` 
- **Header Value**: `Bearer {{ $credentials.miApiKeySecreta }}`
- **Body Content Type**: `JSON`
- **Temperature**: `0.3` (respuestas objetivas)

## 🌟 Opciones de APIs Compatibles

### 1. 🚀 Groq (Recomendado - Más Rápido)

**URL a usar:**
```
https://api.groq.com/openai/v1/chat/completions
```

**Modelos disponibles:**
- `llama3-8b-8192` (configurado por defecto)
- `llama3-70b-8192` 
- `mixtral-8x7b-32768`
- `gemma-7b-it`

**Cómo obtener API Key:**
1. Ve a [console.groq.com](https://console.groq.com/)
2. Crea cuenta gratuita
3. Ve a API Keys
4. Crea nueva API key
5. Úsala en las credenciales de n8n

**Ventajas:**
- ✅ Muy rápido (inferencia optimizada)
- ✅ Generoso plan gratuito
- ✅ Compatible con formato OpenAI
- ✅ Excelente para respuestas jurídicas

### 2. 🤗 Hugging Face Inference API

**URL a usar:**
```
https://api-inference.huggingface.co/models/microsoft/DialoGPT-large
```

**Otros modelos compatibles:**
- `microsoft/DialoGPT-large`
- `facebook/blenderbot-400M-distill`
- `microsoft/DialoGPT-medium`

**Cómo obtener API Key:**
1. Ve a [huggingface.co](https://huggingface.co/)
2. Crea cuenta → Settings → Access Tokens
3. Crea token con permisos de lectura
4. Úsala en las credenciales de n8n

**Ventajas:**
- ✅ Muchos modelos disponibles
- ✅ Plan gratuito
- ✅ Especializado en ML/NLP

### 3. 🦙 Ollama (Local)

**URL a usar:**
```
http://localhost:11434/api/generate
```

**Modelos recomendados:**
- `llama3:8b`
- `mistral:7b`
- `codellama:7b`

**Configuración:**
1. Instala Ollama en tu servidor
2. Descarga modelo: `ollama pull llama3:8b`
3. No necesitas API key (es local)
4. Cambia Authentication a "None"

**Ventajas:**
- ✅ 100% local y privado
- ✅ Sin costos de API
- ✅ Control total del modelo

## 🔐 Configuración de Credenciales en n8n

### Paso 1: Crear Credencial
1. En n8n, ve a **Settings** → **Credentials**
2. Clic en **Create new credential**
3. Busca **"API Key Auth"** o **"Generic Credential"**
4. Ponle nombre: `miApiKeySecreta`

### Paso 2: Configurar Credencial
```
Name: miApiKeySecreta
API Key: tu_api_key_aqui_sin_bearer
```

**Importante:** Solo pon la API key, **NO** incluyas "Bearer " porque ya está en el nodo.

## 🎛️ Personalización del Prompt

El prompt está optimizado para respuestas jurídicas:

```javascript
"Eres un asistente jurídico especializado en el Código Penal español. 
Responde basándote únicamente en el contexto proporcionado del Código Penal.

{{ $json.tieneContexto ? 'CONTEXTO DEL CÓDIGO PENAL:\n' + $json.contexto + '\n\n' : 'No se encontró información específica en el Código Penal para esta consulta.\n\n' }}

PREGUNTA:
{{ $json.pregunta }}

INSTRUCCIONES:
- Responde basándote únicamente en el contexto del Código Penal proporcionado
- Si la información no está en el contexto, indícalo claramente
- Cita los artículos específicos cuando sea posible
- Usa un lenguaje claro y profesional
- Si es relevante, menciona las penas asociadas

RESPUESTA:"
```

## 🔄 Cambios en el Workflow

### Nuevos Nodos:
1. **🤖 LLM Open Source** - HTTP Request a tu API elegida
2. **🔧 Procesar Respuesta LLM** - Extrae la respuesta del formato de cada API

### Flujo Actualizado:
```
Webhook → Embedding Python → Búsqueda Pinecone → LLM Open Source → Procesar Respuesta → Frontend
```

## 🧪 Pruebas Recomendadas

### 1. Probar con Groq (Recomendado)
```bash
# Configuración rápida:
URL: https://api.groq.com/openai/v1/chat/completions
Modelo: llama3-8b-8192
API Key: tu_groq_api_key
```

### 2. Fallback con Hugging Face
```bash
# Si Groq no funciona:
URL: https://api-inference.huggingface.co/models/microsoft/DialoGPT-large
API Key: tu_hf_token
```

## 💡 Recomendaciones

### Para Producción:
- **Groq**: Mejor rendimiento y respuestas
- **Modelo**: `llama3-8b-8192` o `llama3-70b-8192`
- **Backup**: Configura Hugging Face como respaldo

### Para Desarrollo:
- **Ollama**: Desarrollo local sin costos
- **Modelo**: `llama3:8b` funciona bien
- **Sin API keys**: Perfecto para pruebas

## 🆘 Troubleshooting

### Error: "API Key inválida"
- Verifica que la credencial `miApiKeySecreta` existe
- Asegúrate de no incluir "Bearer " en la API key
- Prueba la API key con curl directamente

### Error: "Modelo no encontrado"
- Cambia el modelo en el parámetro `model`
- Verifica que el modelo existe en tu proveedor elegido

### Error: "Respuesta vacía"
- El nodo "🔧 Procesar Respuesta LLM" maneja diferentes formatos
- Revisa los logs para ver qué formato está llegando

¡El sistema ahora es más flexible y potente! 🚀