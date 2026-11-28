# Auditoría de Discrepancias — Plan de Proyecto (`SGD-AVEIT`)

> **Fecha de auditoría:** 27/11/2026  
> **Alcance del entregable:** Propuesta de solución — **NO incluye la ejecución del Sprint 5** (`auditoria/entregables/_brief-comun.md`).  
> **Fuentes contrastadas:**
> - Entregable presentado: `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Plan_de_Proyecto.docx` (`v2.0.0`, `03/09/2026`, inmutable).
> - Copia alineada en repositorio: `docs/formales/Plan_de_Proyecto.docx` (`v2.1.0`, `27/11/2026`).
> - Fuente canónica y código/tests: `auditoria/registro-canonico.md`, `auditoria/traspaso-sprint6.md`.
> - Devoluciones docentes: `retroalimentaciónS0.txt` y `retroalimentaciónS4.txt`.

---

## a) Qué afirma el documento que el sistema no hace o que no está verificado

### 1. Corregido en el repo (`v2.1.0`) respecto del presentado (`v2.0.0`)

| Tema | Qué afirmaba `v2.0.0` (presentado) | Estado en `v2.1.0` (repo) |
|---|---|---|
| Acrónimo y nombre | Carátula: `SDG-AVEIT – (Nombre provisional, en discusión)` | Corregido a `SGD-AVEIT`. |
| Expresión ambigua | Objetivo en carátula: *"cómputo algorítmico de puntajes"* | Corregido a *"cómputo transaccional e inmutable de puntajes mediante libro mayor"*. |
| Stack frontend | Ficha de Rosales (§3): `Tailwind CSS` y `JavaScript` | Corregido a `SPA Angular 14.2+ / TypeScript (strict), Angular Material y Material Dashboard PRO`. |
| Mecanismo de inmutabilidad | §3 (Villegas), §4.2 y `RNF-02`: *"triggers en MySQL (`BEFORE UPDATE/INSERT`) que registran en `auditoria_puntos`"* | Corregido en esos 3 puntos a `AsientoLibroMayor` InsertOnly y `PuntajeAplicado` (Django ORM). |
| Votación nominal | `RF-09` y `RN-06`: voto nominal individual y mayoría absoluta (2 de 3) | Reemplazado por editor unificado + firma colegiada de 3 activos (`4.º, 5.º y 6.º`) y apartamiento automático (`IsNotInvolvedInExpediente`). |
| Categorías y firmantes | §6.1 (fila 10), `RF-11`, `RF-14`, `RN-07`, `RN-10`: `Juniors/Seniors (3.º–6.º)` y *"al menos dos Seniors"* | Corregido a `Pasivo (1.º–3.º)` / `Activo (4.º–6.º)` y firma colegiada de los **3** representantes activos. |
| Alertas `-7` / `-10` | §4.2, §6.1 (fila 11), `RF-13`, `RN-09`: disparo automático implementado | Marcadas como `trasladada al Sprint 6` (`SCRUM-62`). |
| Balance Art. 137 en PDF | `RF-14` y `RN-10`: exportación automática a PDF formal | Aclarado que existe en JSON/CSV; PDF y brecha RBAC marcados como trasladados al Sprint 6 (`SCRUM-63/124`). |
| Prueba de carga 50 usuarios | `RNF-04`: prueba de carga en staging con 50 usuarios concurrentes | Marcada en Meter como trasladada al Sprint 6 (`SCRUM-65/66`). |
| Competencias T01 | `RN-01`: 5 órganos textuales sin reflejar implementación | Ajustada a `opening_policy.py` y rol `FISCALIZADORA` vigente. |

### 2. Afirmaciones falsas, desactualizadas o no verificadas que **persisten incluso en `v2.1.0`**

1. **Votación nominal residual:**
   - **§6.1 Matriz RBAC (fila 9):** sigue afirmando `"Votar nominalmente y redactar Resoluciones | TD: C/U"`.
   - **§8 Matriz de Trazabilidad (fila 6):** sigue referenciando `RN-06 (Quórum y Mayoría Absoluta del Tribunal)`.
2. **Triggers SQL inexistentes:**
   - **`RF-12` (§7):** sigue diciendo *"mediante lógica de backend y triggers en base de datos"*.
   - **Riesgo `R-03` (§13.1):** sigue diciendo *"triggers de auditoría inmutables en base de datos"*. En el código no existen triggers MySQL ni tabla `auditoria_puntos`.
