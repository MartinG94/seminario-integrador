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
|  - App `accounts`: Custom User, JWT login, RBAC roles     |
|  - App `socios`: Modelos de Socio, Subcomisión, Categoría |
|  - App `ranking`: Servicio de agregación de saldos        |
+─────────────────────────────┬─────────────────────────────+
                              │ ORM (mysqlclient)
+─────────────────────────────v─────────────────────────────+
|                   BASE DE DATOS (MySQL 8.0)               |
|  - Tablas: `socios_socio`, `socios_subcomision`,          |
|    `ranking_transaccionpuntos`, `auth_user`               |
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
- `legajo` (VARCHAR 20, Unique, Indexed) — Número de legajo UTN/AVEIT
- `first_name` (VARCHAR 100)
- `last_name` (VARCHAR 100)
- `email` (VARCHAR 150, Unique)
- `subcomision_id` (FK `socios_subcomision`, Indexed)
- `social_year` (INT) — Año social (1 a 6)
- `category` (VARCHAR 10) — `PASSIVE` (mostrar "Pasivo"; alias anterior Junior; años 1–3) o `ACTIVE` (mostrar "Activo"; alias anterior Senior; años 4–6)
- `role` (VARCHAR 20) — 'SOCIO', 'TD', 'CD', 'FISCALIZADORA', 'ADMIN'
- `is_enabled` (BOOLEAN, default True) — vigencia operativa de la cuenta; es independiente de `category`

### Tabla: `ranking_transaccionpuntos` (Libro Mayor Inmutable)
- `id` (BIGINT, PK, Auto)
- `socio_id` (FK `socios_socio`, Indexed)
- `points` (DECIMAL(4,1)) — Valor (+/-) en múltiplos de 0.5
- `reason` (VARCHAR 255)
- `reference_code` (VARCHAR 50, Nullable) — Identificador de expediente o evento
- `created_at` (DATETIME, auto_now_add=True, Indexed)
- `created_by_id` (FK `auth_user`)

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

## 4. Estrategia de Pruebas

- **Backend (Pytest):**
  - `tests/test_auth.py`: Login exitoso, login con contraseña errónea, login de usuario inactivo, refresco de token JWT.
  - `tests/test_socios.py`: Creación de socio con categoría automática (Pasivo/Activo según año social), unicidad de legajo.
  - `tests/test_ranking.py`: Cálculo de saldo neto con transacciones mixtas (+/-), filtros por subcomisión, ordenamiento descendente, filtros RBAC.
- **Frontend (Karma/Jasmine):**
  - `auth.service.spec.ts`: Almacenamiento seguro de tokens y decodificación de roles.
  - `ranking-socios.component.spec.ts`: Renderizado de lista, aplicación de filtros de búsqueda y estados de carga/vacío.

---

## 5. Matriz de Trazabilidad Requisitos vs Componentes

| Requisito Funcional | Componente Backend | Componente Frontend | Test Automatizado |
| :--- | :--- | :--- | :--- |
| **RF-01-WS** (Login JWT) | `accounts.views.CustomTokenObtainPairView` | `AuthService.login()` | `test_auth.py::test_login_success` |
| **RF-02-WS** (Error 401) | `accounts.serializers.CustomTokenObtainPairSerializer` | `LoginComponent` (alert) | `test_auth.py::test_login_invalid_credentials` |
| **RF-03-WS** (Ranking & Filtros) | `ranking.views.RankingListView` | `RankingSociosComponent` | `test_ranking.py::test_ranking_filters` |
| **RF-04-WS** (Buscador Legajo) | `socios.views.SocioViewSet` (`SearchFilter`) | `RankingSociosComponent` (input debounce) | `test_socios.py::test_search_socio` |
| **RF-05-WS** (Seguridad RBAC) | `accounts.permissions.IsTribunalOrDirectiva` | `RoleGuard` (Angular Router) | `test_auth.py::test_unauthorized_access_forbidden` |
| **RF-06-WS** (Cálculo Inmutable) | `ranking.services.get_member_balance` | `BadgePuntosComponent` | `test_ranking.py::test_points_aggregation` |
