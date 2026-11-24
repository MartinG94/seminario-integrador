# Snapshot de Base de Datos — Rama `Regularidad`

Este directorio contiene el snapshot completo (estructura + datos, 95 tablas) de la base de datos `aveit_tribunal_dev` (`mysql:8.0`, contenedor `sgd_aveit_mysql`).

- **Archivo:** `database/snapshot_regularidad.sql`
- **Formato:** UTF-8 sin BOM, `utf8mb4_unicode_ci`, con `DROP TABLE IF EXISTS` + `CREATE TABLE` + `INSERT` (restauración limpia e idempotente).
- **Nota:** No se ubica dentro de `docker/mysql/init/` para no colisionar con los scripts iniciales de arranque limpio (`01-test-db-grants.sql`, `02-initial-data.sql`, `03-scrum50-eventos-asistencias-apercibimientos.sql`).

## Cómo restaurar el snapshot

Asegúrate de tener el contenedor `sgd_aveit_mysql` levantado y saludable (`docker compose up -d db`).

### Opción 1: Windows (PowerShell)

```powershell
docker cp database/snapshot_regularidad.sql sgd_aveit_mysql:/tmp/snapshot_regularidad.sql
docker exec -e MYSQL_PWD=aveit_dev_password_2026 sgd_aveit_mysql sh -c "mysql -uaveit_dev --default-character-set=utf8mb4 < /tmp/snapshot_regularidad.sql && rm -f /tmp/snapshot_regularidad.sql"
```

### Opción 2: Linux / macOS / Git Bash

```bash
docker exec -i -e MYSQL_PWD=aveit_dev_password_2026 sgd_aveit_mysql \
  mysql -uaveit_dev --default-character-set=utf8mb4 < database/snapshot_regularidad.sql
```

> Si en tu `.env` cambiaste `MYSQL_USER`, `MYSQL_PASSWORD` o `MYSQL_DATABASE`, reemplaza las credenciales correspondientes (por defecto: usuario `aveit_dev`, contraseña `aveit_dev_password_2026`, base `aveit_tribunal_dev`).