3. **Firma colegiada desactualizada en `RNF-03`:** exige *"al menos dos firmas electrónicas válidas"*, contradiciendo `RF-11`/`RN-07` y el código (exige **3** firmas activas de 4.º, 5.º y 6.º año en `Resolucion.firmantes`).
4. **Matriz RBAC (§6.1) desalineada con el código:**
   - Usa `AUTORIDAD SUBCOMISIÓN` en lugar del rol vigente `FISCALIZADORA` (`backend/socios/models.py`).
   - Fila 6 conserva `"(filtros Jr/Sr)"` en lugar de `Pasivo/Activo`.
   - Fila 2 asigna `❌` a `CD` y `TD` para presentar T02/T03 (cuando cualquier socio imputado puede presentar descargo en su propio expediente).
   - No refleja la brecha real de `reportes_views.py` (6 vistas solo exigen `IsAuthenticated`).
5. **Requerimientos No Funcionales no verificados o falsos:**
   - **`RNF-01`:** declara medición con Google Lighthouse Mobile `>= 90/100` y prueba de usabilidad `SUS >= 85` con 10 socios en Android/iOS (**no verificable**, sin evidencia).
   - **`RNF-05`:** afirma *"100% de endpoints protegidos por... RBAC"* y *"Suite de pruebas de penetración automatizadas (OWASP Top 10)"* (**falso/no verificado**: 6 vistas de reportes sin rol específico y sin suite OWASP en el repo).
6. **Catálogo de Casos de Uso inconsistente e inexacto (§12):**
   - El Historial `v2.0.0` afirma haber incluido `CU-01 a CU-12`, pero §12.1 solo lista **6** (`CU-01` a `CU-06`) y §12.2 solo especifica **`CU-01`**.
   - En `CU-01` (paso 7 y Gherkin) usa el nombre no canónico `"Las justificaciones están siendo revisadas"` (en código: `revision_resolucion` / *"Justificaciones en revisión"*) e identifica al socio por `legajo "87414"` en lugar de `numero_socio`.
7. **Regla `RN-05` simplificada y nombres de estados no canónicos:** lista `E1(Creado) -> E2(En Justificación) -> E3(En Revisión) -> E4(En Espera Resolución) -> E5(Pendiente Firma) -> E6(Emitido)` y afirma transición estrictamente sin retrocesos, omitiendo **Apelación/Adecuación T01** (`SCRUM-70`) y **Enmienda con contra-asientos `REVERSION`** (`SCRUM-103`).
8. **Infraestructura y acceso no verificables o inexistentes:**
   - **§5, `RES-04`, `R-02`:** dan por existente un *"entorno de staging propio"* activo con entregas desplegables por sprint (**no verificable**, `SCRUM-66` trasladado al Sprint 6).
   - **Riesgo `R-04` (§13.1):** afirma *"envío de links directos por correo electrónico con token de acceso seguro para simplificar la carga"* (no existe acceso por token en link; la autenticación es JWT por `numero_socio`).
9. **Defectos formales y de alcance que persisten en `v2.1.0`:**
   - Carátula: título dice `"Análisis del Sistema"`, `Fecha de Entrega: xx/xx/2026`, `FECHA DE EXAMEN: DD/MM/AAAA`; §2 dice `"Nombre Oficial(Provicional)"`.
   - Menciones explícitas a skills/comandos internos de IA en el cuerpo formal (`systemClassifier`, `/requirementsExtractor`, `useCaseExtractor` en §§4, 7 y 12).
   - Sección **`4.1. Diagnóstico mediante Teoría General de Sistemas (TGS)`** completamente vacía.
   - En **`CU-01` (§12.2)** las subsecciones `3. Disparador (Trigger)` y `4. Postcondiciones Duales` están duplicadas.
   - **Desborde de alcance temporal en `v2.1.0`:** el Plan de Proyecto **no debe incluir la ejecución del Sprint 5**, pero `v2.1.0` incorporó notas de ejecución de Sprints 3–5, tickets `SCRUM-*` y referencias a `auditoria/traspaso-sprint6.md`.

---

## b) Qué hace el sistema que el documento no dice

Alcance funcional y arquitectónico implementado en código (y pertinente a la propuesta de solución del Plan de Proyecto) que **no figura en `RF-01..RF-15` ni en §11** (en `v2.0.0` está totalmente ausente; en `v2.1.0` parte solo se menciona al pasar en una nota dentro de `RF-14`):

