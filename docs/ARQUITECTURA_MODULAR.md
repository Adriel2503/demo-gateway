# Arquitectura Modular del Gateway WhatsApp

## Visión General

El servicio de envío de mensajes ha sido implementado de forma **modular y escalable**, dividiendo las responsabilidades en módulos independientes y reutilizables.

```
main.py (FastAPI app)
    ↓
POST /send {payload}
    ↓
send_service.SendWhatsAppService
    ├── Validación
    ├── Formateo
    └── Orquestación
    ↓
Selecciona según tipo:
    ├── message_types.SendPayload (validación)
    ├── formatters.format_phone_number (formateo)
    └── meta_client.MetaWhatsAppClient (envío)
    ↓
Meta WhatsApp Cloud API
    ↓
Respuesta procesada y retornada
```

## Módulos

### 1. `main.py` - Aplicación FastAPI

**Responsabilidad:** Exponer endpoints HTTP

**Endpoints:**
- `GET /health` - Health check
- `GET /webhook` - Verificación de webhook de Meta
- `POST /webhook` - Recepción de mensajes entrantes
- `POST /send` - **NUEVO** - Envío de mensajes
- `OPTIONS /webhook` - CORS preflight
- `OPTIONS /send` - CORS preflight

**Características:**
- Manejo de requests/responses HTTP
- Middleware CORS
- Integración con BackgroundTasks para webhook async
- Logging estructurado

---

### 2. `send_service.py` - Orquestador Principal

**Responsabilidad:** Coordinar el flujo completo de envío

**Clase:** `SendWhatsAppService`

**Método público:** `async process(payload: Dict) -> Dict`

**Flujo:**
1. Valida el payload
2. Extrae datos
3. Formatea el número telefónico
4. Selecciona método según tipo de mensaje
5. Envía a Meta
6. Procesa respuesta
7. Retorna resultado estructurado

**Ventajas:**
- Lógica central y fácil de mantener
- Testeable
- Independiente de FastAPI
- Puede usarse en otros contextos (CLI, workers, etc.)

---

### 3. `message_types.py` - Validación de Tipos

**Responsabilidad:** Validar y parsear diferentes tipos de mensajes

**Clase principal:** `SendPayload`

**Tipos soportados:**
- `text` - Mensaje de texto
- `image` - Imagen (con caption opcional)
- `document` - Documento PDF, Word, etc. (con filename)
- `audio` - Audio MP3, WAV, etc.
- `video` - Video MP4, etc. (con caption opcional)

**Método público:** `validate() -> Tuple[bool, Optional[str]]`

**Validaciones específicas:**
- `TEXT`: Requiere `message`
- `IMAGE`: Requiere `image_url`
- `DOCUMENT`: Requiere `document_url` y `filename`
- `AUDIO`: Requiere `audio_url`
- `VIDEO`: Requiere `video_url`

**Getters especializados:**
```python
payload.get_type()              # Tipo normalizado
payload.get_phone()             # Número formateado
payload.get_phone_number_id()   # ID del número que envía
payload.get_message()           # Mensaje/caption
payload.get_image_url()         # URL de imagen
# ... etc
```

---

### 4. `formatters.py` - Utilidades de Formateo

**Responsabilidad:** Formatear y normalizar datos

**Funciones:**

#### `format_phone_number(phone: str, default_country_code: str = '51') -> str`

Formatea números telefónicos para Meta:
- Elimina espacios, guiones, paréntesis, +
- Quita 0 inicial (formato peruano)
- Agrega código de país si falta

**Ejemplos:**
```python
format_phone_number('980253258')           # → '51980253258'
format_phone_number('+51 9 8025 3258')     # → '51980253258'
format_phone_number('09 8025 3258')        # → '51980253258'
```

#### `format_response_success(...) -> dict`

Formatea respuesta exitosa con estructura uniforme

#### `format_response_error(...) -> dict`

Formatea respuesta de error con estructura uniforme

---

### 5. `meta_client.py` - Cliente HTTP a Meta

**Responsabilidad:** Comunicación HTTP con Meta WhatsApp Cloud API

**Clase:** `MetaWhatsAppClient`

**Métodos async:**
- `send_text(phone_number_id, to, message)`
- `send_image(phone_number_id, to, image_url, caption=None)`
- `send_document(phone_number_id, to, document_url, filename, caption=None)`
- `send_audio(phone_number_id, to, audio_url)`
- `send_video(phone_number_id, to, video_url, caption=None)`

**Características:**
- Totalmente async con `httpx`
- Timeout configurable (60s)
- Manejo robusto de errores
- Logging detallado
- Headers correctos (Content-Type, Authorization)
- Respuestas estructuradas

**Método privado:** `_send_request(phone_number_id, payload) -> Dict`

---

## Flujo de Envío Paso a Paso

### 1. Request llega a `/send`

```python
POST /send HTTP/1.1
Content-Type: application/json

{
  "phone_number_id": "122110111111111",
  "phone": "51980253258",
  "type": "text",
  "message": "Hola"
}
```

### 2. FastAPI llama `send_message()`

```python
@app.post('/send')
async def send_message(request_payload: Dict[str, Any]):
    send_service = SendWhatsAppService(WHATSAPP_TOKEN)
    response = await send_service.process(request_payload)
    return response
```

### 3. `SendWhatsAppService.process()` ejecuta

**Paso 3a: Validación**
```python
payload = SendPayload(request_payload)
is_valid, error = payload.validate()
# Verifica que 'phone', 'type' estén presentes
# Verifica campos específicos según tipo
```

