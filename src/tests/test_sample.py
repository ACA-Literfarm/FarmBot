import pytest
import json
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Asegurar que src/ esté en PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.services.ai_service import query_ai_model
from src.services.api_service import handle_api_transaction
from src.prompts import FINANCIAL_CLASSIFIER_PROMPT

# Dummy expense types para pasar a query_ai_model
DUMMY_EXPENSE_TYPES = [{"expense_type_id": "1", "expense_name": "dummy"}]

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
# Casos básicos existentes
# ------------------------

@pytest.mark.asyncio
async def test_handle_api_transaction_logs(caplog):
    api_response = {"note": "Compra de fertilizante", "value": "500", "type": "plantas"}
    with caplog.at_level("INFO"):
        await handle_api_transaction(api_response)
        assert "Compra de fertilizante" in caplog.text
        assert "500" in caplog.text
        assert "plantas" in caplog.text

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model(mock_create):
    user_input = "Gasté 300 en semillas"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "He registrado un gasto 💰",
        "respuesta_api": {"note": "Compra de semillas", "value": "300", "type": "plantas"}
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    parsed = json.loads(result)
    assert parsed["clasificacion"] == "gasto"
    assert "💰" in parsed["respuesta"]
    assert parsed["respuesta_api"]["type"] == "plantas"

def test_prompt_exists():
    assert isinstance(FINANCIAL_CLASSIFIER_PROMPT, str)
    assert "clasificacion" in FINANCIAL_CLASSIFIER_PROMPT

# ------------------------
# Casos adicionales
# ------------------------

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_gasto_fertilizando(mock_create):
    user_input = "Gasto 10 en fertilizante"
    json_text = json.dumps({
        "clasificacion": "gasto",
        "respuesta": "He registrado el gasto",
        "respuesta_api": {"note": "gasto en fertilizante", "value": "10.0", "type": "Control de plagas"}
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    parsed = json.loads(result)
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["value"] == "10.0"

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_gasto_incompleto(mock_create):
    user_input = "Consumi gasolina"
    # respuesta directa del modelo sin JSON
    content = "Por favor indica el monto del gasto."
    mock_create.return_value = make_fake_response(content)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    assert content in result

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_ingreso_valido(mock_create):
    user_input = "Ayer vendí 1 kilo de tomates por 15 a David"
    json_text = json.dumps({
        "clasificacion": "ingreso",
        "respuesta_api": {"nombre_cliente": "David", "fecha": "ayer", "cultivo": "tomate", "cantidad": "1", "unidad_medida": "kg", "monto": "15"}
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    parsed = json.loads(result)
    assert parsed["clasificacion"] == "ingreso"

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_ingreso_incompleto(mock_create):
    user_input = "Ayer vendí tomates por 15 a David"
    content = "Por favor indica la cantidad del cultivo vendido."
    mock_create.return_value = make_fake_response(content)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    assert content in result

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_irrelevante(mock_create):
    user_input = "Hola, ¿cómo estás?"
    json_text = json.dumps({
        "clasificacion": "no_relacionado",
        "respuesta": "Estoy aquí para ayudarte a registrar transacciones.",
        "respuesta_api": {}
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    parsed = json.loads(result)
    assert "transacciones" in parsed["respuesta"]

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", side_effect=Exception("API caída"))
async def test_query_ai_model_logs_error(mock_create, caplog):
    user_input = "Vender manzanas"
    with caplog.at_level("ERROR"):
        result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
        assert result.startswith("⚠️")
        assert "API caída" in caplog.text

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_transaccion_guiada(mock_create):
    user_input = "Hice un gasto"
    json_text = json.dumps({
        "clasificacion": "pendiente",
        "respuesta": "¿Cuál fue el monto del gasto?",
        "respuesta_api": {}
    })
    mock_create.return_value = make_fake_response(json_text)

    result = await query_ai_model(user_input, DUMMY_EXPENSE_TYPES)
    parsed = json.loads(result)
    assert "monto" in parsed["respuesta"]

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_multiple_transacciones(mock_create):
    # Primer llamada
    json1 = json.dumps({"clasificacion": "gasto", "respuesta_api": {"note": "abono", "value": "100", "type": "suelo"}})
    # Segunda llamada
    json2 = json.dumps({"clasificacion": "ingreso", "respuesta_api": {"nombre_cliente": "Luis", "fecha": "hoy", "cultivo": "lechuga", "cantidad": "3", "unidad_medida": "kg", "monto": "90"}})
    mock_create.side_effect = [make_fake_response(json1), make_fake_response(json2)]

    r1 = await query_ai_model("Gasté 100 en abono", DUMMY_EXPENSE_TYPES)
    r2 = await query_ai_model("Hoy vendí lechuga", DUMMY_EXPENSE_TYPES)
    p1, p2 = json.loads(r1), json.loads(r2)
    assert p1["clasificacion"] == "gasto"
    assert p2["clasificacion"] == "ingreso"
