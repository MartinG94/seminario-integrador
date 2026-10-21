# Plan Técnico — Spec 006: Resolver Causal T02 con Fundamento Trazable (S4-02)

## 1. Esquema legacy

El esquema legacy (`tribunal_expediente`, `tribunal_puntajeaplicado`, `tribunal_puntajegeneral`, `tribunal_valorsancion`) no modela decisiones por causal ni su fundamento. Se crea una tabla nueva dentro del módulo `expedientes` (AGENTS.md, regla 6).

## 2. Arquitectura

| Capa | Archivo | Responsabilidad |
| :--- | :--- | :--- |
| Dominio puro | `backend/expedientes/domain/causal_resolution.py` | Regla sugerida, exigencia de fundamento y validación. Sin dependencias de Django. |
| Persistencia | `backend/expedientes/models.py` (`DecisionCausalDescargo`) | Registro inmutable y versionado. `save()` sólo inserta; `delete()` se rechaza. |
| Aplicación | `backend/expedientes/services/causal_resolution_service.py` | Transacción con `select_for_update`, control de etapa, evidencia, versión y copia del descargo. |
| API | `views.py` / `urls.py` / `serializers.py` | `GET`/`POST /api/v1/expedientes/{id}/descargos/{descargo_id}/decisiones/`. |
| Frontend | `expediente-api.service.ts`, `gestionar-expedientes` | Panel "Causales T02" en el detalle del expediente para TD. |

## 3. DDL (tabla `expedientes_decision_causal`)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK → `expedientes_expediente` | `PROTECT` |
| `descargo_id` | FK → `expedientes_descargo` | `PROTECT` |
| `version` | INT UNSIGNED | Única junto con `descargo_id` |
| `decision` | VARCHAR(10) | `ACCEPTED` / `REJECTED` |
| `regla_sugerida` | VARCHAR(10) | Regla calculada al decidir |
| `se_aparta_de_regla` | BOOL | |
| `fundamento` | TEXT | Obligatorio al rechazar o apartarse |
| `evidencias_valoradas` | JSON | `[{id, nombre_original, sha256_hash}]` |
| `descargo_snapshot` | JSON | Copia del descargo valorado |
| `autor_id` | FK → `auth_user` | `PROTECT` |
| `autor_legajo`, `autor_rol` | VARCHAR | Copia al momento de decidir |
| `created_at` | DATETIME(6) | Fecha del servidor |

## 4. Decisiones y alternativas descartadas

- **Versionado con filas nuevas** en lugar de actualizar la decisión: cumple CA3 y la regla de cero `UPDATE` sobre registros auditables.
- **Sin impacto en puntos:** la decisión por causal no mueve saldos; los puntos se aplican con la resolución emitida (Sprint 5).
- **Regla sugerida simple** (comprobante vigente ⇒ aceptar): única regla objetiva hoy disponible (Spec 005). Se descartó codificar baremos por causal porque no están definidos por el PO.
- **Descartado:** guardar la decisión como columna en `DescargoExpediente`, porque modificaría el descargo (CA4) y perdería el historial.
- **Descartado:** asentar la decisión en `CambioEstadoExpediente`, porque ese historial es visible para el socio imputado y expondría la deliberación del TD antes de la emisión. La tabla de decisiones es la pista de auditoría.
