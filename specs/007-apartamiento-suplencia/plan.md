# Plan Técnico — Spec 007: Gestionar Apartamiento y Suplencia conforme al Estatuto (S4-04)

## 1. Esquema legacy

- **Nómina del TD:** el legado ya la modela. El cargo de cada socio está en `socio_lista.idTipoSocio` (`socio_tipoSocio`: 10 = Titular TD, 11 = Suplente TD) y el año social se deriva del grupo con `(Año Actual - 1962) - Número de Grupo` (`socio_lista.anoSocial` sólo como respaldo). Se lee en sólo lectura con `padron.models.Socio` y se vincula con la cuenta local por `socio_lista.user_id`. **No se crea una tabla de integrantes** (AGENTS.md, regla 6).
- **Grupo (Gxx):** último `socio_estadoHistorial.idGrupo` del socio.
- **Responsables por causa:** el legado sólo guarda tres firmantes en `tribunal_datosresolucion.responsable1..3`, ligados a `tribunal_expediente` (legado). No modela condición Titular/Suplente, reemplazo ni apartados, y el expediente nuevo vive en `expedientes_expediente`. Se crean tablas nuevas en el módulo `expedientes`.

## 2. Arquitectura

| Capa | Archivo | Responsabilidad |
| :--- | :--- | :--- |
| Dominio puro | `backend/expedientes/domain/tribunal_composition.py` | Validación de nómina (CA1), apartamiento automático, suplencia y Casos A/B. Sin Django. |
| Puerto/Adaptador | `backend/expedientes/services/tribunal_roster.py` | Lee la nómina y el cargo legado desde `socio_lista`. |
| Persistencia | `backend/expedientes/models.py` | `ComposicionTribunal`, `IntegranteComposicion`; sólo-inserción. |
| Aplicación | `backend/expedientes/services/tribunal_composition_service.py` | Involucrados, consulta en vivo, estampado al resolver y aviso a CD por Outbox. |
| Flujo | `backend/expedientes/services/workflow_service.py` | Estampa los asientos disponibles al pasar a `pendiente_correos`; encola el aviso al abrir. |
| Permisos | `backend/expedientes/permissions.py` | `IsNotInvolvedInExpediente` (403). |
| API | `views`, `urls` | `GET /composicion/`; inhibición en decisiones y transiciones. |
| Frontend | `expediente-api.service.ts`, `gestionar-expedientes` | Banner de participación restringida y aviso sutil de causa derivada a Asamblea (sin panel de responsables). |

## 3. DDL

**`expedientes_composicion_tribunal`** — una por expediente (`OneToOne`), estampada al resolver.

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK única | `PROTECT` |
| `apartados` | JSON | Copia de los integrantes involucrados: `[{socio_id, nro_socio, nombre, anio_social, condicion}]` |
| `created_at` | DATETIME(6) | Momento del estampado |

**`expedientes_integrante_composicion`** — hasta tres filas por composición (asientos con integrante disponible).

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `composicion_id` | FK | Único con `anio_social` |
| `anio_social` | SMALLINT | 4, 5 o 6 |
| `socio_id` | FK → `socios_socio` | `PROTECT` |
| `condicion` | VARCHAR(10) | `TITULAR` / `SUPLENTE` |
| `nro_socio` | INT | Copia de `socio_lista.nroSocio` |
| `nombre_completo` | VARCHAR(200) | Copia |
| `grupo` | VARCHAR(10) | Copia (`G59`), puede ser vacío |
| `reemplaza_a` | VARCHAR(200) | Titular involucrado al que reemplaza |

## 4. Algoritmo de composición

1. Involucrados = imputados ∪ solicitante del T01.
2. Asiento de cada año: titular si no está involucrado; si no, suplente si no está involucrado; si no, vacante.
3. Caso A = titular y suplente del mismo año involucrados. Caso B = tres o más integrantes involucrados. Cualquiera de los dos dispara el aviso a CD para convocar a Asamblea, sin inmovilizar la causa.
4. La nómina inválida (CA1) no impide la resolución: se estampan los asientos disponibles (decisión del PO, 31/10/2026).

## 5. Decisiones y alternativas descartadas

- **Nómina desde el legado** y no tabla propia de integrantes: el cargo ya está en `idTipoSocio` (regla 6).
- **Inhibición como permiso DRF** reutilizable sobre el `pk` de la URL: un único punto para decisiones y transiciones.
- **Estampado dentro de la transición** a `pendiente_correos` y no con un botón: la composición cambia con los imputados hasta adoptar la resolución (revisión del PO).
- **Aviso idempotente** con `idempotency_key` del Outbox por expediente: se evalúa al abrir y al vincular el solicitante sin duplicar correos.
- **Descartado (revisión del PO):** apartamiento voluntario por conflicto de interés, designación manual de integrantes ad hoc y constitución manual del cuerpo.
- **Descartado (decisión del PO, 31/10/2026):** acta de Asamblea en el sistema e inmovilización de la causa; la Asamblea designa integrantes y se les asigna el rol TD por fuera del flujo.
- **Descartado:** escribir `tribunal_datosresolucion.responsable1..3`; pertenece al expediente legado.
