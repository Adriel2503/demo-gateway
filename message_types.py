"""
Validadores y esquemas para tipos de mensajes
Basado en la API de Meta WhatsApp Cloud
"""

from typing import Optional, Dict, Any, Tuple
from enum import Enum


class MessageType(str, Enum):
    """Tipos de mensajes soportados"""
    TEXT = 'text'
    IMAGE = 'image'
    DOCUMENT = 'document'
    AUDIO = 'audio'
    VIDEO = 'video'


class SendPayload:
    """
    Validador y contenedor para payloads de envío.
    
    Formato esperado:
    {
        'phone_number_id': 'ID del número que envía',
        'phone': 'Número destino (cliente)',
        'type': 'text | image | document | audio | video',
        'message': 'Contenido (obligatorio para text, opcional para image/video/document)',
        'image_url': 'Para type=image',
        'document_url': 'Para type=document',
        'filename': 'Para type=document',
        'audio_url': 'Para type=audio',
        'video_url': 'Para type=video'
    }
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Valida el payload según el tipo de mensaje.
        
        Returns:
            Tupla (es_válido, mensaje_de_error)
        """
        self.errors = []
        self.warnings = []
        
        # Validar campos requeridos siempre
        if not self._validate_required_fields():
            return False, '; '.join(self.errors)
        
        # Validar según el tipo
        message_type = self.get('type', 'text')
        
        if message_type == MessageType.TEXT:
            valid = self._validate_text()
        elif message_type == MessageType.IMAGE:
            valid = self._validate_image()
        elif message_type == MessageType.DOCUMENT:
            valid = self._validate_document()
        elif message_type == MessageType.AUDIO:
            valid = self._validate_audio()
        elif message_type == MessageType.VIDEO:
            valid = self._validate_video()
        else:
            self.errors.append(f'Tipo de mensaje no soportado: {message_type}')
            valid = False
        
        if not valid:
            return False, '; '.join(self.errors)
        
        return True, None
    
    def _validate_required_fields(self) -> bool:
        """Valida campos requeridos en todos los tipos."""
        required = ['phone', 'type']
        
        for field in required:
            if not self.get(field):
                self.errors.append(f'Campo requerido: {field}')
                return False
        
        # phone_number_id debe estar presente (extraído del webhook)
        if not self.get('phone_number_id'):
            self.warnings.append('phone_number_id no proporcionado (se extraerá del contexto)')
        
        return True
    
    def _validate_text(self) -> bool:
        """Valida mensaje de texto."""
        if not self.get('message'):
            self.errors.append('Campo requerido para texto: message')
            return False
        return True
    
    def _validate_image(self) -> bool:
        """Valida mensaje de imagen."""
        if not self.get('image_url'):
            self.errors.append('Campo requerido para imagen: image_url')
            return False
        return True
    
    def _validate_document(self) -> bool:
        """Valida mensaje de documento."""
        if not self.get('document_url'):
            self.errors.append('Campo requerido para documento: document_url')
            return False
        
        if not self.get('filename'):
            self.errors.append('Campo requerido para documento: filename')
            return False
        
        return True
    
    def _validate_audio(self) -> bool:
        """Valida mensaje de audio."""
        if not self.get('audio_url'):
            self.errors.append('Campo requerido para audio: audio_url')
            return False
        return True
    
    def _validate_video(self) -> bool:
        """Valida mensaje de video."""
        if not self.get('video_url'):
            self.errors.append('Campo requerido para video: video_url')
            return False
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del payload."""
        return self.data.get(key, default)
    
    def get_type(self) -> str:
        """Obtiene el tipo de mensaje normalizado."""
        msg_type = self.get('type', 'text').lower()
        try:
            return MessageType[msg_type.upper()].value
        except KeyError:
            return 'text'
    
    def get_phone(self) -> str:
        """Obtiene el número de teléfono destino."""
        return str(self.get('phone', '')).strip()
    
    def get_phone_number_id(self) -> Optional[str]:
        """Obtiene el phone_number_id del que envía."""
        return self.get('phone_number_id')
    
    def get_message(self) -> Optional[str]:
        """Obtiene el mensaje/caption."""
        return self.get('message')
    
    def get_image_url(self) -> Optional[str]:
        """Obtiene la URL de imagen."""
        return self.get('image_url')
    
    def get_document_url(self) -> Optional[str]:
        """Obtiene la URL de documento."""
        return self.get('document_url')
    
    def get_document_filename(self) -> Optional[str]:
        """Obtiene el nombre del documento."""
        return self.get('filename')
    
    def get_audio_url(self) -> Optional[str]:
        """Obtiene la URL de audio."""
        return self.get('audio_url')
    
    def get_video_url(self) -> Optional[str]:
        """Obtiene la URL de video."""
        return self.get('video_url')


def validate_send_request(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Función helper para validar un request de envío.
    
    Args:
        data: Payload del request
    
    Returns:
        Tupla (es_válido, mensaje_de_error)
    """
    payload = SendPayload(data)
    return payload.validate()
