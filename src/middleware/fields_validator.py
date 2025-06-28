"""
Field validation functions for expense and revenue transactions.
This module contains all the validation logic for required fields
based on the API requirements in api_service.py.
"""

from typing import Tuple, List, Dict, Any, Optional
from datetime import date
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
    
    # Set current date if "date" field is missing or empty
    if not api_response.get("date"):
        api_response["date"] = date.today().strftime("%Y-%m-%d")
    
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
    
    API Requirements (register_sale parameters):
    - customer_name: str (mapped from "customer" - defaults to "Cliente General")
    - sale_date: str (mapped from "date" - defaults to today)
    - revenue_type_id: int (mapped from "type")
    - note: str (required)
    - crop_variety_sale: list (built from "crop_variety" and "value")
      - crop_variety_id: from "crop_variety"
      - quantity: 1 (default)
      - quantity_unit: "kg" (default)
      - sale_value: from "value"
    
    Returns: (missing_fields, error_message)
    """
    missing_fields = []
    
    # Required fields for all revenue transactions
    if not api_response.get("note"):
        missing_fields.append("note")
    if not api_response.get("value"):
        missing_fields.append("value")
    if not api_response.get("type"):
        missing_fields.append("type")
    
    # Set default customer if not provided
    if not api_response.get("customer"):
        api_response["customer"] = "Cliente General"
    
    # Set current date if "date" field is missing or empty
    if not api_response.get("date"):
        api_response["date"] = date.today().strftime("%Y-%m-%d")
    
    # For crop sales (type = "1"), validate additional fields
    revenue_type = api_response.get("type", "")
    if str(revenue_type) == "1":  # Crop sale
        if not api_response.get("crop_variety"):
            missing_fields.append("crop_variety")
        if not api_response.get("quantity"):
            missing_fields.append("quantity")
        if not api_response.get("quantity_unit"):
            missing_fields.append("quantity_unit")
    
    error_message = ""
    if missing_fields:
        error_message = f"❌ **Faltan campos para registrar el ingreso:**\n"
        field_names = {
            "note": "📝 Descripción de la venta",
            "value": "💰 Valor/monto",
            "type": "📂 Tipo de ingreso",
            "crop_variety": "🌱 Variedad de cultivo",
            "quantity": "📊 Cantidad vendida",
            "quantity_unit": "📏 Unidad de medida (ej: kg, unidades)"
        }
        for field in missing_fields:
            error_message += f"• {field_names.get(field, field)}\n"
        
        # Add helpful messages for crop sales
        if any(field in missing_fields for field in ["crop_variety", "quantity", "quantity_unit"]):
            error_message += "\n💡 **Nota:** Para ventas de cultivos, especifica el cultivo, cantidad y unidad (ej: 10 kg de tomates)"
    
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


def validate_crop_variety_input(value: str, available_crops: list) -> Tuple[bool, str]:
    """
    Validate that the crop variety input matches one of the available crops.
    
    Args:
        value: The user input for crop variety
        available_crops: List of available crop varieties from the API
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, "❌ La variedad de cultivo no puede estar vacía. Por favor, especifica la variedad de cultivo."
    
    # Check if the input matches any available crop (by ID or name)
    for crop in available_crops:
        crop_id = str(crop.get("crop_variety_id", ""))
        crop_name = crop.get("crop_variety_name", "").lower()
        input_value = value.strip().lower()
        
        # Check if input matches crop ID or crop name
        if input_value == crop_id or input_value == crop_name:
            return True, ""
    
    # If no match found, return error with available options
    available_names = [crop.get("crop_variety_name", "") for crop in available_crops if crop.get("crop_variety_name")]
    error_message = f"❌ '{value}' no es un cultivo válido en tu granja.\n\n"
    error_message += "💡 **Cultivos disponibles:**\n"
    for name in available_names:
        error_message += f"• {name}\n"
    error_message += "\n🔄 **Por favor:**\n"
    error_message += "• Selecciona un cultivo de la lista de botones, o\n"
    error_message += "• Escribe exactamente el nombre de uno de los cultivos disponibles"
    
    return False, error_message


def validate_field(field_name: str, value: Any, available_crops: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, str]:
    """
    Validate a single field's value based on its name.

    Args:
        field_name: The name of the field to validate.
        value: The value of the field to validate.
        available_crops: List of available crops for crop_variety validation.

    Returns:
        A tuple containing a boolean indicating if the field is valid,
        and an error message if it's not.
    """
    # Handle empty or None values
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"❌ El campo '{field_name}' no puede estar vacío. Por favor, proporciona un valor."
    
    # Numeric field validation
    if field_name in ["value", "quantity"]:
        try:
            # Remove commas for thousands separators if present
            if isinstance(value, str):
                value = value.replace(",", "").replace("$", "").strip()
            numeric_value = float(value)
            if numeric_value <= 0:
                return False, f"❌ El valor para '{field_name}' debe ser mayor que cero. Por favor, inténtalo de nuevo."
        except (ValueError, TypeError):
            return False, f"❌ El valor para '{field_name}' debe ser un número válido. Por favor, inténtalo de nuevo."

    # Text field validation
    if field_name == "note":
        if not isinstance(value, str) or not value.strip():
            return False, "❌ La descripción no puede estar vacía. Por favor, proporciona una descripción de la transacción."
        if len(value.strip()) < 3:
            return False, "❌ La descripción debe tener al menos 3 caracteres. Por favor, proporciona una descripción más detallada."

    # Type field validation (for both expense and revenue types)
    if field_name == "type":
        if not isinstance(value, str) or not value.strip():
            return False, "❌ El tipo de transacción no puede estar vacío. Por favor, indica el tipo de transacción."
        # Additional validation could be added here if we have access to the available types

    # Customer field validation
    if field_name == "customer":
        if not isinstance(value, str) or not value.strip():
            return False, "❌ El nombre del cliente no puede estar vacío. Por favor, indica el nombre del cliente."
        if len(value.strip()) < 2:
            return False, "❌ El nombre del cliente debe tener al menos 2 caracteres. Por favor, proporciona un nombre válido."

    # Crop variety field validation - special validation against available crops
    if field_name == "crop_variety":
        if available_crops is None:
            # If no crops available, just check it's not empty
            if not isinstance(value, str) or not value.strip():
                return False, "❌ La variedad de cultivo no puede estar vacía. Por favor, especifica la variedad de cultivo."
        else:
            # Validate against available crops
            return validate_crop_variety_input(value, available_crops)

    # Quantity unit field validation
    if field_name == "quantity_unit":
        valid_units = ["kg", "g", "lb", "ton", "unidades", "litros", "ml", "galones", "piezas", "cajas", "sacos"]
        if not isinstance(value, str) or not value.strip():
            return False, "❌ La unidad de medida no puede estar vacía. Por favor, especifica la unidad (ej: kg, unidades, litros)."
        if value.strip().lower() not in [unit.lower() for unit in valid_units]:
            return False, f"❌ Unidad de medida no reconocida. Unidades válidas: {', '.join(valid_units)}. Por favor, inténtalo de nuevo."

    return True, ""
