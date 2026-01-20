"""
Ejemplos de requests para el endpoint POST /send

Usar con curl, Postman, httpx, requests, etc.
"""

# ============================================================================
# EJEMPLO 1: Enviar mensaje de texto
# ============================================================================

SEND_TEXT = {
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "text",
    "message": "Hola, este es un mensaje de prueba desde el Gateway"
}

# Curl:
# curl -X POST http://localhost:8000/send \
#   -H "Content-Type: application/json" \
#   -d '{"phone_number_id":"122110111111111","phone":"51980253258","type":"text","message":"Hola"}'


# ============================================================================
# EJEMPLO 2: Enviar imagen
# ============================================================================

SEND_IMAGE = {
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "image",
    "image_url": "https://ejemplo.com/imagen.jpg",
    "message": "Mira esta imagen"
}

# Curl:
# curl -X POST http://localhost:8000/send \
#   -H "Content-Type: application/json" \
#   -d '{
#     "phone_number_id":"122110111111111",
#     "phone":"51980253258",
#     "type":"image",
#     "image_url":"https://ejemplo.com/imagen.jpg",
#     "message":"Mira esta imagen"
#   }'


# ============================================================================
# EJEMPLO 3: Enviar documento
# ============================================================================

SEND_DOCUMENT = {
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "document",
    "document_url": "https://ejemplo.com/documento.pdf",
    "filename": "contrato.pdf",
    "message": "Adjunto el contrato firmado"
}

# Curl:
# curl -X POST http://localhost:8000/send \
#   -H "Content-Type: application/json" \
#   -d '{
#     "phone_number_id":"122110111111111",
#     "phone":"51980253258",
#     "type":"document",
#     "document_url":"https://ejemplo.com/documento.pdf",
#     "filename":"contrato.pdf",
#     "message":"Adjunto el contrato firmado"
#   }'


# ============================================================================
# EJEMPLO 4: Enviar audio
# ============================================================================

SEND_AUDIO = {
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "audio",
    "audio_url": "https://ejemplo.com/audio.mp3"
}

# Curl:
# curl -X POST http://localhost:8000/send \
#   -H "Content-Type: application/json" \
#   -d '{
#     "phone_number_id":"122110111111111",
#     "phone":"51980253258",
#     "type":"audio",
#     "audio_url":"https://ejemplo.com/audio.mp3"
#   }'


# ============================================================================
# EJEMPLO 5: Enviar video
# ============================================================================

SEND_VIDEO = {
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "video",
    "video_url": "https://ejemplo.com/video.mp4",
    "message": "Aquí está el video que solicitaste"
}

# Curl:
# curl -X POST http://localhost:8000/send \
#   -H "Content-Type: application/json" \
#   -d '{
#     "phone_number_id":"122110111111111",
#     "phone":"51980253258",
#     "type":"video",
#     "video_url":"https://ejemplo.com/video.mp4",
#     "message":"Aquí está el video que solicitaste"
#   }'


# ============================================================================
# SCRIPT PYTHON PARA TESTEAR
# ============================================================================

import asyncio
import httpx
import json


async def test_send_endpoint():
    """Test del endpoint /send"""
    
    async with httpx.AsyncClient() as client:
        # Test 1: Mensaje de texto
        print("\n1. Enviando mensaje de texto...")
        response = await client.post(
            'http://localhost:8000/send',
            json=SEND_TEXT,
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        # Test 2: Imagen
        print("\n2. Enviando imagen...")
        response = await client.post(
            'http://localhost:8000/send',
            json=SEND_IMAGE,
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        # Test 3: Documento
        print("\n3. Enviando documento...")
        response = await client.post(
            'http://localhost:8000/send',
            json=SEND_DOCUMENT,
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))


# Ejecutar tests
# asyncio.run(test_send_endpoint())


# ============================================================================
# FLUJO COMPLETO: Webhook -> Agent Service -> Gateway /send
# ============================================================================

"""
1. Meta envía mensaje al webhook (/webhook POST)
   {
     "object": "whatsapp_business_account",
     "entry": [{
       "changes": [{
         "field": "messages",
         "value": {
           "messaging_product": "whatsapp",
           "metadata": {
             "phone_number_id": "122110111111111",
             "display_phone_number": "51 987 654 321"
           },
           "contacts": [{
             "profile": {"name": "Juan Perez"},
             "wa_id": "51980253258"
           }],
           "messages": [{
             "type": "text",
             "text": {"body": "Hola, necesito ayuda"},
             "id": "wamid.xxx",
             "timestamp": "1234567890"
           }]
         }
       }]
     }]
   }

2. Gateway procesa webhook y envía a Agent Service
   - Extrae: phone_number_id, from (wa_id), message_text
   - Envía POST a AGENT_SERVICE_URL con los datos

3. Agent Service procesa el mensaje
   - Genera una respuesta inteligente
   - Retorna: {"reply": "Claro, ¿cómo puedo ayudarte?"}

4. Agent Service llama al endpoint /send del Gateway
   POST /send {
     "phone_number_id": "122110111111111",
     "phone": "51980253258",
     "type": "text",
     "message": "Claro, ¿cómo puedo ayudarte?"
   }

5. Gateway envía a Meta y retorna respuesta
   {
     "success": true,
     "message_id": "wamid.yyy",
     "message": "Mensaje enviado correctamente"
   }

6. Meta entrega el mensaje al cliente
"""
