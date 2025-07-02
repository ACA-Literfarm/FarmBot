# FarmBot - Documentación de Arquitectura

## Resumen General

FarmBot es un chatbot de Telegram desarrollado en Python que integra inteligencia artificial con la API de LiteFarm para gestionar transacciones financieras agrícolas. El bot permite a los usuarios registrar gastos e ingresos de manera conversacional y los procesa automáticamente a través de la API de LiteFarm.

## Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   FarmBot Core  │    │   LiteFarm API  │
│                 │◄──►│                 │◄──►│                 │
│  - Interfaz     │    │  - Procesamiento│    │  - Base de      │
│  - Comandos     │    │  - IA           │    │    Datos        │
│  - Mensajes     │    │  - Validación   │    │  - Endpoints    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │                 │
                       │  - Procesamiento│
                       │    de Lenguaje  │
                       │  - Clasificación│
                       └─────────────────┘
```

### Flujo de Datos

1. **Usuario** envía mensaje → **Telegram Bot**
2. **Telegram Bot** → **FarmBot Core** (procesamiento)
3. **FarmBot Core** → **OpenAI API** (análisis de IA)
4. **FarmBot Core** → **LiteFarm API** (validación y registro)
5. **FarmBot Core** → **Telegram Bot** → **Usuario** (respuesta)

## Estructura del Proyecto

### Módulos Principales

```
src/
├── main.py                    # Punto de entrada principal
├── config.py                  # Configuración centralizada
├── prompts.py                 # Prompts para IA
├── commands/                  # Comandos del bot
│   ├── command_controller.py  # Controlador de comandos
│   ├── start.py              # Comando /start
│   ├── help.py               # Comando /help
│   └── skip.py               # Comando /skip
├── handlers/                  # Manejadores de mensajes
│   └── regular_message.py    # Procesamiento de mensajes
├── services/                  # Servicios principales
│   ├── ai_service.py         # Integración con OpenAI
│   ├── api_service.py        # Integración con LiteFarm
│   └── typing_context.py     # Indicador de escritura
└── tests/                     # Pruebas unitarias
    └── test_sample.py
