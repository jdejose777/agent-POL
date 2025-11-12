/**
 * CONFIGURACIÓN DE LA APLICACIÓN DE CHAT RAG
 * Este script maneja la interfaz de usuario para el chat con el sistema RAG
 */

// URL de la nueva API FastAPI (reemplaza n8n)
const WEBHOOK_URL = 'http://10.1.162.145:8000/chat';

// Elementos del DOM - obtenemos referencias a los elementos principales
const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const loadingIndicator = document.getElementById('loadingIndicator');

// Estado de la aplicación
let isLoading = false;
let typingIndicatorElement = null;
let conversationHistory = []; // ⚡ MEJORA #3: Historial conversacional

/**
 * INICIALIZACIÓN DE LA APLICACIÓN
 * Se ejecuta cuando el DOM está completamente cargado
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Aplicación de chat inicializada');
    
    // Enfocar el campo de entrada para mejor UX
    messageInput.focus();
    
    // Configurar todos los event listeners
    setupEventListeners();
    
    // Configurar comparador
    setupComparador();
    
    // Verificar configuración del webhook
    checkWebhookConfiguration();
});

/**
 * CONFIGURACIÓN DE EVENT LISTENERS
 * Establece todos los manejadores de eventos de la interfaz
 */
function setupEventListeners() {
    // Manejar envío del formulario
    chatForm.addEventListener('submit', handleFormSubmit);
    
    // Permitir envío con Enter (sin Shift)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleFormSubmit(e);
        }
    });
    
    // Habilitar/deshabilitar botón según contenido del input
    messageInput.addEventListener('input', () => {
        const hasText = messageInput.value.trim().length > 0;
        sendButton.disabled = !hasText || isLoading;
    });
    
    console.log('✅ Event listeners configurados');
}

/**
 * MANEJO DEL ENVÍO DEL FORMULARIO
 * Función principal que procesa el envío de mensajes del usuario
 */
async function handleFormSubmit(e) {
    // Prevenir el comportamiento por defecto (recargar la página)
    e.preventDefault();
    
    // Obtener el texto del input y limpiarlo de espacios
    const userMessage = messageInput.value.trim();
    
    // Si el mensaje está vacío o ya estamos procesando, no hacer nada
    if (!userMessage || isLoading) {
        return;
    }
    
    console.log('📝 Procesando mensaje del usuario:', userMessage);
    
    // Crear y añadir el mensaje del usuario al chat
    addUserMessage(userMessage);
    
    // Limpiar el input y deshabilitar el botón
    messageInput.value = '';
    sendButton.disabled = true;
    isLoading = true;
    
    // Mostrar indicador de "escribiendo..."
    showTypingIndicator();
    
    try {
        // Hacer petición POST al webhook de n8n
        const botResponse = await sendMessageToWebhook(userMessage);
        
        // Quitar el indicador de "escribiendo..."
        hideTypingIndicator();
        
        // Crear y añadir la respuesta del bot al chat
        addBotMessage(botResponse);
        
        console.log('✅ Respuesta del bot recibida y mostrada');
        
    } catch (error) {
        console.error('❌ Error al procesar el mensaje:', error);
        
        // Quitar el indicador de "escribiendo..."
        hideTypingIndicator();
        
        // Mostrar mensaje de error al usuario
        addBotMessage(
            'Lo siento, hubo un error al procesar tu mensaje. Por favor, verifica tu conexión e inténtalo de nuevo.',
            'error'
        );
    } finally {
        // Restaurar el estado de la interfaz
        isLoading = false;
        sendButton.disabled = false;
        messageInput.focus();
        
        // Hacer scroll automático al último mensaje
        scrollToLastMessage();
    }
}

/**
 * ENVÍO DE MENSAJE AL WEBHOOK DE N8N
 * Realiza la petición HTTP al webhook con el mensaje del usuario
 * 
 * ⚡ MEJORA #3: Incluye historial conversacional en cada petición
 */
