# 🗄️ PostgreSQL Integration - Historial de Conversaciones

## 📋 Índice
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Modelos de Datos](#modelos-de-datos)
- [Uso en la API](#uso-en-la-api)
- [Endpoints](#endpoints)
- [Consultas SQL Útiles](#consultas-sql-útiles)
- [Monitoreo](#monitoreo)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Instalación

### **Opción 1: Docker (Recomendado)**

```bash
# Crear contenedor PostgreSQL 16 con persistencia
docker run -d \
  --name postgres-agentpol \
  -e POSTGRES_PASSWORD=agentpol2025 \
  -e POSTGRES_USER=agentpol \
  -e POSTGRES_DB=conversations_db \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine
```

**PowerShell:**
```powershell
docker run -d --name postgres-agentpol -e POSTGRES_PASSWORD=agentpol2025 -e POSTGRES_USER=agentpol -e POSTGRES_DB=conversations_db -p 5432:5432 -v postgres-data:/var/lib/postgresql/data --restart unless-stopped postgres:16-alpine
```

### **Opción 2: PostgreSQL Nativo (Windows)**

1. Descargar desde: https://www.postgresql.org/download/windows/
2. Instalar con las credenciales configuradas
3. Crear base de datos `conversations_db`

---

## ⚙️ Configuración

### **Variables de Entorno**

Crear archivo `.env` en `backend-api/`:

```bash
# PostgreSQL Configuration
POSTGRES_USER=agentpol
POSTGRES_PASSWORD=agentpol2025
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=conversations_db
```

### **Paquetes Python Requeridos**

```bash
pip install sqlalchemy psycopg2-binary alembic
```

---

## 📊 Modelos de Datos

### **Tabla: `conversations`**
Almacena información de cada sesión de chat.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | ID único autoincremental |
| `session_id` | String(100) | UUID de la sesión (único) |
| `user_id` | String(100) | ID del usuario (opcional) |
| `user_ip` | String(50) | IP del usuario |
| `user_agent` | String(255) | User-Agent del navegador |
| `started_at` | DateTime | Inicio de la conversación |
| `last_message_at` | DateTime | Último mensaje |
| `ended_at` | DateTime | Fin de la conversación |
| `total_messages` | Integer | Total de mensajes |
| `total_tokens` | Integer | Total de tokens usados |
| `is_active` | Boolean | Si está activa |

### **Tabla: `messages`**
Almacena cada mensaje (usuario y asistente).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | ID único |
| `conversation_id` | Integer (FK) | ID de la conversación |
| `role` | String(20) | "user" o "assistant" |
| `content` | Text | Contenido del mensaje |
| `created_at` | DateTime | Timestamp del mensaje |
| `tokens` | Integer | Tokens del mensaje |
| `response_time_ms` | Float | Tiempo de respuesta (ms) |
| `extra_data` | JSON | Metadata adicional |

### **Tabla: `users`** (Opcional)
Almacena información de usuarios registrados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | ID único |
| `user_id` | String(100) | ID del usuario (único) |
| `username` | String(100) | Nombre de usuario |
| `email` | String(255) | Email (único) |
| `created_at` | DateTime | Fecha de registro |
| `last_seen` | DateTime | Última conexión |
| `total_conversations` | Integer | Total de conversaciones |
| `total_messages` | Integer | Total de mensajes |
| `is_active` | Boolean | Si está activo |

### **Tabla: `article_queries`**
Registra consultas de artículos del Código Penal.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | ID único |
| `article_number` | String(20) | Número de artículo |
| `query_timestamp` | DateTime | Momento de la consulta |
| `conversation_id` | Integer (FK) | ID de conversación |
| `search_type` | String(50) | Tipo de búsqueda |
| `search_query` | Text | Consulta original |
| `found` | Boolean | Si se encontró |
| `source` | String(50) | Fuente (redis, memory, pinecone) |
| `response_time_ms` | Float | Tiempo de respuesta |

---

## 🔌 Uso en la API

### **Automático en `/chat`**

El endpoint `/chat` **guarda automáticamente** cada conversación:

```json
POST /chat
{
  "pregunta": "¿Qué es el homicidio?",
  "historial": [...],
  "session_id": "uuid-opcional",
  "user_id": "usuario-opcional"
}
```

**Lo que se guarda:**
1. ✅ Pregunta del usuario → `messages` (role: "user")
2. ✅ Respuesta del asistente → `messages` (role: "assistant")
3. ✅ Metadata (tokens, tiempo de respuesta, modelo usado)
4. ✅ Conversación completa con estadísticas

---

## 🌐 Endpoints

### **1. Obtener todas las conversaciones**

```http
GET /conversations?skip=0&limit=20&user_id=opcional
```

**Respuesta:**
```json
{
  "conversations": [
    {
      "id": 1,
      "session_id": "abc-123",
      "started_at": "2025-01-10T10:00:00",
      "total_messages": 10,
      "is_active": true
    }
  ],
  "total": 1
}
```

### **2. Obtener conversación específica con mensajes**

```http
GET /conversations/{conversation_id}
```

**Respuesta:**
```json
{
  "conversation": {
    "id": 1,
    "session_id": "abc-123",
    "started_at": "2025-01-10T10:00:00",
    "total_messages": 2,
    "total_tokens": 500
  },
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "¿Qué es el homicidio?",
      "created_at": "2025-01-10T10:00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "El homicidio según el Código Penal...",
      "created_at": "2025-01-10T10:00:05",
      "tokens": 250,
      "response_time_ms": 1234.56
    }
  ]
}
```

### **3. Estadísticas globales**

```http
GET /analytics
```

**Respuesta:**
```json
{
  "global_stats": {
    "total_conversations": 100,
    "active_conversations": 15,
    "total_messages": 500,
    "avg_messages_per_conversation": 5.0,
    "avg_response_time_ms": 1234.56
  },
  "daily_analytics": [...],
  "most_queried_articles": [
    {"article": "138", "queries": 50}
  ]
}
```

### **4. Health Check (incluye PostgreSQL)**

```http
GET /health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "database": {
    "postgresql": {
      "status": "connected",
      "connected": true,
      "database": "conversations_db"
    },
    "stats": {
      "available": true,
      "total_conversations": 100,
      "total_messages": 500
    }
  }
}
```

---

## 🔍 Consultas SQL Útiles

### **Conectar a PostgreSQL**

```bash
# Desde Docker
docker exec -it postgres-agentpol psql -U agentpol -d conversations_db

# Desde CLI local
psql -U agentpol -h localhost -d conversations_db
```

### **Ver todas las tablas**

```sql
\dt
```

### **Ver estructura de una tabla**

```sql
\d conversations
\d messages
```

### **Últimas 10 conversaciones**

```sql
SELECT id, session_id, started_at, total_messages, is_active
FROM conversations
ORDER BY started_at DESC
LIMIT 10;
```

### **Mensajes de una conversación**

```sql
SELECT 
    m.id,
    m.role,
    LEFT(m.content, 100) as content_preview,
    m.created_at,
    m.tokens,
    m.response_time_ms
FROM messages m
WHERE m.conversation_id = 1
ORDER BY m.created_at;
```

### **Estadísticas por día**

```sql
SELECT 
    DATE(started_at) as date,
    COUNT(*) as conversations,
    SUM(total_messages) as messages,
    AVG(total_tokens) as avg_tokens
FROM conversations
GROUP BY DATE(started_at)
ORDER BY date DESC
LIMIT 7;
```

### **Artículos más consultados (últimos 30 días)**

```sql
SELECT 
    article_number,
    COUNT(*) as queries,
    AVG(response_time_ms) as avg_response_time
FROM article_queries
WHERE query_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY article_number
ORDER BY queries DESC
LIMIT 10;
```

### **Conversaciones más largas**

```sql
SELECT 
    id,
    session_id,
    total_messages,
    total_tokens,
    started_at
FROM conversations
ORDER BY total_messages DESC
LIMIT 10;
```

### **Tiempo promedio de respuesta por hora**

```sql
SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as responses,
    AVG(response_time_ms) as avg_time_ms
FROM messages
WHERE role = 'assistant' AND response_time_ms IS NOT NULL
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;
```

---

## 📈 Monitoreo

### **1. Verificar conexión**

```python
from database import check_db_connection

status = check_db_connection()
print(status)
```

### **2. Ver estadísticas**

```python
from database import get_db_stats

stats = get_db_stats()
print(stats)
```

### **3. Logs de PostgreSQL**

```bash
# Ver logs del contenedor
docker logs postgres-agentpol

# Seguir logs en tiempo real
docker logs -f postgres-agentpol
```

### **4. Espacio usado**

```sql
SELECT 
    pg_size_pretty(pg_database_size('conversations_db')) as size;
```

---

## 🛠️ Troubleshooting

### **Error: "could not connect to server"**

**Causa:** PostgreSQL no está corriendo.

**Solución:**
```bash
# Verificar contenedor
docker ps -a | findstr postgres

# Iniciar contenedor
docker start postgres-agentpol
```

### **Error: "password authentication failed"**

**Causa:** Credenciales incorrectas.

**Solución:**
1. Verificar variables de entorno en `.env`
2. Recrear contenedor con credenciales correctas:
```bash
docker rm -f postgres-agentpol
# Volver a ejecutar docker run con las credenciales correctas
```

### **Error: "relation does not exist"**

**Causa:** Tablas no creadas.

**Solución:**
```python
# En Python
from database import engine
from models import Base

Base.metadata.create_all(bind=engine)
```

### **Puerto 5432 en uso**

**Causa:** Otra instancia de PostgreSQL corriendo.

**Solución:**
```bash
# Ver qué está usando el puerto
netstat -ano | findstr :5432

# Usar otro puerto
docker run ... -p 5433:5432 ...
# Y actualizar POSTGRES_PORT=5433 en .env
```

### **Resetear base de datos (⚠️ Cuidado)**

```python
from database import reset_database

reset_database()  # Elimina y recrea todas las tablas
```

---

## 🔐 Seguridad

### **Recomendaciones:**

1. ✅ **NO** uses credenciales por defecto en producción
2. ✅ Cambia `POSTGRES_PASSWORD` a algo seguro
3. ✅ Usa SSL/TLS para conexiones remotas
4. ✅ Limita acceso por IP con firewall
5. ✅ Habilita backups automáticos

### **Conexión segura:**

```python
# En database.py
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode=require"
```

---

## 📦 Backup y Restore

### **Crear backup**

```bash
# Backup completo
docker exec postgres-agentpol pg_dump -U agentpol conversations_db > backup.sql

# Solo datos (sin esquema)
docker exec postgres-agentpol pg_dump -U agentpol --data-only conversations_db > backup_data.sql
```

### **Restaurar backup**

```bash
# Restaurar
docker exec -i postgres-agentpol psql -U agentpol conversations_db < backup.sql
```

---

## 📊 Performance

### **Índices recomendados** (ya incluidos en modelos):

- `conversations.session_id` → Búsqueda rápida por sesión
- `conversations.user_id` → Filtrar por usuario
- `messages.conversation_id` → JOIN rápido con conversaciones
- `article_queries.article_number` → Artículos más consultados
- `article_queries.query_timestamp` → Analytics por fecha

### **Optimizaciones:**

```sql
-- Ver queries lentas
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Vacuuming (mantenimiento)
VACUUM ANALYZE;
```

---

## 🎯 Próximos Pasos

- [ ] Implementar autenticación de usuarios
- [ ] Dashboard de analytics en frontend
- [ ] Exportar conversaciones a PDF
- [ ] Alertas de anomalías (uso excesivo, errores)
- [ ] Replicación para alta disponibilidad

---

## 📚 Recursos

- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **FastAPI + Databases:** https://fastapi.tiangolo.com/advanced/sql-databases/

---

**🎉 ¡PostgreSQL integrado y funcionando!**