```

## Componentes Detallados

### 1. Main Application (`main.py`)

**Responsabilidades:**

- Inicialización del bot de Telegram
- Configuración del dispatcher de aiogram
- Registro de handlers y comandos
- Gestión del ciclo de vida de la aplicación

**Tecnologías:**

- `aiogram`: Framework asíncrono para bots de Telegram
- `asyncio`: Programación asíncrona

### 2. Configuration (`config.py`)

**Responsabilidades:**

- Carga de variables de entorno
- Validación de configuración requerida
- Centralización de configuraciones

**Variables Principales:**

- `TELEGRAM_API_KEY`: Token del bot de Telegram
- `AI_API_KEY`: Clave de API de OpenAI
- `MODEL_NAME`: Modelo de IA a utilizar
- `URL_LITEFARM`: URL de la API de LiteFarm

### 3. Commands Module (`commands/`)

#### Command Controller (`command_controller.py`)

- Registra todos los manejadores de comandos
- Configura el routing de comandos del bot

#### Comandos Disponibles:

- **`/start`**: Mensaje de bienvenida
- **`/help`**: Ayuda y ejemplos de uso
- **`/skip`**: Omitir campos opcionales en transacciones

### 4. Message Handlers (`handlers/`)

#### Regular Message Handler (`regular_message.py`)

**Responsabilidades:**

- Procesamiento de mensajes de texto libre
- Gestión de estados de conversación
- Validación de datos de transacciones
- Coordinación entre servicios

**Flujo de Procesamiento:**

1. Recibe mensaje del usuario
2. Verifica estado de conversación existente
3. Solicita datos a APIs externas (tipos de gastos, ingresos, variedades)
4. Envía mensaje a servicio de IA para análisis
5. Valida respuesta de IA
6. Procesa transacción si está completa
7. Solicita datos faltantes si es necesario

### 5. Services Module (`services/`)

#### AI Service (`ai_service.py`)

**Responsabilidades:**

- Integración con OpenAI API
- Clasificación de mensajes de usuario
- Extracción de datos de transacciones
- Generación de respuestas contextuales

**Funciones Principales:**

- `query_ai_model()`: Consulta al modelo de IA
- `format_expense_types_context()`: Formatea contexto de gastos
- `format_revenue_types_context()`: Formatea contexto de ingresos
- `format_crop_varieties_context()`: Formatea contexto de variedades

#### API Service (`api_service.py`)

**Responsabilidades:**

- Comunicación con LiteFarm API
- Gestión de tipos de transacciones
- Envío de datos de transacciones
- Manejo de errores de API

**Endpoints Utilizados:**

- `/expense_type/all`: Obtiene tipos de gastos
- `/revenue_type/all`: Obtiene tipos de ingresos
- `/crop_variety/all`: Obtiene variedades de cultivos

#### Typing Context (`typing_context.py`)

**Responsabilidades:**

- Mostrar indicador de "escribiendo..." en Telegram
- Mejorar experiencia de usuario durante procesamiento
- Gestión asíncrona de indicadores visuales

## Inteligencia Artificial

### Procesamiento de Lenguaje Natural

El bot utiliza **OpenAI GPT** para:

1. **Clasificación de Mensajes:**

   - Determinar si es gasto o ingreso
   - Identificar tipo de transacción
   - Extraer detalles específicos

2. **Extracción de Datos:**

   - Monto de la transacción
   - Fecha (si se especifica)
   - Descripción/nota
   - Cliente (para ingresos)
   - Variedad de cultivo

3. **Validación Contextual:**
   - Verificar coherencia de datos
   - Sugerir correcciones
   - Manejar ambigüedades

### Prompts del Sistema

Los prompts están diseñados para:

- Clasificar transacciones financieras agrícolas
- Extraer información estructurada de texto libre
- Mantener coherencia en las respuestas
- Manejar múltiples idiomas (español principalmente)

## Gestión de Estados

### User States

El bot mantiene estados de conversación para:

- **Transacciones Incompletas**: Cuando faltan datos requeridos
- **Validación de Campos**: Verificación de tipos y variedades
- **Flujo de Conversación**: Continuidad en múltiples mensajes

### Estado de Transacción

```python
{
    "api_response": {
        "note": "Descripción",
        "value": "Monto",
        "type": "ID del tipo",
        "date": "YYYY-MM-DD",
        "crop_variety": "ID variedad",
        "customer": "Nombre cliente"
    },
    "respuesta": "Mensaje para usuario",
    "missing_fields": ["campo1", "campo2"]
}
```

## Integración con LiteFarm

### API Endpoints Utilizados

1. **Tipos de Gastos**: `/expense_type/all`
2. **Tipos de Ingresos**: `/revenue_type/all`
3. **Variedades de Cultivos**: `/crop_variety/all`

### Flujo de Validación

1. Obtener tipos disponibles desde LiteFarm
2. Validar que el tipo extraído por IA existe
3. Verificar campos requeridos según tipo
4. Enviar transacción a LiteFarm
5. Confirmar registro exitoso

## Manejo de Errores

### Tipos de Errores Manejados

1. **Errores de API:**

   - Timeout de conexión
   - Respuestas inválidas
   - Servicios no disponibles

2. **Errores de IA:**

   - Respuestas malformadas
   - Clasificaciones incorrectas
   - Límites de tokens

3. **Errores de Usuario:**
   - Datos faltantes
   - Formatos incorrectos
   - Valores inválidos

### Estrategias de Recuperación

- **Reintentos automáticos** para errores de red
- **Valores por defecto** para campos opcionales
- **Solicitud de clarificación** para datos ambiguos
- **Mensajes de error descriptivos** para el usuario

## Seguridad

### Gestión de Credenciales

- Variables de entorno para APIs sensibles
- Validación de configuración al inicio
- No exposición de tokens en logs

### Validación de Datos

- Sanitización de entrada de usuario
- Validación de tipos de datos
- Límites en longitud de mensajes

## Escalabilidad

### Diseño Asíncrono

- Uso de `asyncio` para operaciones concurrentes
- Handlers no bloqueantes
- Gestión eficiente de múltiples usuarios

### Modularidad

- Separación clara de responsabilidades
- Servicios intercambiables
- Fácil extensión de funcionalidades

## Tecnologías Utilizadas

### Core

- **Python 3.8+**: Lenguaje principal
- **aiogram**: Framework para bots de Telegram
- **asyncio**: Programación asíncrona

### APIs

- **OpenAI API**: Procesamiento de lenguaje natural
- **Telegram Bot API**: Interfaz de usuario
- **LiteFarm API**: Gestión de datos agrícolas

### Utilities

- **requests**: Cliente HTTP
- **logging**: Sistema de logs
- **json**: Manejo de datos estructurados

## Deployment

### Requisitos del Sistema

- Python 3.8 o superior
- Acceso a internet para APIs
- LiteFarm API ejecutándose en rama `develop`

### Variables de Entorno Requeridas

```bash
TELEGRAM_API_KEY=token_del_bot
AI_API_KEY=clave_openai
MODEL_NAME=gpt-4o
URL_LITEFARM=http://localhost:5001
```

### Ejecución

```bash
# Activar entorno virtual
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar bot
python3 src/main.py
```

## Desarrollo y Testing

### Estructura de Tests

- Tests unitarios en `src/tests/`
- Configuración con `pytest`
- Cobertura de servicios principales

### Desarrollo Local

1. Configurar entorno virtual
2. Instalar dependencias de desarrollo
3. Configurar variables de entorno
4. Ejecutar LiteFarm API localmente
5. Iniciar bot en modo desarrollo