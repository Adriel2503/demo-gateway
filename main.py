"""
WhatsApp Gateway Service
Migración de ws_trigger.php y ws_send_whatsapp_oficial.php a Python/FastAPI
Recibe webhooks de Meta, envía a Agent Service, y proporciona endpoint de envío
"""

import os
import json
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from dotenv import load_dotenv

from send_service import SendWhatsAppService

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv()

# Variables de entorno
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', 'EAAQFs6SYPWIBQeqI6SmhXdwHLBHhFfOAbAqcU3aZBjbKuRpfo7MKK8ZAtYOPW1DhofhL7DoUFqb4hNwXGOYD63R0zBVbi5gvFaVZBLHhfglBhJvczk4KoLxLFA2V1hoFPbPZCkYBgihdZBaCJZA7sujWqnpyb2gcpJ2vx3HY1b05f356ftdfOI28Cd0hyvN1zSOAZDZD')
APP_SECRET = os.getenv('APP_SECRET', '4c7ac78dcda3619bbbb224c66c1189c3')
AGENT_SERVICE_URL = os.getenv('AGENT_SERVICE_URL', 'http://localhost:8001/process')

# Constantes
GRAPH_API_VERSION = 'v21.0'
GRAPH_API_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}'
REQUEST_TIMEOUT = 60.0
AGENT_REQUEST_TIMEOUT = 30.0

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# APLICACIÓN FASTAPI
# ============================================================================

app = FastAPI(
    title='WhatsApp Gateway Service',
    description='Recibe webhooks de Meta WhatsApp y envía a Agent Service',
    version='1.0.0'
)

# CORS headers
@app.middleware('http')
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validate_webhook_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Valida la firma HMAC-SHA256 del webhook de Meta.
    
    Args:
        raw_body: Body raw de la solicitud
        signature_header: Header X-Hub-Signature-256
    
    Returns:
        True si la firma es válida o si APP_SECRET no está configurado
    """
    if not APP_SECRET:
        logger.warning('APP_SECRET no configurado - validación de firma deshabilitada')
        return True
    
    if not signature_header:
        logger.warning('Header X-Hub-Signature-256 no presente')
        return False
    
    # Formato esperado: "sha256=<hash>"
    if not signature_header.startswith('sha256='):
        logger.warning(f'Formato de firma inválido: {signature_header}')
        return False
    
    expected_hash = signature_header[7:]  # Quitar "sha256="
    
    # Calcular hash HMAC-SHA256
    calculated_hash = hmac.new(
        APP_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    # Comparación segura contra timing attacks
    is_valid = hmac.compare_digest(expected_hash, calculated_hash)
    
    if is_valid:
        logger.info('Firma de webhook validada correctamente')
    else:
        logger.error(f'Firma no coincide - Expected: {expected_hash}, Calculated: {calculated_hash}')
    
    return is_valid

def extract_phone_number_id(data: Dict[str, Any]) -> Optional[str]:
    """
    Extrae el phone_number_id del payload nested de Meta.
    
    Args:
        data: Payload JSON del webhook
    
    Returns:
        phone_number_id o None si no se encuentra
    """
    try:
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    phone_number_id = change.get('value', {}).get('metadata', {}).get('phone_number_id')
                    if phone_number_id:
                        return phone_number_id
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f'Error extrayendo phone_number_id: {e}')
    
    return None

def extract_message_content(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae el contenido del mensaje según su tipo.
    
    Args:
        message: Objeto mensaje del webhook
    
    Returns:
        Dict con type, text y media_data
    """
    message_type = message.get('type', 'text')
    message_text = ''
    media_data = None
    
    try:
        if message_type == 'text':
            message_text = message.get('text', {}).get('body', '')
        
        elif message_type == 'image':
            media_data = message.get('image', {})
            message_text = media_data.get('caption', '')
        
        elif message_type == 'video':
            media_data = message.get('video', {})
            message_text = media_data.get('caption', '')
        
        elif message_type == 'audio':
            media_data = message.get('audio', {})
        
        elif message_type == 'document':
            media_data = message.get('document', {})
            message_text = media_data.get('caption', '')
        
        elif message_type == 'location':
            location = message.get('location', {})
            lat = location.get('latitude')
            lon = location.get('longitude')
            message_text = f'Ubicación: {lat}, {lon}'
        
        elif message_type == 'interactive':
            interactive = message.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                message_text = interactive.get('button_reply', {}).get('title', '')
            elif interactive.get('type') == 'list_reply':
                message_text = interactive.get('list_reply', {}).get('title', '')
        
        else:
            message_text = f'[Tipo de mensaje no soportado: {message_type}]'
    
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f'Error extrayendo contenido del mensaje: {e}')
    
    return {
        'type': message_type,
        'text': message_text,
        'media_data': media_data
    }

