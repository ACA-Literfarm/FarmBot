import pytest
import json
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.main import handle_api_transaction, query_ai_model
from src.prompts import FINANCIAL_CLASSIFIER_PROMPT

# ------------------------
# Casos básicos ya existentes
# ------------------------

@pytest.mark.asyncio
async def test_handle_api_transaction_logs(caplog):
    api_response = {
        "note": "Compra de fertilizante",
        "value": "500",
        "type": "plantas"
    }
    print(f"🔧 Enviando a handle_api_transaction: {api_response}")
    with caplog.at_level("INFO"):
        await handle_api_transaction(api_response)
        assert "Compra de fertilizante" in caplog.text
        assert "500" in caplog.text
        assert "plantas" in caplog.text
    print("✅ test_handle_api_transaction_logs pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model(mock_create):
    user_input = "Gasté 300 en semillas"
    fake_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "gasto",
                    "respuesta": "He registrado un gasto 💰",
                    "respuesta_api": {
                        "note": "Compra de semillas",
                        "value": "300",
                        "type": "plantas"
                    }
                })
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    parsed = json.loads(result)
    assert parsed["clasificacion"] == "gasto"
    assert "💰" in parsed["respuesta"]
    assert parsed["respuesta_api"]["type"] == "plantas"
    print("✅ test_query_ai_model pasó correctamente.\n")

def test_prompt_exists():
    print("🔍 Verificando prompt base...")
    assert isinstance(FINANCIAL_CLASSIFIER_PROMPT, str)
    assert "clasificacion" in FINANCIAL_CLASSIFIER_PROMPT
    print("✅ test_prompt_exists pasó correctamente.\n")

# ------------------------
# Casos adicionales con impresión de entradas/salidas
# ------------------------

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_gasto_fertilizando(mock_create):
    user_input = "Gasto 10 en fertilizante"
    fake_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "gasto",
                    "respuesta": "He registrado el gasto",
                    "respuesta_api": {
                        "note": "gasto en fertilizante",
                        "value": "10.0",
                        "type": "Control de plagas"
                    }
                })
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    parsed = json.loads(result)
    assert parsed["clasificacion"] == "gasto"
    assert parsed["respuesta_api"]["value"] == "10.0"
    print("✅ test_query_ai_model_gasto_fertilizando pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_gasto_incompleto(mock_create):
    user_input = "Consumi gasolina"
    fake_response = {
        "choices": [{
            "message": {
                "content": "Por favor indica el monto del gasto."
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    assert "Por favor" in result or "monto" in result
    print("✅ test_query_ai_model_gasto_incompleto pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_ingreso_valido(mock_create):
    user_input = "Ayer vendí 1 kilo de tomates por 15 a David"
    fake_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "ingreso",
                    "respuesta_api": {
                        "nombre_cliente": "David",
                        "fecha": "ayer",
                        "cultivo": "tomate",
                        "cantidad": "1",
                        "unidad_medida": "kg",
                        "monto": "15"
                    }
                })
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    parsed = json.loads(result)
    assert parsed["clasificacion"] == "ingreso"
    print("✅ test_query_ai_model_ingreso_valido pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_ingreso_incompleto(mock_create):
    user_input = "Ayer vendí tomates por 15 a David"
    fake_response = {
        "choices": [{
            "message": {
                "content": "Por favor indica la cantidad del cultivo vendido."
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    assert "cantidad" in result
    print("✅ test_query_ai_model_ingreso_incompleto pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_irrelevante(mock_create):
    user_input = "Hola, ¿cómo estás?"
    fake_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "no_relacionado",
                    "respuesta": "Estoy aquí para ayudarte a registrar transacciones.",
                    "respuesta_api": {}
                })
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    parsed = json.loads(result)
    assert "transacciones" in parsed["respuesta"]
    print("✅ test_query_ai_model_irrelevante pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", side_effect=Exception("API caída"))
async def test_query_ai_model_logs_error(mock_create, caplog):
    user_input = "Vender manzanas"
    with caplog.at_level("ERROR"):
        result = await query_ai_model(user_input)
        # Confirmamos que retorna el mensaje de error
        assert result == "⚠️ There was an error processing your message. Try again later."
        # Confirmamos que loguea el error original
        assert "API caída" in caplog.text

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_transaccion_guiada(mock_create):
    user_input = "Hice un gasto"
    fake_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "pendiente",
                    "respuesta": "¿Cuál fue el monto del gasto?",
                    "respuesta_api": {}
                })
            }
        }]
    }
    mock_create.return_value = fake_response
    print(f"🔧 Enviando a query_ai_model: {user_input}")
    result = await query_ai_model(user_input)
    print(f"📥 Respuesta: {result}")
    parsed = json.loads(result)
    assert "monto" in parsed["respuesta"]
    print("✅ test_query_ai_model_transaccion_guiada pasó correctamente.\n")

@pytest.mark.asyncio
@patch("src.main.client.chat.completions.create", new_callable=AsyncMock)
async def test_query_ai_model_multiple_transacciones(mock_create):
    input_1 = "Gasté 100 en abono"
    input_2 = "Hoy vendí 3 kilos de lechuga a Luis por 90"

    fake_response_1 = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "gasto",
                    "respuesta_api": {
                        "note": "abono",
                        "value": "100",
                        "type": "suelo"
                    }
                })
            }
        }]
    }
    fake_response_2 = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "clasificacion": "ingreso",
                    "respuesta_api": {
                        "nombre_cliente": "Luis",
                        "fecha": "hoy",
                        "cultivo": "lechuga",
                        "cantidad": "3",
                        "unidad_medida": "kg",
                        "monto": "90"
                    }
                })
            }
        }]
    }

    mock_create.side_effect = [fake_response_1, fake_response_2]

    print(f"🔧 Enviando a query_ai_model: {input_1}")
    result_1 = await query_ai_model(input_1)
    print(f"📥 Respuesta 1: {result_1}")

    print(f"🔧 Enviando a query_ai_model: {input_2}")
    result_2 = await query_ai_model(input_2)
    print(f"📥 Respuesta 2: {result_2}")

    parsed_1 = json.loads(result_1)
    parsed_2 = json.loads(result_2)

    assert parsed_1["clasificacion"] == "gasto"
    assert parsed_2["clasificacion"] == "ingreso"
    print("✅ test_query_ai_model_multiple_transacciones pasó correctamente.\n")
