# Esquema RBAC — SGD-AVEIT

Control de acceso basado en roles del Walking Skeleton (Spec 001). Documenta los roles vigentes, qué habilita cada uno, la equivalencia con los permisos del sistema legado y los endpoints protegidos.

**Implementación de referencia:** `backend/accounts/permissions.py`, `backend/accounts/legacy_rbac.py` y el campo `Socio.role` (`backend/socios/models.py`). La tabla de equivalencias existe además como código para quedar cubierta por tests (`backend/tests/test_rbac.py`).

---

## 1. Principios

1. **La autorización se resuelve en el servidor.** Que la SPA oculte un botón o una ruta es sólo una mejora de experiencia de usuario. Toda ruta protegida valida el rol en cada petición; un acceso directo por URL sin autorización recibe `403 Forbidden`.
2. **El rol se relee del padrón, no del token.** Las clases de permiso consultan `Socio.role` e `is_enabled` en cada request. Una baja o un cambio de rol surte efecto de inmediato, sin esperar a que expire el JWT ya emitido.
3. **El cargo estatutario no confiere permisos.** Se mantiene la separación que ya regía en el sistema legado: el cargo y la categoría social (Pasivo/Activo) son datos del padrón; el acceso lo determina únicamente `Socio.role`.
4. **Privilegio mínimo por defecto.** DRF está configurado con `IsAuthenticated` como permiso por defecto: un endpoint nuevo queda protegido salvo que declare explícitamente lo contrario.

---

## 2. Roles disponibles

| Rol | Actor (catálogo de actores) | Alcance funcional |
| :--- | :--- | :--- |
| `SOCIO` | ACT-01 Socio Ordinario | Consulta de su propio legajo, saldo y expedientes; presentación de descargos T02/T03. |
| `FISCALIZADORA` | ACT-04 Autoridad de Subcomisión / Líder de Equipo | Lo de `SOCIO`, más el inicio de solicitudes T01 sobre integrantes de su propia subcomisión o equipo (Arts. 25 y 26). Rol vigente en Sprint 5; su partición en `AUTORIDAD_SC` y `REVISORES` + página 403 (`SCRUM-121`/`SCRUM-122`) queda **trasladada al Sprint 6** (ver [`auditoria/traspaso-sprint6.md`](../../auditoria/traspaso-sprint6.md)). |
| `CD` | ACT-03 Comisión Directiva | Lo de `SOCIO`, más ranking consolidado del padrón, inicio de T01 general (Art. 21) y carga de eventos/asistencias. El despacho automático de alertas de -7 y -10 puntos (`SCRUM-62`) queda **trasladado al Sprint 6** (ver [`auditoria/traspaso-sprint6.md`](../../auditoria/traspaso-sprint6.md)). |
| `TD` | ACT-02 Miembro del Tribunal de Disciplina | Lo de `SOCIO`, más tablero de los 6 estados, buscador integral de legajos, ranking, sustanciación de T02/T03, valoraciones, resoluciones, firmas colegiadas, enmiendas y exclusiones. |
| `ADMIN` | ACT-05 Admin de Cómputos | Gestión de cuentas, miembros del TD y parámetros del sistema (`/admin/parametros`, `SCRUM-91 / MACRO-03`), auditoría de seguridad y configuración. **Sin atribuciones funcionales** sobre resolución de expedientes ni saldos. |

> `FISCALIZADORA` continúa vigente en Sprint 5 (decisión D-02). La separación en roles diferenciados (`AUTORIDAD_SC`, `REVISORES`) y la vista dedicada de acceso denegado (403) quedan **trasladadas al Sprint 6** ([`auditoria/traspaso-sprint6.md`](../../auditoria/traspaso-sprint6.md)).

---

## 3. Equivalencia con los permisos legados

El sistema legado usaba tres permisos de Django acumulativos. Equivalencia con los roles nuevos:

| Permiso legado | Qué habilitaba | Roles nuevos equivalentes |
| :--- | :--- | :--- |
| `tribunal_bajo` (`tribunal.bajo`) | Consultar reglamentos, cargar y ver solicitudes T01 propias, presentar descargos. | `SOCIO`, `FISCALIZADORA`, `CD`, `TD`, `ADMIN` (acceso base de todo usuario autenticado) |
| `tribunal_medio` (`tribunal.medio`) | Gestionar eventos, cargar asistencias, fijar hora de fin, filtrar expedientes. | `CD`, `TD` |
| `tribunal_alto` (`tribunal.alto`) | Dictaminar T01, calificar T02/T03, dictar resoluciones, emitir disposiciones. | `TD` (exclusivo) |

`ADMIN` queda excluido de `tribunal_medio` y `tribunal_alto` de forma deliberada: ACT-05 no tiene atribuciones funcionales sobre expedientes.

### 3.1 Cargos estatutarios legados (`socio_tipoSocio`)

Rol con el que se da de alta cada cuenta migrada:

