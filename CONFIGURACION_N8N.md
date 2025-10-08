# 🔧 Configuración de n8n para el Sistema RAG

## 📋 Variables de Entorno Requeridas

Para que el workflow funcione correctamente, necesitas configurar las siguientes variables de entorno en tu instancia de n8n:

### 1. 🤗 Hugging Face API Key
```
HUGGINGFACE_API_KEY=tu_hugging_face_api_key_aqui
```

**¿Cómo obtenerla?**
1. Ve a [Hugging Face](https://huggingface.co/)
2. Crea una cuenta gratuita
3. Ve a Settings → Access Tokens
4. Crea un nuevo token con permisos de lectura
5. Copia el token generado

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

### ❌ Problema Anterior:
- Usaba `child_process` para ejecutar Python localmente
- Este módulo está bloqueado en n8n por seguridad

### ✅ Solución Implementada:
- Cambiado a **Hugging Face API** para generar embeddings
- Usa el mismo modelo: `sentence-transformers/all-MiniLM-L6-v2`
- Compatible con las restricciones de seguridad de n8n
- Mantiene la misma calidad y dimensiones (384) de embeddings

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

- **Hugging Face API:** Tiene límites gratuitos, pero es suficiente para pruebas
- **Compatibilidad:** Los embeddings generados son compatibles con los ya almacenados en Pinecone
- **Backup:** Guarda siempre una copia del workflow antes de hacer cambios

## 🆘 Troubleshooting

### Si hay errores de API:
1. Verifica que todas las API keys están correctas
2. Comprueba que no hay caracteres extra o espacios
3. Asegúrate de que las APIs están activas

### Si no encuentra contexto:
1. Verifica que el índice de Pinecone tiene los 949 vectores
2. Comprueba que el nombre del índice es correcto: `developer-quickstart-py`

¡El sistema debería funcionar perfectamente con estos cambios! 🎉