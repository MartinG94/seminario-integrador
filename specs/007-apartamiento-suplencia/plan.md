# Plan Técnico — Spec 007: Gestionar Apartamiento y Suplencia conforme al Estatuto (S4-04)

## 1. Esquema legacy

- **Nómina del TD:** el legado ya la modela. El cargo de cada socio está en `socio_lista.idTipoSocio` (`socio_tipoSocio`: 10 = Titular TD, 11 = Suplente TD, 12 = Socio Ordinario, 1–9 y 13–15 = otros cargos) y el año social en `socio_lista.anoSocial`. Se lee en sólo lectura con `padron.models.Socio` y se vincula con la cuenta local por `socio_lista.user_id`. **No se crea una tabla de integrantes** (AGENTS.md, regla 6).
- **Grupo (Gxx):** último `socio_estadoHistorial.idGrupo` del socio.
- **Composición por causa:** el legado sólo guarda tres firmantes en `tribunal_datosresolucion.responsable1..3`, ligados a `tribunal_expediente` (legado). No modela la causa del apartamiento, la condición Titular/Suplente/Ad hoc, el reemplazo ni el bloqueo, y el expediente nuevo vive en `expedientes_expediente`. Se crean tablas nuevas en el módulo `expedientes`.

## 2. Arquitectura

| Capa | Archivo | Responsabilidad |
| :--- | :--- | :--- |
| Dominio puro | `backend/expedientes/domain/tribunal_composition.py` | Validación de nómina (CA1/CA5), apartamiento, suplencia, caso ad hoc y validación de designados. Sin Django. |
| Puerto/Adaptador | `backend/expedientes/services/tribunal_roster.py` | Lee la nómina y el cargo legado desde `socio_lista`. |
| Persistencia | `backend/expedientes/models.py` | `ApartamientoTribunal`, `DesignacionAdHoc`, `ComposicionTribunal`, `IntegranteComposicion`; todas sólo-inserción. |
| Aplicación | `backend/expedientes/services/tribunal_composition_service.py` | Transacciones con `select_for_update`, etapa procesal, permisos de apartados y constitución. |
| Flujo | `backend/expedientes/services/workflow_service.py` | Bloquea `espera_resolucion → pendiente_correos` sin cuerpo constituido. |
| API | `views`, `urls`, `serializers` | `GET /composicion/`, `POST /composicion/apartamientos/`, `POST /composicion/designaciones-ad-hoc/`, `POST /composicion/constituir/`. |
| Frontend | `expediente-api.service.ts`, `gestionar-expedientes` | Panel "Composición del Tribunal" en el detalle del expediente. |

## 3. DDL

**`expedientes_apartamiento_tribunal`** — apartamiento voluntario por conflicto (el involucramiento se calcula y se congela al constituir).

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK → `expedientes_expediente` | `PROTECT` |
| `socio_id` | FK → `socios_socio` | Integrante que se aparta; único con `expediente_id` |
| `causa` | VARCHAR(20) | `CONFLICTO_INTERES` / `INVOLUCRADO` |
| `fundamento` | TEXT | ≥ 20 caracteres |
| `autor_id` | FK → `auth_user` | `PROTECT` |
| `created_at` | DATETIME(6) | |

**`expedientes_designacion_ad_hoc`**

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK | `PROTECT` |
| `reemplaza_a_id` | FK → `socios_socio` | Único con `expediente_id` |
| `designado_id` | FK → `socios_socio` | Único con `expediente_id` |
| `anio_social` | SMALLINT | 4, 5 o 6 |
| `acta_asamblea` | VARCHAR(255) | Referencia del acta de Asamblea |
| `autor_id` | FK → `auth_user` | |
| `created_at` | DATETIME(6) | |

**`expedientes_composicion_tribunal`** — una por expediente (`OneToOne`).

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK única | `PROTECT` |
| `es_ad_hoc` | BOOL | |
| `apartamientos` | JSON | Copia de las causas: `[{socio_id, nro_socio, nombre, anio_social, condicion, causa, fundamento}]` |
| `constituida_por_id` | FK → `auth_user` | |
| `constituida_por_legajo` | VARCHAR(20) | |
| `created_at` | DATETIME(6) | |

**`expedientes_integrante_composicion`** — tres filas por composición.

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `composicion_id` | FK | Único con `anio_social` |
| `anio_social` | SMALLINT | 4, 5 o 6 |
| `socio_id` | FK → `socios_socio` | `PROTECT` |
| `condicion` | VARCHAR(10) | `TITULAR` / `SUPLENTE` / `AD_HOC` |
| `nro_socio` | INT | Copia de `socio_lista.nroSocio` |
| `nombre_completo` | VARCHAR(200) | Copia |
| `grupo` | VARCHAR(10) | Copia (`G59`), puede ser vacío |
| `reemplaza_a` | VARCHAR(200) | Integrante apartado al que reemplaza |

## 4. Algoritmo de composición

1. Apartados = integrantes involucrados en el expediente (causa `INVOLUCRADO`, prevalece) ∪ apartamientos declarados (`CONFLICTO_INTERES`).
2. Ad hoc = (≥ 2 involucrados del mismo año) ∨ (≥ 3 involucrados) ∨ (algún año con titular y suplente apartados).
3. Asiento de cada año: titular → (ad hoc) reemplazo del titular → suplente → (ad hoc) reemplazo del suplente; el primero habilitado.
4. Observaciones que impiden constituir: nómina inválida (CA1/CA5), asiento vacante, involucrado sin reemplazo en caso ad hoc.

## 5. Decisiones y alternativas descartadas

- **Nómina desde el legado** y no tabla propia de integrantes: el cargo ya está en `idTipoSocio` (regla 6). Se descartó usar `Socio.role = TD` porque no distingue titular de suplente.
- **Sin endpoint de recusación** ni campo de socio destino en el apartamiento: el endpoint aparta siempre al usuario autenticado (Art. 93).
- **Copia de la composición al constituir** en filas inmutables: la nómina legada cambia con cada mandato y la resolución debe conservar sus firmantes (pie de firma, notasPO §4).
- **Guarda en el flujo** al pasar a `pendiente_correos` y no al entrar a `espera_resolucion`: el cuerpo puede cambiar mientras se revisan justificaciones; se congela antes de adoptar la resolución.
- **Descartado:** escribir `tribunal_datosresolucion.responsable1..3`; pertenece al expediente legado y no guarda causa ni condición.
