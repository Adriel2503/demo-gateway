"""
Cliente HTTP para Meta WhatsApp Cloud API
Maneja todos los requests async a la API de Meta
"""

import logging
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class MetaWhatsAppClient:
    """
    Cliente para interactuar con Meta WhatsApp Cloud API.
    
    Maneja el envío de todos los tipos de mensajes:
    - Texto
    - Imágenes
    - Documentos
    - Audio
    - Video
    """
    
    GRAPH_API_VERSION = 'v21.0'
    GRAPH_API_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}'
    REQUEST_TIMEOUT = 60.0
    
    def __init__(self, access_token: str):
        """
        Inicializa el cliente Meta.
        
        Args:
            access_token: Token de acceso para autenticación en Meta
        """
        if not access_token:
            raise ValueError('access_token no puede estar vacío')
        
        self.access_token = access_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
    
    async def send_text(
        self,
        phone_number_id: str,
        to: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de texto.
        
        Args:
            phone_number_id: ID del número que envía
            to: Número destino formateado
            message: Contenido del mensaje
        
        Returns:
            Respuesta de Meta con status y message_id
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'text',
            'text': {
                'preview_url': True,
                'body': message
            }
        }
        
        return await self._send_request(phone_number_id, payload)
    
    async def send_image(
        self,
        phone_number_id: str,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía una imagen.
        
        Args:
            phone_number_id: ID del número que envía
            to: Número destino formateado
            image_url: URL de la imagen (debe ser accesible públicamente)
            caption: Texto opcional debajo de la imagen
        
        Returns:
            Respuesta de Meta con status y message_id
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'image',
            'image': {
                'link': image_url
            }
        }
        
        if caption:
            payload['image']['caption'] = caption
        
        return await self._send_request(phone_number_id, payload)
    
    async def send_document(
        self,
        phone_number_id: str,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un documento.
        
        Args:
            phone_number_id: ID del número que envía
            to: Número destino formateado
            document_url: URL del documento (debe ser accesible públicamente)
            filename: Nombre del archivo que verá el usuario
            caption: Texto opcional con el documento
        
        Returns:
            Respuesta de Meta con status y message_id
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'document',
            'document': {
                'link': document_url,
                'filename': filename
            }
        }
        
        if caption:
            payload['document']['caption'] = caption
        
        return await self._send_request(phone_number_id, payload)
    
    async def send_audio(
        self,
        phone_number_id: str,
        to: str,
        audio_url: str
    ) -> Dict[str, Any]:
        """
        Envía un audio.
        
        Args:
            phone_number_id: ID del número que envía
            to: Número destino formateado
            audio_url: URL del audio (debe ser accesible públicamente)
        
        Returns:
            Respuesta de Meta con status y message_id
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'audio',
            'audio': {
                'link': audio_url
            }
        }
        
        return await self._send_request(phone_number_id, payload)
    
    async def send_video(
        self,
        phone_number_id: str,
        to: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un video.
        
        Args:
            phone_number_id: ID del número que envía
            to: Número destino formateado
            video_url: URL del video (debe ser accesible públicamente)
            caption: Texto opcional con el video
        
        Returns:
            Respuesta de Meta con status y message_id
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'video',
            'video': {
                'link': video_url
            }
        }
        
        if caption:
            payload['video']['caption'] = caption
        
        return await self._send_request(phone_number_id, payload)
    
    async def _send_request(
        self,
        phone_number_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta un request HTTP POST a Meta WhatsApp Cloud API.
        
        Args:
            phone_number_id: ID del número que envía
            payload: Payload JSON del mensaje
        
        Returns:
            Dict con 'success', 'data', 'http_code' y opcionalmente 'error'
        """
        url = f'{self.GRAPH_API_URL}/{phone_number_id}/messages'
        
        try:
            logger.info(f'Enviando request a Meta: {url}')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.REQUEST_TIMEOUT
                )
            
            http_code = response.status_code
            
            try:
                response_data = response.json()
            except Exception:
                response_data = {'raw': response.text}
            
            logger.info(f'Respuesta de Meta: {http_code}')
            
            # Meta responde con 200 para éxito
            if 200 <= http_code < 300:
                logger.info(f'Mensaje enviado exitosamente a Meta')
                return {
                    'success': True,
                    'data': response_data,
                    'http_code': http_code
                }
            else:
                logger.error(f'Error de Meta: {http_code} - {response_data}')
                return {
                    'success': False,
                    'error': response_data.get('error', {}).get('message', 'Error desconocido'),
                    'data': response_data,
                    'http_code': http_code
                }
        
        except httpx.RequestError as e:
            logger.error(f'Error de conexión con Meta: {e}')
            return {
                'success': False,
                'error': f'Error de conexión: {str(e)}',
                'http_code': 0
            }
        
        except Exception as e:
            logger.error(f'Error inesperado en request a Meta: {e}')
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}',
                'http_code': 0
            }
