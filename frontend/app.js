/**
 * CONFIGURACIÓN DE LA APLICACIÓN DE CHAT RAG
 * Este script maneja la interfaz de usuario para el chat con el sistema RAG
 */

// URL del webhook de n8n (reemplaza con tu URL real)
const WEBHOOK_URL = 'TU_WEBHOOK_URL_AQUI';

// Elementos del DOM - obtenemos referencias a los elementos principales
const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const loadingIndicator = document.getElementById('loadingIndicator');

// Estado de la aplicación
let isLoading = false;
let typingIndicatorElement = null;

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
 */
async function sendMessageToWebhook(pregunta) {
    console.log('🌐 Enviando petición al webhook de n8n...');
    
    // Verificar que la URL del webhook esté configurada
    if (WEBHOOK_URL === 'TU_WEBHOOK_URL_AQUI') {
        throw new Error('URL del webhook no configurada. Por favor, actualiza la variable WEBHOOK_URL en app.js');
    }
    
    try {
        // Realizar petición POST con fetch
        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            // Cuerpo de la petición en formato JSON
            body: JSON.stringify({
                pregunta: pregunta
            })
        });
        
        // Verificar que la respuesta sea exitosa
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} - ${response.statusText}`);
        }
        
        // Obtener la respuesta en formato JSON
        const data = await response.json();
        
        console.log('📨 Respuesta del webhook recibida:', data);
        
        // Extraer la respuesta del bot (ajusta según la estructura de tu webhook)
        // Asumimos que el webhook devuelve { "respuesta": "texto del bot" }
        // Ajusta esta línea según el formato real de tu webhook
        return data.respuesta || data.response || data.message || 'Respuesta recibida del sistema RAG';
        
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
 * CREAR Y AÑADIR MENSAJE DEL BOT AL CHAT
 * Crea un elemento div para mostrar la respuesta del bot
 */
function addBotMessage(message, type = 'normal') {
    console.log('🤖 Añadiendo mensaje del bot al chat');
    
    // Crear el elemento div para el mensaje
    const messageDiv = document.createElement('div');
    messageDiv.className = `message bot-message${type !== 'normal' ? ` ${type}` : ''}`;
    
    // Construir el HTML del mensaje con avatar y contenido
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
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
        console.log('🧹 Chat limpiado');
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

console.log('✨ Aplicación de Chat RAG cargada completamente');
console.log('🔧 Utilidades disponibles en window.ChatUtils');
console.log('📝 Consulta los comentarios del código para instrucciones de configuración');
