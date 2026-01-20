"""
Script de prueba para WhatsApp Gateway.
Simula webhooks de Meta para testing local.
"""

import json
import requests
import hmac
import hashlib
from datetime import datetime

# Configuración
GATEWAY_URL = 'http://localhost:8000'
VERIFY_TOKEN = 'bb16916dccfa54d8ee964f2546b31cb112dec84d60b3aba0aa5201bcf5a0b89c'
APP_SECRET = 'tu_app_secret_aqui'  # Opcional para firma

# ============================================================================
# FUNCIONES DE PRUEBA
# ============================================================================

def test_health_check():
    """Prueba el health check del servicio."""
    print('\n=== Health Check ===')
    try:
        response = requests.get(f'{GATEWAY_URL}/health')
        print(f'Status: {response.status_code}')
        print(f'Response: {json.dumps(response.json(), indent=2)}')
        return response.status_code == 200
    except Exception as e:
        print(f'Error: {e}')
        return False

def test_webhook_verification():
    """Prueba la verificación del webhook (GET request de Meta)."""
    print('\n=== Webhook Verification (GET) ===')
    
    challenge = '1234567890'
    params = {
        'hub_mode': 'subscribe',
        'hub_verify_token': VERIFY_TOKEN,
        'hub_challenge': challenge
    }
    
    try:
        response = requests.get(f'{GATEWAY_URL}/webhook', params=params)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
        
        # Debe devolver el challenge como número
        return response.status_code == 200 and response.text == challenge
    except Exception as e:
        print(f'Error: {e}')
        return False

def test_webhook_verification_invalid_token():
    """Prueba la verificación con token inválido."""
    print('\n=== Webhook Verification - Invalid Token ===')
    
    challenge = '1234567890'
    params = {
        'hub_mode': 'subscribe',
        'hub_verify_token': 'token_invalido',
        'hub_challenge': challenge
    }
    
    try:
        response = requests.get(f'{GATEWAY_URL}/webhook', params=params)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
        
        # Debe rechazar con 403
        return response.status_code == 403
    except Exception as e:
        print(f'Error: {e}')
        return False

def generate_webhook_signature(raw_body):
    """Genera la firma HMAC-SHA256 del webhook."""
    if not APP_SECRET:
        return None
    
    signature = hmac.new(
        APP_SECRET.encode('utf-8'),
        raw_body.encode('utf-8') if isinstance(raw_body, str) else raw_body,
        hashlib.sha256
    ).hexdigest()
    
    return f'sha256={signature}'

def test_text_message_webhook():
    """Prueba recibir un mensaje de texto."""
    print('\n=== Text Message Webhook (POST) ===')
    
    payload = {
        'object': 'whatsapp_business_account',
        'entry': [
            {
                'id': 'ENTRY_ID',
                'changes': [
                    {
                        'field': 'messages',
                        'value': {
                            'messaging_product': 'whatsapp',
                            'metadata': {
                                'display_phone_number': '51999888777',
                                'phone_number_id': '123456789012345',
                                'business_account_id': 'BUSINESS_ACCOUNT_ID'
                            },
                            'contacts': [
                                {
                                    'profile': {
                                        'name': 'Juan Pérez'
                                    },
                                    'wa_id': '51980253258'
                                }
                            ],
                            'messages': [
                                {
                                    'from': '51980253258',
                                    'id': f'wamid_{int(datetime.now().timestamp())}',
                                    'timestamp': str(int(datetime.now().timestamp())),
                                    'type': 'text',
                                    'text': {
                                        'body': 'Hola, esto es una prueba'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    raw_body = json.dumps(payload)
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Agregar firma si está configurado APP_SECRET
    if APP_SECRET:
        signature = generate_webhook_signature(raw_body)
        headers['X-Hub-Signature-256'] = signature
        print(f'Firma: {signature}')
    
    try:
        response = requests.post(
            f'{GATEWAY_URL}/webhook',
            data=raw_body,
            headers=headers
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {json.dumps(response.json(), indent=2)}')
        
        return response.status_code == 200 and response.json().get('success')
    except Exception as e:
        print(f'Error: {e}')
        return False

def test_image_message_webhook():
    """Prueba recibir una imagen."""
    print('\n=== Image Message Webhook (POST) ===')
    
    payload = {
        'object': 'whatsapp_business_account',
        'entry': [
            {
                'id': 'ENTRY_ID',
                'changes': [
                    {
                        'field': 'messages',
                        'value': {
                            'messaging_product': 'whatsapp',
                            'metadata': {
                                'display_phone_number': '51999888777',
                                'phone_number_id': '123456789012345'
                            },
                            'contacts': [
                                {
                                    'profile': {
                                        'name': 'María García'
                                    },
                                    'wa_id': '51987654321'
                                }
                            ],
                            'messages': [
                                {
                                    'from': '51987654321',
                                    'id': f'wamid_{int(datetime.now().timestamp())}',
                                    'timestamp': str(int(datetime.now().timestamp())),
                                    'type': 'image',
                                    'image': {
                                        'mime_type': 'image/jpeg',
                                        'sha256': 'abc123...',
                                        'id': 'media_id_123',
                                        'caption': 'Mi foto'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    raw_body = json.dumps(payload)
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if APP_SECRET:
        signature = generate_webhook_signature(raw_body)
        headers['X-Hub-Signature-256'] = signature
    
    try:
        response = requests.post(
            f'{GATEWAY_URL}/webhook',
            data=raw_body,
            headers=headers
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {json.dumps(response.json(), indent=2)}')
        
        return response.status_code == 200
    except Exception as e:
        print(f'Error: {e}')
        return False

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print('WhatsApp Gateway - Test Suite')
    print(f'Gateway URL: {GATEWAY_URL}')
    print(f'Verify Token: {VERIFY_TOKEN}')
    
    results = {
        'Health Check': test_health_check(),
        'Webhook Verification (Valid)': test_webhook_verification(),
        'Webhook Verification (Invalid)': test_webhook_verification_invalid_token(),
        'Text Message': test_text_message_webhook(),
        'Image Message': test_image_message_webhook(),
    }
    
    print('\n' + '='*50)
    print('RESULTADOS')
    print('='*50)
    
    for test_name, result in results.items():
        status = 'PASS' if result else 'FAIL'
        symbol = '✓' if result else '✗'
        print(f'{symbol} {test_name}: {status}')
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f'\nTotal: {passed}/{total} tests pasaron')
