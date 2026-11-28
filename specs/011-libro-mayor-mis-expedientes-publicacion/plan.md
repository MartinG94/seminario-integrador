# Plan 011 — Libro Mayor Inmutable, Portal "Mis Expedientes" y Publicación Oficial Protegida

## 1. Arquitectura

```
ranking/domain/ledger.py                      Regla 3:1, impacto por socio y hash encadenado (dominio puro)
ranking/models.py                             PuntajeAplicado.registrar_movimiento(): única vía de inserción
expedientes/models.py                         AsientoLibroMayor (solo inserción, QuerySet sin update/delete)
expedientes/services/ledger_service.py        Asientos al emitir, saldo y movimientos del socio
expedientes/services/resolution_service.py    emitir_resolucion() invoca el libro mayor en la misma transacción
expedientes/domain/medical_redaction.py       Detección y censura de datos de salud (dominio puro)
expedientes/services/publication_service.py   DTO de publicación censurado y verificación del hash
expedientes/publication_views.py              Publicación JSON/PDF y saldo del socio
frontend/src/app/mis-expedientes/             Saldo del libro mayor, puntos aplicados y modal de resolución
frontend/src/app/services/expediente-api.service.ts
```

- **Fuente de verdad del saldo:** la suma de `tribunal_puntajeaplicado`, igual que el Ranking (`get_reconciled_ranking_queryset`). No se toca la caché `tribunal_puntajegeneral`.
- **Contadores 3:1:** se reutiliza la tabla `atencionFelicitacion` que ya usa `WarningAccumulationService`, con bloqueo pesimista (`select_for_update`).
- **Número de socio:** el `nroSocio` del libro mayor legado se vincula con el `numero_socio` (`legajo` en el padrón legado) de `socios_socio`.
- **Impacto individual:** se resuelve por socio a partir de `DecisionCausalDescargo` / `ValoracionT03` y de la solicitud; el proveedor de decisión deja de usar ±0,25 como puntos finales.

## 2. Esquema

La tabla legada `tribunal_puntajeaplicado` (`idPuntajeAplicado`, `puntajeAplicado`, `socio_id`, `expediente_id`) se respeta sin cambios (Regla Innegociable 6) y sigue siendo el libro mayor que suma el Ranking. No modela la resolución que origina el movimiento, el tipo (directo o consolidación 3:1), el autor, la fecha ni el encadenamiento de integridad, por lo que se agrega una tabla de auditoría de solo inserción:

```sql
CREATE TABLE expedientes_asiento_libro_mayor (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  resolucion_id BIGINT NOT NULL,        -- FK expedientes_resolucion, PROTECT
  expediente_id BIGINT NOT NULL,        -- FK expedientes_expediente, PROTECT
  socio_id BIGINT NOT NULL,             -- FK socios_socio, PROTECT
  nro_socio INT NULL,                   -- socio_id del libro mayor legado
  tipo VARCHAR(30) NOT NULL,            -- PUNTOS_DIRECTOS | SIN_IMPACTO | LLAMADO_ATENCION | FELICITACION
                                        -- | CONSOLIDACION_LLAMADOS | CONSOLIDACION_FELICITACIONES | REVERSION
  puntos DECIMAL(10,2) NOT NULL,
  contador_resultante INT NULL,
  puntaje_aplicado_id INT NULL,         -- idPuntajeAplicado legado (sin FK física)
  autor_id INT NULL,                    -- FK auth_user, PROTECT
  hash_anterior CHAR(64) NOT NULL,
  hash_transaccion CHAR(64) NOT NULL UNIQUE,
  created_at DATETIME(6) NOT NULL,
  UNIQUE (resolucion_id, socio_id, tipo)
);
```

## 3. Endpoints

| Método | Ruta | Permiso | Respuesta |
| --- | --- | --- | --- |
| GET | `/api/v1/expedientes/mis-expedientes/saldo/` | Autenticado con perfil de socio | Saldo, pendientes 3:1 y movimientos propios |
| GET | `/api/v1/expedientes/<id>/resolucion/publicada/` | Imputado o TD/CD/Admin | Publicación censurada (404 si no está emitida) |
| GET | `/api/v1/expedientes/<id>/resolucion/publicada/pdf/` | Imputado o TD/CD/Admin | PDF censurado |

`mis-expedientes/` agrega `puntos_aplicados` y `medida_aplicada` por causa y oculta el texto de resoluciones no emitidas.

## 4. Alternativas descartadas

- **Agregar columnas a `tribunal_puntajeaplicado`:** alteraría el esquema legado; se prefiere una tabla de auditoría enlazada.
- **Abrir un expediente nuevo por cada consolidación 3:1 originada en una resolución:** obligaría a una segunda resolución para el mismo hecho; la resolución que completa el tercero ya es el acto formal.
- **Actualizar `tribunal_puntajegeneral`:** sería un `UPDATE` sobre un saldo derivado; el Ranking ya suma el libro mayor.
- **Censurar solo para terceros:** la publicación es un documento único; el texto completo queda en la pantalla del Tribunal.
