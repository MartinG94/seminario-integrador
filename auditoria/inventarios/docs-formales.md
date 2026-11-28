# Inventario de Auditoría — Grupo `docs-formales`

> **Fecha de auditoría:** 27/11/2026  
> **Modo:** Solo lectura (contrastado contra `auditoria/registro-canonico.md`, código y tests del repositorio).  
> **Archivos auditados:** 5 (`docs/formales/Estudio_Inicial.docx`, `docs/formales/Estudio_Inicial.pdf`, `docs/formales/Plan_de_Proyecto.docx`, `docs/formales/Plan_de_Proyecto.pdf`, `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`).

---

## 1. `docs/formales/Estudio_Inicial.docx`

- **Ruta:** `docs/formales/Estudio_Inicial.docx`
- **Extensión:** 337 párrafos totales (296 no vacíos), 3 tablas, 5.406 palabras
- **Última modificación (`git log`):** `2026-09-06` (commit `d3ab31f`)
- **Tema que cubre:** Estudio Inicial del dominio A.V.E.I.T., estructura organizacional, marco normativo 2018 vs. 2026, procesos disciplinarios, recursos informáticos y problemas/oportunidades.
- **Quién lo lee:** cátedra / equipo
- **Qué pasa si desaparece:** alguien pregunta (es uno de los entregables formales exigidos por la Guía de Documentación UTN FRC, aunque el registro canónico indica que existe una versión posterior `v1.5.0` fuera del repositorio en `Documentación Actual Humana\Estudio_Inicial.docx`).
- **Clasificación:** **3. Redundante e incompleto** — Redundante con `docs/formales/Estudio_Inicial.pdf` (mismo contenido textual `v1.0.1`) y con la versión externa `Documentación Actual Humana\Estudio_Inicial.docx` (`v1.5.0` registrada en `auditoria/registro-canonico.md §5.1`, frente a la cual este archivo del repo queda desactualizado en `v1.0.1`). Incompleto respecto de las observaciones docentes de Sprint 0 (`#1` a `#5` del registro): mantiene placeholders sin completar en carátula (`"Acá debería ir la carátula"`, `"Fondo-Imagen-Integrantes"`, `"DD/MM/AAAA"`, `"Nombre provisional, en discusión"`), describe procesos TO-BE mediados por SGD-AVEIT en lugar de AS-IS y omite técnicas y fuentes detalladas del relevamiento.
- **Contradicciones con el registro:**
  - **Acrónimo del sistema:** en carátula dice `SDG-AVEIT – (Nombre provisional, en discusión)`; el registro (`§3`) establece `SGD-AVEIT`.
  - **Historial de versiones:** este archivo registra solo `1.0.0` (15/08/2026) y `1.0.1` (31/08/2026); el registro (`§5.1`) documenta para `Documentación Actual Humana\Estudio_Inicial.docx` las versiones `v1.0.0` a `v1.5.0` (hasta 18/08/2026).
  - **Votación nominal del TD:** el Proceso 3 y la sección 4.2 describen *"emitir votos nominales fundados"* y *"Votación y Dictamen del Tribunal de Disciplina"*; el registro (`§1.2 #23`, `§1.3 #24`, `§1.4 #31`, `§2`, `§3`) indica que la votación nominal fue descartada por el PO el 07/10/2026 y reemplazada por firma colegiada de 3 años sociales activos (`4.º`, `5.º`, `6.º`) en `Resolucion.firmantes`.
  - **Categorías de socios:** define `Socios Juniors` (1.º y 2.º año) y `Socios Seniors` (3.º a 6.º año); el código y el registro (`§3`) modelan `PASSIVE` (años sociales 1, 2, 3) y `ACTIVE` (años sociales 4, 5, 6).
  - **Expresión ambigua:** utiliza *"cómputo algorítmico de puntajes"* en el objetivo de carátula; el registro (`§1.1 #8`) consigna observación docente para reemplazarla por reglas de negocio precisas.
  - **Validación normativa 2018 vs. 2026:** declara que 2018 es el último reglamento formalmente aprobado por Asamblea pero adopta 2026 sin documentar quién valida institucionalmente su uso (observación docente `#3` del registro).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Describe como parte del flujo/oportunidades la **votación nominal fundada** (no implementada / descartada por PO).
  - Describe en Proceso 4 y §4.2 el **disparo automático de alertas escalonadas** (`-7` preventiva amarilla y `-10` crítica roja notificando a socio, CD y Asamblea) (el registro `§2` la marca **parcial**: falta conectar `ThresholdAlertEngine` al flujo productivo y exponer endpoint/vista).
  - Describe en Proceso 3 y §4.2 un **repositorio unificado de antecedentes y jurisprudencia interna** con motor de búsqueda categorizado (el registro `§2` lo marca **parcial**: solo existe búsqueda de antecedentes dentro de valoraciones T03).
  - Describe en Proceso 5 y §4.2 la **generación instantánea con un clic de Balances Cuatrimestrales Art. 137 en formatos ejecutivos** (el registro `§2` lo marca **parcial**: falta exportación PDF y permisos RBAC específicos en 6 vistas de `reportes_views.py`).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Como Estudio Inicial AS-IS del dominio disciplinario, no releva el procedimiento operativo real previo (sin SGD-AVEIT) ni las fuentes/entrevistados del relevamiento (observaciones `#1` y `#2`). Tampoco refleja el criterio operativo vigente de resolución colegiada sin votación nominal (observación `#23` y `#31`).
