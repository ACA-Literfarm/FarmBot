# 🤖 FarmBot - Manual Técnico

**Microservicio de Chatbot con IA para LiteFarm**

Un chatbot inteligente desarrollado en Python que se integra con LiteFarm a través de Telegram, utilizando inteligencia artificial para gestionar granjas y automatizar procesos agrícolas.

---

## 📋 Índice

1. [Descripción del Proyecto](#-descripción-del-proyecto)
2. [Arquitectura del Sistema](#️-arquitectura-del-sistema)
3. [Componentes Principales](#-componentes-principales)
4. [Tecnologías Utilizadas](#-tecnologías-utilizadas)
5. [Estructura del Proyecto](#-estructura-del-proyecto)
6. [Base de Datos](#️-base-de-datos)
7. [Configuración del Entorno](#️-configuración-del-entorno)
8. [Instalación y Despliegue](#-instalación-y-despliegue)
9. [API y Endpoints](#-api-y-endpoints)
10. [Comandos del Bot](#-comandos-del-bot)
11. [Servicios de IA](#-servicios-de-ia)
12. [Autenticación y Seguridad](#-autenticación-y-seguridad)
13. [Testing](#-testing)
14. [Migración de Base de Datos](#-migración-de-base-de-datos)
15. [Contribución](#-contribución)
16. [Soporte y Contacto](#-soporte-y-contacto)
17. [Licencia](#-licencia)
18. [Referencias y Links Útiles](#-referencias-y-links-útiles)

---

## 🎯 Descripción del Proyecto

FarmBot es un microservicio que forma parte del ecosistema LiteFarm, diseñado para proporcionar una interfaz conversacional inteligente a través de Telegram. El sistema permite a los usuarios gestionar sus granjas, registrar gastos, obtener información agrícola y realizar consultas mediante procesamiento de lenguaje natural.

### Características Principales

- **Chatbot de Telegram**: Interfaz conversacional accesible desde cualquier dispositivo
- **Integración con IA**: Utiliza modelos de OpenAI/DeepSeek para procesamiento de lenguaje natural
- **Autenticación OAuth2**: Sistema de login seguro con Google
- **Base de Datos PostgreSQL**: Persistencia de datos de usuarios y sesiones
- **Servidor Web Flask**: Panel de administración y autenticación web
- **Integración LiteFarm**: Conexión directa con la API de LiteFarm
- **Arquitectura Asíncrona**: Manejo eficiente de múltiples conversaciones simultáneas

---

## 🏗️ Arquitectura del Sistema

![Arquitectura del Sistema](documentation_resources/FarmBot-Arquitecture.jpeg)

### Flujo Principal

1. **Usuario → Telegram Bot**: El usuario interactúa con el bot a través de Telegram
2. **Bot → AI Service**: Las consultas se procesan con IA para entender la intención
3. **Bot → LiteFarm API**: Se realizan operaciones en la plataforma LiteFarm
4. **Web Server**: Maneja la autenticación OAuth2 y panel de administración
5. **Database**: Persiste información de usuarios, sesiones y tokens

---

## 🔧 Componentes Principales

### 1. **Telegram Bot (Core)**
- **Framework**: aiogram 3.x
- **Funcionalidad**: Manejo de comandos, conversaciones y estados
- **Ubicación**: `src/main.py`, `src/commands/`, `src/handlers/`

### 2. **Servidor Web Flask**
- **Framework**: Flask 3.1.1
- **Funcionalidad**: Autenticación OAuth2, panel de administración
- **Ubicación**: `web_server/login-server.py`

### 3. **Base de Datos**
- **Motor**: PostgreSQL 15
- **ORM**: SQLAlchemy con modelos asincrónicos
- **Migraciones**: Alembic
- **Ubicación**: `shared/db/`

### 4. **Servicios de IA**
- **Proveedor**: OpenAI/DeepSeek API
- **Funcionalidad**: Procesamiento de lenguaje natural, clasificación de gastos
- **Ubicación**: `src/services/ai_service.py`

### 5. **Sistema de Autenticación**
- **OAuth2**: Google Authentication
- **JWT**: Tokens para sesiones
- **Ubicación**: `shared/services/token_service.py`, `shared/utils/jwt_utils.py`

---

## 💻 Tecnologías Utilizadas

### Backend
- **Python 3.11+**: Lenguaje principal
- **aiogram 3.x**: Framework para Telegram Bot
- **Flask 3.1.1**: Servidor web
- **SQLAlchemy**: ORM asíncrono
- **asyncpg**: Driver PostgreSQL asíncrono
- **Alembic**: Migraciones de base de datos

### Base de Datos
- **PostgreSQL 15**: Base de datos principal
- **Docker**: Contenedorización de la base de datos

### Servicios Externos
- **OpenAI/DeepSeek API**: Servicios de IA
- **Telegram Bot API**: Plataforma de mensajería
- **Google OAuth2**: Autenticación
- **LiteFarm API**: Integración con la plataforma principal

### Herramientas de Desarrollo
- **pytest**: Testing framework
- **python-dotenv**: Gestión de variables de entorno
- **PyJWT**: Manejo de tokens JWT
- **requests**: Cliente HTTP

---

## 📁 Estructura del Proyecto

```
FarmBot/
├── 📄 README.md                    # Este archivo
├── 📄 requirements.txt             # Dependencias Python
├── 📄 docker-compose.yml           # Configuración Docker
├── 📄 alembic.ini                 # Configuración Alembic
├── 📄 .env.example                # Plantilla variables entorno
├── 📄 CONFIGURATION.md            # Guía de configuración
│
├── 📁 src/                        # Código fuente principal
│   ├── 📄 main.py                 # Punto de entrada del bot
│   ├── 📄 config.py               # Configuración centralizada
│   ├── 📄 prompts.py              # Prompts para IA
│   │
│   ├── 📁 commands/               # Comandos del bot
│   │   ├── 📄 command_controller.py
│   │   ├── 📄 start.py
│   │   ├── 📄 help.py
│   │   ├── 📄 login.py
│   │   └── 📄 farm_commands.py
│   │
│   ├── 📁 handlers/               # Manejadores de mensajes
│   ├── 📁 services/               # Lógica de negocio
│   │   ├── 📄 ai_service.py
│   │   ├── 📄 api_service.py
│   │   └── 📄 farm_service.py
│   │
│   ├── 📁 middleware/             # Middlewares
│   └── 📁 models/                 # Modelos de datos
│
├── 📁 web_server/                 # Servidor web Flask
│   ├── 📄 login-server.py         # Servidor principal
│   ├── 📁 templates/              # Templates HTML
│   └── 📁 static/                 # Archivos estáticos
│
├── 📁 shared/                     # Código compartido
│   ├── 📁 db/                     # Base de datos
│   │   ├── 📄 base.py
│   │   ├── 📄 session.py
│   │   └── 📁 models/             # Modelos SQLAlchemy
│   │       ├── 📄 user.py
│   │       ├── 📄 chat_session.py
│   │       ├── 📄 token.py
│   │       └── 📄 farm.py
│   │
│   ├── 📁 services/               # Servicios compartidos
│   ├── 📁 repositories/           # Repositorios de datos
│   ├── 📁 DTO/                    # Data Transfer Objects
│   └── 📁 utils/                  # Utilidades
│
├── 📁 alembic/                    # Migraciones de BD
│   ├── 📄 env.py
│   └── 📁 versions/               # Archivos de migración
│
├── 📁 tests/                      # Tests unitarios
├── 📁 cache/                      # Cache temporal
└── 📁 initdb.d/                   # Scripts inicialización BD
```

---

## 🗄️ Base de Datos

### Esquema de Datos
#### Tabla: `users`
```sql
CREATE TABLE users (
    litefarm_user_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabla: `chat_sessions`
```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(litefarm_user_id),
    telegram_user_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabla: `tokens`
```sql
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(litefarm_user_id),
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabla: `farms`
```sql
CREATE TABLE farms (
    farm_id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(litefarm_user_id),
    farm_name VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Relaciones
- Un usuario puede tener múltiples sesiones de chat
- Un usuario puede tener múltiples tokens (refresh/access)
- Un usuario puede estar asociado a múltiples granjas
- Las sesiones de chat mantienen el estado de conversación

---

## ⚙️ Configuración del Entorno

### Variables de Entorno Requeridas

```bash
# Bot de Telegram
TELEGRAM_API_KEY=tu_token_de_bot_telegram

# Servicio de IA
AI_API_KEY=tu_api_key_de_openai_o_deepseek
MODEL_NAME=gpt-3.5-turbo

# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=farmbot_db
DB_USER=farmbot_user
DB_PASSWORD=tu_password_seguro

# LiteFarm API
URL_LITEFARM=https://api.litefarm.org

# Servidor Web
FLASK_SECRET_KEY=tu_secret_key_flask
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
LINK_SERVER=http://localhost:5000
```

### Configuración de Desarrollo

1. **Copiar variables de entorno:**
```bash
cp .env.example .env
```

2. **Editar archivo .env con valores reales**

3. **Validación automática:**
El sistema valida automáticamente las variables requeridas al inicio.

---

## 🚀 Instalación

### Instalación Local

#### 1. Prerrequisitos

**LiteFarm Sistema Principal**
- **API, Base de Datos y Cliente Web de LiteFarm**: Debes tener ejecutándose localmente la plataforma principal LiteFarm
- **Documentación de instalación**: [Ver README de LiteFarm](https://github.com/ACA-Literfarm/ACA-SSHROOTUCA-LiteFarm/blob/main/README.md)

**Entorno Local**
```bash
# Python 3.11+
python3 --version

# Docker y Docker Compose
docker --version
docker-compose --version
```

#### 2. Clonar y Configurar
```bash
git clone [repository-url]
cd FarmBot

# Crear entorno virtual
python3 -m venv env
source env/bin/activate  # Linux/macOS
# .\env\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

#### 3. Configurar Base de Datos
```bash
# Iniciar PostgreSQL con Docker
docker-compose up -d db

# Ejecutar migraciones
alembic upgrade head
```

#### 4. Configurar Variables de Entorno
```bash
cp .env.example .env
# Editar .env con valores reales (No hacer si ya lo hizo)
```

#### 5. Ejecutar Aplicación
```bash
# Servidor Web (en terminal separado)
flask --app web_server/login-server.py run

# Bot de Telegram
python3 src/main.py
```

### Despliegue con Docker

```bash
# Construcción completa
docker-compose up --build

# Solo base de datos
docker-compose up db

# Modo producción
docker-compose -f docker-compose.prod.yml up
```

### Despliegue en Producción

#### Consideraciones
- Usar variables de entorno del sistema en lugar de archivos .env
- Configurar proxy reverso (nginx)
- Habilitar HTTPS
- Configurar monitoreo y logs
- Backups automáticos de base de datos

---

## 🌐 API y Endpoints

### Servidor Web Flask

#### Endpoints de Autenticación
```
GET  /                    # Página principal
GET  /login              # Página de login
GET  /authorize/<provider> # Iniciar OAuth2
GET  /callback/<provider>  # Callback OAuth2
POST /logout             # Cerrar sesión
```

### Integración con LiteFarm API

#### Endpoints Utilizados

##### Gestión de Granjas
```
GET  /user_farm/user/{userId}     # Obtener granjas del usuario
```

##### Gestión de Gastos
```
POST /expense/farm/{farm_id}      # Registrar gastos en una granja
GET  /expense_type/all            # Obtener todos los tipos de gastos disponibles
```

##### Gestión de Ingresos/Ventas
```
POST /sale                        # Registrar ventas/ingresos
GET  /revenue_type/farm/{farm_id} # Obtener tipos de ingresos por granja
```

##### Gestión de Cultivos
```
GET  /crop_variety/farm/{farm_id} # Obtener variedades de cultivos por granja
```

#### Códigos de Respuesta
- **200 OK**: Solicitud exitosa (GET requests)
- **201 Created**: Recurso creado exitosamente (POST requests)
- **400 Bad Request**: Datos inválidos en la solicitud
- **401 Unauthorized**: Token de autenticación inválido o expirado
- **403 Forbidden**: Sin permisos para acceder al recurso
- **404 Not Found**: Recurso no encontrado
- **500 Internal Server Error**: Error del servidor

---

## 🤖 Comandos del Bot

### Comandos Básicos
- `/start` - Inicializar bot y mostrar bienvenida
- `/help` - Mostrar ayuda y comandos disponibles
- `/login` - Iniciar proceso de autenticación
- `/cancel` - Cancelar operación actual
- `/skip` - Saltar paso actual en conversación

### Comandos de Granja
- `/selectfarm` - Seleccionar granja activa
- `/currentfarm` - Información de la granja actual
- `/clearfarm` - Quitar selección de granja

### Comandos de Configuración
- `/habilitar_validacion` - Habilitar validación de transacciones
- `/deshabilitar_validacion` - Deshabilitar validación de transacciones
---

## 🤖 Servicios de IA

### Servicio Principal (ai_service.py)

#### Funcionalidades
1. **Clasificación de Gastos**: Analiza descripciones y sugiere categorías
2. **Procesamiento de Lenguaje Natural**: Interpreta comandos en lenguaje natural
3. **Validación de Datos**: Verifica coherencia de información ingresada

#### Prompts Configurados

```python
FINANCIAL_CLASSIFIER_PROMPT = """
Eres un asistente experto en agricultura que ayuda a clasificar gastos agrícolas.
Analiza la descripción del gasto y sugiere la categoría más apropiada.

Categorías disponibles:
{expense_types}

Descripción del gasto: {description}
Monto: {amount}

Responde con el ID de la categoría más apropiada.
"""
```

### Configuración de IA

#### Modelos Soportados
- **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- **DeepSeek**: deepseek-chat, deepseek-coder

#### Parámetros de Configuración
```python
{
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 150,
    "top_p": 1.0
}
```

---

## 🔐 Autenticación y Seguridad

### OAuth2 con Google

#### Flujo de Autenticación
1. Usuario hace clic en "Login con Google"
2. Redirección a Google OAuth2
3. Usuario autoriza aplicación
4. Google retorna código de autorización
5. Intercambio de código por tokens
6. Almacenamiento seguro de tokens
7. Creación de sesión de usuario

### Seguridad

#### Medidas Implementadas
- **Encriptación de tokens**: Almacenamiento seguro en BD
- **Expiración de sesiones**: Tokens con tiempo limitado
- **Validación de requests**: Verificación de origen y autenticidad
- **Rate limiting**: Prevención de spam y abuso
- **HTTPS obligatorio**: En producción

#### Variables Sensibles
```bash
# Nunca commitear estos valores
TELEGRAM_API_KEY=secret
AI_API_KEY=secret
FLASK_SECRET_KEY=secret
GOOGLE_CLIENT_SECRET=secret
DB_PASSWORD=secret
```

---

## 🧪 Testing

### Estructura de Tests

```
tests/
├── unit/                    # Tests unitarios
│   ├── test_commands.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # Tests de integración
│   ├── test_database.py
│   └── test_api.py
└── fixtures/               # Datos de prueba
    └── test_data.py
```

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/

# Tests específicos
pytest tests/unit/test_commands.py

# Con coverage
pytest --cov=src tests/

# Tests en paralelo
pytest -n auto tests/
```

### Tests de Base de Datos

```python
# Configuración de test database
@pytest.fixture
async def test_db():
    # Crear BD de prueba
    engine = create_async_engine("postgresql://test_user:test_pass@localhost/test_db")
    # ... configuración
    yield session
    # Cleanup
```

### Mocking de APIs Externas

```python
@pytest.fixture
def mock_openai():
    with patch('src.services.ai_service.client') as mock:
        mock.chat.completions.create.return_value = MockResponse()
        yield mock
```

---

## 🔄 Migración de Base de Datos

### Alembic - Gestión de Migraciones

#### Comandos Principales
```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1

# Ver historial
alembic history

# Ver migración actual
alembic current
```

#### Estructura de Migración
```python
"""Crear tabla users

Revision ID: a54c8d560ded
Revises: 
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('users',
        sa.Column('litefarm_user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('litefarm_user_id')
    )

def downgrade():
    op.drop_table('users')
```

### Buenas Prácticas para Migraciones

1. **Siempre revisar antes de aplicar**
2. **Hacer backup antes de migraciones en producción**
3. **Probar migraciones en entorno de desarrollo**
4. **Usar nombres descriptivos para migraciones**
5. **No editar migraciones ya aplicadas**

---

## 🤝 Contribución

### Guías de Desarrollo

#### Estilo de Código
- **PEP 8**: Estándar de Python
- **Type hints**: Usar anotaciones de tipos
- **Docstrings**: Documentar funciones públicas
- **Nombres descriptivos**: Variables y funciones claras

#### Proceso de Contribución

1. **Fork del repositorio**
2. **Crear rama feature**: `git checkout -b feature/nueva-funcionalidad`
3. **Desarrollar y testear**
4. **Commit con mensajes claros**
5. **Push y crear Pull Request**
6. **Code review**
7. **Merge tras aprobación**

#### Convenciones de Commit
```
tipo(alcance): descripción corta

Descripción más detallada si es necesaria

Fixes #123
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Roadmap de Desarrollo

#### Próximas Funcionalidades
- [ ] Soporte para múltiples idiomas
- [ ] Dashboard web avanzado
- [ ] Notificaciones push
- [ ] Integración con sensores IoT
- [ ] Análisis predictivo con ML

#### Mejoras Técnicas
- [ ] Implementar Redis para cache
- [ ] Añadir tests E2E
- [ ] Containerización completa

---

## 📞 Soporte

### Recursos de Ayuda
- **Documentación técnica**: Este archivo
- **Issues de GitHub**: Para reportar bugs
- **Discussions**: Para preguntas generales

---

## 📄 Licencia

Este proyecto está bajo la licencia GNU GENERAL PUBLIC LICENSE. Ver archivo `LICENSE` para más detalles.

---

## 📚 Referencias y Links Útiles

- [Documentación aiogram](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [SQLAlchemy Async Tutorial](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

*Última actualización: Diciembre 2024*
*Versión del documento: 1.0*
