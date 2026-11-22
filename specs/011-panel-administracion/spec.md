# Spec 010 — Panel de Administración: Parámetros del Sistema y Miembros con Rol TD (MACRO-03 / SCRUM-91)

> **Origen:** Notas del PO del 13/11/2026, sección 4 ("Panel de Administración (solo Admin)") y `PLAN_SPRINT_5_CONSOLIDADO.md` (N-07).
> **Subtareas Jira:** `SCRUM-107` (S5-03.1), `SCRUM-108` (S5-03.2), `SCRUM-109` (S5-03.3).

## 1. Historia de usuario

**Como** Administrador de Cómputos (`ADMIN`), **quiero** una pantalla propia para configurar los parámetros del sistema y designar a los miembros del Tribunal de Disciplina, **para** que los plazos, umbrales, correos y límites de adjuntos dejen de estar fijos en el código y el alta o baja del rol TD no requiera intervención manual sobre la base de datos.

## 2. Alcance

### 2.1 Parámetros del sistema

| Tarjeta | Parámetro | Clave | Valor inicial | Regla |
| --- | --- | --- | --- | --- |
| Plazos | Plazo de descargo | `plazo_descargo_dias_habiles` | 5 | Entero entre 1 y 30 días hábiles |
| Plazos | Plazo de apelación del T01 | `plazo_apelacion_dias_habiles` | 5 | Entero entre 1 y 30 días hábiles |
| Umbrales | Umbral crítico | `umbral_critico` | -10 | Solo lectura (Art. 93 del Reglamento Interno) |
| Umbrales | Umbral preventivo | `umbral_preventivo` | -7 | Decimal entre -9,99 y -0,01 |
| Umbrales | Alerta preventiva activa | `umbral_preventivo_activo` | No | Sí / No |
| Correos | Comisión Directiva | `email_comision_directiva` | Valor de entorno | Correo válido |
| Correos | Tribunal de Disciplina | `email_tribunal_disciplina` | Valor de entorno | Correo válido |
| Adjuntos | Tamaño máximo por archivo | `adjuntos_tamano_maximo_mb` | 5 | Entero entre 1 y 20 MB |
| Adjuntos | Cantidad máxima de comprobantes | `adjuntos_cantidad_maxima` | 5 | Entero entre 1 y 10 |

### 2.2 Miembros del Tribunal de Disciplina

Tabla de usuarios con rol TD, alta mediante búsqueda reactiva de socios y revocación del rol.

## 3. Requisitos (EARS)

- **RF-01 — Acceso exclusivo.** MIENTRAS el usuario autenticado no tenga rol `ADMIN`, EL SISTEMA rechaza con `403` toda petición a `/api/v1/admin/…` y no muestra la opción "Administración" en el menú ni permite navegar a su ruta. Sin token responde `401`.
- **RF-02 — Consulta de parámetros.** CUANDO un `ADMIN` consulta los parámetros, EL SISTEMA devuelve cada parámetro con su valor vigente, valor inicial, límites, unidad, si es editable y la autoría y fecha de su último cambio.
- **RF-03 — Modificación validada.** CUANDO un `ADMIN` guarda un valor, EL SISTEMA lo valida contra el tipo y los límites del parámetro; SI es inválido, responde `400` con un mensaje en español y no registra nada.
- **RF-04 — Auditoría inmutable.** CUANDO se guarda un valor válido, EL SISTEMA inserta un registro nuevo con valor anterior, valor nuevo, autor y fecha. Los registros no se modifican ni se eliminan, y el historial de cada parámetro puede consultarse.
- **RF-05 — Umbral crítico fijo.** EL SISTEMA muestra el umbral crítico de -10 como dato reglamentario de solo lectura y rechaza cualquier intento de modificarlo.
- **RF-06 — Efecto hacia adelante.** CUANDO cambia un plazo, EL SISTEMA lo aplica a los plazos que se abran desde ese momento y conserva sin cambios los vencimientos ya registrados.
- **RF-07 — Consumo real.** EL SISTEMA usa los valores vigentes al abrir el plazo de descargo, al evaluar el umbral preventivo, al dirigir avisos a Comisión Directiva y al Tribunal, y al validar el tamaño y la cantidad de comprobantes. SI un parámetro no fue modificado nunca, rige su valor inicial.
- **RF-08 — Plazo de apelación único.** EL SISTEMA mantiene un solo valor vigente del plazo de apelación del T01, sea que se modifique desde este panel o desde Calendario Institucional.
- **RF-09 — Límites de adjuntos visibles.** CUANDO un socio carga comprobantes, la interfaz informa y aplica los límites vigentes de tamaño y cantidad.
- **RF-10 — Nómina del TD.** CUANDO un `ADMIN` abre la tarjeta de miembros, EL SISTEMA lista a los socios con rol TD con columnas atómicas: `N° de Socio` · `Apellido` · `Nombre` · `Año social` · `Email` · `Acciones`.
- **RF-11 — Alta de miembro.** CUANDO un `ADMIN` busca un socio por nombre o número de socio, EL SISTEMA muestra coincidencias a medida que escribe y, al confirmar, asigna el rol TD. SI el socio no existe, está inhabilitado, ya integra el Tribunal o tiene otro rol institucional (`CD`, `FISCALIZADORA`, `ADMIN`), EL SISTEMA rechaza el alta con `400` y explica el motivo.
- **RF-12 — Revocación.** CUANDO un `ADMIN` confirma la revocación, EL SISTEMA devuelve al socio a `SOCIO` (Socio Ordinario) con efecto inmediato sobre sus permisos. SI el socio no tiene rol TD, responde `404`.
- **RF-13 — Auditoría de roles.** CUANDO se asigna o revoca el rol TD, EL SISTEMA registra de forma inmutable socio, acción, rol anterior, rol nuevo, autor y fecha, y deja constancia en la pista de seguridad.
- **RF-14 — Avisos.** La pantalla comunica éxitos y errores por el servicio central de notificaciones y usa exclusivamente tokens de `DESIGN.md`.

## 4. Fuera de alcance

- Modificar el umbral crítico de -10 (reglamentario).
- Cambiar el remitente de los correos y las credenciales SMTP: siguen siendo variables de entorno a cargo de Cómputos.
- Asignar o revocar roles distintos de TD.
- Recalcular plazos ya abiertos o reemitir alertas por cambios de configuración.

## 5. Decisiones a confirmar con el PO

1. El umbral crítico se muestra pero no se edita.
2. El alta en el TD solo admite Socios Ordinarios; quien tenga otro rol institucional debe quedar primero como Socio Ordinario.
3. El límite de cantidad de comprobantes es único (5); el tope de 3 para descargos tipificados que aplica la pantalla de carga no cambia.
