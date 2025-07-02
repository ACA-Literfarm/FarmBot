import pytest
import json
import sys
import os
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Asegurar que src/ esté en PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.ai_service import query_ai_model
from prompts import FINANCIAL_CLASSIFIER_PROMPT

# Mock data that simulates realistic API responses
DUMMY_EXPENSE_TYPES = [
    {"expense_type_id": "1", "expense_name": "Semillas"},
    {"expense_type_id": "2", "expense_name": "Fertilizantes"},
    {"expense_type_id": "3", "expense_name": "Control de plagas"},
    {"expense_type_id": "4", "expense_name": "Combustible"},
    {"expense_type_id": "5", "expense_name": "Herramientas"}
]

DUMMY_REVENUE_TYPES = [
    {"revenue_type_id": "101", "revenue_name": "Venta de cultivos"},
    {"revenue_type_id": "405", "revenue_name": "Otros"}
]

DUMMY_CROP_VARIETIES = [
    {"crop_variety_id": "201", "crop_variety_name": "Tomate", "crop_id": "10"},
    {"crop_variety_id": "202", "crop_variety_name": "Lechuga", "crop_id": "11"},
    {"crop_variety_id": "203", "crop_variety_name": "Maíz", "crop_id": "12"},
    {"crop_variety_id": "204", "crop_variety_name": "Acacia amarilla", "crop_id": "13"}
]

# Utilidad para crear una respuesta falsa tipo OpenAI
def make_fake_response(content_str: str):
    fake = MagicMock()
    choice = MagicMock()
    message = MagicMock()
    message.content = content_str
    choice.message = message
    fake.choices = [choice]
    return fake

# ------------------------
# Tests for basic functionality
# ------------------------

def test_basic_functionality():
    """Test basic imports and module structure"""
    # Test that we can import the main functions without issues
    from services.ai_service import query_ai_model, format_expense_types_context
    from prompts import FINANCIAL_CLASSIFIER_PROMPT
    
    # Test that constants are accessible
    assert isinstance(FINANCIAL_CLASSIFIER_PROMPT, str)
    assert len(DUMMY_EXPENSE_TYPES) > 0
    assert len(DUMMY_REVENUE_TYPES) > 0
    assert len(DUMMY_CROP_VARIETIES) > 0

def test_prompt_exists():
    """Test that the financial classifier prompt exists and contains required fields"""
    assert isinstance(FINANCIAL_CLASSIFIER_PROMPT, str)
    assert "clasificacion" in FINANCIAL_CLASSIFIER_PROMPT
    assert "gasto" in FINANCIAL_CLASSIFIER_PROMPT
    assert "ingreso" in FINANCIAL_CLASSIFIER_PROMPT
    assert "saludo" in FINANCIAL_CLASSIFIER_PROMPT
    assert "no_relacionado" in FINANCIAL_CLASSIFIER_PROMPT

