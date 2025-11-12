# ⚡ INICIO RÁPIDO - Agent-POL

## 🚀 Método 1: Todo en uno (Recomendado)

```powershell
cd C:\agent-POL\backend-api; C:\agent-POL\.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

Luego abrir: `C:\agent-POL\frontend\index.html`

---

## 📋 Método 2: Paso a paso

### 1️⃣ Verificar servicios (Docker)

```powershell
# Redis
docker ps --filter "name=redis-cache"

# PostgreSQL
docker ps --filter "name=postgres-agentpol"

# Si no están corriendo, iniciarlos:
docker start redis-cache postgres-agentpol
```

### 2️⃣ Activar entorno virtual

```powershell
C:\agent-POL\.venv\Scripts\activate
```

### 3️⃣ Iniciar backend

```powershell
cd C:\agent-POL\backend-api
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4️⃣ Verificar que funciona

```powershell
curl http://127.0.0.1:8000/health
```

### 5️⃣ Abrir frontend

```powershell
start chrome C:\agent-POL\frontend\index.html
```

---

## 🧪 Probar la API desde PowerShell

```powershell
# Consulta simple
$body = @{ pregunta = "¿Qué es el homicidio?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -Body $body -ContentType "application/json"

# Comparar artículos
curl "http://127.0.0.1:8000/comparar?art1=138&art2=142"

# Ver conversaciones
curl http://127.0.0.1:8000/conversations

# Ver analytics
curl http://127.0.0.1:8000/analytics
```

---

## 🔍 Endpoints Disponibles

- **Health:** http://127.0.0.1:8000/health
- **Docs:** http://127.0.0.1:8000/docs
- **Chat:** POST http://127.0.0.1:8000/chat
- **Comparar:** http://127.0.0.1:8000/comparar?art1=X&art2=Y
- **Conversaciones:** http://127.0.0.1:8000/conversations
- **Analytics:** http://127.0.0.1:8000/analytics

---

## 🛑 Detener todo

```powershell
# Backend: Ctrl + C en la terminal

# Servicios Docker (opcional)
docker stop redis-cache postgres-agentpol
```

---

## 🧹 Limpiar logs/cache

```powershell
cd C:\agent-POL
Remove-Item logs\* -Recurse -Force
Remove-Item backend-api\__pycache__\* -Recurse -Force
```

---

## 📝 Notas:

- ✅ Redis y PostgreSQL deben estar corriendo
- ✅ El backend se recarga automáticamente con `--reload`
- ✅ Los embeddings ya están en Pinecone
- ✅ El PDF se carga automáticamente al inicio
- ✅ Todas las conversaciones se guardan en PostgreSQL

---

**⚡ ¡Listo para usar!**
