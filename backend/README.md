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

# 3. Configuración local
cp .env.example .env

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

## Endpoints

| Método | Endpoint | Autorización |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login/` | Anónimo |
| `POST` | `/api/v1/auth/refresh/` | Refresh token válido |
| `GET` | `/api/v1/auth/me/` | Autenticado |
| `GET` | `/api/v1/socios/` | `TD`, `CD`, `ADMIN` |

### Ejemplo

```bash
# Login (devuelve access, refresh y perfil con rol y categoría)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"408917","password":"Aveit-Demo-2026!"}'

# Consumo de una ruta protegida
curl http://localhost:8000/api/v1/socios/ -H "Authorization: Bearer <access>"
```

Usuarios de demostración creados por `seed_demo` (contraseña `Aveit-Demo-2026!`):

| Legajo | Rol |
| :--- | :--- |
| 74907 | `SOCIO` |
| 85194 | `FISCALIZADORA` |
| 87414 | `CD` |
| 408917 | `TD` |
| 403655 | `ADMIN` |

## Auditoría

Los eventos de autenticación y autorización se emiten al logger `security` (`accounts/audit.py`), diferenciando `AUTH_SUCCESS`, `AUTH_FAILURE`, `ACCESS_GRANTED` y `ACCESS_DENIED`. Nunca registran contraseñas, tokens ni secretos.
