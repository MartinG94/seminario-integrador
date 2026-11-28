# Guía de Configuración de Correo Gmail (SMTP)

Este documento detalla cómo configurar el envío de correos electrónicos institucionales en **SGD-AVEIT** mediante casillas de Gmail / Google Workspace usando SMTP con Contraseña de Aplicación (App Password), único esquema implementado actualmente en `backend/notifications/services.py` (`EmailMultiAlternatives` + `Transactional Outbox`).

---

## 1. Esquema Implementado

| Método de Conexión | ¿Requiere Google Cloud Console? | Estado en el código | Recomendado para |
|---|:---:|---|---|
| **SMTP con Contraseña de Aplicación (App Password)** | **NO** | **Implementado** (`django.core.mail.backends.smtp.EmailBackend`) | Desarrollo local, entornos de prueba y cuentas de Gmail o Google Workspace que permitan contraseñas de app. |

> **Nota:** La integración vía Google Cloud Console OAuth 2.0 / Gmail API **no está implementada** en el backend actual (`backend/notifications/`).

---

## 2. Contraseña de Aplicación (SMTP directo)

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

## 3. Configuración en las Variables de Entorno (`.env`)

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

# Credenciales SMTP directas
EMAIL_HOST_USER=notificaciones@aveit.utn.edu.ar
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion_16_caracteres
```

---

## 4. Verificación de Funcionamiento

Para verificar que el despacho de correos opera correctamente con las credenciales configuradas:

1. Asegúrate de que los contenedores estén activos:
   ```bash
   docker compose up -d db backend
   ```
2. Realiza un envío de prueba contra el endpoint protegido de la API (admite `X-Internal-Service-Key` o autenticación JWT de usuario `ADMIN` vía `HasInternalServiceKeyOrAdmin`, y soporta `idempotency_key` opcional):
   ```bash
   curl -X POST http://localhost:8000/api/v1/notifications/email/ \
     -H "Content-Type: application/json" \
     -H "X-Internal-Service-Key: aveit-internal-service-secret-2026" \
     -d '{
       "to": "destinatario_prueba@aveit.utn.edu.ar",
       "subject": "Prueba de Integración Gmail - SGD-AVEIT",
       "body_text": "Este es un correo de verificación del encolador transaccional.",
       "idempotency_key": "test-gmail-2026-01",
       "metadata": {"entorno": "pruebas", "modulo": "notificaciones"}
     }'
   ```
3. Verifica la respuesta:
   - **`200 OK` (Estado `SENT`):** El servidor SMTP de Gmail aceptó y entregó el mensaje de inmediato.
   - **`202 Accepted` (Estado `PENDING`):** Si hubo una pérdida de conexión de red temporal, el correo fue encolado en la tabla `notifications_email_outbox` de MySQL y puede reintentarse mediante `POST /api/v1/notifications/email/retry/` o con el comando `python manage.py process_email_queue`.