- **Referencias rotas:** No cita rutas de archivos del repositorio ni funciones de código. Presenta placeholders sin completar (`"Acá debería ir la carátula"`, `"Fondo-Imagen-Integrantes"`, `"DD/MM/AAAA"`).

---

## 2. `docs/formales/Estudio_Inicial.pdf`

- **Ruta:** `docs/formales/Estudio_Inicial.pdf`
- **Extensión:** 20 páginas, 5.621 palabras
- **Última modificación (`git log`):** `2026-09-06` (commit `d3ab31f`)
- **Tema que cubre:** Exportación en formato PDF del Estudio Inicial `v1.0.1` de A.V.E.I.T. y sus procesos disciplinarios.
- **Quién lo lee:** cátedra / nadie (copia renderizada del `.docx` homónimo en la misma carpeta).
- **Qué pasa si desaparece:** nada (su fuente textual idéntica existe en `docs/formales/Estudio_Inicial.docx`).
- **Clasificación:** **3. Redundante con `docs/formales/Estudio_Inicial.docx` e incompleto** — Contiene el mismo texto que `docs/formales/Estudio_Inicial.docx` (`v1.0.1`, ambos desactualizados respecto de `v1.5.0` en `Documentación Actual Humana\Estudio_Inicial.docx` citado en el registro `§5.1`) y arrastra las mismas omisiones de Sprint 0 (`#1`–`#5`).
- **Contradicciones con el registro:**
  - Idénticas a `docs/formales/Estudio_Inicial.docx`: acrónimo `SDG-AVEIT – (Nombre provisional, en discusión)`, historial solo hasta `1.0.1` (31/08/2026) frente a `v1.5.0` del registro `§5.1`, votación nominal fundada en Proceso 3 y §4.2, categorías `Juniors (1.º–2.º)` / `Seniors (3.º–6.º)` frente a `PASSIVE (1–3)` / `ACTIVE (4–6)`, uso de *"cómputo algorítmico"* y falta de validación institucional documentada para el Reglamento 2026.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Idénticas a `docs/formales/Estudio_Inicial.docx`: votación nominal fundada (descartada por PO), alertas automáticas `-7` / `-10` (parcial), repositorio de antecedentes/jurisprudencia (parcial) y balances cuatrimestrales ejecutivos con un clic (parcial).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Idéntico a `docs/formales/Estudio_Inicial.docx`: no describe el proceso AS-IS sin SGD-AVEIT, no documenta fuentes/entrevistados del relevamiento y no refleja la eliminación de la votación nominal.
- **Referencias rotas:** Sin rutas de código. Conserva placeholders sin completar en portada y carátula (`"Acá debería ir la carátula"`, `"Fondo-Imagen-Integrantes"`, `"DD/MM/AAAA"`).

---

## 3. `docs/formales/Plan_de_Proyecto.docx`

