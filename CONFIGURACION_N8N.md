# 🔧 Configuración de n8n para el Sistema RAG

## 📋 Variables de Entorno Requeridas

Para que el workflow funcione correctamente, necesitas configurar las siguientes variables de entorno en tu instancia de n8n:

### 1. 🐍 Python Environment
**Ya no necesitas API Key externa!**

El nodo ahora usa **Python nativo** en n8n con sentence-transformers local:
- ✅ Sin dependencias de APIs externas
- ✅ Más rápido y confiable
- ✅ Sin límites de rate limiting
- ✅ Procesamiento completamente local

### 2. 🌲 Pinecone Configuration
```
PINECONE_API_KEY=tu_pinecone_api_key_aqui
PINECONE_ENVIRONMENT=tu_pinecone_environment
PINECONE_INDEX_NAME=developer-quickstart-py
```

**Ya configurado previamente:**
- Environment: Usa el mismo que configuraste antes
- Index Name: `developer-quickstart-py` (donde están los 949 vectores del código penal)

### 3. 🤖 Google Gemini API Key
```
GOOGLE_API_KEY=tu_google_gemini_api_key_aqui
```

**Si no tienes una:**
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una API key gratuita
3. Copia la key generada

## 🚀 Pasos para Implementar

### 1. Configurar Variables en n8n
1. Ve a tu instancia n8n: `https://jdejose.app.n8n.cloud`
2. Ve a Settings → Environment variables
3. Añade todas las variables listadas arriba

### 2. Importar el Workflow Actualizado
1. Copia el contenido de `plantilla_n8n.json`
2. En n8n, ve a Workflows → Import
3. Pega el JSON y importa
4. Activa el workflow

### 3. Verificar el Webhook URL
- Después de importar, verifica que la URL sea:
- `https://jdejose.app.n8n.cloud/webhook-test/rag-chat-agent`
- ✅ Sin duplicación del "webhook-test"

## 🔄 Cambios Realizados

### ❌ Problemas Anteriores:
1. **v1:** Usaba `child_process` para ejecutar Python (bloqueado por seguridad)
2. **v2:** Usaba Hugging Face API (dependencia externa, rate limits)

### ✅ Solución Final Implementada:
- Cambiado a **Python nativo** en n8n con sentence-transformers
- Usa el mismo modelo: `sentence-transformers/all-MiniLM-L6-v2`
- Procesamiento 100% local sin APIs externas
- Mantiene la misma calidad y dimensiones (384) de embeddings
- Compatible con los vectores ya almacenados en Pinecone

## 🧪 Probar el Sistema

1. **Verificar las Variables:**
   - Todas las API keys están configuradas
   - El workflow está activo

2. **Probar desde el Frontend:**
   - Abre `frontend/index.html`
   - Envía una pregunta sobre el código penal
   - Verifica que recibas una respuesta

3. **Ejemplo de Pregunta:**
   ```
   ¿Cuáles son las penas por robo en el código penal?
   ```

## ⚠️ Notas Importantes

- **Python Local:** Sin límites de API, procesamiento completamente local
- **Compatibilidad:** Los embeddings generados son compatibles con los ya almacenados en Pinecone
- **Backup:** Guarda siempre una copia del workflow antes de hacer cambios

## 🆘 Troubleshooting

### Si hay errores de Python:
1. Verifica que n8n tiene sentence-transformers instalado
2. Comprueba que el nodo está configurado en modo Python
3. Asegúrate de que el modelo se puede descargar (primera ejecución)

### Si no encuentra contexto:
1. Verifica que el índice de Pinecone tiene los 949 vectores
2. Comprueba que el nombre del índice es correcto: `developer-quickstart-py`

¡El sistema debería funcionar perfectamente con estos cambios! 🎉