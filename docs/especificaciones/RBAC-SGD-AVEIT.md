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
| `FISCALIZADORA` | ACT-04 Autoridad de Subcomisión / Líder de Equipo | Lo de `SOCIO`, más el inicio de solicitudes T01 sobre integrantes de su propia subcomisión o equipo (Arts. 25 y 26). |
| `CD` | ACT-03 Comisión Directiva | Lo de `SOCIO`, más ranking consolidado del padrón, inicio de T01 general (Art. 21), alertas de 7 y 10 puntos y carga de cierres de asambleas. |
| `TD` | ACT-02 Miembro del Tribunal de Disciplina | Lo de `SOCIO`, más tablero de los 6 estados, buscador integral de legajos, ranking, sustanciación de T02/T03, resoluciones y disposiciones firmadas. |
| `ADMIN` | ACT-05 Admin de Cómputos | Gestión de cuentas y asignación de roles RBAC, auditoría de logs de seguridad y configuración. **Sin atribuciones funcionales** sobre expedientes ni saldos. |

> `FISCALIZADORA` está asignado a ACT-04 (autoridades de subcomisión y líderes de equipo). Los **Órganos de Fiscalización** del ERS (STK-06: Comisión Fiscalizadora y Comisión Revisora de Cuentas) no tienen rol propio en el enum de la spec; ver la sección 5.

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

Los endpoints de ranking, búsqueda y legajo integral (RF-03-WS, RF-04-WS) se incorporan en las tareas T6 y T7 y reutilizan `IsTribunalOrDirectiva`.

---

## 5. Cuestiones abiertas para el Product Owner

1. **Cargos 13, 14 y 15 sin equivalencia unívoca.** Los 7 cargos de Comisión Directiva que enumera ACT-03 no incluyen un "Secretario" a secas, por lo que no puede deducirse si el cargo 13 es de CD o de subcomisión. Los Revisores de Cuentas (14 y 15) pertenecen a STK-06 "Órganos de Fiscalización", que no tiene rol propio en el enum de cinco roles de la spec. Hasta que se decida, esas cuentas se migran como `SOCIO` (privilegio mínimo) y requieren revisión manual.
2. **Órganos de Fiscalización sin rol propio.** El ERS les asigna competencia para iniciar acciones disciplinarias (Arts. 22 y 23) y auditoría de legalidad sobre TD y CD. Si se confirma que necesitan acceso diferenciado, hace falta un sexto rol y su modificación en la spec.
3. **Sesión de `tribunal_medio` sin módulo destino.** Las capacidades de gestión de eventos y asistencias del nivel medio legado no tienen módulo equivalente dentro del alcance de Spec 001; la equivalencia queda definida pero sin endpoints que la ejerzan todavía.
4. **Auditoría sin persistencia.** Los eventos de autenticación y autorización se emiten al logger `security` (`backend/accounts/audit.py`), no a una tabla. Si el Balance Cuatrimestral (Art. 137) o ACT-05 requieren consultar la pista desde la aplicación, hace falta especificar un modelo persistente.
