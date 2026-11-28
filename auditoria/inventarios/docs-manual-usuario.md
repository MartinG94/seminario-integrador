# Inventario y Auditoría — Grupo `docs-manual-usuario`

> **Fecha de auditoría:** 27/11/2026  
> **Modo:** Solo lectura (contrastado contra `auditoria/registro-canonico.md`).  
> **Alcance:** 11 archivos exactos (`docs/manual-usuario/README.md` y 10 PDFs en `docs/manual-usuario/pdfs/`).

---

## Resumen Ejecutivo

- **Total de archivos auditados:** 11 (1 Markdown + 10 PDFs).
- **Verificación de consolidación:** `Manual_Usuario_SGD_AVEIT_Completo.pdf` (32 páginas) es la concatenación exacta página a página de los 9 PDFs individuales (`01` a `09`, suma = 32 páginas, 0 diferencias de texto extraído).
- **Hallazgos transversales principales:**
  - Uso sistemático del nombre de rol `Revisores` / `REVISORES` en lugar del rol canónico del código `FISCALIZADORA`.
  - Ausencia de secciones formales exigidas por la guía de cátedra en el PDF consolidado (carátula general con fecha/equipo, historia de revisión, tabla de contenido, propósito del documento y configuración).
  - Mención de funcionalidades que el registro canónico marca como **parciales** (alertas de umbrales `-10`/`-7`, campana de alertas, chip `3 en alerta`, exploración libre de antecedentes, reportes sin RBAC en 6 vistas) o no verificadas (modo biométrico en asistencia, URL `https://aveit.frc.utn.edu.ar/`).
  - Omisión de funcionalidades ya **implementadas** (apelación y adecuación T01 `SCRUM-70`, censura médica en publicación, Legajo Integral, diferenciación T02 vs T03, preview PDF de resolución, bloqueo automático por conflicto de interés `IsNotInvolvedInExpediente`, rediseño completo de Eventos `SCRUM-86`).

---

## 1. `docs/manual-usuario/README.md`

- **Ruta:** `docs/manual-usuario/README.md`
- **Extensión:** 67 líneas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Índice de los 9 módulos del Manual de Usuario por rol y guía técnica de compilación de HTML a PDF.
- **Quién lo lee:** equipo
- **Qué pasa si desaparece:** alguien se equivoca (al intentar regenerar los PDFs sin conocer los scripts `render_pdfs.py` / `merge_pdfs.py`, su orden ni sus flags).
- **Clasificación:** **4. Vigente** (con discrepancias terminológicas y rutas locales no portables).
- **Contradicciones con el registro:**
  - **Roles RBAC:** nombra al rol como `Revisores` / `Revisores de Cuentas` (líneas 13, 14, 18, 20 y 21), mientras que el registro canónico (§3) establece que el identificador en el código es `FISCALIZADORA` (*"Autoridad de Subcomisión / Líder de Equipo"*).
  - **Permisos de Reportes:** indica `Reportes: TD, CD, Revisores, Admin` (línea 21), mientras que el registro canónico (§2, filas *RBAC* y *Reportes analíticos*) advierte que 6 vistas en `backend/expedientes/views/reportes_views.py` solo exigen `IsAuthenticated` sin restricción de rol específico.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - En la tabla de módulos (línea 16) atribuye al módulo 04 *"privacidad de alertas"*, cuando el registro canónico (§2) marca las alertas automáticas por umbrales (`SCRUM-62`) y por acumulación 3:1 (`SCRUM-61`) como **parciales** (sin conexión al flujo productivo ni endpoint/vista de alertas).
  - En la línea 21 referencia *Reportes y Balances*, funcionalidad marcada como **parcial** en el registro (§2).
