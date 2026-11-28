# Historial de Decisiones de Documentación — SGD-AVEIT

> **Regla:** Este archivo es incremental (solo agregar entradas nuevas con su fecha real). No se modifican decisiones históricas.

---

## 2026-11-27

### D-01: Línea base de autoridad en lo más avanzado (código y tests del repositorio)
- **Decisión:** Mantener como línea base de verdad lo más avanzado actualmente en el proyecto, es decir, el código y los tests del repositorio (`regularidadDocs`, commit `6a60167` del `23/11/2026`), dejando [`auditoria/registro-canonico.md`](registro-canonico.md) y [`auditoria/traspaso-sprint6.md`](traspaso-sprint6.md) anclados en el estado real del repositorio sin modificarlos por ahora con reajustes provenientes de Jira.
- **Motivo:** Al cruzar [`auditoria/traspaso-sprint6.md`](traspaso-sprint6.md) contra el tablero vivo de Jira (`SCRUM`, 81 issues), se constató que Jira tuvo una reestructuración el `05/11/2026` (`MACRO-01` a `MACRO-08`, `SCRUM-89`–`SCRUM-129`) con estados administrativos desactualizados respecto del código real (por ejemplo, `SCRUM-129` Manual de Usuario y subtareas `SCRUM-99`–`SCRUM-113` figuran `Por hacer` pese a estar implementados en el repo, mientras `SCRUM-62` figura `Finalizado` sin integración productiva).
- **Acción:** Se deja el criterio regido por el código/tests del repositorio y se registran los desfasajes concretos entre Jira, documentación y código en [`auditoria/pendientes.md`](pendientes.md) para su resolución en Sprint 6 / cierre administrativo.

### D-02: Conservación/actualización de specs `001` y `003`, y traslado de la partición del rol `FISCALIZADORA` al Sprint 6
- **Decisión:**
  1. Conservar y completar `specs/001-walking-skeleton/spec.md`, `specs/001-walking-skeleton/plan.md` y `specs/003-monitorear-solicitudes-t01/spec.md` (en lugar de archivarlos), actualizándolos al estado real del código por ser las únicas especificaciones en `specs/` para Login/JWT, RBAC base, Socios, Ranking y Mis Solicitudes T01.
  2. Mantener `FISCALIZADORA` como el rol vigente documentado para la entrega actual (coherente con el código en `backend/socios/models.py` y `frontend/src/app/services/auth.service.ts`), y trasladar formalmente al Sprint 6 la partición de `FISCALIZADORA` en `AUTORIDAD_SC` + `REVISORES` (y vista `403` dedicada de `SCRUM-121`/`SCRUM-122`).
- **Impacto:** Se actualizan [`auditoria/evaluacion_documentacion.md`](evaluacion_documentacion.md), [`auditoria/propuesta-destinos.md`](propuesta-destinos.md) (casillas pre-marcadas `[x] aprobar` para `001`/`003`), [`auditoria/traspaso-sprint6.md`](traspaso-sprint6.md), [`auditoria/registro-canonico.md`](registro-canonico.md) y [`auditoria/pendientes.md`](pendientes.md).

### D-03: Ejecución de edición controlada — archivo, alineación canónica y trazabilidad Sprint 6
- **Decisión:** Ejecutar exclusivamente las acciones aprobadas (`[x] aprobar`) en [`auditoria/propuesta-destinos.md`](propuesta-destinos.md) más la corrección explícita de `docs/gestion-proyecto/notasPO.md` solicitada por el usuario, agrupadas en commits por tipo de corrección:
  1. **Archivo y cuarentena (29 archivos, 0 borrados):** Mover 18 archivos aprobados a `auditoria/archivados/` y 11 archivos de 6B (propuestos para eliminación tras un sprint sin reclamos) a `auditoria/archivados/cuarentena/` conforme a la Regla 9 de `AGENTS.md`, documentando origen y motivo en [`auditoria/archivados/LEEME.md`](archivados/LEEME.md) (commit `4d0d3a2`).
  2. **Alineación de gobernanza, guías técnicas y `notasPO.md` (13 archivos):** Eliminar menciones a votación nominal, corregir nombres de modelos/rutas (`AsientoLibroMayor`, `PuntajeAplicado`, `SystemParameterChange`, `EmailOutbox`, `numero_socio`), agregar funcionalidad implementada respaldada por el registro (ABM Reglamentos, `SCRUM-86`, `SCRUM-93`, `SCRUM-129`, `NotificationCenter`) y marcar parciales como `"trasladada al Sprint 6"` enlazando a [`traspaso-sprint6.md`](traspaso-sprint6.md) (commit `1a761ec`).
  3. **Alineación de especificaciones, Modelo de Dominio, BPMN y Seguimiento (5 archivos):** Alinear `RBAC-SGD-AVEIT.md`, `ERS-SGD-AVEIT.md`, `MODELO_DOMINIO_SGD_AVEIT.md`, `BPMN_Proceso_Operativo_Tribunal.md` y `Seguimiento de Proyecto.md` (preservando inmutables las fechas históricas `v1.0.0`–`v1.3.0`) a 6 estados canónicos, firma colegiada sin votación nominal, `PASSIVE`/`ACTIVE`, rol `FISCALIZADORA` vigente y traspaso al Sprint 6 (commit `2879cd4`).
  4. **Sincronización de specs SDD aprobadas (19 archivos):** Actualizar solo los archivos `specs/` aprobados en 7A/7C con discrepancias verificadas (commit `6cec57f`).
