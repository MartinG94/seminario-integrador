# Plan 012 — Panel de Administración: Parámetros del Sistema y Miembros con Rol TD

## 1. Arquitectura

```
core/domain/system_parameters.py      Catálogo y validación (dominio puro, sin Django)
core/models.py                        SystemParameterChange, TribunalRoleChange (solo inserción)
core/services/system_parameters.py    Lectura del valor vigente, alta de versión e historial
core/services/tribunal_members.py     Alta y revocación del rol TD con auditoría
core/api/                             Serializers, vistas y rutas REST
frontend/src/app/pages/admin/parametros/   Pantalla Angular
frontend/src/app/services/admin-api.service.ts
```

- El catálogo de parámetros vive en código: define clave, tarjeta, tipo, límites y valor inicial. La base solo guarda los cambios.
- El valor vigente de una clave es su último registro; si no hay registros, rige el valor inicial del catálogo.
- El plazo de apelación reutiliza `ParametroPlazoApelacion` (PB-02) como almacenamiento, para no tener dos fuentes de verdad.
- Los correos sin modificar se resuelven con las variables de entorno existentes (`CD_EMAIL` como única fuente para Comisión Directiva —`COMISION_DIRECTIVA_EMAIL` queda como alias que la hereda— y `TRIBUNAL_EMAIL`).

## 2. Esquema (tablas nuevas)

No existe en el esquema legacy ni en el actual una tabla de configuración general ni de auditoría de roles (Regla Innegociable 6), por lo que se crean dos tablas:

```sql
CREATE TABLE core_parametro_sistema (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  `key` VARCHAR(50) NOT NULL,
  value JSON NOT NULL,
  previous_value JSON NULL,
  author_id INT NULL,             -- FK auth_user, PROTECT
  created_at DATETIME(6) NOT NULL,
  INDEX (`key`, created_at)
);

CREATE TABLE core_cambio_rol_tribunal (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  socio_id BIGINT NOT NULL,       -- FK socios_socio, PROTECT
  action VARCHAR(10) NOT NULL,    -- ALTA | BAJA
  previous_role VARCHAR(20) NOT NULL,
  new_role VARCHAR(20) NOT NULL,
  author_id INT NOT NULL,         -- FK auth_user, PROTECT
  created_at DATETIME(6) NOT NULL
);
```

Ambos modelos rechazan `save()` sobre registros existentes y `delete()`, y su `QuerySet` bloquea `update()`, `delete()`, `bulk_update()` y `bulk_create(update_conflicts=True)`.

La migración se llama `core/0001_parametros_sistema_y_rol_tribunal.py`: no reutiliza `0001_initial`, porque entornos con el volumen MySQL previo ya registran una migración histórica `('core', '0001_initial')` y Django la daría por aplicada sin crear las tablas.

## 3. Endpoints

| Método | Ruta | Permiso | Respuesta |
| --- | --- | --- | --- |
| `GET` | `/api/v1/admin/parametros/` | `ADMIN` | Lista de parámetros con valor vigente y metadatos |
| `PUT` | `/api/v1/admin/parametros/<clave>/` | `ADMIN` | Parámetro actualizado · `400` inválido o no editable · `404` clave inexistente |
| `GET` | `/api/v1/admin/parametros/<clave>/historial/` | `ADMIN` | Cambios del parámetro, del más reciente al más antiguo |
| `GET` | `/api/v1/admin/usuarios-td/` | `ADMIN` | Socios con rol TD |
| `POST` | `/api/v1/admin/usuarios-td/` | `ADMIN` | `201` socio designado · `400` no elegible |
| `DELETE` | `/api/v1/admin/usuarios-td/<socio_id>/` | `ADMIN` | `204` · `404` si no tiene rol TD |
| `GET` | `/api/v1/admin/usuarios-td/candidatos/?search=` | `ADMIN` | Socios Ordinarios habilitados que coinciden (búsqueda en servidor, hasta 20) |
| `GET` | `/api/v1/parametros/adjuntos/` | Autenticado | Límites vigentes de tamaño y cantidad |
| `GET` | `/api/v1/parametros/umbrales/` | Autenticado | Umbral crítico, umbral preventivo y si la alerta preventiva está activa |
| `GET` | `/api/v1/parametros/plazos/` | Autenticado | Plazos vigentes de descargo y de apelación |

## 4. Integración con el código existente

| Consumidor | Antes | Ahora |
| --- | --- | --- |
| `ExpedienteWorkflowService.transition` y `OpeningNotificationService` | `5` fijo | `plazo_descargo_dias_habiles` |
| `ranking.services` (evaluación de umbrales) | `UmbralConfig()` | `UmbralConfig` construido con `umbral_preventivo` y `umbral_preventivo_activo` |
| `resolver_destinatarios_alerta_critica`, `T01AppealService`, `TribunalCompositionService` | `settings.*_EMAIL` | Correo configurado, con la variable de entorno como respaldo |
| `EvidenceValidator` / `EvidenceService` / carga de evidencias | `5 MB` y `5` fijos | `adjuntos_tamano_maximo_mb` y `adjuntos_cantidad_maxima` |
| `MisExpedientesComponent` | Constantes locales | Límites leídos de `/api/v1/parametros/adjuntos/` |

## 5. Frontend

- Ruta `/admin/parametros` protegida con `TribunalGuard` y `data.roles = ['ADMIN']`; entrada "Administración" en el menú solo para `ADMIN`.
- Cuatro tarjetas temáticas (Plazos, Umbrales, Correos, Adjuntos) y una tarjeta "Miembros del Tribunal de Disciplina".
- Alta de miembro en un diálogo con `mat-autocomplete` y búsqueda con espera de 300 ms sobre `/api/v1/admin/usuarios-td/candidatos/?search=`.
- Revocación con diálogo de confirmación.

## 6. Alternativas descartadas

- **Una fila por clave con `UPDATE`:** pierde el historial; se descarta por el requisito de auditoría inmutable.
- **Migrar el plazo de apelación a la tabla nueva:** obligaba a tocar PB-02 y sus pruebas sin beneficio funcional.
- **Guardar los parámetros en variables de entorno:** exige reiniciar el servicio y no deja autoría.
- **Tope de adjuntos por tipo de descargo configurable:** cambia reglas procesales de la spec 005; queda fuera de alcance.
