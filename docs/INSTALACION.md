# Instalación y Configuración - WhatsApp Gateway

## Paso 1: Instalar Dependencias

```bash
cd whatsapp_gateway
pip install fastapi uvicorn httpx python-dotenv
```

O si tienes un requirements.txt global:

```bash
pip install -r requirements.txt
```

## Paso 2: Configurar Variables de Entorno

### Opción A: Crear archivo .env (recomendado)

Crear un archivo `.env` en el directorio `whatsapp_gateway/`:

```bash
# whatsapp_gateway/.env

# Token de verificación para Meta
VERIFY_TOKEN=bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c

# Token de acceso a WhatsApp API
WHATSAPP_TOKEN=EAAB7ZCxxxx...

# Secret para validar firma de webhooks
APP_SECRET=mi_app_secret_123

# URL del Agent Service
AGENT_SERVICE_URL=http://localhost:8001/process

# Puerto
PORT=8000
HOST=0.0.0.0
```

### Opción B: Variables de entorno del sistema

```bash
# Windows (PowerShell)
$env:VERIFY_TOKEN="bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c"
$env:WHATSAPP_TOKEN="EAAB7ZCxxxx..."
$env:APP_SECRET="mi_app_secret_123"
$env:AGENT_SERVICE_URL="http://localhost:8001/process"

# O en CMD
set VERIFY_TOKEN=bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c
set WHATSAPP_TOKEN=EAAB7ZCxxxx...
```

```bash
# Linux/Mac
export VERIFY_TOKEN="bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c"
export WHATSAPP_TOKEN="EAAB7ZCxxxx..."
export APP_SECRET="mi_app_secret_123"
export AGENT_SERVICE_URL="http://localhost:8001/process"
```

## Paso 3: Ejecutar el Servicio

### Opción A: Ejecución directa

```bash
python main.py
```

Output esperado:

```
INFO:__main__:Iniciando WhatsApp Gateway en 0.0.0.0:8000
INFO:__main__:Agent Service URL: http://localhost:8001/process
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Opción B: Con uvicorn directamente

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Opción C: En background (Linux/Mac)

```bash
nohup python main.py > whatsapp_gateway.log 2>&1 &
```

## Paso 4: Obtener Credenciales de Meta

### Obtener VERIFY_TOKEN

1. Ir a: https://developers.facebook.com/apps
2. Seleccionar tu app
3. En "WhatsApp" → "Configuration"
4. Usar cualquier string seguro (el que ya está en .env es válido)

### Obtener WHATSAPP_TOKEN

1. En https://developers.facebook.com/apps
2. Seleccionar tu WhatsApp Business Account
3. En "API Setup" → "Permanent Access Token"
4. Generar o copiar el token existente

### Obtener APP_SECRET

1. En https://developers.facebook.com/apps
2. En "Settings" → "Basic"
3. Copiar el "App Secret"

## Paso 5: Configurar Webhook en Meta

1. Ir a: https://developers.facebook.com/apps
2. Seleccionar tu app
3. En "WhatsApp" → "Configuration"
4. En "Webhook URL": Ingresar `https://tu-dominio.com/webhook`
5. En "Verify Token": Ingresar el mismo valor de `VERIFY_TOKEN` en tu `.env`
6. En "Webhook fields": Seleccionar:
   - `messages`
   - `message_status`
   - `message_template_status_update`
7. Click en "Verify and Save"

## Paso 6: Verificar que Funciona

### Test Local (sin Meta)

```bash
# Verificación del webhook
curl "http://localhost:8000/webhook?hub_mode=subscribe&hub_verify_token=bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c&hub_challenge=test123"

# Respuesta esperada: test123
```

### Test con Python

```bash
python test_webhook.py
```

Output:

```
WhatsApp Gateway - Test Suite
Gateway URL: http://localhost:8000

=== Health Check ===
Status: 200
Response: {
  "status": "ok",
  "service": "WhatsApp Gateway",
  "timestamp": "2026-01-19T10:30:00"
}

✓ Health Check: PASS
✓ Webhook Verification (Valid): PASS
✓ Text Message: PASS

Total: 3/3 tests pasaron
```

## Cambiar URL de Agent Service

Para cambiar donde se envían los mensajes procesados:

### Para N8N:
```env
AGENT_SERVICE_URL=https://maravia-n8n-maravia-externo.dvmssk.easypanel.host/webhook/whatsapp_trigger
```

### Para tu Agent Service:
```env
AGENT_SERVICE_URL=https://tu-agente-service.com/process
```

### Para desarrollo local:
```env
AGENT_SERVICE_URL=http://localhost:8001/process
```

Solo edita el archivo `.env` y reinicia el servicio.

## Solucionar Problemas

### Error: "Port 8000 already in use"

Cambiar el puerto en `.env`:

```env
PORT=8001
```

O matar el proceso que usa el puerto:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Error: "WHATSAPP_TOKEN not found"

Asegúrate que el archivo `.env` está en el mismo directorio que `main.py`:

```bash
ls -la whatsapp_gateway/.env
```

O verifica que las variables de entorno están configuradas:

```bash
echo $WHATSAPP_TOKEN
```

### Error: "Agent Service connection refused"

Verificar que:

1. El Agent Service está corriendo en la URL configurada
2. La URL en `AGENT_SERVICE_URL` es correcta
3. No hay firewall bloqueando la conexión

```bash
# Probar conexión
curl http://localhost:8001/health
```

### Verificación del webhook falla

Verificar que:

1. El `VERIFY_TOKEN` coincide entre `.env` y Meta Dashboard
2. El HTTPS está correctamente configurado (usar certificado válido)
3. La URL es accesible desde internet

## Deployment en Producción

### Con Gunicorn + Nginx

```bash
# Instalar Gunicorn
pip install gunicorn

# Ejecutar
gunicorn main:app -w 4 -b 0.0.0.0:8000
```

### Con Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t whatsapp-gateway .
docker run -e WHATSAPP_TOKEN=xxx -e AGENT_SERVICE_URL=http://agent-service:8001 -p 8000:8000 whatsapp-gateway
```

### Con systemd (Linux)

Crear archivo `/etc/systemd/system/whatsapp-gateway.service`:

```ini
[Unit]
Description=WhatsApp Gateway Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/whatsapp_gateway
Environment="PATH=/var/www/whatsapp_gateway/venv/bin"
ExecStart=/var/www/whatsapp_gateway/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable whatsapp-gateway
systemctl start whatsapp-gateway
systemctl status whatsapp-gateway
```

## Monitoreo

Ver logs en tiempo real:

```bash
# Con journalctl (si usas systemd)
journalctl -u whatsapp-gateway -f

# Con tail (si corres manualmente)
tail -f whatsapp_gateway.log
```

Salud del servicio:

```bash
curl http://localhost:8000/health
```

---

¿Necesitas ayuda adicional?
