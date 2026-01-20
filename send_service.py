"""
Servicio de envío de mensajes WhatsApp
Orquestador principal que coordina validación, formato y envío
"""

import logging
from typing import Dict, Any, Optional

from message_types import SendPayload, MessageType
from meta_client import MetaWhatsAppClient
from formatters import format_phone_number, format_response_success, format_response_error

logger = logging.getLogger(__name__)


class SendWhatsAppService:
    """
    Servicio orquestador para enviar mensajes WhatsApp.
    
    Responsabilidades:
    - Validar el payload del request
    - Formatear números telefónicos
    - Seleccionar el método de envío según tipo
    - Procesar respuesta de Meta
    - Retornar respuesta estructurada
    """
    
    def __init__(self, access_token: str):
        """
        Inicializa el servicio.
        
        Args:
            access_token: Token de acceso a Meta WhatsApp Cloud API
        """
        if not access_token:
            raise ValueError('access_token es requerido')
        
        self.access_token = access_token
        self.meta_client = MetaWhatsAppClient(access_token)
    
    async def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un request completo de envío.
        
        Flujo:
        1. Valida el payload
        2. Formatea el número destino
        3. Selecciona método según tipo
        4. Envía a Meta
        5. Procesa respuesta
        
        Args:
            payload: Payload del request con all fields
        
        Returns:
            Response estructurada (success o error)
        """
        logger.info(f'Procesando request de envío')
        
        # Paso 1: Validar payload
        validation_result = self._validate_payload(payload)
        if not validation_result['valid']:
            return validation_result['response']
        
        # Extraer datos validados
        send_payload = validation_result['payload']
        message_type = send_payload.get_type()
        phone = send_payload.get_phone()
        phone_number_id = send_payload.get_phone_number_id()
        
        # Paso 2: Formatear número
        formatted_phone = format_phone_number(phone)
        logger.info(f'Número formateado: {phone} -> {formatted_phone}')
        
        # Paso 3: Enviar según tipo
        logger.info(f'Enviando mensaje tipo: {message_type}')
        meta_response = await self._send_by_type(
            send_payload,
            formatted_phone
        )
        
        # Paso 4: Procesar respuesta
        return self._process_meta_response(
            meta_response,
            message_type,
            formatted_phone,
            phone_number_id
        )
    
    def _validate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida el payload del request.
        
        Returns:
            Dict con 'valid' (bool), 'payload' (SendPayload) y 'response' (si es inválido)
        """
        send_payload = SendPayload(payload)
        is_valid, error_msg = send_payload.validate()
        
        if not is_valid:
            logger.warning(f'Validación fallida: {error_msg}')
            return {
                'valid': False,
                'response': {
                    'success': False,
                    'error': 'Validación fallida',
                    'details': error_msg
                }
            }
        
        logger.info('Payload validado correctamente')
        return {
            'valid': True,
            'payload': send_payload
        }
    
    async def _send_by_type(
        self,
        send_payload: SendPayload,
        formatted_phone: str
    ) -> Dict[str, Any]:
        """
        Envía el mensaje según su tipo.
        
        Args:
            send_payload: Payload validado
            formatted_phone: Número formateado
        
        Returns:
            Respuesta de Meta
        """
        message_type = send_payload.get_type()
        phone_number_id = send_payload.get_phone_number_id()
        
        try:
            if message_type == MessageType.TEXT:
                return await self.meta_client.send_text(
                    phone_number_id,
                    formatted_phone,
                    send_payload.get_message()
                )
            
            elif message_type == MessageType.IMAGE:
                return await self.meta_client.send_image(
                    phone_number_id,
                    formatted_phone,
                    send_payload.get_image_url(),
                    caption=send_payload.get_message()
                )
            
            elif message_type == MessageType.DOCUMENT:
                return await self.meta_client.send_document(
                    phone_number_id,
                    formatted_phone,
                    send_payload.get_document_url(),
                    send_payload.get_document_filename(),
                    caption=send_payload.get_message()
                )
            
            elif message_type == MessageType.AUDIO:
                return await self.meta_client.send_audio(
                    phone_number_id,
                    formatted_phone,
                    send_payload.get_audio_url()
                )
            
            elif message_type == MessageType.VIDEO:
                return await self.meta_client.send_video(
                    phone_number_id,
                    formatted_phone,
                    send_payload.get_video_url(),
                    caption=send_payload.get_message()
                )
            
            else:
                return {
                    'success': False,
                    'error': f'Tipo no soportado: {message_type}'
                }
        
        except Exception as e:
            logger.error(f'Error enviando {message_type}: {e}')
            return {
                'success': False,
                'error': f'Error procesando {message_type}: {str(e)}'
            }
    
    def _process_meta_response(
        self,
        meta_response: Dict[str, Any],
        message_type: str,
        formatted_phone: str,
        phone_number_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Procesa la respuesta de Meta en una respuesta uniforme.
        
        Args:
            meta_response: Respuesta del cliente Meta
            message_type: Tipo de mensaje enviado
            formatted_phone: Número destino formateado
            phone_number_id: ID del número que envía
        
        Returns:
            Response estructurada
        """
        if meta_response.get('success'):
            logger.info(f'Mensaje {message_type} enviado exitosamente')
            
            response_data = meta_response.get('data', {})
            message_id = response_data.get('messages', [{}])[0].get('id')
            
            return format_response_success(
                message_id=message_id,
                message='Mensaje enviado correctamente',
                response_data=response_data,
                message_type=message_type,
                to=formatted_phone,
                phone_number_id=phone_number_id
            )
        
        else:
            logger.error(f'Error enviando {message_type}: {meta_response.get("error")}')
            
            return format_response_error(
                error=meta_response.get('error', 'Error desconocido'),
                details=str(meta_response.get('data', {})),
                message_type=message_type,
                to=formatted_phone,
                http_code=meta_response.get('http_code')
            )
