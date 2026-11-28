# Auditoría de Discrepancias — Seguimiento del Proyecto (`SGD-AVEIT`)

> **Fecha de auditoría:** 27/11/2026  
> **Alcance del entregable:** Acuerdos de trabajo y progreso real del proyecto — **SÍ incluye la ejecución del Sprint 5**, documentando todo lo incompleto o no verificable como `"trasladada al Sprint 6"` (`auditoria/entregables/_brief-comun.md`).  
> **Fuentes contrastadas:**
> - Entregable presentado más reciente: `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Seguimiento_de_ProyectoVersionSprint4.pdf` (`v1.4.0`, `04/11/2026`, inmutable) y contraste con `...Sprint0.pdf` (`v1.1.0`) y `...Sprint2.pdf` (`v1.2.0`).
> - Copia del repositorio: `docs/gestion-proyecto/Seguimiento de Proyecto.md` (`v1.5.0`, `27/11/2026`).
> - Fuente canónica y código/git: `auditoria/registro-canonico.md`, `auditoria/traspaso-sprint6.md`, `auditoria/entregables/plan-de-proyecto-discrepancias.md`, historial `git` (`main` / `regularidadDocs`).
> - Devoluciones docentes: `retroalimentaciónS0.txt`, `Nuevo documento de texto.txt` (S3) y `retroalimentaciónS4.txt`.

---

## a) Qué afirma el documento que el sistema no hace o que no está verificado