async function sendMessageToWebhook(pregunta) {
    console.log('🌐 Enviando petición al webhook de n8n...');
    
    // Verificar que la URL del webhook esté configurada
    if (WEBHOOK_URL === 'TU_WEBHOOK_URL_AQUI') {
        throw new Error('URL del webhook no configurada. Por favor, actualiza la variable WEBHOOK_URL en app.js');
    }
    
    console.log('🌐 Enviando petición a:', WEBHOOK_URL);
    console.log('💬 Historial actual:', conversationHistory.length, 'mensajes');
    
    // ⚡ IMPORTANTE: Mostrar el historial que se va a enviar
    if (conversationHistory.length > 0) {
        console.log('📋 Enviando historial:');
        conversationHistory.forEach((msg, idx) => {
            console.log(`   ${idx + 1}. ${msg.role}: ${msg.content.substring(0, 50)}...`);
        });
    }
    
    try {
        // Realizar petición POST con fetch, incluyendo el historial
        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            // Cuerpo de la petición en formato JSON con historial
            body: JSON.stringify({
                pregunta: pregunta,
                historial: conversationHistory  // ⚡ Enviar historial conversacional
            })
        });
        
        // Verificar que la respuesta sea exitosa
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} - ${response.statusText}`);
        }
        
        // Obtener la respuesta en formato JSON
        const data = await response.json();
        
        console.log('📨 Respuesta del webhook recibida:', data);
        
        // ⚡ DESPUÉS de recibir respuesta, guardar AMBOS mensajes en el historial
        conversationHistory.push({
            role: "user",
            content: pregunta
        });
        
        const respuestaBot = data.respuesta || data.response || data.message || 'Respuesta recibida del sistema RAG';
        
        conversationHistory.push({
            role: "assistant",
            content: respuestaBot
        });
        
        // Limitar historial a últimos 10 mensajes (5 intercambios) para no sobrecargar
        if (conversationHistory.length > 10) {
            conversationHistory = conversationHistory.slice(-10);
        }
        
        console.log('💾 Historial actualizado a:', conversationHistory.length, 'mensajes');
        
        return respuestaBot;
        
    } catch (error) {
        console.error('🚨 Error en la petición al webhook:', error);
        
        // Relanzar el error para que sea manejado por la función principal
        throw new Error(`Error al conectar con el sistema RAG: ${error.message}`);
    }
}

/**
 * CREAR Y AÑADIR MENSAJE DEL USUARIO AL CHAT
 * Crea un elemento div para mostrar el mensaje del usuario
 */
function addUserMessage(message) {
    console.log('👤 Añadiendo mensaje del usuario al chat');
    
    // Crear el elemento div para el mensaje
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    // Construir el HTML del mensaje con avatar y contenido
    messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    
    // Añadir el mensaje al contenedor del chat
    chatContainer.appendChild(messageDiv);
    
    // Hacer scroll automático al nuevo mensaje
    scrollToLastMessage();
}

/**
 * RESALTAR ARTÍCULOS EN EL CONTENIDO
 * Detecta menciones a artículos del Código Penal y les añade highlighting
 * @param {string} htmlContent - Contenido HTML procesado por marked
 * @returns {string} - Contenido con artículos resaltados
 */
function highlightArticulos(htmlContent) {
    // Patrones para detectar artículos:
    // - "Artículo 234"
    // - "artículo 234"
    // - "art. 234"
    // - "Art. 234"
    // - "arts. 234 y 456" (múltiples artículos)
    // - "Artículos 234, 456 y 789"
    
    const patronArticulos = /(Artículo|artículo|Art\.|art\.|Arts\.|arts\.|Artículos|artículos)\s+(\d+(?:\s*,\s*\d+)*(?:\s+y\s+\d+)?)/gi;
    
    const contentWithHighlight = htmlContent.replace(patronArticulos, (match, prefix, numeros) => {
        // Extraer todos los números de artículos mencionados
        const numerosArray = numeros.match(/\d+/g);
        
        // Construir el texto resaltado
        let highlightedText = '';
        
        if (numerosArray.length === 1) {
            // Un solo artículo
            highlightedText = `<span class="article-highlight" data-article="${numerosArray[0]}" onclick="scrollToArticle(${numerosArray[0]})">${prefix} ${numerosArray[0]}</span>`;
        } else {
            // Múltiples artículos - resaltar cada uno
            const numerosParts = numeros.split(/(\d+)/);
            highlightedText = prefix + ' ';
            numerosParts.forEach(part => {
                if (/^\d+$/.test(part)) {
                    // Es un número - resaltarlo
                    highlightedText += `<span class="article-highlight" data-article="${part}" onclick="scrollToArticle(${part})">${part}</span>`;
                } else if (part.trim()) {
                    // Es texto separador (comas, "y", etc.)
                    highlightedText += part;
                }
            });
        }
        
        return highlightedText;
    });
    
    console.log('🎨 Artículos resaltados en el contenido');
    return contentWithHighlight;
}

/**
 * SCROLL A UN ARTÍCULO ESPECÍFICO (FUNCIONALIDAD FUTURA)
 * Placeholder para navegación a artículos específicos
 * @param {number} numeroArticulo - Número del artículo
 */
function scrollToArticle(numeroArticulo) {
    console.log(`📜 Navegando al Artículo ${numeroArticulo} (funcionalidad futura)`);
    // TODO: Implementar navegación o búsqueda del artículo en el chat
    // Por ahora solo mostramos un mensaje
    alert(`Artículo ${numeroArticulo} del Código Penal\n\n(La navegación automática se implementará en una futura versión)`);
}

/**
 * CREAR Y AÑADIR MENSAJE DEL BOT AL CHAT
 * Crea un elemento div para mostrar la respuesta del bot con formato Markdown
 */
function addBotMessage(message, type = 'normal') {
    console.log('🤖 Añadiendo mensaje del bot al chat');
    
    // Crear el elemento div para el mensaje
    const messageDiv = document.createElement('div');
    messageDiv.className = `message bot-message${type !== 'normal' ? ` ${type}` : ''}`;
    
    // Procesar el mensaje con Markdown si está disponible
    let formattedMessage;
    if (typeof marked !== 'undefined') {
        // Configurar marked para mejor formato
        marked.setOptions({
            breaks: true,  // Respetar saltos de línea
            gfm: true,     // GitHub Flavored Markdown
        });
        formattedMessage = marked.parse(message);
        
        // ⚡ MEJORA #8: Resaltar artículos del Código Penal
        formattedMessage = highlightArticulos(formattedMessage);
    } else {
        // Fallback si marked no está disponible
        formattedMessage = `<p>${escapeHtml(message)}</p>`;
        
        // Intentar highlighting incluso sin marked
        formattedMessage = highlightArticulos(formattedMessage);
    }
    
    // Construir el HTML del mensaje con avatar y contenido formateado
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content markdown-content">
            ${formattedMessage}
        </div>
    `;
    
    // Añadir el mensaje al contenedor del chat
    chatContainer.appendChild(messageDiv);
    
    // Hacer scroll automático al nuevo mensaje
    scrollToLastMessage();
}

