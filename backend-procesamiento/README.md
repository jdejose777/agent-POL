# Procesador de PDFs para Sistema RAG

Script Python profesional para procesar archivos PDF y cargarlos en Pinecone para sistemas de Retrieval-Augmented Generation (RAG).

## 🚀 Características

- ✅ Extracción de texto de archivos PDF con `pdfplumber`
- ✅ División inteligente del texto en chunks con superposición
- ✅ Generación de embeddings usando OpenAI API
- ✅ Almacenamiento en base de datos vectorial Pinecone
- ✅ Manejo robusto de errores
- ✅ Mensajes informativos del progreso
- ✅ Configuración mediante variables de entorno

## 📋 Requisitos

- Python 3.8 o superior
- Cuenta en OpenAI con créditos de API
- Cuenta en Pinecone (gratuita disponible)

## 🔧 Instalación

1. **Instalar las dependencias:**

```powershell
pip install -r requirements.txt
```

2. **Configurar las variables de entorno:**

Copia el archivo `.env.example` a `.env` y completa con tus credenciales:

```powershell
copy .env.example .env
```

Edita el archivo `.env` con tus claves reales:

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=mi-indice-rag
```

## 💻 Uso

### Uso básico

```powershell
python procesar_pdf.py ruta/al/archivo.pdf
```

### Con parámetros personalizados

```powershell
python procesar_pdf.py ruta/al/archivo.pdf --chunk-size 1500 --chunk-overlap 300
```

### Parámetros disponibles

- `pdf_path`: (Requerido) Ruta al archivo PDF a procesar
- `--chunk-size`: Tamaño de cada fragmento en caracteres (default: 1000)
- `--chunk-overlap`: Superposición entre fragmentos (default: 200)

## 📊 Ejemplo de salida

```
============================================================
🚀 PROCESADOR DE PDFs PARA SISTEMA RAG
============================================================

📋 Cargando variables de entorno...
✅ Variables de entorno cargadas correctamente

📄 Abriendo archivo PDF: documento.pdf
📖 Procesando 25 páginas...
✅ Texto extraído correctamente (45678 caracteres)

✂️  Dividiendo texto en chunks (tamaño: 1000, overlap: 200)...
✅ Texto dividido en 52 fragmentos

🤖 Generando embeddings para 52 fragmentos...
   Procesando fragmentos 1 a 52...
✅ Embeddings generados correctamente (52 vectores)

🌲 Conectando con Pinecone (índice: mi-indice-rag)...
📤 Subiendo 52 vectores a Pinecone...
   Subidos 52/52 vectores...
✅ Datos subidos correctamente a Pinecone
📊 Total de vectores en el índice: 52

============================================================
✨ PROCESO COMPLETADO EXITOSAMENTE
============================================================
📄 Archivo procesado: documento.pdf
📊 Total de fragmentos: 52
🤖 Embeddings generados: 52
🌲 Índice Pinecone: mi-indice-rag
============================================================
```

## 🏗️ Arquitectura del Script

El script está organizado en funciones modulares:

1. **`cargar_variables_entorno()`**: Carga y valida las variables de entorno
2. **`extraer_texto_pdf()`**: Extrae el texto del PDF
3. **`dividir_texto_en_chunks()`**: Divide el texto en fragmentos
4. **`generar_embeddings()`**: Genera embeddings con OpenAI
5. **`subir_a_pinecone()`**: Sube los datos a Pinecone
6. **`main()`**: Orquesta todo el proceso

## 🔍 Detalles técnicos

- **Modelo de embeddings**: `text-embedding-3-small` de OpenAI
- **Dimensión de vectores**: 1536 (automático según el modelo)
- **Métrica de similitud**: Cosine similarity
- **Procesamiento por lotes**: Optimizado para APIs (100 items/batch)

## 🛠️ Solución de problemas

### Error: Variables de entorno faltantes

Asegúrate de que el archivo `.env` existe y contiene todas las variables necesarias.

### Error: Archivo PDF no encontrado

Verifica que la ruta al PDF sea correcta y que el archivo existe.

### Error: Rate limit de OpenAI

Si procesas muchos documentos, considera agregar delays entre llamadas o usar una cuenta con mayor límite.

### Error: Índice de Pinecone no existe

El script creará automáticamente el índice si no existe, pero asegúrate de tener permisos en tu cuenta de Pinecone.

## 📝 Notas

- El script guarda metadata útil en cada vector (texto original, nombre del archivo, ID del chunk)
- Los IDs de vectores siguen el formato: `{nombre_archivo}_chunk_{numero}`
- El procesamiento es eficiente y muestra el progreso en tiempo real

## 🤝 Contribuciones

Este script está diseñado para ser extensible. Posibles mejoras futuras:

- Soporte para otros formatos de documentos (Word, TXT, etc.)
- Múltiples modelos de embeddings
- Cache de embeddings para evitar regeneración
- Soporte para múltiples archivos en lote

## 📄 Licencia

Este script es de uso libre para proyectos educativos y comerciales.
