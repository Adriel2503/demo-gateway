"""
Formatters para WhatsApp Gateway Service
Utilidades para formatear y normalizar datos
"""

import re
from typing import Optional


def format_phone_number(phone: str, default_country_code: str = '51') -> str:
    """
    Formatea un número de teléfono para la API de Meta WhatsApp.
    
    Características:
    - Elimina espacios, guiones, paréntesis y caracteres especiales
    - Elimina el + si existe al inicio
    - Si empieza con 0, lo quita (formato peruano)
    - Si no tiene código de país, agrega el código por defecto
    
    Args:
        phone: Número de teléfono sin formato
        default_country_code: Código de país por defecto (por defecto 51 para Perú)
    
    Returns:
        Número de teléfono formateado sin espacios y con código de país
    
    Ejemplo:
        >>> format_phone_number('980253258')
        '51980253258'
        >>> format_phone_number('+51 9 8025 3258')
        '51980253258'
        >>> format_phone_number('09 8025 3258')
        '51980253258'
    """
    if not phone:
        return ''
    
    # Eliminar espacios, guiones, paréntesis, + y caracteres especiales
    cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))
    
    # Si empieza con 0, quitarlo (formato peruano)
    if cleaned.startswith('0'):
        cleaned = cleaned[1:]
    
    # Si no tiene código de país (menos de 11 dígitos para Perú típicamente),
    # agregar el código de país por defecto
    if len(cleaned) <= 9:
        cleaned = default_country_code + cleaned
    
    return cleaned


def format_response_success(
    message_id: Optional[str] = None,
    message: str = 'Mensaje enviado correctamente',
    response_data: Optional[dict] = None,
    message_type: str = 'text',
    to: Optional[str] = None,
    phone_number_id: Optional[str] = None
) -> dict:
    """
    Formatea una respuesta exitosa estructurada.
    
    Args:
        message_id: ID del mensaje de Meta
        message: Mensaje de éxito
        response_data: Datos de la respuesta de Meta
        message_type: Tipo de mensaje enviado
        to: Número destino
        phone_number_id: ID del número que envía
    
    Returns:
        Dict con estructura de respuesta exitosa
    """
    result = {
        'success': True,
        'message': message
    }
    
    if message_id:
        result['message_id'] = message_id
    
    if response_data:
        result['response'] = response_data
    
    # Debug info
    debug = {'type': message_type}
    if to:
        debug['to'] = to
    if phone_number_id:
        debug['phone_number_id'] = phone_number_id
    
    result['debug'] = debug
    
    return result


def format_response_error(
    error: str,
    details: Optional[str] = None,
    message_type: Optional[str] = None,
    to: Optional[str] = None,
    http_code: Optional[int] = None
) -> dict:
    """
    Formatea una respuesta de error estructurada.
    
    Args:
        error: Descripción del error principal
        details: Detalles adicionales
        message_type: Tipo de mensaje que se intentaba enviar
        to: Número destino
        http_code: Código HTTP de Meta
    
    Returns:
        Dict con estructura de respuesta de error
    """
    result = {
        'success': False,
        'error': error
    }
    
    if details:
        result['details'] = details
    
    if http_code:
        result['http_code'] = http_code
    
    # Debug info
    debug = {}
    if message_type:
        debug['type'] = message_type
    if to:
        debug['to'] = to
    
    if debug:
        result['debug'] = debug
    
    return result