/**
 * MOSTRAR INDICADOR DE "ESCRIBIENDO..."
 * Añade un indicador visual mientras se espera la respuesta del bot
 */
function showTypingIndicator() {
    console.log('⏳ Mostrando indicador de escritura...');
    
    // Crear el elemento del indicador de escritura
    typingIndicatorElement = document.createElement('div');
    typingIndicatorElement.className = 'message bot-message typing-message';
    
    // HTML del indicador con puntos animados
    typingIndicatorElement.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    // Añadir al contenedor del chat
    chatContainer.appendChild(typingIndicatorElement);
    
    // Hacer scroll al indicador
    scrollToLastMessage();
}

/**
 * OCULTAR INDICADOR DE "ESCRIBIENDO..."
 * Remueve el indicador de escritura cuando se recibe la respuesta
 */
function hideTypingIndicator() {
    console.log('✅ Ocultando indicador de escritura...');
    
    // Remover el elemento si existe
    if (typingIndicatorElement && typingIndicatorElement.parentNode) {
        typingIndicatorElement.parentNode.removeChild(typingIndicatorElement);
        typingIndicatorElement = null;
    }
}

/**
 * SCROLL AUTOMÁTICO AL ÚLTIMO MENSAJE
 * Hace scroll automáticamente hacia el mensaje más reciente
 */