- **Ruta:** `docs/formales/Plan_de_Proyecto.docx`
- **Extensión:** 341 párrafos totales (291 no vacíos), 5 tablas, 3.725 palabras
- **Última modificación (`git log`):** `2026-09-06` (commit `d3ab31f`)
- **Tema que cubre:** Plan de Proyecto (`v2.0.0`) de SGD-AVEIT con alcance funcional (`RF-01` a `RF-15`), trazabilidad normativa (`RN-01` a `RN-10`), RNF, restricciones (`RES-01` a `RES-06`), Scrumban, equipo y `CU-01`.
- **Quién lo lee:** cátedra / equipo
- **Qué pasa si desaparece:** alguien pregunta (es entregable formal exigido por la Guía de Documentación UTN FRC y es la copia editable más avanzada del Plan de Proyecto dentro del repositorio).
- **Clasificación:** **3. Redundante e incompleto** — Redundante con `docs/formales/Plan_de_Proyecto.pdf` (donde el PDF queda desactualizado en `v1.0.1`). Incompleto e internamente inconsistente:
  - El historial de revisiones (`v2.0.0`, fila duplicada dos veces seguidas) declara incorporar *"especificación formal de casos de uso Cockburn en 2 columnas con BDD Gherkin"* (y el registro `§5.2` refiere `CU-01 a CU-12`), pero el documento solo incluye `CU-01` en un único párrafo corrido, sin tabla de 2 columnas ni escenarios Gherkin.
  - Conserva sin limpiar el bloque antiguo de `v1.0.1` en la primera mitad (carátula con `"SDG-AVEIT – (Nombre provisional, en discusión)"`, `"DD/MM/AAAA"`, `"(A definir logo y variantes)"`, tabla de RNF con celda `"-"` en `Base de Datos Relacional`, `Python` listado como RNF #2 y `"Prohibición absoluta de UPDATE directos"` como RNF #4) y anexa los bloques de `v2.0.0` al final con etiquetas literales de herramientas/skills de IA en los títulos (`(systemClassifier)`, `(requirementsExtractor)`, `(useCaseExtractor)`).
  - La tabla de revisión `1.0.1` tiene fecha `31/08/2026` anterior a la `1.0.0` del `01/09/2026` (mientras el registro `§5.2` consigna `02/09/2026` para `1.0.1` en `Documentación Actual Humana\Plan_de_Proyecto.docx`).
- **Contradicciones con el registro:**
  - **Acrónimo del sistema:** la carátula dice `SDG-AVEIT – (Nombre provisional, en discusión)` (contradice `SGD-AVEIT` del registro `§3`, aunque el encabezado superior sí dice `Grupo 04 — SGD-AVEIT`).
  - **Votación nominal del TD:** incluye `RF-09: Registro Nominal de Votación del TD` (*"Cómputo formal de mayoría absoluta en votación nominal individual de miembros habilitados"*, Must Have) y *"Registrar Resoluciones y Votaciones"*; el registro (`§1.2 #23`, `§1.3 #24`, `§1.4 #31`, `§2`, `§3`) indica que fue eliminada por el PO el 07/10/2026 y reemplazada por firma colegiada en `Resolucion.firmantes`.
  - **Stack Frontend:** en el perfil de Nicolás Rosales declara `Tailwind CSS`; el registro (`§3`) y el código usan **Angular 14.2+ + TypeScript + Angular Material** (Material Dashboard PRO).
  - **Mecanismo de libro mayor e inmutabilidad:** `RF-12` y `RNF-02` afirman que los saldos se impactan *"mediante triggers en MySQL en la tabla `auditoria_puntos`"*; el registro (`§2` y `§3`) verifica que el código usa el modelo Django `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly) y `PuntajeAplicado` (`tribunal_puntajeaplicado`), sin triggers MySQL ni tabla `auditoria_puntos`.
  - **Expresión ambigua remanente:** la carátula y el bloque `v1.0.1` de alcances mantienen *"cómputo algorítmico"* (contradiciendo la propia nota de `v2.0.0` que afirma haberla erradicado y la observación docente `#8`).
  - **Estados del expediente en `CU-01`:** usa nombres literales `'En período de subida de justificaciones'`, `'Las justificaciones están siendo revisadas'` y `'En Revisión'`; el registro (`§3`) documenta los valores canónicos de `EstadoExpedienteEnum` (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`).
  - **Fecha de `v1.0.1` y número de grupo:** este archivo dice `Grupo 04` y `1.0.1` del `31/08/2026`; el registro (`§3` y `§5.2`) reporta para `Documentación Actual Humana\Plan_de_Proyecto.docx` `Grupo 13` en carátula y `1.0.1` del `02/09/2026`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - `RF-09` (*Registro Nominal de Votación del TD*, Must Have): **no implementada (descartada por PO)**.
  - `RF-13` (*Disparo de Alertas Escalonadas `-7` y `-10`*, Must Have): **parcial** en el registro (`§2`).
  - `RF-14` (*Emisión instantánea en PDF del Balance Cuatrimestral Art. 137*, Must Have): **parcial** en el registro (`§2`, solo existe JSON y CSV, falta PDF y permisos RBAC en 6 vistas).
  - `RNF-04` (*latencia P95 < 1.5 s*) y validación de Staging (`RES-04`, `RES-05`): pruebas de carga (`SCRUM-65`) **no implementadas** y Staging/Homologación (`SCRUM-66`/`SCRUM-67`) **no verificables** según el registro (`§2` y `§6`).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No cubre módulos implementados que pasaron a formar parte del producto (`§2` del registro): **Eventos, Reuniones y Asistencia** (`SCRUM-50`/`SCRUM-86`), **Apelación y Adecuación de T01** (`SCRUM-70`), **Exclusión fundada de involucrados** (`SCRUM-102`), **Enmienda trazable de resoluciones con contra-asientos** (`SCRUM-103`), **Composición del Tribunal, apartamiento por conflicto y suplencias** (`SCRUM-54`), **ABM de Reglamentos** con auditoría inmutable, **Calendario Institucional** de feriados/plazos y **Panel de Administración** de parámetros y miembros del TD (`SCRUM-91`). Tampoco define la matriz de roles RBAC (`SOCIO`, `FISCALIZADORA`, `CD`, `TD`, `ADMIN`) pese a la observación docente `#11`.
- **Referencias rotas:**
  - Menciona la tabla MySQL `auditoria_puntos` en `RNF-02`, que no existe en el esquema del código (`backend/expedientes/models.py` usa `expedientes_asiento_libro_mayor`).
  - Conserva placeholders sin completar (`"DD/MM/AAAA"`, `"(A definir logo y variantes)"`, `"-"`) y restos de prompts/herramientas (`systemClassifier`, `requirementsExtractor`, `useCaseExtractor`).

---

## 4. `docs/formales/Plan_de_Proyecto.pdf`

- **Ruta:** `docs/formales/Plan_de_Proyecto.pdf`
- **Extensión:** 12 páginas, 961 palabras
- **Última modificación (`git log`):** `2026-09-06` (commit `d3ab31f`)
- **Tema que cubre:** Exportación PDF preliminar (`v1.0.1`) del Plan de Proyecto de SGD-AVEIT, anterior a la reestructuración `v2.0.0`.
- **Quién lo lee:** nadie (si alguien de la cátedra o el equipo lo consulta, recibe una versión preliminar truncada).
- **Qué pasa si desaparece:** nada (su versión posterior `v2.0.0` está en `docs/formales/Plan_de_Proyecto.docx`).
- **Clasificación:** **3. Redundante con `docs/formales/Plan_de_Proyecto.docx` (desactualizado) e incompleto** — `Plan_de_Proyecto.pdf` quedó congelado en `v1.0.1` frente a `Plan_de_Proyecto.docx` (`v2.0.0`). Además está severamente incompleto: tiene carátula con `"Acá debería ir la carátula / Fondo-Imagen-Integrantes"`, fecha `"DD/MM/AAAA"`, `"(A definir logo y variantes)"`, 6 de 7 integrantes con el campo `SKILLS:` vacío, celda `"-"` en RNF #3 (`Base de Datos Relacional`), y no incluye ninguno de los cambios exigidos en Sprint 0 (`#6` a `#15` del registro).
- **Contradicciones con el registro:**
  - **Acrónimo:** `SDG-AVEIT – (Nombre provisional, en discusión)` frente a `SGD-AVEIT` (`§3`).
  - **Historial de revisiones:** solo llega a `1.0.1` con fecha `31/08/2026` (anterior a `1.0.0` del `01/09/2026`), contradiciendo `v2.0.0` (03/09/2026) registrada en `§5.2`.
  - **Votación del TD:** incluye *"Registrar Resoluciones y Votaciones"* (descartada por el PO el 07/10/2026, `§2` y `§3`).
  - **Expresión ambigua y mezcla RNF/restricciones:** mantiene *"cómputo algorítmico"* (observación `#8`), lista `Python` como RNF #2 (observación `#12`) y `"Prohibición absoluta de UPDATE directos"` como RNF #4 (observación `#13`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - *"Registrar Resoluciones y Votaciones"* (votación nominal **no implementada / descartada por PO**).
  - *"Emitir Alertas Preventivas y Críticas"* (alertas `-7`/`-10` **parcial** en `§2`).
  - *"Generar Balances Cuatrimestrales de Auditoría"* Art. 137 (**parcial** en `§2`, falta PDF y permisos RBAC).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Omite todo el desglose `RF-01..RF-15`, `RN-01..RN-10`, roles/permisos RBAC, restricciones `RES-01..RES-06`, detalle operativo de Scrumban y todos los módulos implementados listados en `Plan_de_Proyecto.docx` (Eventos/Asistencia, Apelaciones T01, Enmiendas, Exclusiones, Composición/Suplencias TD, ABM Reglamentos, Calendario Institucional, Panel Admin).
- **Referencias rotas:** Sin rutas de código. Presenta múltiples placeholders sin completar (`"Acá debería ir la carátula"`, `"Fondo-Imagen-Integrantes"`, `"DD/MM/AAAA"`, `"(A definir logo y variantes)"`, `"-"` y `SKILLS:` vacíos).

---

## 5. `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`

- **Ruta:** `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`
- **Extensión:** 181 líneas
- **Última modificación (`git log`):** `2026-10-21` (commit `87d7df1`)
- **Tema que cubre:** Plan de pruebas de aceptación (UAT), casos de borde y dictamen de cierre QA para la historia `SCRUM-50 / S3-06` (reuniones, asistencia y consolidación 3:1 de apercibimientos).
- **Quién lo lee:** equipo (eventualmente nadie tras el cierre de Sprint 3; no es uno de los 5 entregables formales definidos en la Guía de Documentación UTN FRC).
- **Qué pasa si desaparece:** nada (los tests automatizados reales viven en `backend/tests/expedientes/` y `frontend/src/app/pages/eventos/`, y la documentación formal de UAT según la Guía corresponde a Definición del Producto).
- **Clasificación:** **1. Residuo de fabricación** — Es un reporte interno de cierre de Fase 5 emitido durante Sprint 3 (14/10/2026) para una única rama de feature (`feature/US-S3-06-sanciones-reuniones-solicitudes`), ubicado en `docs/formales/` aunque no constituye un entregable formal de la Guía de Documentación (`registro-canonico.md §4`), y presenta referencias rotas a archivos de test y columnas SQL inexistentes.
- **Contradicciones con el registro:**
  - **Calendario de Sprint 3:** declara `Sprint 3 (07/10 al 20/10/2026)`; el registro (`§1.3 #26`) advierte la inconsistencia abierta entre inicio el `07/10` y el `08/10`.
  - **Identificador de autenticación:** en §2.2 y Caso UAT-1 (paso 1.1) utiliza `Legajo / Identificador` (con los legajos UTN de los integrantes del equipo: `87414`, `403655`, `408917`, `85194`, `74907`) como credencial de login; el registro (`§2` y `§3`) indica que la autenticación vigente opera por `N.º de Socio` (`numero_socio`).
  - **Nomenclatura de roles RBAC:** en §2.2 y UAT-5 usa el rol `Revisores de Cuentas`; el registro (`§3`) señala que el enum en código sigue siendo `FISCALIZADORA`.
  - **Esquema de BD y migraciones:** declara `migración 0012 aplicada` (el repositorio cuenta con migraciones posteriores, p. ej. `0033_drop_legacy_socio_fks_eventos.py`) y afirma en §1.1, UAT-4 paso 4.4 y §6 verificar la columna `saldo` en la tabla `socios_socio`, pero `backend/socios/models.py` no define tabla `socios_socio` ni columna `saldo` (los saldos se gestionan vía `PuntajeGeneral`, `PuntajeAplicado` y `AsientoLibroMayor`).
  - **Conteo de pruebas:** declara *"537+ tests pasando en verde"* en backend y *"175+ tests pasando en verde"* en frontend al 14/10/2026; el registro (`§6`) marca la ejecución viva de suites como **No verificable** en esta auditoría (y el conteo corresponde a una foto histórica de Sprint 3).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - No atribuye como implementada ninguna funcionalidad que el registro marque como no implementada; `SCRUM-50` figura como **implementada** en `registro-canonico.md §2`. Sin embargo, respecto de la acumulación de apercibimientos 3:1 (`SCRUM-61`), el documento valida la consolidación 3:1 en `WarningAccumulationService` (implementada), mientras el registro (`§2`) aclara que la alerta formal previa a autoridades ante inminencia de descuento `-1 pt` sigue **parcial**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Por su alcance acotado a `SCRUM-50`, no cubre el rediseño UI posterior de Eventos y Asistencia (`SCRUM-86`) ni las pruebas E2E agregadas posteriormente en `test_qa_e2e_eventos_sanciones.py` (no listado en §5.1).
- **Referencias rotas:**
  - `test_meeting_compliance.py` (§5.1, línea 150): **archivo inexistente** en `backend/`.
  - `test_warning_service.py` (§5.1, línea 151): **archivo inexistente** en `backend/` (existen `test_evento_services.py` y `test_apercibimientos_consolidation.py`).
  - Tabla `socios_socio` y columna `saldo` (§1.1 línea 26, UAT-4 paso 4.4 línea 113, §6 línea 173): **inexistentes** en `backend/socios/models.py` (`socios_socio` solo aparece en migración histórica de limpieza `0033_drop_legacy_socio_fks_eventos.py` y scripts de seed/performance).
  - Rama `feature/US-S3-06-sanciones-reuniones-solicitudes` (línea 8): referencia a rama puntual de Sprint 3.

---

## Decisiones pendientes

1. **Sincronización entre `docs/formales/` del repositorio y `Documentación Actual Humana\`:** `Estudio_Inicial.docx` en `docs/formales/` está en `v1.0.1` (31/08/2026), mientras el registro canónico (`§5.1`) documenta una versión `v1.5.0` (18/08/2026) en `Documentación Actual Humana\Estudio_Inicial.docx`; del mismo modo, `Plan_de_Proyecto.docx` en `docs/formales/` difiere en número de grupo (`Grupo 04` vs `Grupo 13`) y fecha de `v1.0.1` (`31/08/2026` vs `02/09/2026`) respecto de `Documentación Actual Humana\Plan_de_Proyecto.docx` (`§3` y `§5.2`). Debe definirse cuál es la fuente canónica editable para ambos entregables sin alterar las fechas/versiones ya presentadas.
2. **Conservación o archivado de exportaciones PDF duplicadas en `docs/formales/`:** Definir si `Estudio_Inicial.pdf` (duplicado textual `v1.0.1` del `.docx`) y `Plan_de_Proyecto.pdf` (exportación desactualizada `v1.0.1` frente al `.docx` `v2.0.0`) deben archivarse en `auditoria/archivados/` o mantenerse junto a sus fuentes editables.
3. **Destino de `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`:** Definir si este reporte de cierre QA de Sprint 3 se archiva en `auditoria/archivados/` por no ser un entregable formal de la Guía de Documentación UTN FRC, o si sus escenarios UAT deben consolidarse en el entregable formal **Definición del Producto**.
4. **Alcance de actualización de `Estudio_Inicial` y `Plan_de_Proyecto` ante las observaciones docentes de Sprint 0, Sprint 3 y Sprint 4:** Definir si se abrirá una nueva versión fechada para cerrar las observaciones `#1`–`#15`, `#23`, `#24` y `#31` (en particular la eliminación de la votación nominal, `RF-09`, `CU-01..CU-12`, limpieza de secciones `v1.0.1` remanentes y etiquetas de IA en `Plan_de_Proyecto.docx`) o si ambos documentos permanecen congelados como entregables históricos de inicio de proyecto.
