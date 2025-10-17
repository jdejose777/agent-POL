# 🔐 Configuración de Variables de Workflow en n8n

## 📋 Cambio Importante: De Environment Variables a Workflow Variables

He refactorizado el código para usar **Workflow Variables** en lugar de variables de entorno (`process.env`), que están bloqueadas por seguridad en n8n.

## 🔄 ¿Qué ha Cambiado?

### ❌ Antes (Bloqueado):
```javascript
const pineconeApiKey = $env.PINECONE_API_KEY;  // No funciona en n8n
```

### ✅ Ahora (Funcional):
```javascript
const pineconeApiKey = $vars.PINECONE_API_KEY;  // Variables del workflow
```

## 🛠️ Cómo Configurar las Variables en n8n

### Método 1: Variables del Workflow (Recomendado)

1. **Abre tu workflow** en n8n
2. **Clic en el menú** (tres puntos) → **Settings**
3. **Ve a la pestaña "Variables"**
4. **Añade estas variables:**

```
Variable Name: PINECONE_API_KEY
Value: tu_pinecone_api_key_aqui

Variable Name: PINECONE_ENVIRONMENT
Value: tu_pinecone_environment (ej: gcp-starter)

Variable Name: PINECONE_INDEX_NAME
Value: developer-quickstart-py
```

5. **Guarda los cambios**
6. **Activa el workflow**

### Método 2: Variables de Entorno del Sistema (Alternativo)

Si tienes acceso al servidor donde corre n8n:

```bash
# Configurar en el archivo .env de n8n
PINECONE_API_KEY=tu_api_key
PINECONE_ENVIRONMENT=tu_environment
PINECONE_INDEX_NAME=developer-quickstart-py
```

Luego reinicia n8n:
```bash
docker restart n8n  # Si usas Docker
# O
pm2 restart n8n     # Si usas PM2
```

## 🔐 Ventajas de Usar Workflow Variables

### ✅ Seguridad:
- Variables específicas por workflow
- No expuestas globalmente
- Fácil de gestionar desde la UI

### ✅ Flexibilidad:
- Diferentes valores por workflow
- Cambios sin reiniciar n8n
- Versionamiento con el workflow

### ✅ Portabilidad:
- El workflow se puede exportar
- Configuración independiente
- Fácil de clonar y modificar

## 📊 Variables Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `PINECONE_API_KEY` | Tu API key de Pinecone | `abc123-def456-ghi789` |
| `PINECONE_ENVIRONMENT` | El environment de tu índice | `gcp-starter` o `us-east-1-aws` |
| `PINECONE_INDEX_NAME` | Nombre del índice | `developer-quickstart-py` |

## 🔍 Cómo Obtener tus Valores de Pinecone

### 1. API Key:
1. Ve a [app.pinecone.io](https://app.pinecone.io/)
2. Dashboard → API Keys
3. Copia tu API key

### 2. Environment:
1. En Pinecone, ve a tu índice
2. Pestaña "Connect"
3. Verás algo como: `index-name-abc123.svc.gcp-starter.pinecone.io`
4. El environment es la parte después de `svc.`: **gcp-starter**

### 3. Index Name:
- Es el nombre que le diste al índice
- En tu caso: `developer-quickstart-py` (ya procesado con 949 vectores)

## 🧪 Verificación de Variables

Para verificar que las variables están correctamente configuradas, puedes crear un nodo temporal de prueba:

```javascript
// Nodo Code temporal para verificar
console.log('🔍 Verificando variables de Pinecone...');

const apiKey = $vars.PINECONE_API_KEY;
const environment = $vars.PINECONE_ENVIRONMENT;
const indexName = $vars.PINECONE_INDEX_NAME;

console.log('API Key configurada:', apiKey ? '✅ Sí (oculta por seguridad)' : '❌ No');
console.log('Environment configurado:', environment || '❌ No');
console.log('Index Name configurado:', indexName || '❌ No');

if (!apiKey || !environment || !indexName) {
  throw new Error('❌ Faltan variables. Ve a Workflow Settings → Variables');
}

return {
  status: 'success',
  message: '✅ Todas las variables están configuradas correctamente'
};
```

## 🆘 Troubleshooting

### Error: "Variables de Pinecone no configuradas"

**Solución:**
1. Ve a Workflow Settings → Variables
2. Verifica que los nombres sean **exactamente**:
   - `PINECONE_API_KEY`
   - `PINECONE_ENVIRONMENT`
   - `PINECONE_INDEX_NAME`
3. Verifica que no haya espacios extra
4. Guarda los cambios y recarga el workflow

### Error: "Cannot read property of undefined"

**Solución:**
- Las variables del workflow solo están disponibles cuando el workflow está **guardado**
- Guarda el workflow primero
- Luego configura las variables
- Recarga la página

### Error: "$vars is not defined"

**Solución:**
- Estás usando una versión antigua de n8n
- Actualiza n8n a la versión más reciente: `npm update -g n8n`
- O usa variables de entorno del sistema

## 📝 Checklist de Configuración

Antes de ejecutar el workflow, verifica:

- [ ] Workflow guardado en n8n
- [ ] Variables configuradas en Workflow Settings
- [ ] API Key de Pinecone válida
- [ ] Environment correcto (sin .svc. ni .pinecone.io)
- [ ] Index Name exacto (developer-quickstart-py)
- [ ] Workflow activado
- [ ] sentence-transformers instalado (para nodo Python)

## 🎯 Resumen

El nodo de búsqueda en Pinecone ahora usa **`$vars`** en lugar de **`$env`** para acceder a las credenciales de forma segura y conforme a las políticas de seguridad de n8n.

**Beneficios:**
- ✅ Compatible con n8n Cloud
- ✅ No requiere acceso al servidor
- ✅ Configuración desde la UI
- ✅ Más seguro y aislado

¡Tu workflow está ahora configurado de forma óptima y segura! 🎉