- **Funcionalidad implementada que debería cubrir y no cubre:** Ninguna fuera de su alcance como índice y guía de compilación del directorio.
- **Referencias rotas:**
  - Línea 44: ruta local de desarrollador `c:\git\seminario-integrador\docs\manual-usuario\` (inexistente en este entorno y no portable).
  - Líneas 54 y 67: rutas locales de Google Drive `G:\My Drive\Estudios\Seminario\Manual de Usuario\` (dependientes de unidad local externa al repositorio).
  - Las rutas relativas internas al repositorio (`shared/manual-base.css`, `shared/aveit_template.py`, `scripts/render_pdfs.py`, `scripts/merge_pdfs.py`, `src/01_*.html`..`09_*.html`, `pdfs/*.pdf`) existen.

---

## 2. `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf`
- **Extensión:** 3 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Inicio de sesión con Número de Socio, navegación por menú lateral, barra superior (tema/notificaciones), cierre de sesión y avisos toast.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (su contenido está duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 1–3 y se regenera desde `src/01_Acceso_y_Navegacion.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 1–3 idénticas, ambos del `2026-11-23`; ninguno está desactualizado respecto al otro hoy, pero duplicar binarios expone a desincronización si se recompila solo uno).
- **Contradicciones con el registro:**
  - **Roles RBAC:** cita `Revisores` / `REVISORES` (pág. 2, Paso 3 y mockup de chips demo `REVISORES 85194`), mientras que el registro canónico (§3) indica que el rol en código es `FISCALIZADORA`.
  - **URL en encabezado:** muestra `https://aveit.frc.utn.edu.ar/` en págs. 2–3, cuando el registro canónico (§2 y §6) indica que el despliegue en Staging/Producción (`SCRUM-66`) es **No verificable**.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - Paso 4 (pág. 3): *"La campana alerta sobre plazos próximos a vencer y citaciones activas."* El registro canónico (§2) marca las alertas automáticas como **parciales** (sin endpoint/vista de alertas conectada al flujo productivo) y señala que la suite universal de los 10 disparadores de notificaciones no existe (solo están verificados el Outbox de email y los toasts UI).
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - Reglas de elegibilidad en el inicio de sesión por N.º de Socio (`test_login_socios_eligibility.py`) y manejo de expiración/renovación de sesión JWT.
  - El mockup de pág. 3 muestra un buscador global `"Buscar en el sistema..."` en la barra superior sin explicar si existe o cómo funciona.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (La URL `https://aveit.frc.utn.edu.ar/` no corresponde a un despliegue verificado según §6.)

---

## 3. `docs/manual-usuario/pdfs/02_Mis_Expedientes_y_Descargos.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/02_Mis_Expedientes_y_Descargos.pdf`
- **Extensión:** 4 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Consulta de saldo propio y expedientes del socio, presentación, edición y retiro de descargos T02/T03 con adjuntos, y consulta/descarga de resoluciones.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 4–7 y regenerable desde `src/02_Mis_Expedientes_y_Descargos.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 4–7 idénticas, ambos del `2026-11-23`) e **incompleto** (omite flujos implementados en el módulo *Mis Expedientes*).
- **Contradicciones con el registro:**
  - **Estados del expediente:** la tabla de pág. 2 usa etiquetas `En plazo · 74h`, `Emitido` y `En Revisión` sin explicar su correspondencia con los 6 estados canónicos del backend (§3: `creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`).
  - **Firmas colegiadas:** el mockup de resolución (pág. 4) muestra `"Firmas: G57 · G58 · G59"` sin indicar que corresponden a los 3 años sociales activos 4.º, 5.º y 6.º (`Resolucion.firmantes`, §3).
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Apelación del Formulario T01 (`SCRUM-70`):** marcada como **implementada** en `frontend/src/app/mis-expedientes/` (§2), no se menciona en el módulo.
  - **Publicación oficial protegida con censura médica (`SCRUM-60` / `SCRUM-105` / `SCRUM-106`):** marcada como **implementada** en `mis-expedientes` (§2), no se explica cómo opera la censura de datos médicos ni su visualización.
  - **Versionado inmutable de descargos (`DescargoVersion`):** solo muestra un `"Registro de Operaciones"` (pág. 4) sin detallar el historial de versiones previas.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 4. `docs/manual-usuario/pdfs/03_Reglamentos.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/03_Reglamentos.pdf`
- **Extensión:** 3 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Consulta de Reglamento Interno y Estatuto para todos los socios, y alta, edición y baja lógica de artículos para TD, CD y Admin.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 8–10 y regenerable desde `src/03_Reglamentos.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 8–10 idénticas, ambos del `2026-11-23`).
- **Contradicciones con el registro:**
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
  - Sin contradicciones funcionales respecto al registro (§2: ABM de Reglamentos implementado).
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Auditoría inmutable de artículos (`AuditoriaArticuloReglamento`):** el registro (§2) indica que el ABM cuenta con auditoría inmutable, pero el documento no menciona el registro de auditoría sobre altas, ediciones y bajas.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 5. `docs/manual-usuario/pdfs/04_Ranking_de_Socios.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/04_Ranking_de_Socios.pdf`
- **Extensión:** 3 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Consulta del ranking disciplinario de socios, filtros por subcomisión/grupo/texto, ordenamiento por saldo y detalle de expedientes del socio.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 11–13 y regenerable desde `src/04_Ranking_de_Socios.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 11–13 idénticas, ambos del `2026-11-23`).
- **Contradicciones con el registro:**
  - **Impacto de expedientes no emitidos en el saldo:** el mockup de pág. 3 muestra para el socio `74907` (saldo `+1.00`) dos expedientes: `EXP-0031/2026` (`Emitido`, `+3.00`) y `EXP-0042/2026` (`En plazo`, `-2.00`), dando a entender que un expediente en trámite impacta el saldo. Según el registro canónico (§2 *Libro Mayor Transaccional Inmutable*), solo las resoluciones emitidas impactan en el saldo definitivo.
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - Paso 2 (pág. 2): *"Puede filtrar socios en alerta desde el chip superior"* y mockup `"3 en alerta"`. El registro canónico (§2) marca las alertas automáticas por umbrales `-10` / `-7` (`SCRUM-62`) como **parciales** (motor no conectado al flujo productivo ni endpoint/vista de alertas productivas). Además, `README.md` atribuye a este módulo *"privacidad de alertas"*, tema que el PDF no desarrolla.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Legajo Integral del Socio (`socio-legajo-dialog`):** marcado como **implementado** en `frontend/src/app/ranking-socios/socio-legajo-dialog/` (§2), no se documenta en este módulo (solo cubre `expedientes-socio-dialog`).
  - **Paginación del ranking (`test_ranking_pagination.py`):** solo aparece `"10 filas"` en el mockup sin explicación operativa.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 6. `docs/manual-usuario/pdfs/05_Calendario_Institucional.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/05_Calendario_Institucional.pdf`
- **Extensión:** 3 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Consulta de feriados institucionales, simulador de vencimientos en días hábiles, carga de feriados y actualización del plazo de apelación.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 14–16 y regenerable desde `src/05_Calendario_Institucional.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 14–16 idénticas, ambos del `2026-11-23`).
- **Contradicciones con el registro:**
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
  - Sin contradicciones funcionales respecto al registro (§2: Calendario Institucional, cálculo en días hábiles y plazo parametrizable de apelación implementados).
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Versionado de calendario y excepciones (`CalendarioVersion`, `FeriadoExcepcion`)** y el efecto operativo del cierre automático de plazos vencidos (`close_expired_deadlines`, §2).
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 7. `docs/manual-usuario/pdfs/06_Crear_Expediente.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/06_Crear_Expediente.pdf`
- **Extensión:** 4 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Creación y emisión de solicitudes T01, borradores, selección multi-socio con Select2, hoja de anexo y gestión de Mis Solicitudes.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 17–20 y regenerable desde `src/06_Crear_Expediente.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 17–20 idénticas, ambos del `2026-11-23`).
- **Contradicciones con el registro:**
  - **Roles RBAC:** nombra `Revisores` en Paso 1 y en el mockup (`TD / CD / Revisores`, pág. 2), mientras que el registro canónico (§3) indica que el rol en código es `FISCALIZADORA`.
  - **Estados en Mis Solicitudes:** la tabla de pág. 4 muestra `EN DESCARGO` y `BORRADOR`, etiquetas distintas de los 6 estados canónicos del backend (§3) sin aclarar correspondencia.
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Reglas de competencias de apertura (`opening_policy.py`, §2):** no explica qué tipos de acciones o puntajes está habilitado a solicitar cada rol.
  - **Adecuación de T01 tras apelación (`AdecuacionT01` / `SCRUM-70`, §2):** no describe el flujo ante una solicitud apelada.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 8. `docs/manual-usuario/pdfs/07_Gestionar_Expedientes_TD.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/07_Gestionar_Expedientes_TD.pdf`
- **Extensión:** 5 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Operación de la Sala del Tribunal (Kanban/Tabla), visor, notificación de apertura, valoración de descargos, apartamientos/exclusiones, dictado de resolución, firma colegiada y enmiendas.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 21–25 y regenerable desde `src/07_Gestionar_Expedientes_TD.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 21–25 idénticas, ambos del `2026-11-23`) e **incompleto** (omite partes del ciclo y flujos implementados en la Sala del Tribunal).
- **Contradicciones con el registro:**
  - **6 estados del expediente:** el Kanban de pág. 2 muestra solo 4 columnas (`Creados`, `Justificando`, `En Revisión`, `Pend. Firma`) y omite dos de los 6 estados canónicos del backend (§3: `espera_resolucion` *"En espera de resolución"* y `emitido` *"Expedientes ya emitidos"*).
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - En pág. 4, el mockup incluye `"Expedientes Antecedentes — 📂 EXPLORAR..."`. El registro canónico (§2) indica que solo existe búsqueda de antecedentes dentro de valoraciones T03 (`AntecedenteT03View`), mientras que el **Repositorio de precedentes y jurisprudencia disciplinaria** dedicado (`SCRUM-68` / `SCRUM-125`) está marcado como **parcial**.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Diferenciación entre resolución de causal T02 (`SCRUM-52` / `SCRUM-101`) y valoración extraordinaria T03 (`SCRUM-53`, `valoracion-t03-panel/`):** el Paso 5 las agrupa sin distinguir ambos flujos.
  - **Revisión y adecuación de apelaciones T01 (`SCRUM-70`):** implementada también en `gestionar-expedientes/` (§2), ausente en el documento.
  - **Previsualización PDF de resolución (`test_resolution_preview_api.py`, §2):** no se menciona.
  - **Bloqueo automático por conflicto de interés (`IsNotInvolvedInExpediente`, §1.4 #32 y §2):** solo describe el apartamiento manual (Paso 6), sin mencionar la restricción automática sobre miembros involucrados.
  - **Concepto / clasificación del expediente (`test_concepto_expediente.py`, §2):** no se documenta.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 9. `docs/manual-usuario/pdfs/08_Eventos_y_Asistencia.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/08_Eventos_y_Asistencia.pdf`
- **Extensión:** 3 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Generación de eventos y reuniones institucionales, convocatoria, toma de asistencia y cierre con generación automática de expedientes.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 26–28 y regenerable desde `src/08_Eventos_y_Asistencia.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 26–28 idénticas, ambos del `2026-11-23`) e **incompleto** (el propio documento declara en pág. 2: *"Vista resumida de referencia (módulo en proceso de rediseño)"*).
- **Contradicciones con el registro:**
  - **Estado del módulo:** el PDF afirma *"módulo en proceso de rediseño"* (pág. 2), mientras que el registro canónico (§2) marca *"Eventos, Reuniones, Asistencia (Strategy) y rediseño UI (`SCRUM-50` / `SCRUM-86`)"* como **implementada**.
  - **Roles RBAC:** usa `Revisores` en Paso 1 y en el mockup (`CD / TD / Revisores`, pág. 2), mientras que el registro canónico (§3) indica que el rol en código es `FISCALIZADORA`.
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - En pág. 3, el mockup indica `"Planilla Nominal de Asistencia · Modo Manual / Biométrico"`. El registro canónico (§2) no registra integración biométrica alguna.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - Flujo completo del rediseño UI ya implementado (`SCRUM-86`, `frontend/src/app/pages/eventos/asistencia-evento/`).
  - La acción `"FIJAR FIN"` mostrada en el mockup de pág. 3 sin explicación en los pasos, y el criterio de cada estado de asistencia (`Presente`, `Ausente Injustificado`, `Tardanza Leve`).
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 10. `docs/manual-usuario/pdfs/09_Reportes_y_Administracion.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/09_Reportes_y_Administracion.pdf`
- **Extensión:** 4 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Consulta y exportación CSV de reportes y balance institucional, edición de parámetros del sistema y gestión de miembros del Tribunal de Disciplina.
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (duplicado en `Manual_Usuario_SGD_AVEIT_Completo.pdf` págs. 29–32 y regenerable desde `src/09_Reportes_y_Administracion.html`).
- **Clasificación:** **3. Redundante con `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`** (págs. 29–32 idénticas, ambos del `2026-11-23`).
- **Contradicciones con el registro:**
  - **Control de acceso a Reportes:** Paso 1 (pág. 2) declara acceso para *"Roles TD, CD, Revisores y Admin"*, mientras que el registro canónico (§2, filas *RBAC* y *Reportes analíticos*) señala que 6 vistas en `backend/expedientes/views/reportes_views.py` (`ReportesT01View`, `ReportesReunionesView`, `ReportesSubcomisionesListView`, `ReportesSubcomisionView`, `ReportesHistoricoRecordsView`, `ExpedienteClasificacionPatchView`) solo exigen `IsAuthenticated` sin restricción de rol específico.
  - **Roles RBAC:** usa `Revisores` en Paso 1 y en el mockup (pág. 2), mientras que el registro canónico (§3) indica que el rol en código es `FISCALIZADORA`.
  - **URL en encabezado:** `https://aveit.frc.utn.edu.ar/` (despliegue **No verificable** según §6).
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - **Reportes analíticos y Balance Cuatrimestral Art. 137 (`SCRUM-63` / `SCRUM-124`):** marcado como **parcial** en el registro (§2: falta exportación a PDF del balance y RBAC en 6 vistas; el PDF solo muestra `EXPORTAR CSV` e `IMPRIMIR`, sin prometer exportación PDF).
  - **Umbrales y alerta preventiva (`SCRUM-62`):** Paso 4 (pág. 3) presenta la configuración de `"Umbral crítico (fijo) -10 puntos"`, `"Umbral preventivo -7 puntos"` y `"Alerta preventiva activa / Inactiva"`. Aunque el ABM de parámetros está implementado (`SCRUM-91`), el registro canónico (§2) marca las alertas automáticas por umbrales como **parciales** (motor `ThresholdAlertEngine` no conectado al flujo productivo ni vista/endpoint de alertas).
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - Uso del botón `"IMPRIMIR"` presente en el mockup (pág. 2) y detalle operativo de las pestañas `"Solicitudes"`, `"Reuniones"` y `"Subcomisiones"`.
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` no verificable según §6.)

---

## 11. `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`

- **Ruta:** `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`
- **Extensión:** 32 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Consolidado único en PDF del Manual de Usuario de SGD-AVEIT (concatenación exacta de los 9 módulos `01` a `09`).
- **Quién lo lee:** usuario final / cátedra
- **Qué pasa si desaparece:** alguien pregunta (es el entregable consolidado de Manual de Usuario referenciado en `registro-canonico.md` §5.5, aunque puede reconstruirse desde `01..09` mediante `scripts/merge_pdfs.py`).
- **Clasificación:** **3. Incompleto** (respecto a las secciones obligatorias de la guía de cátedra en `registro-canonico.md` §4 y por heredar el módulo 08 incompleto) y **redundante con `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf` .. `09_Reportes_y_Administracion.pdf`** (concatenación exacta con 0 diferencias de texto, ambos del `2026-11-23`).
- **Contradicciones con el registro:**
  - Hereda todas las contradicciones relevadas en los capítulos `01` a `09`:
    - Rol `Revisores` / `REVISORES` en lugar de `FISCALIZADORA` (§3) en págs. 2, 18, 27 y 30.
    - Etiquetas de estado en tablas/Kanban (`En plazo`, `EN DESCARGO`, `BORRADOR`, Kanban de 4 columnas) sin correspondencia con los 6 estados canónicos del backend (§3).
    - Capítulo 04 (pág. 13): expediente `En plazo` apareciendo como parte del saldo del socio, en contradicción con el Libro Mayor (§2).
    - Capítulo 08 (pág. 27): afirma que el módulo está *"en proceso de rediseño"*, cuando el registro (§2) marca `SCRUM-50` / `SCRUM-86` como **implementada**.
    - Capítulo 09 (pág. 30): declara acceso a Reportes restringido a `TD, CD, Revisores y Admin`, mientras 6 vistas de `reportes_views.py` solo exigen `IsAuthenticated` (§2).
    - Encabezado `https://aveit.frc.utn.edu.ar/` en todas las páginas de contenido cuando el despliegue Staging/Producción es **No verificable** (§6).
    - Paginación reiniciada por capítulo (`1 de 2`, `1 de 3`, etc.) en lugar de numeración continua del documento completo.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - Campana de alertas por plazos y citaciones (pág. 3) y filtro `"3 en alerta"` en Ranking (pág. 12), frente a alertas marcadas como **parciales** (`SCRUM-61`, `SCRUM-62`, §2).
  - Botón `"EXPLORAR..."` antecedentes en Sala del Tribunal (pág. 24), frente a repositorio libre de precedentes marcado como **parcial** (`SCRUM-68` / `SCRUM-125`, §2).
  - `"Modo Manual / Biométrico"` en asistencia (pág. 28), sin evidencia en el registro (§2).
  - Configuración de alerta preventiva (pág. 31) y Reportes & Balance (págs. 30–31), ambos marcados como **parciales** en §2.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - **Secciones obligatorias según Guía de Cátedra (`registro-canonico.md` §4 — Anexo Guía: Manual de Usuario):** Carátula formal del documento completo (con fecha/equipo/versión), Historia de Revisión, Tabla de Contenido / Índice general, Propósito del documento y sección de Configuración.
  - **Funcionalidades implementadas omitidas en los módulos:** apelación y adecuación de T01 (`SCRUM-70`), censura médica en publicación oficial (`SCRUM-60` / `SCRUM-105` / `SCRUM-106`), Legajo Integral del socio (`socio-legajo-dialog`), diferenciación entre resolución de causal T02 (`SCRUM-52`) y valoración extraordinaria T03 (`SCRUM-53`), preview PDF de resolución, bloqueo automático por conflicto de interés (`IsNotInvolvedInExpediente`), competencias de apertura T01 (`opening_policy.py`), elegibilidad de login y detalle del rediseño de Eventos & Asistencia (`SCRUM-86`).
- **Referencias rotas:** Ninguna referencia a archivos del repositorio. (URL `https://aveit.frc.utn.edu.ar/` en encabezados: despliegue no verificable según §6.)

---

## Decisiones pendientes

1. **Coexistencia de PDFs individuales (`01..09`) y PDF consolidado (`Manual_Usuario_SGD_AVEIT_Completo.pdf`) en el repositorio:** definir si se conservan los 10 binarios PDF versionados en Git o solo el consolidado (o ninguno si se generan bajo demanda desde `src/*.html`).
2. **Alineación formal con la Guía de Cátedra (`registro-canonico.md` §4):** definir si el Manual de Usuario consolidado incorporará carátula general con fecha y versión, tabla de historial de revisiones, tabla de contenido, propósito del documento, sección de configuración y numeración continua de páginas.
3. **Unificación terminológica del rol `FISCALIZADORA` vs `Revisores`:** definir si la documentación de usuario adopta la denominación del código (`FISCALIZADORA` / *Autoridad de Subcomisión*) o si el código/interfaz formalizará otro nombre, manteniendo consistencia con el resto de los entregables.
4. **Tratamiento de funcionalidades parciales o no verificadas en los mockups del manual:** definir cómo reflejar la campana de alertas, el chip `"3 en alerta"`, el toggle de alerta preventiva, el botón `"EXPLORAR..."` antecedentes, la mención `"Modo Manual / Biométrico"` y la URL `https://aveit.frc.utn.edu.ar/` respecto al estado real verificado en `registro-canonico.md`.
5. **Alcance de actualización de capítulos incompletos u omisiones:** definir si se ampliarán los capítulos `02`, `04`, `06`, `07`, `08` y `09` para cubrir las funcionalidades ya implementadas omitidas (apelación T01 `SCRUM-70`, censura médica, Legajo Integral, T02 vs T03, bloqueo por conflicto de interés y rediseño finalizado de Eventos `SCRUM-86`).
6. **Rutas locales hardcodeadas en `docs/manual-usuario/README.md`:** definir qué criterio usar para las rutas locales (`c:\git\...` y `G:\My Drive\...`) documentadas en la guía de compilación.
