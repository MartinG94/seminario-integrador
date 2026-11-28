# Inventario de Auditoría — Grupo `docs-analisis-proceso-actual`

> **Fecha de relevamiento:** 27/11/2026  
> **Modo:** Solo lectura sobre fuentes del grupo y `auditoria/registro-canonico.md`.  
> **Cantidad de archivos auditados:** 9 (4 Markdown, 5 PDF).

---

## 1. `docs/analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md`

- **Ruta:** `docs/analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md`
- **Extensión:** 243 líneas
- **Última modificación:** `2026-11-12`
- **Tema que cubre:** Catálogo consolidado de 7 actores (5 humanos y 2 automatizados/externos), responsabilidades, reglas de negocio y matriz RBAC de SGD-AVEIT.
- **Quién lo lee:** equipo / cátedra
- **Qué pasa si desaparece:** alguien pregunta (referenciado en `README.md` y `TASK.md`; sirve de consulta sobre competencias y actores).
- **Clasificación:** **3. Redundante con `docs/formales/Plan_de_Proyecto.docx` y la sección de roles de Definición del Producto (este archivo queda desactualizado respecto al código actual y a la eliminación de la votación nominal).**
- **Contradicciones con el registro:**
  - **Votación nominal individual:** El documento (diagrama `emitirVotoNominal()`, ficha `ACT-02` líneas 140, 147, 153 y matriz §4 línea 235) afirma que el Miembro de TD emite *"votos nominales fundados"* y realiza votación nominal. El registro canónico (§2 y §3) indica que la votación nominal individual fue **descartada por el PO el 07/10/2026** y reemplazada por editor unificado de resolución y firma colegiada de 3 integrantes habilitados representando años sociales 4.º, 5.º y 6.º (`Resolucion.firmantes`).
  - **Categorías de socio:** La ficha `ACT-01` (línea 121) divide a los socios en **Socios Juniors (1.º y 2.º año social)** y **Socios Seniors (3.º a 6.º año social)**, mientras que el registro canónico (§3) establece que el código utiliza `PASSIVE` (años sociales 1, 2, 3) y `ACTIVE` (años sociales 4, 5, 6) — denominación que el propio documento sí usa en `ACT-02` y `ACT-03`.
  - **Roles RBAC:** Define 5 actores humanos sin mapear los identificadores canónicos del código (`SOCIO`, `FISCALIZADORA`, `CD`, `TD`, `ADMIN`) y omite modelar `FISCALIZADORA` / Comisión Revisora como rol diferenciado.
  - **Estados del expediente:** Lista las descripciones largas reglamentarias del Art. 12 RP 2026 (línea 142) en lugar de los valores/etiquetas del código (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **Alertas automáticas por umbrales `-7` y `-10` puntos** (diagrama, `ACT-03`, `ACT-06`, `ACT-07`, §4): marcada como **parcial** en el registro (§2; falta conectar `ThresholdAlertEngine` al flujo productivo y exponer endpoint/vista).
  - **Generación y exportación automática de Balances Cuatrimestrales Art. 137** (`ACT-02` ítem 10, `ACT-06` ítem 5): marcada como **parcial** en el registro (§2; falta exportación PDF y permisos de rol en 6 vistas de `reportes_views.py`).
  - **Votación nominal individual** (`ACT-02`, §4): marcada como **no implementada (descartada por PO)**.
  - **Recordatorios preventivos 24 h antes del vencimiento y notificaciones automáticas de corte cuatrimestral** (`ACT-06` ítems 4-5): el registro (§2) aclara que no existe la suite universal de los 10 disparadores de email.
  - **Evaluación cuatrimestral de desempeño (Art. 91)** (`ACT-04` ítem 4, `realizarEvaluacionCuatrimestral()`): no consta como funcionalidad implementada en el registro.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Apelación y adecuación del Formulario T01 (`SCRUM-70`).
  - Exclusión fundada de involucrados (`SCRUM-102`) y enmienda trazable de resoluciones con contra-asientos (`SCRUM-103`).
  - Panel de Administración (`SCRUM-91`: parámetros del sistema y gestión de miembros TD) y gestión de Calendario Institucional (feriados y excepciones).
  - Visor Autorizado Unificado con auditoría de consultas (`SCRUM-51`), valoración extraordinaria T03 con antecedentes (`SCRUM-53`), publicación protegida con censura médica (`SCRUM-105`/`SCRUM-106`), ABM de Reglamentos con auditoría inmutable y módulo de Eventos y Asistencia (`SCRUM-50`/`SCRUM-86`).
- **Referencias rotas:** Ninguna ruta de archivo inexistente. Cita la regla `RN-02` (línea 132) sin definirla localmente (pertenece al Plan de Proyecto).

---

## 2. `docs/analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md`

- **Ruta:** `docs/analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md`
- **Extensión:** 502 líneas
- **Última modificación:** `2026-11-12`
- **Tema que cubre:** Modelado BPMN 2.0 (ficha de proceso, JSON BPMN-IR, diagrama Mermaid y matriz de anti-patrones) del proceso operativo del Tribunal de Disciplina en SGD-AVEIT.
- **Quién lo lee:** equipo / cátedra
- **Qué pasa si desaparece:** alguien pregunta (referenciado en `README.md` y `TASK.md`).
- **Clasificación:** **3. Incompleto / desactualizado (modela 5 estados en lugar de los 6 estados oficiales implementados, conserva la votación nominal descartada por el PO y declara stack tecnológico incorrecto).**
- **Contradicciones con el registro:**
  - **Cantidad y nombres de estados del expediente:** El documento (v1.1.0, líneas 15, 29, 74, 224, 419) consolida el flujo en **5 estados** (*Expediente Creado*, *En período de justificaciones*, *En revisión y resolución*, *Pendiente de firma y envío*, *Expedientes ya emitidos*). El registro canónico (§2 y §3) verifica **6 estados** en el código (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`), concordantes con el Art. 12 del Reglamento Procesal 2026.
  - **Votación nominal y mayoría calificada (`RN-09`):** Modela `Cédula de Votación Nominal` (§1.4), `RN-09` (mínimo 2 de 3 votos), `task_votar_nominal`, `task_verificar_mayoria` (JSON) y `Task_VotoNominal` / `Task_ValMayoria` (Mermaid). El registro canónico (§2 y §3) confirma que la votación nominal individual fue **descartada por el PO** el 07/10/2026 y reemplazada por editor unificado y firma colegiada (`Resolucion.firmantes`).
  - **Stack tecnológico Frontend:** §1.3 (línea 55) afirma *"Frontend HTML5/Tailwind con diseño Material Dashboard PRO"*. El registro canónico (§3) verifica que el frontend real es **Angular 14.2+ + TypeScript + Angular Material**.
  - **Convención de signos en umbrales:** El JSON BPMN-IR (líneas 321, 338, 355) expresa `Saldo >= 10 Puntos Negativos` y `Saldo >= 7 Puntos Negativos`, mientras el diagrama Mermaid (líneas 460-462) usa `Saldo <= -10 pts` y `Saldo <= -7 pts`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **Alertas automáticas `-7` y `-10` puntos** (§1.1, `RN-13`/`RN-14`, `KPI-04`, JSON y Mermaid): marcadas como **parcial** en el registro (§2).
  - **Balances Cuatrimestrales consolidados en PDF/Excel** (§1.1 línea 34): marcados como **parcial** en el registro (§2; solo existen JSON y CSV, falta PDF).
  - **Votación nominal individual** (§1.4, `RN-09`, JSON y Mermaid): marcada como **no implementada (descartada por PO)**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Separación entre `revision_resolucion` y `espera_resolucion` (sexto estado).
  - Apelación y adecuación del Formulario T01 (`SCRUM-70`).
  - Resolución de causal T02 con puntaje ratificado (`SCRUM-52`/`SCRUM-101`) y valoración extraordinaria T03 con antecedentes (`SCRUM-53`).
  - Exclusión fundada de involucrados (`SCRUM-102`) y enmienda trazable de resoluciones con contra-asientos (`SCRUM-103`).
  - Regla de acumulación 3:1 de llamados de atención / felicitaciones (`SCRUM-57`/`SCRUM-59`/`SCRUM-104`) y publicación protegida con censura médica (`SCRUM-105`/`SCRUM-106`).
- **Referencias rotas:** Ninguna ruta de archivo inexistente. En el bloque Mermaid (líneas 475-479), las declaraciones de clase usan sintaxis inválida `Nodo class:estilo;` en lugar de `class Nodo estilo;`.

---

## 3. `docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md`

- **Ruta:** `docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md`
- **Extensión:** 441 líneas
- **Última modificación:** `2026-09-08`
- **Tema que cubre:** Estudio Inicial del proyecto SGD-AVEIT: presentación de AVEIT, marco normativo 2018 vs 2026, procesos AS-IS, recursos informáticos, layout físico, problemas y oportunidades.
- **Quién lo lee:** cátedra / equipo
- **Qué pasa si desaparece:** alguien pregunta (es la fuente Markdown del Estudio Inicial enlazada desde `README.md`, en paralelo a `docs/formales/Estudio_Inicial.{docx,pdf,odt}`).
- **Clasificación:** **3. Redundante con `docs/formales/Estudio_Inicial.docx` (y sus exportaciones `.pdf`/`.odt`; además presenta divergencias frente a la copia humana presentada y frente al registro canónico en materia de votación nominal).**
- **Contradicciones con el registro:**
  - **Votación nominal / colegiada:** Las líneas 97, 350 y 436 mencionan *"votación colegiada"*, *"registro nominal de votos"* y *"emitir votos nominales"*. El registro canónico (§1.2 #23, §1.3 #24, §1.4 #31, §2 y §3) establece que la votación nominal individual fue **descartada por el PO** el 07/10/2026 y registra la observación docente de revisar y actualizar el Estudio Inicial.
  - **Expresión *"cómputo algorítmico"*:** Líneas 21 y 97 utilizan *"cómputo algorítmico de puntajes/saldos"*, expresión explícitamente observada por la cátedra en Sprint 0 (registro §1.1 #8).
  - **Triggers SQL para integridad de saldos:** La tabla TO-BE (§3.7.1, línea 352) afirma *"auditoría inmutable mediante triggers y tabla histórica en MySQL"*, mientras el registro canónico (§2 y §3) indica que el Libro Mayor se implementa con `AsientoLibroMayor` (modelo InsertOnly en Django) y `LedgerService`, no mediante triggers SQL.
  - **Desincronización con el `.docx` presentado sobre categorías de socios:** Este Markdown ya utiliza *Socios Pasivos (1.º, 2.º y 3.º año)* y *Socios Activos (4.º a 6.º año)* (consistente con el código `PASSIVE`/`ACTIVE` en el registro §3), mientras el registro (§3 y §5.1) constata que `Documentación Actual Humana\Estudio_Inicial.docx` conservaba *Juniors (1.º-2.º)* y *Seniors (3.º-6.º)*.
  - **Nombres de los 6 estados del expediente:** §3.5.2 (líneas 192-197) usa las denominaciones extensas del Art. 12 RP 2026, distintas de los enums/etiquetas del código (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **Votación nominal** (líneas 97, 350, 436): **no implementada (descartada por PO)**.
  - **Alertas automáticas `-7` y `-10` puntos** (línea 353, §4.2 ítem 5): **parcial** en el registro (§2).
  - **Generación y exportación instantánea de Balances Cuatrimestrales Art. 137** (líneas 97, 176, 355, 438): **parcial** en el registro (§2; falta PDF y permisos de rol en 6 vistas).
  - **Repositorio unificado de antecedentes y jurisprudencia** (§4.1 ítem 4, §4.2 ítem 4): **parcial** en el registro (§2; solo existe búsqueda de antecedentes dentro de valoraciones T03).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** En su alcance de Estudio Inicial (AS-IS) no corresponde enumerar todo el producto final; en la tabla TO-BE (§3.7.1) omite reflejar el mecanismo definitivo adoptado de decisión colegiada por firma sin votación nominal, la apelación/adecuación T01 y la censura médica en resoluciones públicas.
- **Referencias rotas:** Ninguna ruta de archivo externa rota. En la Tabla de Contenido (líneas 43-58), la numeración visible está corrida en +1 respecto a los encabezados reales del cuerpo (`2. Introducción` enlaza a `## 1. INTRODUCCIÓN...`).

---

## 4. `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Estatuto_AVEIT_Reforma_2026.pdf`

- **Ruta:** `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Estatuto_AVEIT_Reforma_2026.pdf`
- **Extensión:** 55 páginas
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Estatuto Social oficial de A.V.E.I.T. (Reforma Año 2026): estructura de gobierno, categorías de socios, derechos, obligaciones, régimen de sanciones y Tribunal de Disciplina (Título III).
- **Quién lo lee:** equipo / cátedra
- **Qué pasa si desaparece:** alguien se equivoca (es fuente normativa primaria institucional referenciada en `README.md` y en los entregables formales).
- **Clasificación:** **4. Vigente** (documento normativo fuente de la organización).
- **Contradicciones con el registro:** No aplica (fuente normativa institucional externa al software).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** No aplica (documento normativo institucional).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** No aplica (documento normativo institucional).
- **Referencias rotas:** No aplica.

---

## 5. `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2018).pdf`

- **Ruta:** `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2018).pdf`
- **Extensión:** 8 páginas
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Reglamento Procesal Disciplinario histórico de AVEIT (versión 2018, encabezado interno *"Tribunal de Disciplina 2017"*), último formalmente aprobado por Asamblea bajo modalidad presencial/papel.
- **Quién lo lee:** equipo / cátedra
- **Qué pasa si desaparece:** alguien pregunta (respalda la comparativa normativa 2018 vs 2026 y la observación docente #3 de Sprint 0 en el registro canónico; referenciado en `README.md`).
- **Clasificación:** **4. Vigente** (como documento histórico de referencia normativa institucional; la operación del sistema sigue la versión 2026).
- **Contradicciones con el registro:** No aplica (fuente normativa histórica de AVEIT).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** No aplica (documento normativo institucional).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** No aplica (documento normativo institucional).
- **Referencias rotas:** No aplica.

---

## 6. `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2026).pdf`

- **Ruta:** `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2026).pdf`
- **Extensión:** 8 páginas
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Reglamento Procesal Disciplinario vigente en la práctica operativa de AVEIT (versión 2026): sesiones virtuales, 6 estados del expediente (Art. 12), formularios T01/T02/T03, plazos de 5 días hábiles y competencias de autoridades (Arts. 21-26).
- **Quién lo lee:** equipo / cátedra
- **Qué pasa si desaparece:** alguien se equivoca (fuente normativa rectora del ciclo de 6 estados, formularios y competencias implementados en SGD-AVEIT; referenciado en `README.md` y `AGENTS.md`).
- **Clasificación:** **4. Vigente** (documento normativo fuente principal).
- **Contradicciones con el registro:** No aplica (fuente normativa institucional de AVEIT).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** No aplica (documento normativo institucional).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** No aplica (documento normativo institucional).
- **Referencias rotas:** No aplica.

---

## 7. `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Reglamento_Interno_Disciplina_AVEIT_2026.pdf`

- **Ruta:** `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Reglamento_Interno_Disciplina_AVEIT_2026.pdf`
- **Extensión:** 25 páginas
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Reglamento Interno de Disciplina de AVEIT (Versión 2026.2, actualización 04/07/2026): obligaciones sociales, tipificación de faltas y premios, pérdida de condición de socio a los 10 puntos negativos (Art. 93) y Balances Cuatrimestrales (Art. 137).
- **Quién lo lee:** equipo / cátedra
- **Qué pasa si desaparece:** alguien se equivoca (fuente normativa primaria de reglas de puntaje, Art. 93 y Art. 137; referenciado en `README.md`).
- **Clasificación:** **4. Vigente** (documento normativo fuente principal).
- **Contradicciones con el registro:** No aplica (fuente normativa institucional de AVEIT).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** No aplica (documento normativo institucional).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** No aplica (documento normativo institucional).
- **Referencias rotas:** No aplica.

---

## 8. `docs/analisis-proceso-actual/sistema-actual/Rifas - Actas - Entrega - Desde cero.pdf`

- **Ruta:** `docs/analisis-proceso-actual/sistema-actual/Rifas - Actas - Entrega - Desde cero.pdf`
- **Extensión:** 5 páginas
- **Última modificación:** `2026-11-23`
- **Tema que cubre:** Instructivo visual paso a paso del sistema legado de AVEIT (`https://aveit.frc.utn.edu.ar/`) para el módulo de Rifas → Actas → Entrega de boletas.
- **Quién lo lee:** nadie
- **Qué pasa si desaparece:** nada (no está referenciado en ningún archivo del repositorio y pertenece a un módulo ajeno a SGD-AVEIT).
- **Clasificación:** **1. Residuo de fabricación** (ingresado en el commit `6a60167` de manuales de usuario; corresponde al módulo de Rifas del sistema legado, fuera del alcance disciplinario de SGD-AVEIT, y no cumple rol arquitectónico, formal ni de contenido presentable).
- **Contradicciones con el registro:** Fuera de alcance de SGD-AVEIT (el módulo de Rifas no forma parte del sistema ni figura en el registro canónico).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** No aplica.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** No aplica.
- **Referencias rotas:** Ninguna.

---

## 9. `docs/analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md`

- **Ruta:** `docs/analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md`
- **Extensión:** 582 líneas
- **Última modificación:** `2026-10-25`
- **Tema que cubre:** Relevamiento técnico del sistema legado `svaveit` (stack Python 3.5 / Django 2.2 / Angular 9.1 / MySQL 5.7, esquema de tablas `tribunal` y `socios`, DER As-Is, endpoints REST, regla del tercio, permisos `tribunal_bajo/medio/alto` y matriz de brechas).
- **Quién lo lee:** equipo (referenciado directamente desde el código en `backend/accounts/legacy_rbac.py:5`).
- **Qué pasa si desaparece:** alguien se equivoca (es la referencia técnica del esquema MySQL legado `socio_lista`, `tribunal_puntajeaplicado`, `tribunal_puntajegeneral` y del esquema RBAC legado que el backend actual respeta).
- **Clasificación:** **4. Vigente** (como documentación técnica del sistema legado As-Is, con contradicciones localizadas en su encabezado metodológico y en la matriz de brechas §7 frente a la implementación real).
- **Contradicciones con el registro:**
  - **Premisa de *"Borrón y cuenta nueva"* sin restricciones del esquema legado:** El encabezado (líneas 8-9) y §7 afirman reemplazo total sin asumir convenciones ni restricciones del sistema legado. El registro canónico (§2 y §3) verifica que SGD-AVEIT implementa una capa anticorrupción Read-Only sobre el padrón legado MySQL (`socio_lista`), reutiliza tablas legadas (`tribunal_puntajeaplicado`, `tribunal_puntajegeneral`) y mantiene equivalencia con los permisos legados (`tribunal_bajo/medio/alto` en `backend/accounts/legacy_rbac.py`).
  - **Entidad `VotoNominal` en §7 (ítem 7, línea 572):** Propone como acción requerida en SGD-AVEIT la entidad `VotoNominal` con cómputo formal de mayorías. El registro canónico (§2 y §3) establece que la votación nominal fue **descartada por el PO** y no existe entidad `VotoNominal` en el código.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - En §7 (Matriz de Brechas, columna *"Acción Requerida en SGD-AVEIT"*):
    - Ítem 4 (línea 569): Balances Cuatrimestrales Art. 137 — **parcial** en el registro (§2).
    - Ítem 6 (línea 571): Sistema de Alarmas Tempranas (7 y 10 puntos) — **parcial** en el registro (§2).
    - Ítem 7 (línea 572): Votación nominal (`VotoNominal`) — **no implementada (descartada por PO)**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** No aplica respecto a funcionalidades nuevas de SGD-AVEIT (su propósito es relevar el sistema legado As-Is).
- **Referencias rotas:**
  - Cita *"su esquema SQL asociado"* (líneas 10 y 581), pero no existe ningún archivo `.sql` en `docs/analisis-proceso-actual/sistema-actual/`.
  - Referencia rutas del repositorio legado externo (`svaveit/tribunal/models.py`, `svaveit/socios/models.py`, `svaveit/urls.py`, `svaveit/tribunal/funciones.py`, `angular-src/`, `http_public/panel/tribunal/*`, `settings_local_dev.py`, `settings_local_aveit.py`) que no existen en este repositorio (esperable por tratarse de un repositorio externo, aunque no se explicita).

---

## Decisiones pendientes

1. **Vigencia y rol de `ACTORES_DEL_SISTEMA_SGD_AVEIT.md` y `BPMN_Proceso_Operativo_Tribunal.md`:** Definir si se mantienen como documentación técnica activa en el repositorio (requiriendo sincronización con la eliminación de la votación nominal, los 6 estados del código y el stack Angular) o si se archivan como artefactos previos absorbidos por Plan de Proyecto y Definición del Producto.
2. **Fuente de verdad del Estudio Inicial (`TPI_Estudio_Inicial_SGD_AVEIT.md` vs `docs/formales/Estudio_Inicial.docx` vs `Documentación Actual Humana\Estudio_Inicial.docx`):** Resolver la convivencia y desincronización entre las copias (categorías Pasivo/Activo vs Junior/Senior, eliminación de votación nominal, expresión *"cómputo algorítmico"* y alcance AS-IS vs TO-BE).
3. **Destino de `Rifas - Actas - Entrega - Desde cero.pdf`:** Confirmar si se archiva en `auditoria/archivados/` por ser residuo de fabricación ajeno al alcance de SGD-AVEIT.
4. **Encabezado y §7 de `descripcion-sistema-actual-legado.md`:** Definir si se preserva intacto como fotografía histórica de relevamiento o si se alinea su encabezado (*"Borrón y cuenta nueva"*) y el ítem 7 de §7 (`VotoNominal`) con la integración real verificada en el registro canónico y referenciada por `backend/accounts/legacy_rbac.py`.
