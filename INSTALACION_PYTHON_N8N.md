# 🐍 Instalación de sentence-transformers en n8n

## 📦 Requisitos Previos

El nodo Python requiere que **sentence-transformers** esté instalado en el entorno Python de n8n.

## 🚀 Métodos de Instalación

### Opción 1: Si tienes acceso SSH a tu servidor n8n
```bash
# Conectar al servidor donde corre n8n
ssh tu_usuario@tu_servidor

# Instalar sentence-transformers
pip install sentence-transformers

# O si usas conda
conda install -c conda-forge sentence-transformers
```

### Opción 2: Si usas n8n Cloud
```bash
# En n8n Cloud, las dependencias se instalan automáticamente
# cuando importas el workflow con el nodo Python
# No necesitas hacer nada adicional
```

### Opción 3: Docker de n8n
Si usas n8n en Docker, crea un Dockerfile personalizado:

```dockerfile
FROM n8nio/n8n:latest

# Cambiar a usuario root para instalar dependencias
USER root

# Instalar sentence-transformers
RUN pip install sentence-transformers

# Volver al usuario n8n
USER node
```

## 🔧 Verificación de Instalación

Para verificar que sentence-transformers está correctamente instalado, puedes crear un nodo Python de prueba:

```python
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers está instalado correctamente")
    
    # Intentar cargar el modelo
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Modelo all-MiniLM-L6-v2 cargado correctamente")
    
    return [{"json": {"status": "success", "model_loaded": True}}]
    
except ImportError as e:
    print(f"❌ Error: sentence-transformers no está instalado: {e}")
    return [{"json": {"status": "error", "message": str(e)}}]
    
except Exception as e:
    print(f"❌ Error cargando modelo: {e}")
    return [{"json": {"status": "error", "message": str(e)}}]
```

## 📁 Descarga del Modelo

En la primera ejecución, sentence-transformers descargará automáticamente el modelo `all-MiniLM-L6-v2`:

- **Tamaño:** ~90MB
- **Ubicación:** `~/.cache/torch/sentence_transformers/`
- **Tiempo:** 1-2 minutos (solo primera vez)

## 🏃‍♂️ Ejecución del Workflow

Una vez que sentence-transformers esté instalado:

1. **Importa** el workflow actualizado (`plantilla_n8n.json`)
2. **Activa** el workflow
3. **Prueba** enviando una pregunta desde el frontend

El flujo debería ser:
```
Pregunta → Embedding Python → Búsqueda Pinecone → Respuesta Gemini → Frontend
```

## 🐛 Troubleshooting

### Error: "No module named 'sentence_transformers'"
```bash
# Verificar qué Python está usando n8n
which python
pip list | grep sentence

# Instalar en el Python correcto
pip install sentence-transformers
```

### Error: "Model download failed"
```bash
# Verificar conexión a internet
curl -I https://huggingface.co/

# Limpiar cache si hay problemas
rm -rf ~/.cache/torch/sentence_transformers/
```

### Error: "CUDA out of memory"
```python
# El modelo all-MiniLM-L6-v2 funciona bien en CPU
# No necesitas GPU para este modelo pequeño
```

## ✅ Checklist de Instalación

- [ ] sentence-transformers instalado en el entorno Python de n8n
- [ ] Conexión a internet disponible (para descargar modelo)
- [ ] Workflow importado con el nodo Python actualizado
- [ ] Variables de entorno configuradas (Pinecone, Google Gemini)
- [ ] Workflow activado en n8n

¡Listo para usar el sistema RAG con procesamiento 100% local! 🎉