# ============================================================================
# FUNCIONES DE PROCESAMIENTO
# ============================================================================

def extract_webhook_data(data: Dict[str, Any]) -> list:
    """
    Extrae información estructurada del webhook de Meta.
    
    Args:
        data: Payload JSON del webhook
    
    Returns:
        Lista de mensajes procesados
    """
    messages_data = []
    
    try:
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') != 'messages':
                    continue
                
                value = change.get('value', {})
                metadata = value.get('metadata', {})
                
                # Datos de la IA (quien recibe)
                phone_number_id = metadata.get('phone_number_id')
                display_phone_number = metadata.get('display_phone_number')
                
                # Datos del cliente (quien envía)
                contacts = value.get('contacts', [])
                if not contacts:
                    continue
                
                contact = contacts[0]
                push_name = contact.get('profile', {}).get('name', 'Unknown')
                wa_id = contact.get('wa_id')
                
                # Procesar cada mensaje
                messages = value.get('messages', [])
                for message in messages:
                    message_id = message.get('id')
                    timestamp = message.get('timestamp', int(datetime.now().timestamp()))
                    
                    content = extract_message_content(message)
                    
                    messages_data.append({
                        'phone_number_id': phone_number_id,
                        'display_phone_number': display_phone_number,
                        'from': wa_id,
                        'from_number': wa_id,
                        'push_name': push_name,
                        'message_id': message_id,
                        'timestamp': timestamp,
                        'type': content['type'],
                        'text': content['text'],
                        'media_data': content['media_data']
                    })
                
                # Procesar estados de mensaje (optional)
                statuses = value.get('statuses', [])
                for status in statuses:
                    status_type = status.get('status')
                    status_message_id = status.get('id')
                    recipient_id = status.get('recipient_id')
                    logger.info(
                        f'Message status: {status_type}',
                        extra={
                            'message_id': status_message_id,
                            'recipient': recipient_id
                        }
                    )
    
    except (KeyError, TypeError, AttributeError) as e:
        logger.error(f'Error extrayendo datos del webhook: {e}')
    
    return messages_data

