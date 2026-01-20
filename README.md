# WhatsApp Gateway Service

Servicio que recibe webhooks de Meta WhatsApp y los envía a tu Agent Service.

Migración de `ws_trigger.php` a Python/FastAPI.

## Características

- Recepción de webhooks de Meta WhatsApp Cloud API
- Verificación automática del webhook (GET request)
- Validación de firma HMAC-SHA256
- Soporte multi-tipo de mensajes: texto, imagen, video, audio, documento, ubicación
- Procesamiento asincrónico con BackgroundTasks
- Respuesta rápida a Meta (evita timeouts)
- Logging estructurado
- Totalmente modular y fácil de mantener

## Instalación

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn httpx python-dotenv
```

### 2. Crear archivo .env

Copiar `.env.example` a `.env` y completar con tus credenciales:

```bash
cp .env.example .env
```

Editar `.env` con:
- `VERIFY_TOKEN`: Token para verificación de Meta
- `WHATSAPP_TOKEN`: Token de acceso a WhatsApp API
- `APP_SECRET`: Secret para validar firma de webhooks
- `AGENT_SERVICE_URL`: URL de tu Agent Service

### 3. Ejecutar

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuración en Meta

1. Ir a: https://developers.facebook.com/apps
2. Seleccionar tu app y WhatsApp Business Account
3. En "Configuration", establecer:
   - **Callback URL**: `https://tu-dominio.com/webhook`
   - **Verify Token**: El valor de `VERIFY_TOKEN` en tu `.env`
4. En "Webhook fields", seleccionar: `messages`, `message_status`, `message_template_status_update`

## Flujo de Procesamiento

```
Cliente
  ↓
WhatsApp/Meta
  ↓
GET /webhook (verificación)  ← Meta verifica que existe el webhook
  ↓
POST /webhook (mensaje llega)
  ├─ Validar firma
  ├─ Extraer datos
  ├─ Procesar en background
  └─ Responder 200 OK a Meta (rápido)
  ↓ (background)
Agent Service
  ├─ Procesar con IA
  └─ Retornar respuesta
```

## Estructura del Mensaje

### Recibido de Meta:

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "ENTRY_ID",
    "changes": [{
      "field": "messages",
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "51999888777",
          "phone_number_id": "123456789"
        },
        "contacts": [{
          "profile": {
            "name": "Juan"
          },
          "wa_id": "51980253258"
        }],
        "messages": [{
          "from": "51980253258",
          "id": "msg_id_123",
          "timestamp": "1234567890",
          "type": "text",
          "text": {
            "body": "Hola"
          }
        }]
      }
    }]
  }]
}
```

### Enviado a Agent Service:

```json
{
  "message_id": "msg_id_123",
  "from": "51980253258",
  "from_number": "51980253258",
  "timestamp": 1234567890,
  "message_text": "Hola",
  "message_type": "text",
  "push_name": "Juan",
  "phone_number_id": "123456789",
  "source": "whatsapp_cloud_api"
}
```

## Endpoints

### GET /webhook
Verificación del webhook por Meta.

**Parámetros:**
- `hub_mode`: "subscribe"
- `hub_verify_token`: Token de verificación
- `hub_challenge`: Challenge a devolver

**Respuesta:**
```
200: {challenge_value}
403: Verificación fallida
```

### POST /webhook
Recepción de mensajes.

**Body:** Payload JSON de Meta

**Respuesta:**
```json
{
  "success": true,
  "message": "Webhook received",
  "messages_processed": 1
}
```

### GET /health
Health check del servicio.

**Respuesta:**
```json
{
  "status": "ok",
  "service": "WhatsApp Gateway",
  "timestamp": "2026-01-19T10:30:00"
}
```

## Tipos de Mensaje Soportados

- `text`: Mensajes de texto
- `image`: Imágenes (con caption opcional)
- `video`: Videos (con caption opcional)
- `audio`: Audios
- `document`: Documentos
- `location`: Ubicaciones
- `interactive`: Botones y listas
- `button`: Respuestas de botones

## Logging

El servicio registra:
- Recepción de webhooks
- Validaciones
- Errores
- Estados de procesamiento

Logs estructurados con timestamps.

## Ejemplo de Uso

### 1. Iniciar el servicio

```bash
python main.py
```

Output:
```
INFO:__main__:Iniciando WhatsApp Gateway en 0.0.0.0:8000
INFO:__main__:Agent Service URL: http://localhost:8001/process
```

### 2. Meta verifica el webhook (GET)

```bash
curl "http://localhost:8000/webhook?hub_mode=subscribe&hub_verify_token=bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c&hub_challenge=1234567890"
```

Respuesta: `1234567890`

### 3. Mensaje llega (POST)

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=SIGNATURE_HASH" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [...]
  }'
```

Respuesta:
```json
{
  "success": true,
  "message": "Webhook received",
  "messages_processed": 1
}
```

## Próximas Mejoras

- [ ] Persistencia de mensajes
- [ ] Manejo de multimedia (descarga a S3)
- [ ] Retry automático con queue (Redis/Celery)
- [ ] Métricas y monitoreo
- [ ] Autenticación API

## Miración desde PHP

Cambios principales respecto a `ws_trigger.php`:

| PHP | Python |
|-----|--------|
| `define()` | `os.getenv()` + variables |
| `file_get_contents()` | `await request.body()` |
| `curl_init()` | `httpx.AsyncClient()` |
| `error_log()` | `logging` |
| Sincrónico | Asincrónico con BackgroundTasks |
| N8N Webhook | Agent Service (configurable) |
| BD para credenciales | .env (sin BD) |

## Licencia

MIT
