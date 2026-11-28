# Plan Técnico — Spec 001: Walking Skeleton

Plan de arquitectura e implementación para la primera iteración funcional de SGD-AVEIT.

---

## 1. Arquitectura y Módulos

```
+───────────────────────────────────────────────────────────+
|                 FRONTEND (Angular 14 SPA)                 |
|  - AuthService (JWT storage & interceptor)                |
|  - RankingSociosComponent (Filtros, tabla responsive)     |
|  - SocioDetailModalComponent (Legajo integral de socio)   |
+─────────────────────────────┬─────────────────────────────+
                              │ REST API (JSON / Bearer JWT)
+─────────────────────────────v─────────────────────────────+
|               BACKEND (Django 4.2 LTS / DRF)               |
|  - App `accounts`: JWT login, RBAC roles, audit           |
|  - App `socios`: Modelos Socio, Subcomisión, Ranking      |
|  - App `padron`: Capa anticorrupción Read-Only legacy     |
+─────────────────────────────┬─────────────────────────────+
                              │ ORM (mysqlclient)
+─────────────────────────────v─────────────────────────────+
|                   BASE DE DATOS (MySQL 8.0)               |
|  - Tablas: `socios_socio`, `socios_subcomision`,          |
|    `tribunal_puntajeaplicado`,                            |
|    `expedientes_asiento_libro_mayor`, `auth_user`         |
+───────────────────────────────────────────────────────────+
```

---

## 2. Modelo de Datos y Esquema Relacional

### Tabla: `socios_subcomision`
- `id` (INT, PK, Auto)
- `name` (VARCHAR 100, UNIQUE) — Ej: 'Cómputos', 'RRHH', 'Eventos', 'GSA'
- `description` (TEXT, Nullable)

### Tabla: `socios_socio`
- `id` (INT, PK, Auto)
- `user_id` (FK `auth_user`, Unique) — Vínculo con credenciales de autenticación
- `numero_socio` (VARCHAR 20, Unique, Indexed) — Identificador institucional del socio (`legajo` en el padrón legado `socio_lista`)
- `first_name` (VARCHAR 100)
- `last_name` (VARCHAR 100)
- `email` (VARCHAR 150, Unique)
- `subcomision_id` (FK `socios_subcomision`, Indexed)
- `social_year` (INT) — Año social (1 a 6)
- `category` (VARCHAR 10) — `PASSIVE` (mostrar "Pasivo"; alias anterior Junior; años 1–3) o `ACTIVE` (mostrar "Activo"; alias anterior Senior; años 4–6)
- `role` (VARCHAR 20) — 'SOCIO', 'TD', 'CD', 'FISCALIZADORA', 'ADMIN'
- `is_enabled` (BOOLEAN, default True) — vigencia operativa de la cuenta; es independiente de `category`

### Tablas de Libro Mayor Inmutable (Implementación real: `expedientes_asiento_libro_mayor` y `tribunal_puntajeaplicado`)
> *Nota de alineación (27/11/2026):* El modelo `ranking_transaccionpuntos` previsto en el borrador inicial fue reemplazado en código por `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly, con soporte de `REVERSION`) y el esquema legado `PuntajeAplicado` (`tribunal_puntajeaplicado`) / `PuntajeGeneral`.

---

## 3. Decisiones Técnicas y Alternativas Descartadas

1. **Autenticación con JWT (`SimpleJWT`) vs Cookies de Sesión clásicas:**
   - *Decisión:* SimpleJWT con Access Token (60 min) y Refresh Token (7 días).
   - *Justificación:* Permite consumo desacoplado tanto desde la SPA Angular como desde clientes móviles o herramientas CLI sin problemas de CORS ni dependencia de sesiones en servidor.
   - *Alternativa descartada:* Session cookies clásicas de Django (dificulta autenticación desacoplada y pruebas automatizadas de API).

2. **Cálculo dinámico de saldo neto vs Campo `saldo_actual` mutable en la tabla `socio`:**
   - *Decisión:* Cálculo transaccional agregado mediante consulta SQL indexada (`SUM(points)`) con vista materializada o anotación ORM `Coalesce(Sum('transacciones__points'), 0.0)`.
   - *Justificación:* Cumple estrictamente con el principio constitucional innegociable de **cero UPDATE manual en MySQL**. Evita condiciones de carrera en modificaciones concurrentes.
   - *Alternativa descartada:* Campo estático actualizado por triggers o código (riesgo de inconsistencias y manipulación directa).

3. **Arquitectura de Componentes Angular:**
   - *Decisión:* Integración en el módulo `RankingSociosModule` preexistente en `frontend/src/app/ranking-socios/` consumiendo tokens de estilo de `_aveit-tribunal.scss`.
   - *Justificación:* Maximiza la reutilización de las vistas y tarjetas de Material Dashboard PRO ya maquetadas.

---

## 4. Estrategia de Pruebas (Verificada en código)

- **Backend (Pytest):**
  - `backend/tests/test_auth.py`: Login exitoso, login con contraseña errónea, login de usuario inactivo, refresco de token JWT.
  - `backend/tests/test_rbac.py`: Reglas RBAC y equivalencias con permisos legados.
  - `backend/tests/test_ranking_socios.py` / `backend/tests/test_padron_adapter.py`: Ranking, filtros por subcomisión/categoría, legajo integral y capa Read-Only de padrón.
- **Frontend (Karma/Jasmine):**
  - `frontend/src/app/services/auth.service.spec.ts` y `frontend/src/app/ranking-socios/ranking-socios.component.spec.ts`.

---

## 5. Matriz de Trazabilidad Requisitos vs Componentes (Estado real)

| Requisito Funcional | Componente Backend | Componente Frontend | Test Automatizado |
| :--- | :--- | :--- | :--- |
| **RF-01-WS** (Login JWT) | `accounts.views.LoginView` | `AuthService.login()` | `backend/tests/test_auth.py` |
| **RF-02-WS** (Error 401) | `accounts.serializers.LoginSerializer` | `LoginComponent` (`NotificationCenter`) | `backend/tests/test_auth.py` |
| **RF-03-WS** (Ranking & Filtros) | `socios.views.RankingSociosView` | `RankingSociosComponent` | `backend/tests/test_ranking_socios.py` |
| **RF-04-WS** (Buscador Legajo) | `socios.views.SocioListView` / `SocioLegajoView` | `RankingSociosComponent` | `backend/tests/test_ranking_socios.py` |
| **RF-05-WS** (Seguridad RBAC) | `accounts.permissions.IsTribunalOrDirectiva` | `TribunalGuard` | `backend/tests/test_rbac.py` |
| **RF-06-WS** (Cálculo Inmutable) | `expedientes.services.ledger.LedgerService` / `AsientoLibroMayor` | `RankingSociosComponent` | `backend/tests/test_ledger_service.py` |