async def send_to_agent_service(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Envía el mensaje procesado al Agent Service.
    
    Args:
        payload: Datos del mensaje
    
    Returns:
        Respuesta del Agent Service o None
    """
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f'Enviando a Agent Service: {AGENT_SERVICE_URL}')
            response = await client.post(
                AGENT_SERVICE_URL,
                json=payload,
                timeout=AGENT_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            logger.info(f'Respuesta del Agent Service: {response.status_code}')
            return response.json()
    
    except httpx.RequestError as e:
        logger.error(f'Error enviando a Agent Service: {e}')
    except httpx.HTTPStatusError as e:
        logger.error(f'Agent Service retornó error {e.response.status_code}: {e.response.text}')
    except Exception as e:
        logger.error(f'Error inesperado enviando a Agent Service: {e}')
    
    return None

async def process_message_background(message_data: Dict[str, Any]) -> None:
    """
    Procesa un mensaje en background.
    
    Args:
        message_data: Datos del mensaje extraídos del webhook
    """
    logger.info(f'Procesando mensaje: {message_data.get("message_id")}')
    
    try:
        # Construir payload para Agent Service
        payload = {
            'message_id': message_data.get('message_id'),
            'from': message_data.get('from'),
            'from_number': message_data.get('from_number'),
            'timestamp': message_data.get('timestamp'),
            'message_text': message_data.get('text'),
            'message_type': message_data.get('type'),
            'push_name': message_data.get('push_name'),
            'phone_number_id': message_data.get('phone_number_id'),
            'source': 'whatsapp_cloud_api'
        }
        
        # Enviar a Agent Service
        agent_response = await send_to_agent_service(payload)
        
        if agent_response:
            logger.info(f'Mensaje {message_data.get("message_id")} procesado exitosamente')
        else:
            logger.warning(f'No se obtuvo respuesta del Agent Service para {message_data.get("message_id")}')
    
    except Exception as e:
        logger.error(f'Error en background task: {e}')

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'service': 'WhatsApp Gateway',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/webhook')
async def verify_webhook(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None
):
    """
    Verificación del webhook de Meta (GET request).
    Meta requiere esto para activar el webhook.
    """
    logger.info('Recibido GET request de verificación de webhook')
    
    if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
        logger.info('Verificación exitosa')
        return int(hub_challenge)
    
    logger.warning('Verificación fallida')
    raise HTTPException(status_code=403, detail='Verification failed')

@app.post('/webhook')
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Recepción de webhooks de Meta WhatsApp.
    Procesa mensajes en background y responde rápidamente a Meta.
    """
    logger.info('Recibido POST request de webhook')
    
    try:
        # Leer body raw (importante para validación de firma)
        raw_body = await request.body()
        
        # Decodificar JSON
        data = json.loads(raw_body)
        
        # Validar que es webhook de Meta
        is_meta_webhook = data.get('object') == 'whatsapp_business_account'
        
        if not is_meta_webhook:
            logger.warning('Payload no es webhook de Meta válido')
            raise HTTPException(status_code=400, detail='Invalid webhook format')
        
        # Validar firma si está configurado APP_SECRET
        if APP_SECRET:
            signature = request.headers.get('X-Hub-Signature-256', '')
            if not validate_webhook_signature(raw_body, signature):
                logger.warning('Validación de firma fallida')
                raise HTTPException(status_code=401, detail='Invalid signature')
        
        # Extraer datos del webhook
        messages = extract_webhook_data(data)
        
        # Procesar cada mensaje en background
        for message_data in messages:
            background_tasks.add_task(process_message_background, message_data)
            logger.info(f'Mensaje {message_data.get("message_id")} encolado para procesamiento')
        
        # Responder rápidamente a Meta (crítico)
        logger.info('Respondiendo a Meta con 200 OK')
        return {
            'success': True,
            'message': 'Webhook received',
            'messages_processed': len(messages)
        }
    
    except json.JSONDecodeError as e:
        logger.error(f'Error decodificando JSON: {e}')
        raise HTTPException(status_code=400, detail='Invalid JSON')
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f'Error inesperado procesando webhook: {e}')
        # Siempre responder 200 a Meta para evitar reintentos
        return {
            'success': False,
            'error': str(e),
            'message': 'Error processing webhook but Meta notified'
        }

@app.options('/webhook')
async def options_webhook():
    """Manejo de CORS preflight requests."""
    return {}

# ============================================================================
# ENDPOINT DE ENVÍO (Migrado de ws_send_whatsapp_oficial.php)
# ============================================================================

@app.post('/send')
async def send_message(request_payload: Dict[str, Any]):
    """
    Endpoint para enviar mensajes WhatsApp.
    
    Migrado de ws_send_whatsapp_oficial.php
    
    Formato esperado:
    {
        'phone_number_id': 'ID del número de la IA',
        'phone': 'Número destino (cliente)',
        'type': 'text|image|document|audio|video',
        'message': 'Contenido (obligatorio para text)',
        'image_url': 'Para type=image',
        'document_url': 'Para type=document',
        'filename': 'Para type=document',
        'audio_url': 'Para type=audio',
        'video_url': 'Para type=video'
    }
    
    Respuesta exitosa:
    {
        'success': True,
        'message': 'Mensaje enviado correctamente',
        'message_id': 'ID retornado por Meta',
        'response': {...datos de Meta...},
        'debug': {...}
    }
    
    Respuesta de error:
    {
        'success': False,
        'error': 'Descripción del error',
        'details': '...'
    }
    """
    logger.info(f'Recibido POST /send')
    
    try:
        # Inicializar servicio de envío
        send_service = SendWhatsAppService(WHATSAPP_TOKEN)
        
        # Procesar el request
        response = await send_service.process(request_payload)
        
        # Retornar respuesta
        http_code = 200 if response.get('success') else 400
        return {
            'status_code': http_code,
            'data': response
        }
    
    except ValueError as e:
        logger.error(f'Error de configuración: {e}')
        return {
            'status_code': 500,
            'data': {
                'success': False,
                'error': 'Error de configuración del Gateway',
                'details': str(e)
            }
        }
    
    except Exception as e:
        logger.error(f'Error inesperado en /send: {e}')
        return {
            'status_code': 500,
            'data': {
                'success': False,
                'error': 'Error interno del servidor',
                'details': str(e)
            }
        }

@app.options('/send')
async def options_send():
    """Manejo de CORS preflight requests para /send."""
    return {}

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f'Iniciando WhatsApp Gateway en {host}:{port}')
    logger.info(f'Agent Service URL: {AGENT_SERVICE_URL}')
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level='info'
    )
