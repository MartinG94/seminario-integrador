# Guía de Configuración de Correo Gmail (SMTP y Google Cloud Console OAuth 2.0)

Este documento detalla las alternativas disponibles para configurar el envío de correos electrónicos institucionales en **SGD-AVEIT** mediante casillas de Gmail / Google Workspace, explicando cuándo se requiere la consola de Google Cloud y cómo obtener cada conjunto de credenciales.

---

## 1. ¿Es necesario autorizar la aplicación en Google Cloud Console (OAuth 2.0)?

**Respuesta rápida:** Depende del método de autenticación elegido.

| Método de Conexión | ¿Requiere Google Cloud Console (OAuth Client ID / Secret)? | Complejidad | Recomendado para |
|---|:---:|:---:|---|
| **Método 1: SMTP con Contraseña de Aplicación (App Password)** | **NO** | Baja (5 min) | Desarrollo local, entornos de prueba y cuentas estándar de Gmail o Workspace que permitan contraseñas de app. |
| **Método 2: Google Cloud Console (OAuth 2.0 / Gmail API)** | **SÍ** | Media-Alta | Entornos corporativos o cuentas institucionales de Google Workspace que tengan deshabilitado el acceso básico por contraseña o exijan tokens OAuth con rotación. |

Ambos esquemas son compatibles con la arquitectura de encolado transaccional (**Transactional Outbox**) implementada en el backend.

---

## 2. Método 1: Contraseña de Aplicación (Recomendado para SMTP directo)

Google bloquea el ingreso con la contraseña habitual de la cuenta, pero permite generar una **Contraseña de Aplicación (App Password)** de 16 caracteres para servicios de backend que se conectan vía SMTP.

### Requisitos previos
- Una cuenta de Google (`@gmail.com` o cuenta institucional administrada bajo Google Workspace).
- **Verificación en 2 pasos (2FA)** activada obligatoriamente en la cuenta.