1. **Módulos funcionales sin RF dedicado en §7:**
   - **Ranking Oficial de Socios y Buscador / Legajo Integral** (`backend/ranking/`, `backend/socios/`, `/ranking-socios`).
   - **Calendario Institucional y gestión de feriados/excepciones** para cómputo de 5 días hábiles (`Holiday`, `CalendarioVersion`, `FeriadoExcepcion`, `/calendario-institucional`).
   - **Eventos, Reuniones y Asistencia (Strategy) con regla 3:1 de apercibimientos** (`SCRUM-50`/`86`, `EventoInstitucional`, `AsistenciaEvento`, `AtencionFelicitacion`, `/eventos-asistencia`).
   - **Apelación y Adecuación del Formulario T01** con plazo parametrizable (`SCRUM-70`, `PeriodoApelacion`, `ApelacionT01`, `AdecuacionT01`).
   - **Composición del Tribunal, apartamiento automático por conflicto de interés y suplencias** (`SCRUM-54`, `ComposicionTribunal`, `IntegranteComposicion`, `IsNotInvolvedInExpediente`). *(En `v2.1.0` recién aparece en `RN-06`.)*
   - **Visor Autorizado Unificado con auditoría de consultas y descargas de evidencia** (`SCRUM-51`, `AuditoriaConsultaExpediente`, `AuditoriaDescargaEvidencia`, adjuntos protegidos en `BinaryField`).
   - **Versionado inmutable y retiro lógico de descargos** (`DescargoVersion`) y **Valoración T03 con vinculación de precedentes** (`SCRUM-53`, `ValoracionT03`, `ValoracionT03Antecedente`).
   - **Exclusión fundada de involucrados** (`SCRUM-102`) y **Enmienda trazable de resoluciones emitidas con contra-asientos `REVERSION`** (`SCRUM-103`, `EnmiendaResolucion`).
   - **Publicación oficial con censura automática de datos médicos sensibles** (`SCRUM-105`/`106`, `medical_redaction.py`).
   - **ABM de Reglamentos con auditoría inmutable** (`ArticuloReglamento`, `AuditoriaArticuloReglamento`, `/reglamentos`).
   - **Panel de Administración** de parámetros del sistema y gestión de miembros TD (`SCRUM-91`, `SystemParameterChange`, `TribunalRoleChange`, `/admin/parametros`).
   - **Notificaciones Outbox con reintentos** (`EmailOutbox`, `EmailAttachment`, `process_email_queue`) y centro de notificaciones UI (`NotificationCenter`, 10s accesible).
2. **Arquitectura e integración técnica ausente en §11:**
   - **Capa Anticorrupción Read-Only** sobre el padrón legado MySQL (`backend/padron/`, `ReadOnlyModel`).
   - **Autenticación JWT** por `numero_socio` con verificación de elegibilidad y mapeo de permisos legados (`tribunal_bajo/medio/alto`).
   - **Stack real completo:** Django 4.2 LTS + DRF, Angular 14.2+ + Angular Material, Docker Compose y endpoints de healthcheck (`/api/health/`, `/api/v1/padron/health/`).

---

## c) Correcciones de los profesores sin aplicar (cita breve)

Evaluación de cada observación aplicable de `auditoria/registro-canonico.md` (§1):

