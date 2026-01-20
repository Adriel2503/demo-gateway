# Quick Start - WhatsApp Gateway

## En 5 minutos

### 1. Instalar

```bash
cd whatsapp_gateway
pip install fastapi uvicorn httpx python-dotenv
```

### 2. Crear .env

Crear archivo `whatsapp_gateway/.env`:

```env
VERIFY_TOKEN=bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c
WHATSAPP_TOKEN=EAAB7ZCxxxx_TU_TOKEN_AQUI
APP_SECRET=tu_app_secret_aqui
AGENT_SERVICE_URL=http://localhost:8001/process
PORT=8000
```

### 3. Ejecutar

```bash
python main.py
```

Deberías ver:
```
INFO:__main__:Iniciando WhatsApp Gateway en 0.0.0.0:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Verificar que funciona

```bash
# En otra terminal
curl http://localhost:8000/health
```

Respuesta:
```json
{
  "status": "ok",
  "service": "WhatsApp Gateway",
  "timestamp": "2026-01-19T10:30:00"
}
```

### 5. Simular un webhook

```bash
python test_webhook.py
```

## Cambiar URL de servicio

Si necesitas cambiar a dónde enviar los mensajes:

1. Editar `.env`:
   ```env
   # Para N8N
   AGENT_SERVICE_URL=https://maravia-n8n-maravia-externo.dvmssk.easypanel.host/webhook/whatsapp_trigger
   
   # O para tu Agent Service
   AGENT_SERVICE_URL=http://localhost:8001/process
   ```

2. Reiniciar el servicio:
   ```bash
   # Ctrl+C para detener
   # Ejecutar de nuevo
   python main.py
   ```

## Documentación Interactiva

Una vez corriendo, abrir en navegador:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Logs

Ver logs en tiempo real:

```bash
# En Windows (PowerShell)
Get-Content -Path "*.log" -Wait

# En Linux/Mac
tail -f whatsapp_gateway.log
```

## Troubleshooting

### Port 8000 already in use

```bash
# Cambiar en .env
PORT=8001

# O matar el proceso
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Agent Service no responde

Verificar que está corriendo:

```bash
curl http://localhost:8001/health
```

Si no funciona, cambiar `AGENT_SERVICE_URL` en `.env` a la URL correcta.

### WHATSAPP_TOKEN es invalid

1. Ir a: https://developers.facebook.com/apps
2. Seleccionar tu app
3. Copiar el "Permanent Access Token" válido
4. Actualizar en `.env`

## Documentación Completa

- **README.md**: Descripción general y características
- **INSTALACION.md**: Guía detallada de instalación y configuración
- **MIGRACION.md**: Cambios desde PHP

## Next Steps

1. Configura en Meta Dashboard (ver INSTALACION.md)
2. Asegúrate que tu Agent Service está corriendo
3. Prueba enviando un mensaje desde WhatsApp

¡Listo!
