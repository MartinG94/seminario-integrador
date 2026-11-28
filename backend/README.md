# Backend SGD-AVEIT

Django 4.2 LTS + Django REST Framework + MySQL 8.0. Autenticación JWT y RBAC según [Spec 001](../specs/001-walking-skeleton/spec.md). El esquema de roles está documentado en [RBAC-SGD-AVEIT.md](../docs/especificaciones/RBAC-SGD-AVEIT.md).

## Puesta en marcha

```bash
# 1. Base de datos (desde la raíz del repo)
docker compose up -d db

# 2. Entorno e dependencias
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows (Git Bash); en Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt

# 3. Configuración local (el archivo .env.example vive en la raíz del repo)
cp ../.env.example ../.env

# 4. Migraciones y datos de demostración
python manage.py migrate
python manage.py seed_demo

# 5. Servidor
python manage.py runserver 8000
```

> El puerto 3306 debe estar libre: si tenés un MySQL instalado localmente, detenelo antes (`net stop MySQL80` como administrador en Windows).

### Frontend (con el backend ya levantado)

```bash
cd frontend
npm install --legacy-peer-deps   # sólo la primera vez
npm start                        # http://localhost:4200/#/login
```

`ng serve` usa [proxy.conf.json](../frontend/proxy.conf.json) para redirigir `/api` a `http://127.0.0.1:8000`: el navegador ve un solo origen y no hace falta CORS.

## Tests

```bash
pytest -q                  # suite completa
pytest -q tests/test_auth.py
```

El usuario `aveit_dev` recibe permisos sobre `test_%` mediante [docker/mysql/init/01-test-db-grants.sql](../docker/mysql/init/01-test-db-grants.sql), que corre al crearse el volumen de MySQL.

## Endpoints principales (`backend/core/urls.py`)

| Método | Prefijo / Endpoint | Autorización |
| :--- | :--- | :--- |
| `GET` | `/api/health/`, `/api/v1/padron/health/` | Anónimo / monitoreo |
| `POST` | `/api/v1/auth/login/` | Anónimo (N.º de Socio / legajo / email + elegibilidad) |
| `POST` | `/api/v1/auth/refresh/` | Refresh token válido |
| `GET` | `/api/v1/auth/me/` | Autenticado |
| `GET` | `/api/v1/padron/` (`socios/`, `subcomisiones/`) | Autenticado (Read-Only sobre padrón legado) |
| `GET` | `/api/v1/socios/`, `/api/v1/socios/<pk>/legajo/` | `TD`, `CD`, `ADMIN` (legajo según rol) |
| `GET` | `/api/v1/ranking/`, `/api/ranking/` | Autenticado (paginado y reconciliado) |
| `ALL` | `/api/v1/expedientes/` (T01, tablero 6 estados, calendario, descargos T02/T03, evidencias, visor, causal T02, valoración T03, composición TD, apelación T01, resolución/preview/firmas/enmiendas, exclusiones, libro mayor, publicación protegida, reglamentos, reportes) | RBAC por rol y objeto (`IsNotInvolvedInExpediente`; brecha RBAC en 6 vistas de `reportes_views.py` trasladada al Sprint 6, ver [`auditoria/traspaso-sprint6.md`](../auditoria/traspaso-sprint6.md)) |
| `ALL` | `/api/v1/eventos/` (eventos, asistencias, apercibimientos 3:1) | `FISCALIZADORA`, `CD`, `TD`, `ADMIN` |
| `POST` | `/api/v1/notifications/email/`, `/api/v1/notifications/email/retry/` | `X-Internal-Service-Key` o `ADMIN` |
| `ALL` | `/api/v1/admin/` (`parametros/`, `usuarios-td/`), `/api/v1/parametros/` | `ADMIN` (consulta de parámetros para autenticados) |

### Ejemplo

```bash
# Login (devuelve access, refresh y perfil con rol y categoría)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"408917","password":"Aveit-Demo-2026!"}'

# Consumo de una ruta protegida
curl http://localhost:8000/api/v1/socios/ -H "Authorization: Bearer <access>"
```

Usuarios de demostración creados por `seed_demo` (7 usuarios, además ejecuta `seed_production_data`; contraseña `Aveit-Demo-2026!`):

| N.º de Socio / Identificador | Rol |
| :--- | :--- |
| 74907 | `SOCIO` |
| 409953 | `SOCIO` |
| 415327 | `SOCIO` |
| 85194 | `FISCALIZADORA` |
| 87414 | `CD` |
| 408917 | `TD` |
| 403655 | `ADMIN` |

## Auditoría

Los eventos de autenticación y autorización se emiten al logger `security` (`accounts/audit.py`), diferenciando `AUTH_SUCCESS`, `AUTH_FAILURE`, `ACCESS_GRANTED`, `ACCESS_DENIED` y `ROLE_CHANGED`. Nunca registran contraseñas, tokens ni secretos.