| # | Cita textual breve | Estado en `v2.0.0` (presentado) | Estado en `v2.1.0` (repo) | Evidencia / Qué falta |
|---|---|---|---|---|
| **6** | *"Completar formalmente el documento: carátula, nombre definitivo, equipo y habilidades."* | **Parcial** | **Parcial** | Equipo y habilidades completos, pero carátula mantiene `"Análisis del Sistema"`, `xx/xx/2026`, `DD/MM/AAAA` y §2 mantiene `"Nombre Oficial(Provicional)"`. |
| **7** | *"Agregar trazabilidad entre reglas del sistema y normativa de AVEIT: formularios, plazos, puntajes, alertas y balances."* | **Parcial** | **Parcial** | Existe §8, pero faltan módulos normativos reales (apelación T01, apartamiento Art. 95, 3:1, censura médica, reglamentos) y fila 6 aún cita `RN-06 (Quórum y Mayoría Absoluta)`. |
| **8** | *"Reemplazar expresiones ambiguas como 'cómputo algorítmico' por reglas de negocio más precisas."* | **Parcial** | **Aplicada** | `v2.0.0` dejó *"cómputo algorítmico"* en el Objetivo de carátula; `v2.1.0` lo reemplazó y mantuvo `RN-08`. |
| **9** | *"Aclarar qué significa 'firma digital' y no comprometer una solución con validez legal si no es necesaria."* | **Aplicada** | **Aplicada** | Aclarado en `RF-11`, `RNF-03` (sin Ley 25.506) y `R-05`. *(Ajuste menor pendiente en `RNF-03`: 3 firmas activas, no "al menos dos".)* |
| **10** | *"Desglosar los requerimientos funcionales globales en funcionalidades detalladas."* | **Parcial** | **Parcial** | Existe `RF-01..RF-15`, pero omiten módulos sustantivos detallados en la sección b). |
| **11** | *"Definir actores, roles y permisos del sistema."* | **Parcial** | **Parcial** | Existe §6.1, pero desalineada del código (`FISCALIZADORA` vs `AUTORIDAD SUBCOMISIÓN`, fila de votación nominal, `Jr/Sr`, permisos reales de CD/TD/reportes). |
| **12** | *"Separar requerimientos no funcionales de restricciones tecnológicas. Ejemplo: Python es restricción."* | **Aplicada** | **Aplicada** | Separación formal entre §10 (RNF ISO 25010) y §11.1 (`RES-01` Python, `RES-02` MySQL, `RES-03..RES-06`). |
| **13** | *"Reformular la regla de 'no UPDATE directos' como requisito de integridad, inmutabilidad y trazabilidad del saldo."* | **Parcial** | **Parcial** | Reformulada en `RNF-02` (y alineada a `AsientoLibroMayor` en `v2.1.0`), pero `RF-12` y `R-03` aún mencionan triggers SQL inexistentes. |
| **14** | *"Completar cómo aplicarán Scrumban concretamente en el proyecto."* | **Aplicada** | **Aplicada** | §5 especifica sprints de 2 semanas, ceremonias, política de PRs, límites WIP (`4/3/3`) y métricas (`Lead Time`, `Cycle Time`, `CFD`). |
| **15** | *"Explicitar la integración con el sistema existente y restricciones de la BD (repos, uso de BD para consulta, usuarios)."* | **Parcial** | **Parcial** | §11 menciona MySQL y dump anonimizado, pero no explicita la capa Read-Only (`backend/padron/`), usuarios/autenticación legada (`numero_socio`/`legajo`), roles legados ni repos/Docker Compose. |
| **16** | *"Revisar Story Points y corregir diferencias entre documentos 111/116."* | **Sin aplicar** *(no incluido en Plan)* | **Sin aplicar** *(no incluido en Plan)* | El Plan de Proyecto no incluye tabla de Story Points; la discrepancia `111/116` corresponde al cruce con `Seguimiento de Proyecto`, donde debe quedar unificada. |
| **18** | *"Redefinir el Story Map con al menos un corte horizontal de MVP." / "Reorganizar las entregas para dar valor antes... no todo Must al final."* | **Sin aplicar** | **Sin aplicar** | En §7, **14 de 15 RF (`RF-01..RF-14`) siguen marcados como `Must Have`** (solo `RF-15` es `Should Have`) y §13 no plantea entregas tempranas ni corte de MVP. |
| **23** | *"Evaluar si la eliminación de la votación nominal corresponde reflejarla en Plan de Proyecto, Estudio Inicial y Definición de Producto."* | **Sin aplicar** | **Parcial** | `v2.0.0` conserva votación nominal en todo el texto; `v2.1.0` la quitó de `RF-09`/`RN-06` pero la dejó en §6.1 (fila 9) y §8 (fila 6). |
| **31** | *"¿Qué documentos y modelos generales fueron actualizados para reflejar definitivamente la eliminación de la votación nominal?"* | **Sin aplicar** | **Parcial** | Mismo estado que #23: el Plan presentado (`v2.0.0`) nunca se actualizó y `v2.1.0` conserva residuos en §6.1, §8 y `RNF-03`. |

---

## d) Datos que la cátedra o la plantilla exigen y no existen en ninguna fuente