### Paso a paso
1. Inicia sesión en tu cuenta de Google y dirígete a:  
   👉 [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. En la sección **"Cómo inicias sesión en Google"**, asegúrate de que la **Verificación en 2 pasos** esté activada.
3. Ingresa directamente al apartado de contraseñas de aplicación:  
   👉 [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Escribe un nombre descriptivo en el campo correspondiente (por ejemplo: `SGD-AVEIT-Backend`) y haz clic en **Crear**.
5. Se mostrará una ventana con una contraseña de 16 letras amarillas (ejemplo: `abcd efgh ijkl mnop`).
6. Copia esta clave (sin espacios) y configúrala en tu archivo `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_correo_institucional@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=notificaciones@aveit.utn.edu.ar
```

---

## 3. Método 2: Google Cloud Console (OAuth 2.0 Client ID y Client Secret)

Si tu organización de Google Workspace tiene restringidas las contraseñas de aplicación, debes registrar una aplicación en Google Cloud Platform y autorizar los alcances de envío de Gmail.

### Paso 1: Crear o seleccionar un proyecto en Google Cloud Console
1. Ingresa a la consola de Google Cloud:  
   👉 [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. En la barra superior, haz clic en el selector de proyectos y luego en **"Proyecto Nuevo"**.
3. Asigna un nombre al proyecto (ejemplo: `SGD-AVEIT-Notificaciones`) y haz clic en **Crear**.

### Paso 2: Habilitar la API de Gmail
1. En el menú de navegación lateral (hamburguesa), ve a **APIs y servicios** > **Biblioteca**.
2. En la barra de búsqueda, escribe **Gmail API** y selecciónala.
3. Haz clic en el botón **Habilitar**.

### Paso 3: Configurar la Pantalla de Consentimiento OAuth
1. En el menú lateral, dirígete a **APIs y servicios** > **Pantalla de consentimiento de OAuth**.
2. Selecciona el **Tipo de usuario (User Type)**:
   - **Interno:** Si utilizas Google Workspace institucional de AVEIT / UTN (solo usuarios de la organización podrán enviar correos).
   - **Externo:** Si utilizas una cuenta `@gmail.com` estándar (permanecerá en modo de prueba "Testing").
3. Haz clic en **Crear**.
4. Completa la información básica de la aplicación:
   - **Nombre de la aplicación:** `SGD-AVEIT Notificaciones`
   - **Correo electrónico de asistencia:** Tu correo de administrador.
   - **Datos de contacto del desarrollador:** Tu correo electrónico.
5. En el paso **Permisos (Scopes)**, haz clic en **"Agregar o quitar permisos"**:
   - Busca y marca el scope: `https://www.googleapis.com/auth/gmail.send` (o `https://mail.google.com/` para acceso integral de correo).
   - Haz clic en **Actualizar** y luego en **Guardar y continuar**.
6. En el paso **Usuarios de prueba** (si seleccionaste tipo Externo):
   - Agrega la dirección de correo que actuará como remitente.
7. Guarda y finaliza la configuración.

### Paso 4: Crear las Credenciales OAuth 2.0 (Client ID y Client Secret)
1. En el menú lateral, ve a **APIs y servicios** > **Credenciales**.
2. Haz clic en **+ Crear credenciales** en la parte superior y selecciona **ID de cliente de OAuth**.
3. En **Tipo de aplicación**, selecciona:
   - **Aplicación web** (o **App de escritorio** si autorizas mediante script CLI local).
4. Asigna un nombre descriptivo: `SGD-AVEIT Backend Mailer`.
5. En la sección **URIs de redireccionamiento autorizados**, añade:
   - `https://developers.google.com/oauthplayground` (recomendado para generar el Refresh Token inicial de forma visual).
   - `http://localhost:8000/api/v1/auth/google/callback/` (para retornos locales si aplica).
6. Haz clic en **Crear**.
7. Aparecerá un cuadro de diálogo con tus claves:
   - **ID de cliente** (ejemplo: `123456789-abcdefg.apps.googleusercontent.com`).
   - **Secreto de cliente** (ejemplo: `GOCSPX-xxxxxxxxxxxxxxxxxxxx`).
8. Descarga el archivo JSON o copia ambos valores.

### Paso 5: Obtener el Refresh Token mediante OAuth Playground
1. Ingresa a [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground).
2. En la esquina superior derecha, haz clic en el ícono de engranaje (**OAuth 2.0 configuration**):
   - Marca la casilla **Use your own OAuth credentials**.
   - Pega tu **OAuth Client ID** y tu **OAuth Client Secret**.
3. En la columna izquierda (**Step 1: Select & authorize APIs**):
   - Desplázate hasta **Gmail API v1**.
   - Marca el scope: `https://www.googleapis.com/auth/gmail.send`.
   - Haz clic en el botón azul **Authorize APIs**.
4. Inicia sesión con la cuenta de Google remitente y autoriza los permisos solicitados.
5. En **Step 2: Exchange authorization code for tokens**:
   - Haz clic en **Exchange authorization code for tokens**.
6. Copia el valor del campo **Refresh token** generado.

---

## 4. Configuración en las Variables de Entorno (`.env`)

Abre tu archivo `.env` en la raíz del proyecto y completa los valores correspondientes:

```env
# --- Servicio de Correo / Notificaciones ---
INTERNAL_SERVICE_KEY=aveit-internal-service-secret-2026
DEFAULT_FROM_EMAIL=notificaciones@aveit.utn.edu.ar
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_TIMEOUT=5

# Credenciales SMTP directas (Método 1)
EMAIL_HOST_USER=notificaciones@aveit.utn.edu.ar
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion_16_caracteres

# Credenciales Google Cloud Console OAuth 2.0 (Método 2)
GOOGLE_CLIENT_ID=tu_cliente_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-tu_secreto_de_cliente
GOOGLE_REFRESH_TOKEN=1//tu_refresh_token_obtenido
```

---

## 5. Verificación de Funcionamiento

Para verificar que el despacho de correos opera correctamente con las credenciales configuradas:

1. Asegúrate de que los contenedores estén activos:
   ```bash
   docker compose up -d db backend
   ```
2. Realiza un envío de prueba contra el endpoint protegido de la API:
   ```bash
   curl -X POST http://localhost:8000/api/v1/notifications/email/ \
     -H "Content-Type: application/json" \
     -H "X-Internal-Service-Key: aveit-internal-service-secret-2026" \
     -d '{
       "to": "destinatario_prueba@aveit.utn.edu.ar",
       "subject": "Prueba de Integración Gmail - SGD-AVEIT",
       "body_text": "Este es un correo de verificación del encolador transaccional.",
       "metadata": {"entorno": "pruebas", "modulo": "notificaciones"}
     }'
   ```
3. Verifica la respuesta:
   - **`200 OK` (Estado `SENT`):** El servidor SMTP de Gmail aceptó y entregó el mensaje de inmediato.
   - **`202 Accepted` (Estado `PENDING`):** Si hubo una pérdida de conexión de red temporal, el correo fue encolado en la tabla `notifications_email_outbox` de MySQL y será despachado automáticamente en el próximo ciclo del comando `process_email_queue`.
