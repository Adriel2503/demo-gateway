# Quick Reference - Endpoint /send

## TL;DR

4 módulos + main.py endpoint = Funcionalidad completa de ws_send_whatsapp_oficial.php en Python

## Archivos

| Archivo | Líneas | ¿Qué hace? |
|---------|--------|-----------|
| `main.py` | ~100 | FastAPI app + endpoint /send |
| `formatters.py` | ~120 | Formatea números y respuestas |
| `message_types.py` | ~180 | Valida payload según tipo |
| `meta_client.py` | ~250 | Envía requests a Meta |
| `send_service.py` | ~200 | Orquesta todo |

## Flujo

```
Request JSON
    ↓
SendWhatsAppService.process()
    ├─ Valida (SendPayload)
    ├─ Formatea número (format_phone_number)
    ├─ Envía (MetaWhatsAppClient.send_*)
    └─ Procesa respuesta
    ↓
Response JSON
```

## Tipos de Mensaje

| Tipo | Requiere | Opcional |
|------|----------|----------|
| `text` | `message` | - |
| `image` | `image_url` | `message` |
| `document` | `document_url`, `filename` | `message` |
| `audio` | `audio_url` | - |
| `video` | `video_url` | `message` |

## Ejemplo: Enviar Texto

```bash
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "text",
    "message": "Hola"
  }'
```

## Ejemplo: Enviar Imagen

```bash
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number_id": "122110111111111",
    "phone": "51980253258",
    "type": "image",
    "image_url": "https://ejemplo.com/img.jpg",
    "message": "Caption"
  }'
```

## Respuesta Exitosa

```json
{
  "status_code": 200,
  "data": {
    "success": true,
    "message": "Mensaje enviado correctamente",
    "message_id": "wamid.xxx",
    "response": {...},
    "debug": {
      "type": "text",
      "to": "51980253258",
      "phone_number_id": "122110111111111"
    }
  }
}
```

## Respuesta Error

```json
{
  "status_code": 400,
  "data": {
    "success": false,
    "error": "Validación fallida",
    "details": "Campo requerido: message"
  }
}
```

## Formateo de Números

```python
format_phone_number('980253258')        # → '51980253258'
format_phone_number('+51 9 8025 3258')  # → '51980253258'
format_phone_number('09 8025 3258')     # → '51980253258'
```

## Validación de Payload

```python
payload = SendPayload({
    'phone': '51980253258',
    'type': 'text',
    'message': 'Hola'
})

is_valid, error = payload.validate()
# is_valid = True
# error = None
```

## Envío Manual

```python
import asyncio
from send_service import SendWhatsAppService

async def send():
    service = SendWhatsAppService('YOUR_TOKEN')
    response = await service.process({
        'phone_number_id': '122110111111111',
        'phone': '51980253258',
        'type': 'text',
        'message': 'Hola'
    })
    print(response)

asyncio.run(send())
```

## Desde Agent Service

```python
import httpx

async def send_reply(phone_number_id, phone, reply):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/send',
            json={
                'phone_number_id': phone_number_id,
                'phone': phone,
                'type': 'text',
                'message': reply
            }
        )
        return response.json()
```

## Importes Principales

```python
# En main.py
from send_service import SendWhatsAppService

# En send_service.py
from message_types import SendPayload, MessageType
from meta_client import MetaWhatsAppClient
from formatters import format_phone_number, format_response_success, format_response_error

# En meta_client.py
from typing import Dict, Any, Optional
import httpx

# En message_types.py
from enum import Enum
from typing import Tuple, Optional, Any
```

## Métodos Principales

```python
# formatters.py
format_phone_number(phone: str, default_country_code: str = '51') -> str
format_response_success(...) -> dict
format_response_error(...) -> dict

# message_types.py
payload.validate() -> (bool, Optional[str])
payload.get_type() -> str
payload.get_phone() -> str
payload.get_phone_number_id() -> Optional[str]
payload.get_message() -> Optional[str]
payload.get_image_url() -> Optional[str]
payload.get_document_url() -> Optional[str]
payload.get_document_filename() -> Optional[str]
payload.get_audio_url() -> Optional[str]
payload.get_video_url() -> Optional[str]

# meta_client.py
async client.send_text(phone_number_id, to, message)
async client.send_image(phone_number_id, to, image_url, caption)
async client.send_document(phone_number_id, to, document_url, filename, caption)
async client.send_audio(phone_number_id, to, audio_url)
async client.send_video(phone_number_id, to, video_url, caption)

# send_service.py
async service.process(payload: Dict) -> Dict
```

## Errores Comunes

| Error | Solución |
|-------|----------|
| "Campo requerido: phone" | Agrega `"phone"` al payload |
| "Campo requerido: message" | Agrega `"message"` para tipo text |
| "Invalid recipient" | Formato del número incorrecta |
| "Invalid phone_number_id" | phone_number_id inválido |
| "Invalid access token" | Token expirado o incorrecto |

## Testing

```bash
# Health
curl http://localhost:8000/health

# Enviar texto
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{"phone_number_id":"122110111111111","phone":"51980253258","type":"text","message":"Test"}'

# Enviar imagen
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{"phone_number_id":"122110111111111","phone":"51980253258","type":"image","image_url":"https://ejemplo.com/img.jpg"}'
```

## Documentación Completa

- `ARQUITECTURA_MODULAR.md` - Documentación técnica
- `INTEGRACION_SEND.md` - Guía de integración
- `ESTRUCTURA_MODULAR.txt` - Referencia visual
- `example_send_requests.py` - Ejemplos de código
- Docstrings en cada función

## Status

✅ Implementado  
✅ Documentado  
✅ Listo para testing  
✅ Listo para producción  
