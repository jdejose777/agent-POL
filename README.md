# 🤖 Agent POL - Sistema RAG Completo

Sistema completo de Retrieval-Augmented Generation (RAG) para procesar documentos PDF y crear un chat inteligente que puede responder preguntas sobre el contenido de los documentos.

## 🌟 Características Principales

- **📄 Procesamiento de PDFs**: Extrae texto, crea embeddings y almacena en Pinecone
- **💬 Interfaz de Chat Moderna**: Frontend responsive con tema oscuro
- **🔗 Integración n8n**: Conecta con workflows de automatización
- **🧠 RAG Inteligente**: Respuestas contextuales basadas en documentos
- **🎨 Diseño Responsive**: Funciona en desktop y móvil

## 🏗️ Arquitectura del Sistema

```
agent-POL/
├── backend-procesamiento/          # Procesador de PDFs
│   ├── procesar_pdf.py            # Script principal
│   ├── requirements.txt           # Dependencias Python
│   ├── .env.example              # Variables de entorno
│   └── README.md                 # Documentación del backend
├── frontend/                      # Interfaz de usuario
│   ├── index.html                # Estructura HTML
│   ├── style.css                 # Estilos modernos
│   └── app.js                    # Lógica del chat
└── README.md                     # Este archivo
```

## 🚀 Inicio Rápido

### 1. Clonar el Repositorio
```bash
git clone https://github.com/jdejose777/agent-POL.git
cd agent-POL
```

### 2. Configurar el Backend
```bash
cd backend-procesamiento
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus claves de API
```

### 3. Procesar un PDF
```bash
python procesar_pdf.py ruta/a/tu/documento.pdf
```

### 4. Configurar el Frontend
```bash
cd ../frontend
# Editar app.js y reemplazar 'TU_WEBHOOK_URL_AQUI' con tu webhook de n8n
```

### 5. Abrir la Interfaz
```bash
start index.html  # Windows
# o open index.html  # Mac/Linux
```

## ⚙️ Configuración

### Variables de Entorno (Backend)
```env
OPENAI_API_KEY=tu-clave-openai
PINECONE_API_KEY=tu-clave-pinecone
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=nombre-de-tu-indice
```

### Webhook de n8n (Frontend)
El webhook ya está configurado en `frontend/app.js`:
```javascript
const WEBHOOK_URL = 'https://jdejose.app.n8n.cloud/webhook/rag-chat-agent';
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.8+** - Lenguaje principal
- **pdfplumber** - Extracción de texto de PDFs
- **OpenAI API** - Generación de embeddings
- **Pinecone** - Base de datos vectorial
- **LangChain** - División de texto en chunks

### Frontend
- **HTML5 & CSS3** - Estructura y estilos
- **JavaScript ES6+** - Lógica de la aplicación
- **Variables CSS** - Tema personalizable
- **Fetch API** - Comunicación con n8n

## 📋 Flujo de Trabajo

1. **📄 Procesamiento**: Usuario ejecuta `procesar_pdf.py` con un PDF
2. **🔄 Extracción**: El script extrae texto y lo divide en chunks
3. **🧠 Embeddings**: Se generan embeddings con OpenAI
4. **💾 Almacenamiento**: Los vectores se suben a Pinecone
5. **💬 Chat**: Usuario hace preguntas en la interfaz web
6. **🔗 n8n**: El frontend envía la pregunta al webhook
7. **🔍 Búsqueda**: n8n busca información relevante en Pinecone
8. **📤 Respuesta**: El sistema devuelve una respuesta contextual

## 🎨 Capturas de Pantalla

### Interfaz de Chat
- Tema oscuro moderno
- Mensajes diferenciados por usuario/bot
- Indicador de "escribiendo..."
- Responsive para móvil

### Terminal de Procesamiento
- Progreso en tiempo real
- Mensajes informativos con emojis
- Manejo de errores robusto

## 📖 Documentación Detallada

- [Backend - Procesador de PDFs](backend-procesamiento/README.md)
- [Frontend - Interfaz de Chat](frontend/README.md) *(próximamente)*

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

1. Revisa la documentación en cada directorio
2. Abre un issue en GitHub
3. Consulta los logs en la consola del navegador

## 🔮 Próximas Funcionalidades

- [ ] Subida de archivos desde la interfaz web
- [ ] Soporte para múltiples formatos (Word, TXT, etc.)
- [ ] Historial de conversaciones
- [ ] Modo claro/oscuro configurable
- [ ] API REST nativa (sin n8n)
- [ ] Sistema de autenticación
- [ ] Dashboard de administración

---

**Desarrollado con ❤️ para hacer la información más accesible**

🔗 **Enlaces útiles:**
- [OpenAI API](https://platform.openai.com/)
- [Pinecone](https://www.pinecone.io/)
- [n8n](https://n8n.io/)
- [LangChain](https://langchain.com/)