- **Motivo:** Erradicar contradicciones con el código real, referencias rotas y promesas de funcionalidades incompletas antes de la presentación y del inicio del Sprint 6, respetando estrictamente la prohibición de borrar archivos y la inmutabilidad de fechas históricas.
- **No modificado / pendiente:** No se modifican archivos sin casilla `[x]` en `propuesta-destinos.md` (`docs/manual-usuario/*`, `.github/ISSUE_TEMPLATE/tarea_sprint.md`, `specs/010-optimizacion-rendimiento/memory_audit_report.md`, ni los 15 `specs/*/tasks.md` de 7B) ni los `.docx` binarios (`Estudio_Inicial.docx`, `Plan_de_Proyecto.docx`), los cuales quedan registrados en [`auditoria/pendientes.md`](pendientes.md).

### D-04: Unificación y actualización agéntica de `Estudio_Inicial.docx` y `Plan_de_Proyecto.docx` en `docs/formales/`
- **Decisión:** Adoptar como base en `docs/formales/` las últimas versiones presentadas de `Documentación Actual Humana` (`Estudio_Inicial.docx` v1.5.0 y `Plan_de_Proyecto.docx` v2.0.0) —ya que las copias del repo estaban congeladas en `d3ab31f` del `06/09/2026`— y aplicarles mediante `python-docx`/XML las correcciones de alineación con el registro canónico, agregando `v1.6.0` y `v2.1.0` con fecha `27/11/2026` sin modificar ninguna fecha histórica previa.
- **Motivo:** Dejar el repositorio como fuente única y limpia a partir de la cual se generará la documentación final, preservando carátulas, imágenes, tablas y estilos originales sin requerir edición manual en Word.
- **Cierre:** Queda resuelto el pendiente #6 en [`auditoria/pendientes.md`](pendientes.md).

---

### 28/11/2026 — Resolución de Discrepancias de Verificación Final (`VF-01` a `VF-25`)
- **Alcance:** Corrección integral sobre los 4 entregables consolidados (`Documentación Actual Humana/Entregables/01..04*.html` + SVGs), `auditoria/traspaso-sprint6.md` y copias en `docs/` (`docs/gestion-proyecto/Seguimiento de Proyecto.md`, `docs/formales/Estudio_Inicial.docx`, `docs/formales/Plan_de_Proyecto.docx` y `docs/constitution.md`), manteniendo intacto `docs/gestion-proyecto/notasPO.md` por inmutabilidad (`AGENTS.md` Regla 5).
- **Decisiones confirmadas por el usuario:**
  1. **`VF-01` (Ranking):** Se corrige la documentación para reflejar el acceso de `SOCIO` al ranking (`/ranking-socios`), manteniendo restringido el padrón y legajos de terceros.
  2. **`VF-04` (RBAC secundario) y `VF-05` (Esquema físico en SVGs):** Se corrigen los SVGs (`dp_02`, `pp_02`) al esquema real legacy inmutable (`AGENTS.md` Regla 6); para `VF-04` se mantiene la matriz de `02_Plan` salvo Reportes Art. 137 donde `FISCALIZADORA` conserva lectura (`R`), quedando el ajuste secundario de código registrado en `auditoria/traspaso-sprint6.md`.
  3. **`VF-09` (Evidencia de pruebas):** Se retiran la mención no verificada de `76/76` y la nota obsoleta de capturas pendientes, dejando exclusivamente el inventario estático verificado (`114` archivos backend / `55` `.spec.ts` frontend) y la corrida integral viva trasladada al Sprint 6.
  4. **`VF-17` (Entregables de proceso/calidad S6):** Se incorporan OpenAPI/Swagger, gráficos oficiales de Jira y corrida integral de regresión en la nueva sección §2.1 de `auditoria/traspaso-sprint6.md`.
  5. **`VF-16`, `VF-19`, `VF-20`, `VF-21`, `VF-24`, `VF-25`:** Se restaura la fórmula obligatoria `"trasladada al Sprint 6"`, se restituyen las fechas e historiales inmutables (`v1.0.0`, `v1.4.0`, S0/S1/S2) y se eliminan menciones a artefactos internos (`auditoria/*`, `PR #xx`, `MACRO-xx`, `DESIGN`).

### 28/11/2026 — Paginación y nomenclatura de PDF entregables
- Se corrigió el desborde de contenido (capturas y diagramas cortados al pie de página) repartiendo el contenido sobrante en páginas de continuación; se actualizaron numeración de pies de página e índices (Estudio Inicial 17 págs., Plan de Proyecto 18, Seguimiento 20, Definición del Producto 31).
- Los PDF entregables adoptan la nomenclatura de la cátedra «Producto-Archivo-versión»: `SGD-AVEIT-Estudio_Inicial-v1.6.0.pdf`, `SGD-AVEIT-Plan_de_Proyecto-v2.1.0.pdf`, `SGD-AVEIT-Seguimiento_de_Proyecto-v1.5.0.pdf` y `SGD-AVEIT-Definicion_del_Producto-v2.0.0.pdf`. Los PDF previos se renombraron con `git mv` (sin borrado).
