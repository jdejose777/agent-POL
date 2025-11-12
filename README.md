# 🤖 Agent-POL - Sistema RAG para Código Penal Español# ⚖️ Agent POL - Asistente Jurídico de Derecho Penal Español



Sistema de Recuperación-Generación Aumentada (RAG) para consultas sobre el Código Penal Español utilizando **Vertex AI (Google Cloud)**, **Pinecone**, **Redis** y **PostgreSQL**.Sistema RAG (Retrieval-Augmented Generation) especializado en consultas sobre el Código Penal español. Utiliza Vertex AI de Google Cloud y Pinecone para proporcionar respuestas precisas basadas en el texto oficial del Código Penal.



---## 🌟 Características Principales



## 📋 Tabla de Contenidos- **🎯 Búsqueda Híbrida**: Combina búsqueda exacta de artículos con búsqueda semántica

- **📊 Respuestas Estructuradas**: Fichas legales con artículos, penas, explicación y resumen

- [Características](#características)- **� Exactitud Mejorada**: Sistema que diferencia "Art. 142" de "Art. 142 bis"

- [Arquitectura](#arquitectura)- **� Interfaz Moderna**: Chat responsive con renderizado Markdown

- [Estructura del Proyecto](#estructura-del-proyecto)- **🧠 IA Avanzada**: Google Vertex AI (text-embedding-004 + gemini-2.0-flash-001)

- [Instalación](#instalación)- **⚡ Alto Rendimiento**: FastAPI + Pinecone para respuestas rápidas

- [Uso](#uso)

- [Documentación](#documentación)## 🏗️ Arquitectura del Sistema

- [Testing](#testing)

- [API Endpoints](#api-endpoints)```

- [Tecnologías](#tecnologías)agent-POL/

├── backend-api/                   # API FastAPI con Vertex AI

---│   ├── main.py                   # API principal con lógica RAG

│   ├── requirements.txt          # Dependencias Python

## ✨ Características│   └── .env                      # Variables de entorno (no incluido)

├── backend-procesamiento/        # Procesador de PDFs (legacy)

### 🚀 **Core Features**│   └── procesar-pdf.py          # Script de carga inicial

- ✅ **RAG con Vertex AI**: Generación de respuestas con Gemini 2.0 Flash├── frontend/                     # Interfaz de usuario

- ✅ **Embeddings de Google**: text-embedding-004 para búsqueda semántica│   ├── index.html               # Estructura HTML

- ✅ **Vector Database**: Pinecone para almacenamiento de embeddings│   ├── style.css                # Estilos con tema oscuro

- ✅ **Caché Persistente**: Redis para artículos consultados frecuentemente│   └── app.js                   # Lógica del chat con Markdown

- ✅ **Historial Completo**: PostgreSQL para conversaciones y analytics└── README.md                    # Este archivo

- ✅ **Búsqueda Instantánea**: Caché O(1) para 711 artículos en memoria```

- ✅ **Búsqueda Exacta**: Regex sobre PDF completo del Código Penal

- ✅ **Expansión Semántica**: Sinónimos legales automáticos## 🚀 Inicio Rápido

- ✅ **Memoria Conversacional**: Historial de chat con contexto

### 1. Requisitos Previos

### 🔍 **Funcionalidades Avanzadas**- Python 3.13+

- ⚖️ **Comparador de Artículos**: Análisis comparativo entre artículos- Cuenta de Google Cloud con Vertex AI habilitado

- 📊 **Dashboard de Analytics**: Estadísticas de uso en tiempo real- Cuenta de Pinecone

- 🔄 **Reconstrucción Inteligente**: Reensambla artículos largos fragmentados- Git

- 🎯 **Validación Bidireccional**: Corrige errores comunes del usuario

- 📈 **Métricas de Performance**: Tracking de tiempos de respuesta y tokens### 2. Clonar el Repositorio

```bash

---git clone https://github.com/jdejose777/agent-POL.git

cd agent-POL

## 🏗️ Arquitectura```



```### 3. Configurar el Backend

┌─────────────┐      ┌──────────────┐      ┌─────────────┐

│   Frontend  │────▶ │  Backend API │────▶ │  Vertex AI  │#### Crear entorno virtual

│   (HTML/JS) │      │   (FastAPI)  │      │  (Gemini)   │```bash

└─────────────┘      └──────────────┘      └─────────────┘cd backend-api

                            │python -m venv .venv

                            ├────▶ Pinecone (Vector DB).venv\Scripts\activate  # Windows

                            ├────▶ Redis (Cache)# o source .venv/bin/activate  # Mac/Linux

                            ├────▶ PostgreSQL (History)```

                            └────▶ PDF Local (Exact Search)

```#### Instalar dependencias

```bash

---pip install -r requirements.txt

```

## 📁 Estructura del Proyecto

#### Configurar variables de entorno

```Crea un archivo `.env` en `backend-api/`:

agent-POL/```env

│PINECONE_API_KEY=tu-clave-pinecone

├── 📂 backend-api/              # API principal (FastAPI)PINECONE_INDEX_NAME=codigo-penal-vertex-ai

├── 📂 frontend/                 # Interfaz webPINECONE_ENVIRONMENT=us-east-1

├── 📂 tests/                    # Tests unitarios (25 tests)GOOGLE_CLOUD_PROJECT=tu-proyecto-gcp

├── 📂 scripts/                  # Scripts utilitariosGOOGLE_CLOUD_LOCATION=us-central1

├── 📂 docs/                     # Documentación completa```

├── 📂 config/                   # Archivos de configuración

├── 📂 documentos/               # Documentos fuente#### Iniciar el servidor

└── 📂 logs/                     # Logs de la aplicación```bash

```uvicorn main:app --reload --host 0.0.0.0 --port 8000

```

---

El servidor estará disponible en `http://localhost:8000`

## 🚀 Instalación Rápida

### 4. Configurar el Frontend

```bash

# 1. Clonar repositorioAbre `frontend/index.html` en tu navegador. El frontend ya está configurado para conectarse a `http://localhost:8000`.

git clone https://github.com/jdejose777/agent-POL.git

cd agent-POL## ⚙️ Configuración Detallada



# 2. Crear entorno virtual### Backend (FastAPI + Vertex AI)

python -m venv .venv

.venv\Scripts\activate**Variables de entorno obligatorias:**

- `PINECONE_API_KEY`: Tu API key de Pinecone

# 3. Instalar dependencias- `PINECONE_INDEX_NAME`: Nombre del índice (por defecto: `codigo-penal-vertex-ai`)

cd backend-api- `GOOGLE_CLOUD_PROJECT`: ID de tu proyecto en Google Cloud

pip install -r requirements.txt- `GOOGLE_CLOUD_LOCATION`: Región de Vertex AI (por defecto: `us-central1`)



# 4. Configurar .env (copiar de .env.example)**Modelos utilizados:**

- **Embeddings**: `text-embedding-004` (768 dimensiones)

# 5. Iniciar servicios (Docker)- **Generación**: `gemini-2.0-flash-001`

docker run -d -p 6379:6379 --name redis-cache redis:latest

docker run -d -p 5432:5432 --name postgres-agentpol \**Parámetros RAG:**

  -e POSTGRES_PASSWORD=agentpol2025 \- Chunk size: 800 caracteres

  -e POSTGRES_USER=agentpol \- Chunk overlap: 100 caracteres

  -e POSTGRES_DB=conversations_db \- Top K: 10 resultados

  postgres:16-alpine- Umbral de similitud: 0.35 (artículos específicos) / 0.45 (consultas generales)



# 6. Iniciar backend### Frontend (HTML/CSS/JS)

uvicorn main:app --reload --host 127.0.0.1 --port 8000

**Características:**

# 7. Abrir frontend- Renderizado Markdown con `marked.js`

start chrome ../frontend/index.html- Tema oscuro profesional

```- Diseño responsive

- Indicador de "escribiendo..."

---- Scroll automático



## 📚 Documentación Completa**Para cambiar la URL del backend**, edita `frontend/app.js`:

```javascript

| Documento | Descripción |const API_URL = 'http://localhost:8000/query'; // Cambia si es necesario

|-----------|-------------|```

| [POSTGRESQL_INTEGRATION.md](POSTGRESQL_INTEGRATION.md) | PostgreSQL: instalación, modelos, queries |

| [REDIS_INTEGRATION.md](REDIS_INTEGRATION.md) | Redis: configuración, testing, monitoreo |## 🛠️ Tecnologías Utilizadas

| [SISTEMA-VERTEX-AI.md](SISTEMA-VERTEX-AI.md) | Integración con Vertex AI |

| [COMPARADOR_USO.md](COMPARADOR_USO.md) | Uso del comparador de artículos |### Backend

- **Python 3.13** - Lenguaje principal

---- **FastAPI** - Framework web moderno y rápido

- **Google Vertex AI** - Embeddings y generación con Gemini

## 🌐 API Endpoints- **Pinecone** - Base de datos vectorial (1,146 vectores del Código Penal)

- **PyPDF2** - Procesamiento de PDFs

```http- **LangChain** - División de texto en chunks

POST   /chat                    # Consulta con memoria conversacional

GET    /comparar?art1=X&art2=Y  # Comparar artículos### Frontend

GET    /conversations           # Lista de conversaciones- **HTML5 & CSS3** - Estructura y estilos

GET    /conversations/{id}      # Detalle de conversación- **JavaScript ES6+** - Lógica de la aplicación

GET    /analytics               # Estadísticas de uso- **Marked.js** - Renderizado de Markdown

GET    /health                  # Estado del sistema- **Fetch API** - Comunicación con el backend

GET    /docs                    # Documentación Swagger

```### Infraestructura

- **Google Cloud Platform** - Hosting de Vertex AI

---- **Pinecone Cloud** - Base de datos vectorial (us-east-1)



## 🧪 Testing## 📋 Flujo de Trabajo



```bash### Consulta de Artículo Específico

# Todos los tests (25 tests)1. Usuario pregunta: "artículo 142"

pytest -v2. Sistema detecta número de artículo con regex

3. Búsqueda exacta en Pinecone (evita confusión con "142 bis")

# Tests de Redis (10 tests)4. Respuesta con texto literal del artículo

pytest tests/test_redis_cache.py -v

### Consulta Conceptual

# Tests de PostgreSQL (15 tests)1. Usuario pregunta: "violación a menor de 14 años"

pytest tests/test_postgresql.py -v2. Enriquecimiento de consulta con sinónimos legales

3. Generación de embedding con Vertex AI

# Test interactivo4. Búsqueda semántica en Pinecone (Top 10)

python scripts/test_redis_interactive.py5. Filtrado adaptativo por similitud

```6. Generación de ficha estructurada con Gemini:

   - **Título del delito**

---   - **Artículos relevantes** (máx. 5)

   - **Penas aplicables** (con números: "1 a 6 años")

## 🛠️ Stack Tecnológico   - **Explicación legal** (diferencia dolo/imprudencia)

   - **Resumen final** (fórmula + rango de penas)

**Backend:** FastAPI, SQLAlchemy, Redis, PostgreSQL  

**AI/ML:** Vertex AI, Gemini 2.0, text-embedding-004, Pinecone  ## 🎯 Mejoras Implementadas

**Frontend:** HTML5, CSS3, JavaScript  

**DevOps:** Docker, Pytest, Git### Sistema Híbrido de Búsqueda

- ✅ Búsqueda exacta de artículos por número (regex)

---- ✅ Soporte para artículos bis, ter, quater

- ✅ Fallback a búsqueda semántica si no hay coincidencia exacta

## 📊 Performance

### Formato de Respuestas

| Operación | Tiempo |- ✅ Fichas estructuradas con Markdown

|-----------|--------|- ✅ Títulos y subtítulos jerarquizados (##, ###)

| Redis cache | ~2ms |- ✅ Listas con bullets para mejor legibilidad

| Memoria cache | <1ms |- ✅ Negritas en conceptos clave

| Búsqueda PDF | ~10ms |- ✅ Penas expresadas con números (no letras)

| Búsqueda semántica | ~50ms |

| Generación completa | 1-5s |### Precisión Legal

- ✅ Diferenciación entre dolo (intención) e imprudencia

---- ✅ Aplicación de artículos por analogía si es necesario

- ✅ Terminología legal precisa (sin vaguedades)

## 👤 Autor- ✅ Tono técnico similar a informes jurídicos



**jdejose777** - [GitHub](https://github.com/jdejose777)### Frontend Mejorado

- ✅ Renderizado completo de Markdown

---- ✅ Estilos para tablas, código, listas, encabezados

- ✅ Tema oscuro profesional

**⚡ Hecho con FastAPI, Vertex AI y mucho ☕**- ✅ Mensajes escaneables en 10-15 segundos


## 📊 Datos del Sistema

**Base de Conocimiento:**
- 📄 Código Penal español completo (429 páginas)
- 🧩 1,146 vectores en Pinecone
- 📏 Chunks de 800 caracteres con overlap de 100
- 🎯 768 dimensiones por embedding

**Rendimiento:**
- ⚡ Respuesta típica: 2-4 segundos
- 🔍 Búsqueda exacta: <1 segundo
- 🧠 Generación RAG: 2-3 segundos
- 💾 Índice Pinecone: latencia <100ms

## 🧪 Ejemplos de Uso

### Consulta de Artículo Específico
```
Usuario: "142"
Sistema: [Texto literal completo del Artículo 142 del Código Penal]
```

### Consulta Conceptual
```
Usuario: "robo de coche y accidente"
Sistema: 
## Robo de vehículo con accidente de tráfico

### Artículos relevantes:
- Art. 244 – Uso no autorizado de vehículo a motor
- Art. 379 – Conducción temeraria
- Art. 142 – Homicidio imprudente (si hay víctimas)

### Penas aplicables:
- Art. 244: Multa de 12 a 24 meses o trabajos de 31 a 90 días
- Art. 379: Prisión de 6 meses a 2 años + inhabilitación para conducir
- Art. 142: Prisión de 1 a 4 años (si causa muerte por imprudencia)

[... explicación legal detallada ...]

### Resumen final:
→ Robo + conducción temeraria + accidente = Arts. 244 + 379 (+142 si hay víctimas)
→ Penas: Multa + prisión de 6 meses a 2 años + inhabilitación + posible prisión de 1 a 4 años
```

## 📖 Documentación de la API

### Endpoint Principal: `/query`

**Método:** POST

**Body:**
```json
{
  "query": "tu consulta legal aquí"
}
```

**Respuesta:**
```json
{
  "response": "respuesta formateada en Markdown",
  "metadata": {
    "num_fragmentos": 10,
    "tiene_contexto": true,
    "modelo": "gemini-2.0-flash-001",
    "embedding_model": "text-embedding-004",
    "metodo": "rag_vector_search"
  }
}
```

### Endpoint de Salud: `/health`

**Método:** GET

**Respuesta:**
```json
{
  "status": "healthy",
  "pinecone_stats": {
    "dimension": 768,
    "total_vector_count": 1146
  }
}
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🆘 Soporte

Si encuentras algún problema o tienes preguntas:

1. Revisa los logs del servidor FastAPI
2. Verifica las variables de entorno en `.env`
3. Consulta la consola del navegador (F12)
4. Abre un issue en GitHub

## 🔮 Roadmap

- [x] Migración de n8n a FastAPI nativo
- [x] Integración con Vertex AI (Google Cloud)
- [x] Sistema híbrido de búsqueda exacta + semántica
- [x] Soporte para artículos bis/ter/quater
- [x] Eliminación de límites de truncado
- [x] Frontend con renderizado Markdown
- [x] Fichas estructuradas con penas
- [x] Formato numérico para penas
- [ ] Sistema de memoria conversacional
- [ ] API de autenticación
- [ ] Dashboard de administración
- [ ] Exportación de consultas a PDF
- [ ] Modo de comparación entre artículos
- [ ] Integración con jurisprudencia del TS

## 📈 Historial de Cambios

### v3.0 (Noviembre 2025) - Prompt Legal Profesional
- ✅ Formato de fichas estructuradas
- ✅ Diferenciación dolo vs imprudencia
- ✅ Penas en formato numérico
- ✅ Tono técnico jurídico

### v2.0 (Noviembre 2025) - Frontend Markdown
- ✅ Renderizado completo de Markdown
- ✅ Estilos profesionales para respuestas
- ✅ Mejora significativa en legibilidad

### v1.0 (Noviembre 2025) - Sistema Híbrido
- ✅ Migración completa a Vertex AI
- ✅ Búsqueda exacta + RAG
- ✅ Soporte bis/ter/quater
- ✅ Eliminación de truncado

---

**Desarrollado con ⚖️ para democratizar el acceso al Código Penal español**

🔗 **Enlaces útiles:**
- [Google Vertex AI](https://cloud.google.com/vertex-ai)
- [Pinecone](https://www.pinecone.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Código Penal español (BOE)](https://www.boe.es/buscar/act.php?id=BOE-A-1995-25444)