### 1. Cierre del Sprint 4 declarado al 03/11/2026 vs. integración real en `main`
- **`Seguimiento S4` (`v1.4.0`, §2.7.2) y `v1.5.0` (§2.7.2):** afirman el *"100% de los Story Points comprometidos finalizados e integrados en `main` — 19/19 SP"* al **03/11/2026**.
- **Realidad verificada en `git`:** al `03/11/2026` solo estaban integrados en `main` **`SCRUM-70`** (PR #64, `25/10`), **`SCRUM-51`** (PR #65, `26/10`), **`SCRUM-54`** (PR #63, `02/11`) y **ABM Reglamentos** (PR #69, `03/11`). **NO** estaban aún en `main`:
  - **`SCRUM-56`** (PR #67): mergeado el **05/11/2026** (`ad3d9e8`).
  - **`SCRUM-53`** (PR #71): mergeado el **12/11/2026** (`8c41d02`).
- **Adelantos declarados en Sprint 4 (`+8 SP`):** `Seguimiento S4` (§2.7.2 y §2.8.1) presenta `SCRUM-63` (PR #70, 5 SP) y `SCRUM-62` (PR #72, 3 SP) como *"completados con suites de tests en verde"*. En realidad se mergearon el **04/11** (`2366261`) y **05/11** (`3cbe6df`), y ambos son **parciales** (ver punto 2).

### 2. Ítems del Sprint 5 Consolidado incompletos o no verificables (trasladados al Sprint 6)
- `Seguimiento S4` (§2.1.1 A y §2.8.1) proyecta el cierre total del producto *"100% funcional, homologado y validado"* al **18/11/2026** (44 SP). En el código real (al `23/11/2026`), **10 bloques/ítems** están parciales, no implementados o no verificables y quedan **trasladados al Sprint 6** (`auditoria/traspaso-sprint6.md`):
  1. **`SCRUM-62` (`US-17`, Alertas `-10`/`-7`):** `ThresholdAlertEngine` no está invocado desde `LedgerService` ni `emitir_resolucion`; sin endpoint ni vista.
  2. **`SCRUM-61` (Alertas 3:1):** consolida 3:1, pero falta el aviso preventivo a autoridades al llegar a 2 llamados.
  3. **`SCRUM-63` / `SCRUM-124` (Balance Art. 137 y Reportes):** solo exporta JSON/CSV (falta **PDF**) y 6 vistas de `reportes_views.py` solo exigen `IsAuthenticated` (brecha RBAC).
  4. **`SCRUM-64` (Reconciliación bidireccional `PuntajeAplicado` vs `PuntajeGeneral`):** no implementada (sin comando, endpoint ni reporte de divergencias).
  5. **`SCRUM-65` / `SCRUM-92` (Hardening RBAC, 10 disparadores de email, carga 50 usuarios):** sin scripts/reportes de carga (`locust`/`k6`), sin `email_verification_service.py`, persiste brecha RBAC y ruta stub `EnDesarrolloComponent` (`admin-layout.routing.ts:29-38`).
  6. **`SCRUM-121` / `SCRUM-122` (Partición `FISCALIZADORA` → `AUTORIDAD_SC` + `REVISORES` + vista 403):** no implementada; por decisión D-02 (`27/11/2026`) se mantiene `FISCALIZADORA` vigente en Sprint 5.
  7. **`SCRUM-68` / `SCRUM-125` / `US-19` (Repositorio dedicado de jurisprudencia):** solo búsqueda embebida en T03; sin vista libre ni exportación.
  8. **`PB-01` / `SCRUM-128` (Promoción de Casos Internos a T01):** no implementada.
  9. **`SCRUM-66` / `SCRUM-126` (Staging con réplica MySQL legada):** **no verificable** (sin entorno ni logs en el repositorio).
  10. **`SCRUM-67` / `SCRUM-127` (Homologación institucional AVEIT):** **no verificable** (sin actas UAT firmadas por CD, TD y Cómputos).

### 3. Divergencias de Story Points, Calendario, Stack y Roles
- **Story Points (Sprint 0 y Sprint 5):**
  - En Sprint 0 (§2.1.6) persiste el total de `116 SP` sin conciliar la observación histórica `111/116` contra otros documentos (obs. #16).
  - En Sprint 5 Consolidado (§2.8.1 de `Seguimiento S4`) hay **5 divergencias** de estimación frente a `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`: `SCRUM-59` (`5` vs `3` SP), `SCRUM-61` (`2` vs `3` SP), `SCRUM-64` (`3` vs `5` SP), `SCRUM-66` (`5` vs `3` SP) y `SCRUM-67` (`5` vs `3` SP).
- **Inconsistencias de calendario (S3 y S4):**
  - En `Seguimiento S4` (§2.1.1 A): Sprint 3 `07/10 al 20/10` y Sprint 4 `21/10 al 03/11` (con aclaración en §2.6.1/§2.7.1 de apertura Jira el `08/10` y `22/10`).
  - En `v1.5.0` del repo: §2.1.1 A dice S3 `07/10` y S4 `21/10`, mientras §2.6.1 fija S3 `08/10` y §2.7.1 fija S4 `22/10` sin conciliar (repite la obs. #26). Además, el calendario maestro de `v1.5.0` todavía proyecta S4 con *"Votación"* y S6 en diciembre sin reflejar el Sprint 5 Consolidado ejecutado del `04/11` al `23/11`.
- **Stack tecnológico (`§2.1.5`):** `Seguimiento S4` (`v1.4.0`) sigue declarando *"HTML5 semántico, CSS3 modular (`tokens.css`) y Vanilla JavaScript (`view-cd.js`, `view-td.js`, `view-socio.js`)"* y un entorno de *staging independiente*. El stack real es **Angular 14.2+ + TypeScript + Angular Material** y Staging no está verificado (`v1.5.0` corrigió esto).
- **Rol `FISCALIZADORA` (`§2.5.2`):** `Seguimiento S4` (`v1.4.0`) afirma *"Renombrar Fiscalizadora por Revisores (Revisores de Cuentas): Adecuación terminológica estricta en todo el código"*. El código conserva `Role.FISCALIZADORA` (`backend/socios/models.py`, `auth.service.ts`); `v1.5.0` ya lo alinea a D-02.
- **Criterios DoD no cumplidos en la práctica (`§2.1.1 D`):** exige merge a rama `develop` (se mergea directo a `main`), despliegue en Staging (no verificable) y documentación OpenAPI/Swagger (no verificada).
- **Regresiones y defectos exclusivos de `v1.5.0` (repo):**
  - **Violación de inmutabilidad histórica (Regla 13):** `v1.5.0` sobrescribió la fila histórica de `v1.4.0` (`04/11/2026`) mezclando el cierre de Sprint 5 dentro de la fecha `04/11/2026` (cuando el `v1.4.0` presentado el `04/11` solo cerraba S4 y abría S5 Consolidado).
  - **Regresión de votación nominal:** `v1.5.0` revirtió `US-13` (§2.1.6) y el Story Map (§2.1.7) a *"Deliberación Remota y Votación Nominal Fundada"*, cuando `v1.4.0` ya los había actualizado a *"Editor Unificado de Resolución Oficial"*.
  - **Pérdida de secciones y numeración rota:** `v1.5.0` omitió la Retrospectiva de Sprint 4 (`§2.7.3`) y la tabla del Sprint Backlog de Sprint 5 (`§2.8.1`), dejó una sección `2.9` con subsecciones numeradas `2.8.1–2.8.3` en estado plantilla vacía y el Índice desactualizado.
- **Defectos de carátula (`v1.4.0` y `v1.5.0`):** faltan **N.º de Grupo (`13`)**, **N.º de Entrega** y **Fecha de Entrega**; y los legajos UTN de los 7 integrantes figuran rotulados erróneamente como `"Número de Socio"` en lugar de `Legajo UTN`.

---

## b) Qué hace el sistema que el documento no dice

En el entregable presentado (`Seguimiento S4`, `v1.4.0`), el **Sprint 5 Consolidado solo está planificado en apertura (§2.8.1)** con plantillas vacías de resultado y retrospectiva (§2.8.2–§2.8.3). Faltan documentar como **ejecutados e integrados en `main` durante el Sprint 5 (04/11 al 23/11/2026)** los siguientes módulos y PRs verificados en código y git (y en `v1.5.0` del repo solo figuran en 4 viñetas resumidas sin trazabilidad de PRs, fechas ni cierre formal de Sprint 5):

1. **Libro Mayor Transaccional Inmutable y Regla 3:1 (`SCRUM-57` / `SCRUM-59` / `SCRUM-104`, PR #79, `23/11/2026`):** `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly con `REVERSION`), `PuntajeAplicado.registrar_movimiento`, `LedgerService` y `warning_accumulation_service.py` (cero `UPDATE`/`DELETE` manuales).
2. **Circuito Resolutivo Completo: Firma Colegiada 4.º/5.º/6.º, Exclusión y Enmienda (`SCRUM-58` / `SCRUM-89` / `SCRUM-101` / `SCRUM-102` / `SCRUM-103`, PR #77, `17/11/2026`):** firma colegiada obligatoria en `Resolucion.firmantes`, PDF oficial con escudo TD, puntaje ratificado T02 (`DescargoExpediente.puntaje_ratificado`), exclusión fundada (`exclusion_service.py`) y enmienda trazable (`EnmiendaResolucion`, `enmienda_service.py`) con contra-asientos `REVERSION`.
3. **Portal "Mis Expedientes" y Publicación Oficial con Censura Médica (`SCRUM-60` / `SCRUM-105` / `SCRUM-106`, PR #79, `23/11/2026`):** consulta de saldo propio desde Libro Mayor, `publication_views.py`, `publication_service.py` y sanitización automática de datos médicos sensibles (`domain/medical_redaction.py`).
4. **Panel de Administración (`SCRUM-91` / `MACRO-03`, PR #78, `23/11/2026`):** módulo `/admin/parametros` con auditoría de parámetros del sistema (`SystemParameterChange`) y gestión de miembros con rol TD (`TribunalRoleChange`).
5. **Rediseño UI de Eventos y Asistencia (`SCRUM-86` / `MACRO-04`):** nueva interfaz en `frontend/src/app/pages/eventos/asistencia-evento/` conectada al motor Strategy de asistencias.
6. **N.º de Socio, ID Canónico de Expedientes y Celdas Atómicas (`SCRUM-93` / `SCRUM-114` / `SCRUM-115` / `MACRO-05`, PRs #74 y #75, `16/11/2026`):** unificación de `numero_socio` en login/barra/visor, numeración canónica de expedientes y mejoras UX en Gestión.
7. **Optimización de Rendimiento (`SCRUM-87` / `MACRO-06`, PR #76, `16/11/2026`):** paginación backend (`backend/core/pagination.py`), `OnPush`, `trackBy` (`track-by.util.ts`) y optimización de consultas ORM (`test_orm_performance.py`).
8. **Manual de Usuario Modular (`SCRUM-129`, commit `6a60167`, `23/11/2026`):** 9 capítulos HTML en `docs/manual-usuario/src/` y compilado PDF `Manual_Usuario_SGD_AVEIT_Completo.pdf` (32 páginas).
9. **Reportes Analíticos y Balance Art. 137 en JSON/CSV (`SCRUM-63`, PR #70, `04/11/2026`):** integración efectiva en `main` de 4 pestañas UI y exportación JSON/CSV (dejando constancia de que PDF y RBAC en 6 vistas pasan al Sprint 6).

---

## c) Correcciones de los profesores sin aplicar (cita breve)

Evaluación de las observaciones aplicables de `auditoria/registro-canonico.md` (§1):

| # | Cita textual breve | Estado en `v1.4.0` (presentado) | Estado en `v1.5.0` (repo) | Evidencia / Qué falta |
|---|---|---|---|---|
| **16** | *"Revisar Story Points y corregir diferencias entre documentos 111/116."* | **Sin aplicar** | **Sin aplicar** | §2.1.6 mantiene `116 SP` sin explicar/unificar el `111/116`, y en Sprint 5 Consolidado (§2.8.1) hay 5 divergencias nuevas de SP con `Definición S4`. |
| **17** | *"Cambiar 'velocidad proyectada' por carga promedio planificada, hasta que tengan velocidad real."* | **Sin aplicar** | **Sin aplicar** | §2.1.6 conserva literalmente *"Velocidad Promedio Proyectada: ~19.3 SP por Sprint"*. |
| **18** | *"Redefinir el Story Map con al menos un corte horizontal de MVP."* / *"no todo Must al final."* | **Sin aplicar** | **Sin aplicar** | §2.1.6 tiene **18 de 19 US como `Must`** (solo `US-19` es `Should`); §2.1.7 no marca ningún corte horizontal de MVP. |
| **19** | *"Convertir el calendario Sprint 1–6 en roadmap inicial adaptable, explícitamente sujeto a velocidad y feedback."* | **Sin aplicar** | **Sin aplicar** | §2.1.1 A presenta el calendario como cronograma fijo ("Calendario Maestro") sin explicitar carácter adaptable sujeto a velocidad y feedback. |
| **20** | *"No se llama 'MVP por sprint', sería un release... Apuntar a que el 2do Sprint sea el MVP. Actualizar el documento de seguimiento con el tema de release."* | **Sin aplicar** | **Sin aplicar** | Ni §2.1.7 ni los sprints formalizan el concepto de *Release* ni marcan el Sprint 2 como corte de MVP. |
| **21** | *"La documentación debe ser manejada como el código mismo."* | **Parcial** | **Parcial** | Existe historial en git, pero `v1.4.0` quedó desactualizado respecto de `main` y `v1.5.0` introdujo regresiones (`US-13`, fechas S3/S4, sobrescritura de `v1.4.0`). |
| **22** | *"Para la presentación de regularidad el sistema debe estar al día con la documentación... Manual de usuario y toda la documentación presentable."* | **Parcial** | **Parcial** | Manual de Usuario ya existe (`SCRUM-129`), pero Seguimiento carece del cierre formal del Sprint 5, carátula completa y alineación 1:1 con código. |
| **26** | *"Inconsistencia en el calendario: Seguimiento presenta inicio del Sprint 3 el 07/10 en el calendario maestro, pero la sección específica y Definición del Producto indican 08/10. También diferencias en inicio del Sprint 4."* | **Parcial** | **Sin aplicar** | `v1.4.0` aclaró `07/10` (hito PO) vs `08/10` (Jira) y `21/10` vs `22/10`; `v1.5.0` volvió a dejar `07/10`/`21/10` en §2.1.1 A y `08/10`/`22/10` en §§2.6.1–2.7.1. |
| **28** | *"Poner foco en consistencia entre el estado declarado del desarrollo, la integración real, la aceptación institucional y la planificación del cierre."* | **Sin aplicar** | **Parcial** | `v1.4.0` declaró 100% de S4 integrado al 03/11 y cierre total al 18/11; `v1.5.0` incorporó el traspaso al Sprint 6 pero aún no desglosa fechas reales de merge de S4 ni cierra formalmente S5. |
| **29** | *"¿Cuáles de las historias del Sprint 4 estaban efectivamente integradas en main y aceptadas al 3 de noviembre?"* | **Sin aplicar** | **Sin aplicar** | Ninguna versión distingue qué historias de S4 estaban en `main` al 03/11 (`SCRUM-70`, `51`, `54`, ABM Reglamentos) de las integradas después (`SCRUM-56` el 05/11 y `SCRUM-53` el 12/11). |
| **30** | *"¿Cómo justifican la viabilidad de completar los 36 SP pendientes del Sprint 5 consolidado, incluyendo pruebas y homologación?"* | **Parcial** | **Parcial** | `v1.4.0` solo invocó la velocidad de S3 (`36 SP`); la ejecución real demostró que no todo entró y que 10 bloques debieron trasladarse al Sprint 6, lo cual debe quedar explicado explícitamente en el cierre del Sprint 5. |

---

## d) Datos que la cátedra o la plantilla exigen y no existen en ninguna fuente

1. **Horas reales dedicadas por integrante** en los Sprints 1 a 5 (solo existen las horas nominales planificadas en S0: 11 hs/sem = 154 hs/sprint): **`dato faltante`**.
2. **Métricas reales de flujo de Jira** prometidas en §2.1.4 (Burndown charts, Diagrama de Flujo Acumulado / CFD, *Lead Time* y *Cycle Time* reales por sprint, en particular S4 y S5): **`dato faltante`**.
3. **Fechas reales de Sprint Review y Retrospectiva del Sprint 5** (y detalle de técnica, lecciones aprendidas y acciones de mejora del cierre de Sprint 5): **`dato faltante`**.
4. **Aceptación formal / actas de validación del PO y autoridades de AVEIT** (CD, TD, Cómputos) al cierre del Sprint 4 (`03/11`) y del Sprint 5 (`23/11`): **`dato faltante`**.
5. **Story Points consolidados y asignados en Jira** para las historias/macros ejecutadas en Sprint 5 que no estaban en la tabla original de `Seguimiento S4` (`SCRUM-86`, `SCRUM-87`, `SCRUM-89`/`101`/`102`/`103`, `SCRUM-91`, `SCRUM-93`/`114`/`115`, `SCRUM-129`): **`dato faltante`**.
6. **Resultado de ejecución viva actualizada de `pytest` y `Karma`** al cierre del Sprint 5 (`23/11/2026`, solo existe recuento estático de 114 `test_*.py` y 55 `*.spec.ts`; las cifras `>1000` y `>450` de `v1.4.0` corresponden a S4 y no están revalidadas en S5): **`dato faltante`**.
7. **N.º de Entrega formal y Fecha real de entrega** para la Carátula (y si el equipo mantiene `Grupo 13` en todos los entregables): **`dato faltante`**.
8. **Evidencia de entorno Staging operativo (`SCRUM-66`) y Homologación institucional (`SCRUM-67`)**: **`dato faltante`** *(trasladados al Sprint 6)*.

---

## e) Cambios que dependen de una decisión del usuario (alcance, traslados, criterios)

1. **Criterio de fechas y cierre real del Sprint 4 (obs. #28 y #29):** Confirmar cómo reportar el cierre del Sprint 4: explicitar el corte al `03/11/2026` (3 de 5 historias + ABM Reglamentos integradas en `main`, con `SCRUM-56` mergeada el `05/11` y `SCRUM-53` el `12/11`) y aclarar que los "adelantos" `SCRUM-63` (`04/11`) y `SCRUM-62` (`05/11`) quedaron parciales.
2. **Unificación de fechas del calendario S3 y S4 (obs. #26):** Confirmar la convención única en todo el documento (ej. S3 `07/10–20/10` con aclaración de hito PO `07/10` / tablero Jira `08/10`, y S4 `21/10–03/11` con cierre administrativo S3 el `22/10`) y ajustar la fecha real de cierre del Sprint 5 Consolidado (`04/11–23/11/2026`).
3. **Unificación de Story Points (obs. #16 y Sprint 5):** Definir (a) si se conserva `116 SP` como línea base del Backlog Inicial de Sprint 0 explicando la diferencia con `111 SP`, (b) qué valor de SP prevalece en los 5 ítems con conflicto entre `Seguimiento S4` y `Definición S4` (`SCRUM-59`, `61`, `64`, `66`, `67`), y (c) qué SP se contabilizan como "completados" vs "trasladados al Sprint 6" en el cierre del Sprint 5 (incluyendo los macros ejecutados `SCRUM-86/87/91/93/129`).
4. **Reestructuración del Story Map, Releases y prioridades MoSCoW en Sprint 0 (obs. #17, #18, #19, #20):** Confirmar si se actualiza la sección de Sprint 0 (respetando el historial de versiones) para: (a) cambiar *"Velocidad Promedio Proyectada"* a *"Carga promedio planificada"*, (b) convertir el calendario en *"Roadmap inicial adaptable"*, (c) incorporar un corte horizontal de **MVP en Sprint 2** y **Releases** posteriores, y (d) revisar la priorización `Must`/`Should` de `US-01..US-19`.
5. **Contenido de la Retrospectiva Final / Cierre del Sprint 5 y Plan del Sprint 6:** Proveer la fecha real de Review/Retrospectiva del Sprint 5 y confirmar si se completa la Retrospectiva de cierre con lecciones reales del equipo (y si se mantiene la sección de plantillas para el Sprint 6 con los 10 ítems de `auditoria/traspaso-sprint6.md`).
6. **Corrección del Historial de Revisiones (Regla 13 de inmutabilidad):** Restaurar la descripción original e inmutable de `v1.4.0` (`04/11/2026`, tal como fue presentada en `Seguimiento_de_ProyectoVersionSprint4.pdf`) y registrar el cierre real del Sprint 5, la alineación con `registro-canonico.md` y el traspaso al Sprint 6 en **`v1.5.0` (`27/11/2026`)** (o `v1.6.0` si se emite nueva versión tras esta auditoría).
7. **Datos formales de Carátula y DoD:** Confirmar N.º de Entrega, Fecha de Entrega, reemplazo de `"Número de Socio"` por `"Legajo UTN"` en la tabla de integrantes, inclusión de `Grupo 13` y ajuste del DoD (`main` en vez de `develop`, y notas sobre Staging/Swagger).
