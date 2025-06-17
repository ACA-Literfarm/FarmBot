"""
Field validation functions for expense and revenue transactions.
This module contains all the validation logic for required fields
based on the API requirements in api_service.py.
"""

from typing import Tuple, List, Dict, Any
import logging


def validate_expense_fields(api_response: dict) -> Tuple[List[str], str]:
    """
    Validate required fields for expense transactions based on register_expense API requirements.
    
    API Requirements:
    - note: str (required)
    - value: float (required)
    - expense_type_id: int (required - mapped from "type" field)
    - expense_date: str (optional - defaults to today)
    
    Returns: (missing_fields, error_message)
    """
    missing_fields = []
    
    # Required fields for expenses
    if not api_response.get("note"):
        missing_fields.append("note")
    if not api_response.get("value"):
        missing_fields.append("value")
    if not api_response.get("type"):
        missing_fields.append("type")
    
    error_message = ""
    if missing_fields:
        error_message = f"❌ **Faltan campos para registrar el gasto:**\n"
        field_names = {
            "note": "📝 Descripción del gasto",
            "value": "💰 Valor/monto",
            "type": "📂 Tipo de gasto"
        }
        for field in missing_fields:
            error_message += f"• {field_names.get(field, field)}\n"
    
    return missing_fields, error_message


def validate_revenue_fields(api_response: dict) -> Tuple[List[str], str]:
    """
    Validate required fields for revenue transactions based on register_sale API requirements.
    
    API Requirements:
    - note: str (required)
    - value: float (required) 
    - revenue_type_id: int (required - mapped from "type" field)
    - crop_variety: int (required only for crop sales - revenue_type_id = 1)
    - customer_name: str (optional - defaults to "Cliente General")
    - sale_date: str (optional - defaults to today)
    
    Returns: (missing_fields, error_message)
    """
    missing_fields = []
    
    # Required fields for revenue
    if not api_response.get("note"):
        missing_fields.append("note")
    if not api_response.get("value"):
        missing_fields.append("value")
    if not api_response.get("type"):
        missing_fields.append("type")
    
    # Check if crop_variety is required for crop sales (revenue_type_id = 1)
    revenue_type = api_response.get("type", "")
    if str(revenue_type) == "1" and not api_response.get("crop_variety"):
        missing_fields.append("crop_variety")
    
    error_message = ""
    if missing_fields:
        error_message = f"❌ **Faltan campos para registrar el ingreso:**\n"
        field_names = {
            "note": "📝 Descripción de la venta",
            "value": "💰 Valor/monto",
            "type": "📂 Tipo de ingreso",
            "crop_variety": "🌱 Variedad de cultivo (requerida para ventas de cultivos)"
        }
        for field in missing_fields:
            error_message += f"• {field_names.get(field, field)}\n"
        
        # Add helpful message for crop variety
        if "crop_variety" in missing_fields:
            error_message += "\n💡 **Nota:** Para ventas de cultivos, especifica qué cultivo vendiste (ej: tomates, lechugas, etc.)"
    
    return missing_fields, error_message


def validate_revenue_type(api_response: dict, revenue_types: list) -> Tuple[bool, str, str]:
    """
    Validate if the revenue type exists in the available revenue types.
    
    Args:
        api_response: The API response containing the revenue type
        revenue_types: List of available revenue types from the API
        
    Returns:
        Tuple of (is_valid, revenue_name, error_message)
    """
    revenue_type_id = api_response.get("type", "")
    
    if not revenue_type_id:
        return False, "", "❌ No se especificó el tipo de ingreso"
    
    # Try to find the revenue type by ID or name
    for revenue_type in revenue_types:
        if str(revenue_type.get("revenue_type_id")) == str(revenue_type_id) or \
           str(revenue_type.get("revenue_name", "")).lower() == str(revenue_type_id).lower():
            return True, revenue_type.get("revenue_name", ""), ""
    
    return False, "", f"❌ Tipo de ingreso '{revenue_type_id}' no encontrado en la lista disponible"


def validate_crop_variety(api_response: dict, crop_varieties: list) -> Tuple[bool, str, str]:
    """
    Validate if the crop variety exists in the available crop varieties.
    
    Args:
        api_response: The API response containing the crop variety
        crop_varieties: List of available crop varieties from the API
        
    Returns:
        Tuple of (is_valid, crop_name, error_message)
    """
    crop_variety_id = api_response.get("crop_variety", "")
    
    if not crop_variety_id:
        return True, "", ""  # Crop variety is optional for non-crop sales
    
    # Try to find the crop variety by ID or name
    for variety in crop_varieties:
        if str(variety.get("crop_variety_id")) == str(crop_variety_id) or \
           str(variety.get("crop_variety_name", "")).lower() == str(crop_variety_id).lower():
            return True, variety.get("crop_variety_name", ""), ""
    
    return False, "", f"❌ Variedad de cultivo '{crop_variety_id}' no encontrada en la lista disponible"


def validate_expense_type(api_response: dict, expense_types: list) -> Tuple[bool, str, str]:
    """
    Validate if the expense type exists in the available expense types.
    
    Args:
        api_response: The API response containing the expense type
        expense_types: List of available expense types from the API
        
    Returns:
        Tuple of (is_valid, expense_name, error_message)
    """
    expense_type_id = api_response.get("type", "")
    
    if not expense_type_id:
        return False, "", "❌ No se especificó el tipo de gasto"
    
    # Try to find the expense type by ID or name
    for expense_type in expense_types:
        if str(expense_type.get("expense_type_id")) == str(expense_type_id) or \
           str(expense_type.get("expense_name", "")).lower() == str(expense_type_id).lower():
            return True, expense_type.get("expense_name", ""), ""
    
    return False, "", f"❌ Tipo de gasto '{expense_type_id}' no encontrado en la lista disponible"


def validate_transaction_context(chat_session_id: int, farm_id: str, token: str) -> Tuple[bool, str]:
    """
    Validate that all required context is available for API transactions.
    
    Args:
        chat_session_id: The chat session ID
        farm_id: The selected farm ID
        token: The authentication token
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_context = []
    
    if not chat_session_id:
        missing_context.append("sesión de chat")
    if not farm_id:
        missing_context.append("granja seleccionada")
    if not token:
        missing_context.append("token de autenticación")
    
    if missing_context:
        error_message = f"❌ **Error de contexto:** Faltan los siguientes elementos:\n"
        for context in missing_context:
            error_message += f"• {context}\n"
        
        if "granja seleccionada" in missing_context:
            error_message += "\n💡 Usa el comando /granjas para seleccionar una granja"
        if "token de autenticación" in missing_context:
            error_message += "\n💡 Usa el comando /login para autenticarte"
        
        return False, error_message
    
    return True, ""