**Paso 3b: Extracción**
```python
message_type = payload.get_type()      # 'text'
phone = payload.get_phone()            # '51980253258'
phone_number_id = payload.get_phone_number_id()
message = payload.get_message()        # 'Hola'
```

**Paso 3c: Formateo**
```python
formatted_phone = format_phone_number('51980253258')
# → '51980253258' (ya estaba correcto)
```

**Paso 3d: Envío según tipo**
```python
if message_type == MessageType.TEXT:
    meta_response = await meta_client.send_text(
        phone_number_id,
        formatted_phone,
        message
    )
```

**Paso 3e: Cliente Meta construye payload**
```python
payload = {
    'messaging_product': 'whatsapp',
    'recipient_type': 'individual',
    'to': '51980253258',
    'type': 'text',
    'text': {
        'preview_url': True,
        'body': 'Hola'
    }
}
```

**Paso 3f: Request HTTP a Meta**
```
POST https://graph.facebook.com/v21.0/122110111111111/messages HTTP/1.1
Authorization: Bearer TOKEN
Content-Type: application/json

{...payload...}
```

**Paso 3g: Procesar respuesta Meta**
```python
# Meta responde con 200 y:
{
  "messages": [
    {
      "id": "wamid.xxx"
    }
  ]
}

# SendWhatsAppService procesa:
return {
    'success': True,
    'message': 'Mensaje enviado correctamente',
    'message_id': 'wamid.xxx',
    'response': {...},
    'debug': {'type': 'text', 'to': '51980253258', ...}
}
```

### 4. Response retorna a cliente

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status_code": 200,
  "data": {
    "success": true,
    "message": "Mensaje enviado correctamente",
    "message_id": "wamid.xxx",
    "response": {
      "messages": [{"id": "wamid.xxx"}]
    },
    "debug": {
      "type": "text",
      "to": "51980253258",
      "phone_number_id": "122110111111111"
    }
  }
}
```

---

## Ventajas de la Arquitectura Modular

### ✅ Separación de Responsabilidades
- Cada módulo tiene una función clara
- Fácil de entender y mantener

### ✅ Reutilizable
- `meta_client.py` puede usarse en otros proyectos
- `formatters.py` es agnóstico del dominio
- `message_types.py` es independiente de FastAPI

### ✅ Testeable
- Cada módulo se puede testear aisladamente
- Mocks fáciles de crear

### ✅ Escalable
- Agregar un nuevo tipo de mensaje es trivial
- Cambiar la API de Meta requiere solo cambios en `meta_client.py`

### ✅ Documentado
- Cada función tiene docstrings claros
- Type hints completos
- Ejemplos de uso

### ✅ No Saturado
- `main.py` se mantiene limpio (solo 30 líneas para `/send`)
- Lógica distribuida apropiadamente

---

## Agregar un Nuevo Tipo de Mensaje

Ejemplo: Agregar soporte para mensajes de ubicación (location)

### 1. Agregar enum a `message_types.py`
```python
class MessageType(str, Enum):
    # ... existentes ...
    LOCATION = 'location'
```

### 2. Agregar validación a `SendPayload`
```python
def _validate_location(self) -> bool:
    if not self.get('latitude') or not self.get('longitude'):
        self.errors.append('Requerido: latitude, longitude')
        return False
    return True
```

### 3. Agregar getter a `SendPayload`
```python
def get_location(self) -> tuple[float, float]:
    return (self.get('latitude'), self.get('longitude'))
```

### 4. Agregar método a `MetaWhatsAppClient`
```python
async def send_location(
    self,
    phone_number_id: str,
    to: str,
    latitude: float,
    longitude: float,
    name: str = None
) -> Dict[str, Any]:
    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'location',
        'location': {
            'latitude': latitude,
            'longitude': longitude,
            'name': name
        }
    }
    return await self._send_request(phone_number_id, payload)
```

### 5. Agregar caso a `SendWhatsAppService._send_by_type()`
```python
elif message_type == MessageType.LOCATION:
    lat, lon = send_payload.get_location()
    return await self.meta_client.send_location(
        phone_number_id,
        formatted_phone,
        lat,
        lon,
        name=send_payload.get_message()
    )
```

¡Listo! Sin tocar `main.py`

---

## Estructura de Directorios

```
whatsapp_gateway/
├── main.py                          # FastAPI app (100 líneas)
├── send_service.py                  # Orquestador (200 líneas)
├── message_types.py                 # Validaciones (180 líneas)
├── meta_client.py                   # Cliente HTTP (250 líneas)
├── formatters.py                    # Utilidades (120 líneas)
│
├── test_webhook.py                  # Tests del webhook
├── example_send_requests.py          # Ejemplos de uso
├── example_webhook_payload.json      # Payload ejemplo
│
├── __init__.py                       # Package init
├── config_template.py                # Template de config
├── README.md                         # Descripción general
├── QUICKSTART.md                     # Quick start
└── ARQUITECTURA_MODULAR.md          # Este archivo
```

---

## Próximos Pasos

1. **Testing**: Crear `test_send_service.py` con tests unitarios
2. **Error Handling**: Mejorar manejo de errores (retry logic, circuit breaker)
3. **Logging**: Agregar métricas y tracing distribuido
4. **Rate Limiting**: Implementar rate limiting por cliente
5. **Database** (futuro): Conectar con BD cuando sea necesario
