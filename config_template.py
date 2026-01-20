"""
Template de configuración para WhatsApp Gateway.
Copia este archivo a config.py y completa con tus valores reales.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CREDENCIALES (De Meta WhatsApp)
# ============================================================================

# Token de verificación para Meta (GET request de verificación del webhook)
# Este debe coincidir con el configurado en Meta Dashboard
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c')

# Token de acceso a WhatsApp Cloud API
# Obtener de: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', 'EAAQFs6SYPWIBQeqI6SmhXdwHLBHhFfOAbAqcU3aZBjbKuRpfo7MKK8ZAtYOPW1DhofhL7DoUFqb4hNwXGOYD63R0zBVbi5gvFaVZBLHhfglBhJvczk4KoLxLFA2V1hoFPbPZCkYBgihdZBaCJZA7sujWqnpyb2gcpJ2vx3HY1b05f356ftdfOI28Cd0hyvN1zSOAZDZD')

# App Secret para validar firma HMAC de webhooks
# Obtener de: https://developers.facebook.com/apps/
APP_SECRET = os.getenv('APP_SECRET', '4c7ac78dcda3619bbbb224c66c1189c3')

# ============================================================================
# URLS DE SERVICIOS
# ============================================================================

# URL del Agent Service (donde se procesan los mensajes)
# Cambiar esta URL para redirigir a diferentes servicios:
# - N8N: https://n8n-produccion.com/webhook/whatsapp
# - Agent Service: http://localhost:8001/process
# - Otro servicio: https://otro-servicio.com/api
AGENT_SERVICE_URL = os.getenv('AGENT_SERVICE_URL', 'http://localhost:8001/process')

# ============================================================================
# CONSTANTES (No cambiar)
# ============================================================================

# Versión de Graph API de Meta
GRAPH_API_VERSION = 'v21.0'

# URL base de Graph API
GRAPH_API_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}'

# Timeouts (en segundos)
REQUEST_TIMEOUT = 60.0  # Para descargar archivos
AGENT_REQUEST_TIMEOUT = 30.0  # Para llamadas al Agent Service

# ============================================================================
# SERVIDOR
# ============================================================================

# Host donde escucha el servidor
HOST = os.getenv('HOST', '0.0.0.0')

# Puerto donde escucha el servidor
PORT = int(os.getenv('PORT', 8000))

# ============================================================================
# LOGGING
# ============================================================================

# Nivel de logging: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# ============================================================================
# VALIDACIÓN
# ============================================================================

def validate_config():
    """Valida que la configuración sea correcta."""
    errors = []
    
    if not VERIFY_TOKEN:
        errors.append('VERIFY_TOKEN no está configurado')
    
    if not WHATSAPP_TOKEN:
        errors.append('WHATSAPP_TOKEN no está configurado')
    
    if not AGENT_SERVICE_URL:
        errors.append('AGENT_SERVICE_URL no está configurado')
    
    if errors:
        print('Errores de configuración:')
        for error in errors:
            print(f'  - {error}')
        return False
    
    return True