function scrollToLastMessage() {
    console.log('📜 Haciendo scroll al último mensaje...');
    
    // Usar setTimeout para asegurar que el DOM se haya actualizado
    setTimeout(() => {
        // Scroll suave al final del contenedor
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

/**
 * ESCAPAR HTML PARA SEGURIDAD
 * Previene ataques XSS escapando caracteres HTML peligrosos
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * VERIFICAR CONFIGURACIÓN DEL WEBHOOK
 * Comprueba si el webhook está configurado correctamente
 */
function checkWebhookConfiguration() {
    if (WEBHOOK_URL === 'TU_WEBHOOK_URL_AQUI') {
        console.warn('⚠️  URL del webhook no configurada');
        console.log('📝 Para conectar con tu sistema n8n:');
        console.log('   1. Reemplaza "TU_WEBHOOK_URL_AQUI" con tu URL real de n8n');
        console.log('   2. Asegúrate de que el webhook acepta POST con JSON');
        console.log('   3. El formato esperado es: { "pregunta": "texto del usuario" }');
        
        // Opcional: mostrar advertencia en la interfaz
        addBotMessage(
            'ℹ️  Para conectar con tu sistema RAG, configura la URL del webhook de n8n en el archivo app.js',
            'warning'
        );
    } else {
        console.log('✅ URL del webhook configurada:', WEBHOOK_URL);
        console.log('🔗 Conectando con:', WEBHOOK_URL);
    }
}

// Simulación de llamada a API (reemplazar con llamada real)
async function simulateAPICall(message) {
    // Simular delay de red
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    // Respuestas de ejemplo basadas en el contenido
    const responses = [
        'Entiendo tu pregunta sobre el documento. Basándome en el contenido procesado, puedo decirte que...',
        'Según la información extraída del PDF, la respuesta a tu consulta es...',
        'He encontrado información relevante en el documento que procesamos. Te explico:',
        'Revisando el contenido del archivo PDF, puedo proporcionarte la siguiente información:',
        'Basándome en el análisis del documento, aquí tienes la respuesta:'
    ];
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    
    // Respuestas específicas para ciertas palabras clave
    if (message.toLowerCase().includes('hola')) {
        return '¡Hola! ¿En qué puedo ayudarte con el documento PDF que has procesado?';
    }
    
    if (message.toLowerCase().includes('error') || message.toLowerCase().includes('problema')) {
        return 'Si estás experimentando problemas, asegúrate de que el PDF se haya procesado correctamente y que esté disponible en la base de datos vectorial.';
    }
    
    if (message.toLowerCase().includes('gracias')) {
        return '¡De nada! Si tienes más preguntas sobre el documento, estaré aquí para ayudarte.';
    }
    
    return `${randomResponse} Esta es una respuesta simulada. En la implementación real, aquí se mostraría información específica extraída de tu documento PDF basada en la consulta: "${message}".`;
}

// Función para conectar con el backend real (para implementar después)
async function queryRAGSystem(message) {
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.response;
        
    } catch (error) {
        console.error('Error querying RAG system:', error);
        throw error;
    }
}

/**
 * UTILIDADES ADICIONALES DEL CHAT
 * Funciones auxiliares para mejorar la experiencia del usuario
 */
const ChatUtils = {
    // Formatear timestamps para los mensajes
    formatTime: (date = new Date()) => {
        return date.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    },
    
    // Limpiar el historial del chat
    clearChat: () => {
        const messages = chatContainer.querySelectorAll('.message:not(.welcome-message .message)');
        messages.forEach(msg => msg.remove());
        conversationHistory = [];  // ⚡ Limpiar también el historial conversacional
        console.log('🧹 Chat e historial limpiados');
    },
    
    // Exportar la conversación como archivo de texto
    exportChat: () => {
        const messages = chatContainer.querySelectorAll('.message');
        const conversation = Array.from(messages).map(msg => {
            const isUser = msg.classList.contains('user-message');
            const content = msg.querySelector('.message-content p').textContent;
            return `${isUser ? 'Usuario' : 'Bot'}: ${content}`;
        }).join('\n\n');
        
        const blob = new Blob([conversation], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_rag_${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        console.log('💾 Conversación exportada');
    },
    
    // Obtener estadísticas del chat
    getStats: () => {
        const userMessages = chatContainer.querySelectorAll('.user-message').length;
        const botMessages = chatContainer.querySelectorAll('.bot-message:not(.typing-message)').length;
        
        return {
            userMessages,
            botMessages,
            totalMessages: userMessages + botMessages
        };
    }
};

/**
 * CONFIGURACIÓN Y NOTAS PARA DESARROLLADORES
 */

/*
INSTRUCCIONES PARA CONFIGURAR EL WEBHOOK DE N8N:

1. En n8n, crea un nuevo workflow con un nodo Webhook
2. Configura el webhook para aceptar peticiones POST
3. El formato de datos esperado es:
   {
     "pregunta": "texto de la pregunta del usuario"
   }

4. Tu workflow de n8n debe devolver una respuesta en formato JSON:
   {
     "respuesta": "respuesta del sistema RAG"
   }
   
5. Reemplaza 'TU_WEBHOOK_URL_AQUI' con la URL real de tu webhook

EJEMPLO DE ESTRUCTURA DEL WORKFLOW N8N:
- Nodo Webhook (recibe la pregunta)
- Nodo de procesamiento (consulta a Pinecone/OpenAI)
- Nodo de respuesta (devuelve el resultado)

FORMATO DE RESPUESTA ESPERADO:
El webhook debe devolver un JSON con una de estas estructuras:
- { "respuesta": "texto de respuesta" }
- { "response": "texto de respuesta" }  
- { "message": "texto de respuesta" }

DEBUGGING:
- Abre la consola del navegador para ver los logs
- Usa ChatUtils.getStats() para obtener estadísticas
- Usa ChatUtils.clearChat() para limpiar el chat
- Usa ChatUtils.exportChat() para exportar la conversación
*/

// Hacer disponibles las utilidades globalmente para debugging y uso externo
window.ChatUtils = ChatUtils;

/**
 * ============================================
 * CONFIGURACIÓN DEL COMPARADOR DE ARTÍCULOS
 * ============================================
 */
function setupComparador() {
    console.log('🔧 Iniciando configuración del comparador...');
    console.log('🔧 DOMContentLoaded ya ejecutado');
    
    // Esperar un poco para asegurar que el DOM está completamente cargado
    setTimeout(() => {
        console.log('⏰ Ejecutando configuración tras timeout...');
        
        // Elementos del modal
        const modalComparador = document.getElementById('modalComparador');
        const comparadorBtn = document.getElementById('comparadorBtn');
        const closeModal = document.getElementById('closeModal');
        const compararBtn = document.getElementById('compararBtn');
        const articulo1Input = document.getElementById('articulo1');
        const articulo2Input = document.getElementById('articulo2');
    
    // Verificar que todos los elementos existen
    console.log('📋 Verificando elementos del DOM:');
    console.log('  - modalComparador:', modalComparador ? '✅' : '❌');
    console.log('  - comparadorBtn:', comparadorBtn ? '✅' : '❌');
    console.log('  - closeModal:', closeModal ? '✅' : '❌');
    console.log('  - compararBtn:', compararBtn ? '✅' : '❌');
    console.log('  - articulo1Input:', articulo1Input ? '✅' : '❌');
    console.log('  - articulo2Input:', articulo2Input ? '✅' : '❌');
    
    if (!modalComparador || !comparadorBtn) {
        console.error('❌ Elementos del comparador no encontrados');
        return;
    }
    
    // Abrir modal
    comparadorBtn.addEventListener('click', (e) => {
        console.log('🔍 Click en botón comparador');
        e.preventDefault();
        modalComparador.classList.add('show');
        modalComparador.style.display = 'flex';
        articulo1Input.focus();
        console.log('✅ Modal abierto');
    });
    
    // Cerrar modal
    closeModal.addEventListener('click', (e) => {
        console.log('❌ Cerrando modal comparador');
        e.preventDefault();
        modalComparador.classList.remove('show');
        modalComparador.style.display = 'none';
    });
    
    // Cerrar modal al hacer clic fuera
    modalComparador.addEventListener('click', (e) => {
        if (e.target === modalComparador) {
            console.log('❌ Click fuera del modal - cerrando');
            modalComparador.classList.remove('show');
            modalComparador.style.display = 'none';
        }
    });
    
    // Función para comparar artículos
    async function compararArticulos() {
        const art1 = articulo1Input.value.trim();
        const art2 = articulo2Input.value.trim();
        
        console.log(`⚖️ Iniciando comparación: ${art1} vs ${art2}`);
        
        // Validar inputs
        if (!art1 || !art2) {
            alert('Por favor, introduce ambos números de artículo');
            console.warn('⚠️ Inputs vacíos');
            return;
        }
        
        if (art1 === art2) {
            alert('Por favor, introduce dos artículos diferentes');
            console.warn('⚠️ Artículos iguales');
            return;
        }
        
        // Cerrar modal
        modalComparador.classList.remove('show');
        modalComparador.style.display = 'none';
        console.log('✅ Modal cerrado');
        
        // Mostrar mensaje en el chat
        const userMessage = `⚖️ Comparar artículo ${art1} vs artículo ${art2}`;
        addMessageToChat(userMessage, 'user');
        console.log('📨 Mensaje agregado al chat');
        
        // Mostrar indicador de escritura
        showTypingIndicator();
        console.log('⏳ Indicador de escritura mostrado');
        
        try {
            const url = `http://10.1.162.145:8000/comparar?art1=${art1}&art2=${art2}`;
            console.log(`🌐 Llamando a: ${url}`);
            
            // Llamar al endpoint de comparación
            const response = await fetch(url);
            console.log(`📡 Respuesta recibida: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📦 Datos parseados:', data);
            
            // Remover indicador de escritura
            removeTypingIndicator();
            console.log('✅ Indicador removido');
            
            // Mostrar comparación en el chat
            if (data.comparacion) {
                addMessageToChat(data.comparacion, 'bot');
                console.log('✅ Comparación agregada al chat');
            } else if (data.error) {
                addMessageToChat(`❌ Error: ${data.error}`, 'bot');
                console.error('❌ Error en respuesta:', data.error);
            } else {
                console.error('❌ Formato de respuesta inesperado:', data);
                addMessageToChat('❌ Error: Formato de respuesta inesperado', 'bot');
            }
            
            // Limpiar inputs
            articulo1Input.value = '';
            articulo2Input.value = '';
            console.log('🧹 Inputs limpiados');
            
        } catch (error) {
            console.error('❌ Error al comparar artículos:', error);
            removeTypingIndicator();
            addMessageToChat(`❌ Error al comparar artículos: ${error.message}`, 'bot');
        }
    }
    
    // Event listener para el botón de comparar
    if (compararBtn) {
        compararBtn.addEventListener('click', (e) => {
            console.log('👆 Click en botón COMPARAR');
            e.preventDefault();
            e.stopPropagation();
            compararArticulos();
        });
        console.log('✅ Event listener del botón COMPARAR registrado');
    } else {
        console.error('❌ No se pudo registrar event listener - compararBtn no existe');
    }
    
    // Permitir Enter en los inputs para comparar
    articulo1Input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            console.log('⏎ Enter en artículo 1 - moviendo a artículo 2');
            articulo2Input.focus();
        }
    });
    
    articulo2Input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            console.log('⏎ Enter en artículo 2 - ejecutando comparación');
            compararArticulos();
        }
    });
    
    console.log('✅ Comparador de artículos configurado correctamente');
    }, 100); // Cierre del setTimeout
}

console.log('✨ Aplicación de Chat RAG cargada completamente');
console.log('⚖️  Comparador de artículos disponible');
console.log('🔧 Utilidades disponibles en window.ChatUtils');
console.log('📝 Consulta los comentarios del código para instrucciones de configuración');
