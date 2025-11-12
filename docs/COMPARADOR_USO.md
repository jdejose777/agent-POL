# 🎉 Comparador de Artículos Integrado

## 📋 Cómo usar el comparador en el navegador:

### 1️⃣ Abrir la interfaz
```
http://127.0.0.1:5500/frontend/index.html
```

### 2️⃣ Usar el comparador

**Opción A - Botón en el header:**
1. Click en el botón "⚖️ Comparar Artículos" en la parte superior
2. Se abrirá un modal
3. Introduce el número del primer artículo (ej: 138)
4. Introduce el número del segundo artículo (ej: 142)
5. Click en "🔍 Comparar"
6. La comparación aparecerá en el chat

**Opción B - Directamente en el chat:**
Escribe en el chat cualquiera de estos formatos:
- "compara artículo 138 y 142"
- "diferencias entre 138 y 142"
- "138 vs 142"

### 3️⃣ Ejemplos de comparaciones interesantes:

**Doloso vs Imprudente:**
```
Artículo 1: 138 (homicidio doloso)
Artículo 2: 142 (homicidio imprudente)
```

**Robo vs Hurto:**
```
Artículo 1: 237 (robo con fuerza/violencia)
Artículo 2: 234 (hurto)
```

**Agresión sexual básica vs agravada:**
```
Artículo 1: 178 (agresión sexual básica)
Artículo 2: 179 (agresión sexual agravada)
```

**Lesiones básicas vs agravadas:**
```
Artículo 1: 147 (lesiones dolosas)
Artículo 2: 148 (lesiones con armas/medios peligrosos)
```

## ✨ Características del comparador:

✅ **Modal elegante** con animaciones
✅ **Validación de inputs** (no permite comparar el mismo artículo)
✅ **Integración con el chat** (las comparaciones aparecen como mensajes)
✅ **Shortcuts de teclado:**
   - Enter en Artículo 1 → salta a Artículo 2
   - Enter en Artículo 2 → ejecuta comparación
✅ **Cierre fácil:**
   - Click en X
   - Click fuera del modal
   - ESC (si añades el listener)

## 📊 Formato de respuesta:

El comparador genera:
- 📋 Resumen de cada artículo
- ⚖️ Tabla comparativa (penas, elementos, tipo)
- 🔍 3 diferencias clave explicadas
- 🤝 Similitudes (si existen)
- 📚 3 ejemplos prácticos:
  * Caso que aplica artículo 1
  * Caso que aplica artículo 2
  * Caso dudoso (cómo diferenciar)
- ⚡ Conclusión con criterio diferenciador

## 🎨 Interfaz:

El modal tiene:
- Fondo oscuro con blur
- Animación de entrada suave
- Campos numéricos para artículos
- Botón destacado para comparar
- "VS" entre los campos
- Diseño responsive (móvil/desktop)

## 🐛 Troubleshooting:

**Si el modal no aparece:**
- Verifica que el servidor está corriendo: http://127.0.0.1:8000/health
- Abre la consola del navegador (F12) y busca errores

**Si la comparación no funciona:**
- Verifica que ambos artículos existen en el código penal
- Revisa la consola del navegador para ver el error específico

**Si aparece error CORS:**
- Asegúrate de que el backend tiene CORS habilitado (ya debería estar)

## 🚀 Próximas mejoras posibles:

- [ ] Historial de comparaciones recientes
- [ ] Sugerencias de artículos relacionados
- [ ] Búsqueda por nombre de delito (no solo número)
- [ ] Exportar comparación como PDF
- [ ] Compartir comparación por URL
