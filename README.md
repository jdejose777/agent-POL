# ⚖️ Agent POL - Asistente Jurídico de Derecho Penal Español

Sistema RAG (Retrieval-Augmented Generation) especializado en consultas sobre el Código Penal español. Utiliza Vertex AI de Google Cloud y Pinecone para proporcionar respuestas precisas basadas en el texto oficial del Código Penal.

## 🌟 Características Principales

- **🎯 Búsqueda Híbrida**: Combina búsqueda exacta de artículos con búsqueda semántica
- **📊 Respuestas Estructuradas**: Fichas legales con artículos, penas, explicación y resumen
- **� Exactitud Mejorada**: Sistema que diferencia "Art. 142" de "Art. 142 bis"
- **� Interfaz Moderna**: Chat responsive con renderizado Markdown
- **🧠 IA Avanzada**: Google Vertex AI (text-embedding-004 + gemini-2.0-flash-001)
- **⚡ Alto Rendimiento**: FastAPI + Pinecone para respuestas rápidas

## 🏗️ Arquitectura del Sistema

```
agent-POL/
├── backend-api/                   # API FastAPI con Vertex AI
│   ├── main.py                   # API principal con lógica RAG
│   ├── requirements.txt          # Dependencias Python
│   └── .env                      # Variables de entorno (no incluido)
├── backend-procesamiento/        # Procesador de PDFs (legacy)
│   └── procesar-pdf.py          # Script de carga inicial
├── frontend/                     # Interfaz de usuario
│   ├── index.html               # Estructura HTML
│   ├── style.css                # Estilos con tema oscuro
│   └── app.js                   # Lógica del chat con Markdown
└── README.md                    # Este archivo
```

## 🚀 Inicio Rápido

### 1. Requisitos Previos
- Python 3.13+
- Cuenta de Google Cloud con Vertex AI habilitado
- Cuenta de Pinecone
- Git

### 2. Clonar el Repositorio
```bash
git clone https://github.com/jdejose777/agent-POL.git
cd agent-POL
```

### 3. Configurar el Backend

#### Crear entorno virtual
```bash
cd backend-api
python -m venv .venv
.venv\Scripts\activate  # Windows
# o source .venv/bin/activate  # Mac/Linux
```

#### Instalar dependencias
```bash
pip install -r requirements.txt
```

#### Configurar variables de entorno
Crea un archivo `.env` en `backend-api/`:
```env
PINECONE_API_KEY=tu-clave-pinecone
PINECONE_INDEX_NAME=codigo-penal-vertex-ai
PINECONE_ENVIRONMENT=us-east-1
GOOGLE_CLOUD_PROJECT=tu-proyecto-gcp
GOOGLE_CLOUD_LOCATION=us-central1
```

#### Iniciar el servidor
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en `http://localhost:8000`

### 4. Configurar el Frontend

Abre `frontend/index.html` en tu navegador. El frontend ya está configurado para conectarse a `http://localhost:8000`.

## ⚙️ Configuración Detallada

### Backend (FastAPI + Vertex AI)

**Variables de entorno obligatorias:**
- `PINECONE_API_KEY`: Tu API key de Pinecone
- `PINECONE_INDEX_NAME`: Nombre del índice (por defecto: `codigo-penal-vertex-ai`)
- `GOOGLE_CLOUD_PROJECT`: ID de tu proyecto en Google Cloud
- `GOOGLE_CLOUD_LOCATION`: Región de Vertex AI (por defecto: `us-central1`)

**Modelos utilizados:**
- **Embeddings**: `text-embedding-004` (768 dimensiones)
- **Generación**: `gemini-2.0-flash-001`

**Parámetros RAG:**
- Chunk size: 800 caracteres
- Chunk overlap: 100 caracteres
- Top K: 10 resultados
- Umbral de similitud: 0.35 (artículos específicos) / 0.45 (consultas generales)

### Frontend (HTML/CSS/JS)

**Características:**
- Renderizado Markdown con `marked.js`
- Tema oscuro profesional
- Diseño responsive
- Indicador de "escribiendo..."
- Scroll automático

**Para cambiar la URL del backend**, edita `frontend/app.js`:
```javascript
const API_URL = 'http://localhost:8000/query'; // Cambia si es necesario
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.13** - Lenguaje principal
- **FastAPI** - Framework web moderno y rápido
- **Google Vertex AI** - Embeddings y generación con Gemini
- **Pinecone** - Base de datos vectorial (1,146 vectores del Código Penal)
- **PyPDF2** - Procesamiento de PDFs
- **LangChain** - División de texto en chunks

### Frontend
- **HTML5 & CSS3** - Estructura y estilos
- **JavaScript ES6+** - Lógica de la aplicación
- **Marked.js** - Renderizado de Markdown
- **Fetch API** - Comunicación con el backend

### Infraestructura
- **Google Cloud Platform** - Hosting de Vertex AI
- **Pinecone Cloud** - Base de datos vectorial (us-east-1)

## 📋 Flujo de Trabajo

### Consulta de Artículo Específico
1. Usuario pregunta: "artículo 142"
2. Sistema detecta número de artículo con regex
3. Búsqueda exacta en Pinecone (evita confusión con "142 bis")
4. Respuesta con texto literal del artículo

### Consulta Conceptual
1. Usuario pregunta: "violación a menor de 14 años"
2. Enriquecimiento de consulta con sinónimos legales
3. Generación de embedding con Vertex AI
4. Búsqueda semántica en Pinecone (Top 10)
5. Filtrado adaptativo por similitud
6. Generación de ficha estructurada con Gemini:
   - **Título del delito**
   - **Artículos relevantes** (máx. 5)
   - **Penas aplicables** (con números: "1 a 6 años")
   - **Explicación legal** (diferencia dolo/imprudencia)
   - **Resumen final** (fórmula + rango de penas)

## 🎯 Mejoras Implementadas

### Sistema Híbrido de Búsqueda
- ✅ Búsqueda exacta de artículos por número (regex)
- ✅ Soporte para artículos bis, ter, quater
- ✅ Fallback a búsqueda semántica si no hay coincidencia exacta

### Formato de Respuestas
- ✅ Fichas estructuradas con Markdown
- ✅ Títulos y subtítulos jerarquizados (##, ###)
- ✅ Listas con bullets para mejor legibilidad
- ✅ Negritas en conceptos clave
- ✅ Penas expresadas con números (no letras)

### Precisión Legal
- ✅ Diferenciación entre dolo (intención) e imprudencia
- ✅ Aplicación de artículos por analogía si es necesario
- ✅ Terminología legal precisa (sin vaguedades)
- ✅ Tono técnico similar a informes jurídicos

### Frontend Mejorado
- ✅ Renderizado completo de Markdown
- ✅ Estilos para tablas, código, listas, encabezados
- ✅ Tema oscuro profesional
- ✅ Mensajes escaneables en 10-15 segundos

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