# ------------------------
# Tests for expense classification
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_expense_with_specific_type(mock_create):
    """Test expense classification with specific type matching"""
    user_input = "Compré semillas por 300 pesos"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "¡Perfecto! He registrado una compra de semillas por $300.00 💰. Si quieres registrar otra transacción, solo dime.",
        "respuesta_api": {
            "note": "Compra de semillas",
            "value": "300.00",
            "type": "1",  # Semillas
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "gasto"
    assert "300" in parsed["respuesta"]
    assert parsed["respuesta_api"]["type"] == "1"
    assert parsed["respuesta_api"]["value"] == "300.00"
    assert parsed["respuesta_api"]["customer"] == ""  # Expenses don't have customers

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_expense_with_date(mock_create):
    """Test expense with specific date extraction"""
    user_input = "Ayer gasté 150 en fertilizante"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "¡Perfecto! He registrado un gasto en fertilizante por $150.00 💰.",
        "respuesta_api": {
            "note": "Gasto en fertilizante",
            "value": "150.00",
            "type": "2",  # Fertilizantes
            "date": yesterday,  # Dynamic yesterday
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["date"] == yesterday
    assert parsed["respuesta_api"]["type"] == "2"

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_expense_combustible(mock_create):
    """Test fuel/combustible expense classification"""
    user_input = "Llené el tanque de gasolina por 80 dólares"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "¡Perfecto! He registrado un gasto en combustible por $80.00 ⛽💰.",
        "respuesta_api": {
            "note": "Combustible para tanque",
            "value": "80.00",
            "type": "4",  # Combustible
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["type"] == "4"
    assert "80.00" in parsed["respuesta_api"]["value"]

# ------------------------
# Tests for revenue/income classification
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_crop_sale_with_existing_variety(mock_create):
    """Test crop sale with existing crop variety in the list"""
    user_input = "Vendí 5 kg de tomates por 100 pesos a Juan"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta de tomates por $100.00 a Juan 💰🍅.",
        "respuesta_api": {
            "note": "Venta de tomates",
            "value": "100.00",
            "type": "101",  # Venta de cultivos
            "date": "",
            "crop_variety": "201",  # Tomate exists in our list
            "customer": "Juan",
            "quantity": "5",
            "quantity_unit": "kg"
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["type"] == "101"
    assert parsed["respuesta_api"]["crop_variety"] == "201"
    assert parsed["respuesta_api"]["customer"] == "Juan"
    assert "quantity" in parsed["respuesta_api"]

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_crop_sale_nonexistent_variety(mock_create):
    """Test crop sale with non-existent crop variety"""
    user_input = "Vendí pepinos por 80 pesos"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "Lastimosamente, no podré registrar la venta de pepinos porque no tengo esa variedad en mi lista. Por favor, verifica el nombre del cultivo 😊",
        "respuesta_api": {
            "note": "",
            "value": "",
            "type": "101",
            "date": "",
            "crop_variety": "",  # Empty because pepinos not in list
            "customer": "",
            "quantity": "",
            "quantity_unit": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["crop_variety"] == ""
    assert "no podré registrar" in parsed["respuesta"]

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_animal_sale_otros_type(mock_create):
    """Test animal sale should use 'Otros' type, not crop sale"""
    user_input = "Vendí un caballo por 2000 dólares"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta por $2000.00 💰🐴.",
        "respuesta_api": {
            "note": "Venta de caballo",
            "value": "2000.00",
            "type": "405",  # Otros - not crop sale
            "date": "",
            "crop_variety": "",  # No crop variety for animals
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["type"] == "405"  # Otros
    assert parsed["respuesta_api"]["crop_variety"] == ""

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_revenue_with_customer_variations(mock_create):
    """Test different ways customers can be mentioned"""
    user_input = "La Cooperativa del Campo me compró maíz por 500 pesos"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta de maíz por $500.00 a Cooperativa del Campo 💰🌽.",
        "respuesta_api": {
            "note": "Venta de maíz",
            "value": "500.00",
            "type": "101",
            "date": "",
            "crop_variety": "203",  # Maíz exists
            "customer": "Cooperativa del Campo"
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["customer"] == "Cooperativa del Campo"
    assert parsed["respuesta_api"]["crop_variety"] == "203"

# ------------------------
# Tests for greeting classification
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_greeting_classification(mock_create):
    """Test greeting messages are properly classified"""
    user_input = "Hola, buenos días"
    json_text = json.dumps({
        "clasificacion": "saludo",
        "respuesta": "¡Hola! Soy tu asistente financiero agrícola 🤖. Te ayudo a gestionar las finanzas de tu granja. ¿Qué transacción quieres registrar hoy? 😊",
        "respuesta_api": {
            "note": "",
            "value": "",
            "type": "",
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "saludo"
    assert "asistente financiero agrícola" in parsed["respuesta"]
    assert all(parsed["respuesta_api"][key] == "" for key in parsed["respuesta_api"])

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_greeting_variations(mock_create):
    """Test different greeting variations"""
    greetings = ["hola", "buenos días", "hey", "qué tal", "como estás"]
    
    for greeting in greetings:
        json_text = json.dumps({
            "clasificacion": "saludo",
            "respuesta": "¡Hola! Soy tu asistente financiero agrícola 🤖.",
            "respuesta_api": {
                "note": "",
                "value": "",
                "type": "",
                "date": "",
                "crop_variety": "",
                "customer": ""
            }
        })
        mock_create.return_value = make_fake_response(json_text)
        
        result = await query_ai_model(greeting, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
        parsed = json.loads(result)
        assert parsed["clasificacion"] == "saludo"

# ------------------------
# Tests for non-related classification
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_non_related_classification(mock_create):
    """Test non-agricultural related messages"""
    user_input = "¿Cuál es la capital de Francia?"
    json_text = json.dumps({
        "clasificacion": "no_relacionado",
        "respuesta": "Lo siento, no puedo ayudarte con eso. Mi función es asistir con el registro de gastos e ingresos agrícolas. ¿Hay alguna transacción financiera que quieras registrar? 🤖",
        "respuesta_api": {
            "note": "",
            "value": "",
            "type": "",
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "no_relacionado"
    assert "gastos e ingresos agrícolas" in parsed["respuesta"]
    assert all(parsed["respuesta_api"][key] == "" for key in parsed["respuesta_api"])

# ------------------------
# Tests for error handling
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", side_effect=Exception("API Error"))
async def test_ai_service_error_handling(mock_create, caplog):
    """Test that AI service handles errors gracefully"""
    user_input = "Vendí tomates por 100 pesos"
    
    with caplog.at_level("ERROR"):
        result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
        
        # Should return error response in JSON format
        parsed = json.loads(result)
        assert parsed["clasificacion"] == "no_relacionado"
        assert "⚠️" in parsed["respuesta"]
        assert "API Error" in caplog.text

# ------------------------
# Tests for edge cases
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_incomplete_transaction_data(mock_create):
    """Test handling of incomplete transaction information"""
    user_input = "Hice un gasto pero no recuerdo cuánto"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "Entiendo que hiciste un gasto. ¿Podrías decirme el monto y en qué lo gastaste? 💰",
        "respuesta_api": {
            "note": "Gasto sin especificar",
            "value": "",  # Empty because amount not specified
            "type": "",
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["value"] == ""
    assert "monto" in parsed["respuesta"]

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_exact_crop_variety_matching(mock_create):
    """Test that crop varieties must match exactly"""
    user_input = "Vendí acacia por 200 pesos"  # Should NOT match "Acacia amarilla"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "Lastimosamente, no podré registrar la venta de acacia porque no tengo esa variedad exacta en mi lista. Tengo 'Acacia amarilla' disponible. 😊",
        "respuesta_api": {
            "note": "",
            "value": "",
            "type": "101",
            "date": "",
            "crop_variety": "",  # Empty because exact match not found
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["crop_variety"] == ""

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_multiple_transactions_context(mock_create):
    """Test handling multiple transactions in sequence"""
    # First transaction
    json1 = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "¡Perfecto! He registrado una compra de semillas por $50.00 💰.",
        "respuesta_api": {
            "note": "Compra de semillas",
            "value": "50.00",
            "type": "1",
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    
    # Second transaction
    json2 = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta de lechuga por $75.00 💰🥬.",
        "respuesta_api": {
            "note": "Venta de lechuga",
            "value": "75.00",
            "type": "101",
            "date": "",
            "crop_variety": "202",  # Lechuga
            "customer": ""
        }
    })
    
    mock_create.side_effect = [make_fake_response(json1), make_fake_response(json2)]

    result1 = await query_ai_model("Compré semillas por 50 pesos", DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    result2 = await query_ai_model("Vendí lechuga por 75 pesos", DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    
    parsed1 = json.loads(result1)
    parsed2 = json.loads(result2)
    
    assert parsed1["clasificacion"] == "gasto"
    assert parsed2["clasificacion"] == "ingreso"
    assert parsed1["respuesta_api"]["type"] == "1"  # Semillas
    assert parsed2["respuesta_api"]["crop_variety"] == "202"  # Lechuga

# ------------------------
# Test context formatting functions
# ------------------------

def test_expense_types_context_formatting():
    """Test that expense types are properly formatted for AI context"""
    from services.ai_service import format_expense_types_context
    
    result = format_expense_types_context(DUMMY_EXPENSE_TYPES)
    assert "Expense types available:" in result
    assert "ID: 1 - Semillas" in result
    assert "ID: 2 - Fertilizantes" in result

def test_revenue_types_context_formatting():
    """Test that revenue types are properly formatted for AI context"""
    from services.ai_service import format_revenue_types_context
    
    result = format_revenue_types_context(DUMMY_REVENUE_TYPES)
    assert "Revenue types available:" in result
    assert "ID: 101 - Venta de cultivos" in result
    assert "ID: 405 - Otros" in result

def test_crop_varieties_context_formatting():
    """Test that crop varieties are properly formatted for AI context"""
    from services.ai_service import format_crop_varieties_context
    
    result = format_crop_varieties_context(DUMMY_CROP_VARIETIES)
    assert "Crop varieties available:" in result
    assert "ID: 201 - Tomate" in result
    assert "ID: 204 - Acacia amarilla" in result

def test_empty_context_formatting():
    """Test handling of empty context lists"""
    from services.ai_service import format_expense_types_context, format_revenue_types_context, format_crop_varieties_context
    
    assert format_expense_types_context([]) == "No expense types available"
    assert format_revenue_types_context([]) == "No revenue types available"
    assert format_crop_varieties_context([]) == "No crop varieties available"

# ------------------------
# Additional edge case tests
# ------------------------

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_large_amount_transaction(mock_create):
    """Test handling of large monetary amounts"""
    user_input = "Vendí mi cosecha de maíz por 15000 dólares"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Excelente! He registrado una gran venta de maíz por $15000.00 💰🌽. ¡Felicidades por esa gran cosecha!",
        "respuesta_api": {
            "note": "Venta de cosecha de maíz",
            "value": "15000.00",
            "type": "101",
            "date": "",
            "crop_variety": "203",  # Maíz
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["value"] == "15000.00"
    assert parsed["respuesta_api"]["crop_variety"] == "203"

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_decimal_amounts(mock_create):
    """Test handling of decimal monetary amounts"""
    user_input = "Gasté 45.50 en herramientas"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "¡Perfecto! He registrado un gasto en herramientas por $45.50 🔧💰.",
        "respuesta_api": {
            "note": "Gasto en herramientas",
            "value": "45.50",
            "type": "5",  # Herramientas
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["value"] == "45.50"
    assert parsed["respuesta_api"]["type"] == "5"

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_profanity_classification(mock_create):
    """Test that profanity is classified as no_relacionado"""
    user_input = "Esto es una mierda"
    json_text = json.dumps({
        "clasificacion": "no_relacionado",
        "respuesta": "Lo siento, no puedo ayudarte con eso. Mi función es asistir con el registro de gastos e ingresos agrícolas. ¿Hay alguna transacción financiera que quieras registrar? 🤖",
        "respuesta_api": {
            "note": "",
            "value": "",
            "type": "",
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "no_relacionado"
    assert "gastos e ingresos agrícolas" in parsed["respuesta"]

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_specific_date_formats(mock_create):
    """Test different date format extractions"""
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    test_cases = [
        ("Compré fertilizante el 15/12/2024 por 200 pesos", "2024-12-15"),
        ("Ayer compré semillas por 100 pesos", yesterday),  # Dynamic yesterday
        ("Hoy gasté 50 en combustible", today),  # Dynamic today
    ]
    
    for user_input, expected_date in test_cases:
        json_text = json.dumps({
            "clasificacion": "gasto",
            "respuesta": "¡Perfecto! He registrado el gasto 💰.",
            "respuesta_api": {
                "note": "Gasto registrado",
                "value": "100.00",
                "type": "2",
                "date": expected_date,
                "crop_variety": "",
                "customer": ""
            }
        })
        mock_create.return_value = make_fake_response(json_text)
        
        result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
        parsed = json.loads(result)
        
        assert parsed["clasificacion"] == "gasto"
        assert parsed["respuesta_api"]["date"] == expected_date

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_quantity_and_units_extraction(mock_create):
    """Test extraction of quantity and units for crop sales"""
    user_input = "Vendí 25 kilogramos de lechuga por 300 pesos"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta de 25 kg de lechuga por $300.00 💰🥬.",
        "respuesta_api": {
            "note": "Venta de lechuga",
            "value": "300.00",
            "type": "101",
            "date": "",
            "crop_variety": "202",  # Lechuga
            "customer": "",
            "quantity": "25",
            "quantity_unit": "kg"
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["quantity"] == "25"
    assert parsed["respuesta_api"]["quantity_unit"] == "kg"
    assert parsed["respuesta_api"]["crop_variety"] == "202"

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_mixed_language_input(mock_create):
    """Test handling of mixed Spanish/English input"""
    user_input = "Compré seeds por 80 pesos"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "¡Perfecto! He registrado una compra de semillas por $80.00 💰.",
        "respuesta_api": {
            "note": "Compra de semillas",
            "value": "80.00",
            "type": "1",  # Semillas
            "date": "",
            "crop_variety": "",
            "customer": ""
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["type"] == "1"

def test_malformed_context_data():
    """Test handling of malformed context data"""
    from services.ai_service import format_expense_types_context, format_revenue_types_context, format_crop_varieties_context
    
    # Test with malformed data
    malformed_expenses = [
        {"wrong_key": "value"},
        {"expense_type_id": "1"},  # Missing name
        {"expense_name": "Test"},  # Missing ID
        None,
        "not_a_dict"
    ]
    
    result = format_expense_types_context(malformed_expenses)
    assert "No expense types available" in result

    # Test with mixed valid/invalid data
    mixed_data = [
        {"expense_type_id": "1", "expense_name": "Valid"},
        {"wrong_key": "invalid"},
        {"expense_type_id": "2", "expense_name": "Also Valid"}
    ]
    
    result = format_expense_types_context(mixed_data)
    assert "ID: 1 - Valid" in result
    assert "ID: 2 - Also Valid" in result

@pytest.mark.asyncio
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)  
async def test_ambiguous_customer_extraction(mock_create):
    """Test extraction of customer names from ambiguous sentences"""
    user_input = "María me dijo que Juan compró mis tomates por 150 pesos"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta de tomates por $150.00 a Juan 💰🍅.",
        "respuesta_api": {
            "note": "Venta de tomates",
            "value": "150.00",
            "type": "101",
            "date": "",
            "crop_variety": "201",  # Tomate
            "customer": "Juan"  # Juan is the actual buyer, not María
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["customer"] == "Juan"

@pytest.mark.asyncio  
@patch("services.ai_service.client.chat.completions.create", new_callable=AsyncMock)
async def test_no_customer_general_default(mock_create):
    """Test that sales without specified customer use default 'Cliente General'"""
    user_input = "Vendí tomates por 200 pesos en el mercado"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta": "¡Perfecto! He registrado una venta de tomates por $200.00 💰🍅.",
        "respuesta_api": {
            "note": "Venta de tomates",
            "value": "200.00",
            "type": "101",
            "date": "",
            "crop_variety": "201",
            "customer": ""  # Empty - will use "Cliente General" as default
        }
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES, DUMMY_REVENUE_TYPES, DUMMY_CROP_VARIETIES)
    parsed = json.loads(result)
    
    assert parsed["clasificacion"] == "ingreso"
    assert parsed["respuesta_api"]["customer"] == ""  # Will default to "Cliente General"