| ID | Cargo estatutario | Rol RBAC |
| :---: | :--- | :--- |
| 1 | Presidente de Subcomisión | `FISCALIZADORA` |
| 2 | Vicepresidente de Subcomisión | `FISCALIZADORA` |
| 3 | Presidente de AVEIT | `CD` |
| 4 | Vicepresidente de AVEIT | `CD` |
| 5 | Tesorero | `CD` |
| 6 | Protesorero | `CD` |
| 7 | Secretario de Actas | `CD` |
| 8 | Secretario General | `CD` |
| 9 | Prosecretario | `CD` |
| 10 | Titular del Tribunal de Disciplina | `TD` |
| 11 | Suplente del Tribunal de Disciplina | `TD` |
| 12 | Socio Ordinario | `SOCIO` |
| 13 | Secretario | *Pendiente* → `SOCIO` |
| 14 | Revisor de Cuentas | *Pendiente* → `SOCIO` |
| 15 | Revisor de Cuentas Suplente | *Pendiente* → `SOCIO` |

---

## 4. Endpoints protegidos

| Método | Endpoint | Autorización | Respuesta ante falta de permiso |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login/` | Anónimo | `401` con cuerpo genérico ante credenciales inválidas |
| `POST` | `/api/v1/auth/refresh/` | Refresh token válido | `401` si el token es inválido o expiró |
| `GET` | `/api/v1/auth/me/` | Cualquier rol autenticado y vigente | `401` sin token; `403` si la cuenta no está vigente |
| `GET` | `/api/v1/socios/` | `TD`, `CD`, `ADMIN` (`IsTribunalOrDirectiva`) | `401` sin token; `403` con rol insuficiente |
| `GET` | `/api/v1/socios/ranking/`, `/api/v1/socios/<id>/legajo/` | `TD`, `CD`, `ADMIN` (`IsTribunalOrDirectiva`) | `401` sin token; `403` con rol insuficiente |
| `GET/POST/PATCH` | `/api/v1/expedientes/...` (solicitudes T01, gestión, descargos, visor, T02, T03, apelaciones, resoluciones, firmas, enmiendas, exclusiones) | Según acción: `IsAuthenticated`, `IsTribunal`, `IsTribunalOrDirectiva`, `opening_policy.py` y conflicto de interés `IsNotInvolvedInExpediente` (`backend/expedientes/permissions.py`) | `401` / `403` (incluye inhibición de juez involucrado en `SCRUM-54`) |
| `GET/POST/PATCH` | `/api/v1/eventos/...` (eventos, asistencias, llamados de atención/felicitaciones) | `IsAuthenticated` / `IsTribunalOrDirectiva` según operación | `401` / `403` |
| `GET/POST/PATCH` | `/api/v1/calendario/...`, `/api/v1/reglamentos/...` | Lectura autenticada; escritura `TD`/`ADMIN` según módulo | `401` / `403` |
| `GET/POST/PATCH` | `/api/v1/admin/...` (parámetros del sistema y miembros del TD) | `ADMIN` (`IsAdminRole`) | `401` / `403` |
| `GET` | `/api/v1/expedientes/reportes/...` (6 vistas en `reportes_views.py`) | Actualmente `IsAuthenticated` sin permiso de rol específico (**brecha RBAC trasladada al Sprint 6**, ver [`auditoria/traspaso-sprint6.md`](../../auditoria/traspaso-sprint6.md)) | `401` sin token |

En el frontend, las rutas exclusivas del Tribunal de Disciplina y Administración se resguardan adicionalmente con `TribunalGuard` (`frontend/src/app/services/tribunal.guard.ts`).

---

## 5. Estado de cuestiones abiertas y elementos trasladados al Sprint 6

1. **Cargos 13, 14 y 15 y partición de `FISCALIZADORA` (`SCRUM-121`/`SCRUM-122`):** Por decisión D-02, `FISCALIZADORA` permanece vigente en Sprint 5 y los cargos 13, 14 y 15 se migran con privilegio mínimo (`SOCIO`). La partición en roles diferenciados (`AUTORIDAD_SC`, `REVISORES`) y la pantalla dedicada 403 quedan **trasladadas al Sprint 6** ([`auditoria/traspaso-sprint6.md`](../../auditoria/traspaso-sprint6.md)).
2. **Brecha RBAC en reportes y hardening (`SCRUM-63`/`SCRUM-65`):** Seis vistas en `backend/expedientes/views/reportes_views.py` exigen únicamente `IsAuthenticated`; el cierre de esa brecha y el hardening RBAC quedan **trasladados al Sprint 6** ([`auditoria/traspaso-sprint6.md`](../../auditoria/traspaso-sprint6.md)).
3. **Módulo de `tribunal_medio` (Eventos y Asistencias):** Resuelto e implementado (`SCRUM-50 / SCRUM-86`, `backend/expedientes/urls_eventos.py`).
4. **Persistencia de auditoría:** Los eventos de autenticación continúan en el logger `security` (`backend/accounts/audit.py`), mientras que la auditoría funcional cuenta con tablas persistentes implementadas (`AuditoriaConsultaExpediente`, `AuditoriaDescargaEvidencia`, `AuditoriaArticuloReglamento`, `SystemParameterChange`, `TribunalRoleChange` y `CambioEstadoExpediente`).
