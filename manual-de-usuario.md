# Manual de Usuario – FarmBot (LiteFarmBot)

## Índice

1. Introducción
2. Primeros pasos
3. Comandos disponibles
4. Flujo de trabajo recomendado
5. Ejemplos de registro de transacciones
6. Gestión de la validación de transacciones
7. Gestión de granjas
8. Solución de problemas

---

## 1. Introducción

**FarmBot** es un asistente financiero agrícola integrado con [LiteFarm](https://litefarm.org).  
Permite registrar gastos e ingresos en lenguaje natural, asociarlos a la granja correcta y mantener un historial claro de tus transacciones.

> Todo se realiza a través de un chat de **Telegram**; los comandos que encontrarás a continuación facilitan la interacción.

---

## 2. Primeros pasos

1. **Inicia una conversación** con el bot en Telegram.
2. Escribe `/start` para recibir la bienvenida.
3. Ejecuta `/login` y abre el enlace que aparece para autorizar tu cuenta de LiteFarm. 
```
3.1 Debes dar click al link, o copiarlo y pegarlo en tu navegador web.
3.2 La página web es en donde deberás de iniciar sesión ya sea con tu usuario y contraseña o con google. Debes de tener ya una cuenta de LiteFarm preexistente para poder iniciar sesión.
```
4. Usa `/selectfarm` para elegir la granja sobre la que vas a trabajar.

¡Listo! Ahora puedes empezar a registrar transacciones escribiendo mensajes como:

```
Gasté 50 dólares en fertilizante para tomates
Vendí tomates por 100 dólares a Juan Pérez
```

---

## 3. Comandos disponibles

| Comando | Alias / Argumentos | Descripción |
|---------|-------------------|-------------|
| `/start` | — | Inicia el bot y muestra un mensaje de bienvenida. |
| `/help` | — | Muestra este manual rápido de ayuda dentro del chat. |
| `/login` | — | Abre un enlace para iniciar sesión en LiteFarm y vincular tu cuenta. |
| `/selectfarm` | — | Muestra el listado de granjas disponibles y permite seleccionar una. Si solo tienes una se selecciona automáticamente. |
| `/currentfarm` | — | Indica la granja actualmente seleccionada. |
| `/clearfarm` | — | Quita la selección de granja (deberás elegir otra antes de registrar transacciones). |
| `/skip` | — | Omite el campo *cliente* cuando el bot solicite datos adicionales. Solo salta el campo `customer`. |
| `/cancel` | — | Cancela la transacción en curso y limpia cualquier estado pendiente. |
| `/deshabilitar_validacion` | — | Desactiva la confirmación previa al registro de transacciones. |
| `/habilitar_validacion` | — | Activa la confirmación previa al registro de transacciones (opción por defecto). |

---

## 4. Flujo de trabajo recomendado

1. **Iniciar sesión** (`/login`) → autorización en LiteFarm.  
2. **Seleccionar granja** (`/selectfarm`).  
3. **Registrar transacción**: escribe el gasto/ingreso en lenguaje natural.  
4. **Confirmar** – si la validación está habilitada, pulsa ✅ para registrar o ❌ para cancelar.  
5. **Repetir** según sea necesario.

Puedes cambiar la granja en cualquier momento con `/selectfarm` o verificarla con `/currentfarm`.

---

## 5. Ejemplos de registro de transacciones

_Escribe un mensaje tal cual lo harías en una conversación normal:_

* "Gasté **50 USD** en **fertilizante**"
* "Vendí **tomates** por **100 USD** a **Juan Pérez**"
* "Compré **semillas** por **25 USD**"
* "Hoy gasté **50 USD** en **20 bolsas de fertilizante**"
* "Hoy vendí **manzanas** por **30 USD** (120 unidades)"

El bot interpretará la cantidad, categoría y tipo de transacción.

---

## 6. Gestión de la validación de transacciones

De forma predeterminada FarmBot solicita confirmación antes de registrar cualquier gasto/ingreso.

* Usa `/deshabilitar_validacion` si confías en la clasificación automática y prefieres registrar al instante.
* Usa `/habilitar_validacion` para volver a exigir confirmación.

> El estado actual se muestra en `/help`.

---

## 7. Gestión de granjas

| Acción | Comando | Resultado |
|--------|---------|-----------|
| Seleccionar granja | `/selectfarm` | Muestra las granjas y permite elegir una. |
| Ver granja actual | `/currentfarm` | Indica la granja sobre la que se registrarán las transacciones. |
| Quitar selección | `/clearfarm` | Borra la selección; necesitarás elegir una de nuevo. |

Si solo tienes una granja, el bot la seleccionará automáticamente.

---

## 8. Solución de problemas

| Problema | Solución recomendada |
|----------|----------------------|
| **"❌ No tienes granjas disponibles"** | Crea una granja en LiteFarm y luego usa `/selectfarm`. |
| **"❌ No hay campos pendientes para completar"** después de `/skip` | No hay datos opcionales que omitir; continúa con el flujo normal. |
| Error de token o sesión | Ejecuta `/login` nuevamente para renovar la autorización. |
| El bot no responde | Comprueba tu conexión y vuelve a enviar el comando. |

---

¡Disfruta de tu gestión financiera agrícola con **FarmBot**! 🚜 