1. **Fecha real de entrega y Fecha de examen en Carátula** (figuran como `xx/xx/2026` y `DD/MM/AAAA`): **`dato faltante`**.
2. **N.º de Entrega formal para la presentación definitiva** (actualmente figura `1`): **`dato faltante`**.
3. **Contenido de la sección `4.1. Diagnóstico mediante Teoría General de Sistemas (TGS)`** (el encabezado existe pero está vacío): **`dato faltante`**.
4. **Especificaciones de `CU-02` a `CU-12`** (prometidos en el Historial `v2.0.0`; §12.1 solo enumera hasta `CU-06` y únicamente `CU-01` está especificado): **`dato faltante`**.
5. **Resultados verificados de métricas Planguage en RNF** (Google Lighthouse Mobile, encuesta SUS con 10 socios en `RNF-01`, prueba de carga 50 usuarios concurrentes en `RNF-04`, suite OWASP Top 10 en `RNF-05`): **`dato faltante`**.
6. **Autor/responsable de la versión histórica `1.0.1` (`02/09/2026`)** (figura `-` en Historial de Revisiones): **`dato faltante`** *(registro histórico inmutable)*.
7. **Evidencia de entorno Staging operativo y acuerdo formal de despliegue en servidor AVEIT (`RES-04`/`RES-05`)**: **`dato faltante`**.
8. **Límites de extensión (páginas/palabras) y reglas tipográficas** (no especificados en `Seminario-Guia de Documentación.pdf`): **`dato faltante`**.

---

## e) Cambios que dependen de una decisión del usuario (alcance, traslados, criterios)

1. **Límite temporal del Plan de Proyecto (sin Sprint 5 vs estado actual de `v2.1.0`):** El brief define que el Plan de Proyecto **no incluye la ejecución del Sprint 5**, pero `docs/formales/Plan_de_Proyecto.docx` (`v2.1.0`) incorporó notas de ejecución de Sprints 3–5, tickets `SCRUM-*` y traslados al Sprint 6. Decidir si el Plan definitivo se redacta como **propuesta de solución alineada al diseño/arquitectura vigente (sin reportes de ejecución del Sprint 5)** o si se conserva el formato de `v2.1.0` con marcas de traslado al Sprint 6.
2. **Reorganización del catálogo de Requerimientos Funcionales (§7–§8):** Decidir si se agregan nuevos `RF` para los módulos implementados hoy omitidos (Ranking/Legajo, Calendario, Eventos 3:1, Apelación T01, Apartamiento/Suplencias, Visor/Auditoría, Exclusión/Enmienda, Censura médica, ABM Reglamentos, Panel Admin) o si se mantiene la numeración `RF-01..RF-15` integrándolos en los RF existentes para preservar trazabilidad cruzada.
3. **Repriorización MoSCoW y corte de entregas tempranas (obs. #18):** Definir qué RF dejan de ser `Must Have` (actualmente 14/15 lo son) y qué hitos/entregas incrementales tempranas (MVP en Sprint 2, releases posteriores) se plasman en §7 y §13.
4. **Permanencia o eliminación de §12 (Casos de Uso `CU-01..CU-12` y diagrama BCE):** La Guía de Cátedra no exige Casos de Uso ni BCE en el Plan de Proyecto (el proyecto sigue enfoque Ágil con US). Decidir si se elimina §12 (evitando la promesa incumplida de `CU-01..CU-12`) o si se completa el catálogo.
5. **Ajuste de métricas de RNF no verificados (`RNF-01`, `RNF-04`, `RNF-05`):** Decidir si se conservan las metas Planguage originales (Lighthouse, SUS, 50 usuarios concurrentes, OWASP Top 10) marcándolas explícitamente como **criterios objetivo pendientes de verificación**, o si se reformulan a verificaciones respaldadas por el repositorio.
6. **Cierre de datos formales y limpieza editorial:** Confirmar (a) título de carátula (`Plan de Proyecto` en vez de `Análisis del Sistema`), (b) fechas reales de entrega/examen y N.º de Entrega, (c) eliminación de `"Provicional"` (§2), menciones a skills internas de IA (`systemClassifier`, `/requirementsExtractor`, `useCaseExtractor`) y duplicados de `CU-01`, y (d) si `4.1` (TGS) se completa o se retira.
7. **Número de versión a emitir:** Conservando `v1.0.0` (`01/09`), `v1.0.1` (`02/09`) y `v2.0.0` (`03/09/2026`) inmutables, confirmar si la versión corregida para entrega definitiva se consolida como `v2.1.0` o avanza a `v2.2.0`.
