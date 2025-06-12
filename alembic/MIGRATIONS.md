# 🛠️ Guía para Ejecutar Migraciones de Base de Datos

Este proyecto utiliza **Alembic** para gestionar las migraciones de la base de datos PostgreSQL a partir de los modelos definidos con SQLAlchemy.

## 📦 Requisitos Previos

- Tener activado el entorno virtual (`fbenv`)
- Base de datos en funcionamiento (local o en Docker)
- Archivo `.env` configurado con las credenciales correctas
- Alembic correctamente instalado (Ejecute las dependencias del proyecto: `pip install -r requirements.txt`)

## 🚀 Comandos Comunes

### 1. Aplicar las migraciones existentes
Si le hiciste algún cambio a los modelos de la base, esto actualiza tu base de datos al estado más reciente definido por los archivos de migración:

```bash
alembic upgrade head -x async=true
````

### 2. Crear una nueva migración (por ejemplo, luego de modificar o agregar un modelo)

```bash
alembic revision --autogenerate -m "Descripción del cambio"
```

> ⚠️ Asegúrate de que tu base de datos esté actualizada (`upgrade head`) antes de generar nuevas migraciones.

Luego aplica el cambio:

```bash
alembic upgrade head -x async=true
```

### 3. Ver el estado actual de la base de datos

```bash
alembic current
```

### 4. Marcar la base de datos como sincronizada (⚠️ Solo si estás seguro)

```bash
alembic stamp head
```

## 🧠 Notas Importantes

* Todos los modelos deben estar definidos dentro de `shared/db/models/`.
* **No es necesario importarlos manualmente** en `env.py`, ya que se cargan dinámicamente.
* Si Alembic no detecta tu nuevo modelo, asegúrate de que el archivo `.py` esté en el directorio `models/` y que el archivo `__init__.py` exista.

## 📁 Estructura recomendada

```
shared/
  db/
    base.py          # DeclarativeBase
    models/
      __init__.py    # Debe existir
      user.py
      token.py
      ...
alembic/
  versions/          # Archivos de migración generados
  env.py             # Configuración de Alembic
```