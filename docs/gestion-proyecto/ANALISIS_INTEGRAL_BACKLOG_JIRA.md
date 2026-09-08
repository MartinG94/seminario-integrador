# Análisis integral y propuesta de backlog — SGD-AVEIT

**Fecha de corte:** 08/09/2026

**Destino:** Jira, proyecto `SCRUM`, tablero 1

**Horizonte:** 6 sprints de 14 días posteriores al Sprint 0
**Estado:** propuesta preparada para validación e importación

## 1. Resumen ejecutivo

El repositorio contiene una base documental amplia y un prototipo Angular útil para validar la experiencia, pero todavía no una aplicación integrada: no existe backend Django operativo, el servicio Angular trabaja con datos en memoria y `docker-compose.yml` sólo levanta de forma efectiva MySQL y el frontend. Por lo tanto, el primer incremento no debe tratarse como una simple implementación greenfield ni como una continuación funcional del prototipo. Debe resolver explícitamente el contrato de integración con las aplicaciones y datos actuales de AVEIT.

El backlog anterior tiene seis épicas y veinte ítems por 116 puntos. Su volumen agregado podría parecer compatible con seis sprints, pero no es un pronóstico confiable porque:

- no existe velocidad histórica del equipo;
- las estimaciones mezclan historias de usuario, tareas de homologación y épicas estimadas;
- varias historias de 8 puntos combinan frontend, backend, reglas, seguridad, archivos y notificaciones;
- faltan criterios de aceptación verificables, dependencias, trazabilidad normativa y definición de interfaces con el legado;
- Sprint 4 concentra 26 puntos y una gran cantidad de riesgo jurídico/técnico;
- la estabilización aparece como una única tarea al final, en lugar de formar parte de la Definition of Done de cada historia.

La propuesta v2 contiene **6 épicas y 38 ítems implementables**, con historias mayormente de 2, 3 o 5 puntos. De ellos, 35 forman el horizonte de seis sprints y 3 quedan en el Product Backlog sin calendarizar hasta validar su interpretación normativa. El pronóstico comprometido queda entre **18 y 22 puntos por sprint**; Sprint 6 agrega una historia *stretch* de 3 puntos para jurisprudencia. Los puntos deben reestimarse por Planning Poker y recalibrarse después del Sprint 1; no se convierten en horas.

## 2. Fuentes revisadas

Se revisaron de manera cruzada:

- constitución SDD, `TASK.md`, `README.md`, `DESIGN.md`, `docker-compose.yml` y configuración real del frontend;
- todos los documentos Markdown, JSON, DOCX y PDF de `docs/`;
- Estatuto AVEIT 2026, Reglamento Procesal Disciplinario 2018 y 2026 y Reglamento Interno de Disciplina 2026;
- spec activa `specs/001-walking-skeleton/{spec,plan,tasks}.md`;
- modelo de dominio, ERS, BPMN, catálogo de actores, escenarios de calidad, estudio inicial y plan de proyecto;
- código del frontend Angular y del prototipo HTML/JavaScript;
- archivo externo `C:\Users\mguillen\Downloads\modulo-tribunal-stack-y-modelos(2).md`, tomado como fuente técnica primaria del ecosistema legado que debe integrarse;
- backlog CSV previo `docs/gestion-proyecto/jira_backlog_import.csv`.

## 3. Diagnóstico del producto y del código

### 3.1 Estado real de implementación

- El frontend es Angular 14.2 con Angular Material, Bootstrap 4.6.1 y Material Dashboard PRO. Hay documentación que todavía lo describe como HTML/CSS/JavaScript o Tailwind; esas referencias deben corregirse en una futura tarea documental.
- No hay backend Django implementado. El servicio backend de Compose está comentado.
- `TribunalDataService` usa `BehaviorSubject` y colecciones mock. Los expedientes, votos, firmas, notificaciones y saldos se mutan sólo en memoria.
- El prototipo genera un hash simulado, usa nombres/subcomisiones de muestra y aplica quórum/firma con constantes. No puede considerarse evidencia de integridad, seguridad ni cumplimiento reglamentario.
- No se localizaron pruebas unitarias Angular específicas del dominio ni pruebas backend.
- Hay credenciales de desarrollo dentro de Compose. Deben pasar a variables de entorno y secretos locales no versionados.

### 3.2 Implicación arquitectónica

El documento externo describe un ecosistema existente con Python 3.5, Django 2.2.4, DRF 3.10.1, MySQL 5.7 y Angular 9.1.13. El proyecto nuevo propone Python 3.11+, Django 4.2, DRF moderno, MySQL 8 y Angular 14. No es seguro duplicar padrón, permisos o saldos sin una decisión explícita de convivencia.

El backlog incorpora una decisión arquitectónica temprana y una capa anticorrupción/adaptador. Hasta validar acceso, esquema, volumetría y responsables, la opción más segura es:

1. consumir padrón, roles y movimientos históricos del legado en modo sólo lectura;
2. mantener el expediente disciplinario nuevo en un bounded context propio;
3. aplicar puntos mediante un servicio idempotente y auditable, nunca mediante `UPDATE` manual;
4. reconciliar `PuntajeAplicado` —fuente histórica indicada— con `PuntajeGeneral`, tratado como caché;
5. evitar crear un segundo “Socio” maestro que pueda divergir.

La decisión final es un entregable de Sprint 1 y requiere aprobación del responsable de Cómputos/AVEIT.

## 4. Hallazgos normativos que cambian el backlog

| Tema | Fuente normativa | Corrección necesaria |
|---|---|---|
| Categorías sociales | Decisión de Product Owner del 08/09/2026 y Estatuto 2026, art. 3 | La denominación canónica es Pasivo para 1.º–3.º (equivalente anterior: Junior) y Activo para 4.º–6.º (equivalente anterior: Senior). La vigencia de cuenta/membresía es un concepto separado. |
| Composición del TD | Estatuto 2026, arts. 92 y 95 | Tres titulares y tres suplentes, con un titular y un suplente por cada grupo Activo. Debe modelarse el apartamiento y la sustitución estatutaria. |
| Recusación | Estatuto 2026, art. 93 | Los miembros no pueden ser recusados. El backlog anterior hablaba de “recusaciones”; se reemplaza por apartamiento/conflicto y suplencia. |
| Mayoría | Estatuto 2026, art. 96 | Decisiones por mayoría absoluta; para el cuerpo ordinario de tres titulares, dos votos afirmativos. Los casos ad hoc deben derivar la mayoría de su composición efectiva. |
| Estados | Reglamento Procesal 2026, art. 12 | Son exactamente seis: Creado; período para justificaciones; justificaciones en revisión; espera de resolución; pendiente de correos; emitido. La UI actual consolida cinco. |
| T01 y anexo | Reglamento Procesal 2026, art. 16 bis | El anexo puede acompañar al T01; no es obligatorio en todos los casos. |
| T02/T03 | Reglamento Procesal 2026, arts. 17 y 18 | T02 es tipificado y estructurado; T03 cubre causales extraordinarias no previstas y requiere valoración fundada/precedentes. |
| Resolución | Reglamento Procesal 2026, art. 19 | Conserva el número del expediente y debe contener Vistos, Considerandos y parte resolutiva articulada. |
| Firma y emisión | Reglamento Procesal 2026, art. 12 | Antes de emitir debe existir una firma por cada grupo social representado y enviarse el correo de resolución. |
| Enmienda | Reglamento Procesal 2026, diagrama del art. 13 | El proceso dibuja una decisión “¿Enmienda?” posterior a Emitido que retorna a la aprobación/desaprobación de justificaciones. Debe conciliarse con la prohibición de alterar decisiones de una gestión anterior antes de implementar. |
| Apelación/adecuación T01 | Reglamento Procesal 2026, diagrama del art. 14 | El T01 posee un período de apelación vía correo, debate/adecuación de puntos e involucrados y comunicación de motivos antes de la resolución final. No estaba en el backlog anterior. |
| Gestión interna de casos | Reglamento Procesal 2026, diagrama del art. 15 | Una solicitud de socio o actuación de oficio inicia entrevistas, debate, comunicación y eventual generación de T01/procedimiento. No estaba modelado como flujo propio. |
| Apercibimientos | Reglamento Interno 2026, art. 83 | Cada tres apercibimientos corresponde descontar un punto. Se descarta la ambigüedad de 0,33 o 0,5 por apercibimiento. |
| Escalas | Reglamento Interno 2026, arts. 80–85 | La unidad mínima es 0,5 y existen valores de 1,5; el modelo debe usar decimal, nunca `float`. |
| Avisos/reporte de reuniones | Reglamento Interno 2026, arts. 95 y 99 | Para sancionar, la reunión obligatoria debe publicarse con dos días hábiles; el responsable informa asistencia dentro de 72 horas hábiles. |
| Pérdida de condición | Reglamento Interno 2026, art. 93 | El umbral estatutario/reglamentario localizado es saldo negativo de 10 o más. La alerta preventiva en -7 debe quedar como política configurable pendiente de aprobación, no como obligación normativa. |
| Balance art. 137 | Reglamento Interno 2026, arts. 135 y 137 | El balance es cuatrimestral, por subcomisión/autoridad y lo elabora/controla Auditoría Interna/Vicepresidencia; el TD es receptor, no propietario exclusivo. |
| Evidencia médica | Reglamento Interno 2026, art. 102 | Se exige certificado original. La digitalización necesita una regla de custodia/validación aprobada; adjuntar una foto no resuelve por sí solo la exigencia. |

## 5. Inconsistencias documentales a resolver

1. **Integración vs. reemplazo:** el documento técnico externo describe integración con aplicaciones existentes, mientras la versión incorporada al repositorio afirma greenfield/reemplazo. La ADR de Sprint 1 debe ser la fuente canónica.
2. **Cinco vs. seis estados:** ERS y diseño visual no coinciden con el reglamento ni con la constitución.
3. **Categorías Pasivo/Activo:** resuelto por decisión del Product Owner: Junior = Pasivo (1.º–3.º) y Senior = Activo (4.º–6.º). Debe mantenerse separada la vigencia de la cuenta.
4. **Firma:** aparecen dos o tres firmas. La regla operativa propuesta es una firma por cada uno de los tres grupos Activos representados, salvo composición ad hoc formalmente documentada.
5. **Adjuntos:** hay límites de 5 MB y 10 MB. La política v2 propone 5 MB por archivo, tipos permitidos, análisis de contenido y acceso restringido; requiere validación de Infraestructura.
6. **Rendimiento:** existen objetivos de 250 ms, 500 ms y 1,5 s. Se propone p95 ≤ 500 ms para lectura de ranking/búsqueda con 515 socios y p95 ≤ 1,5 s para operaciones complejas, medido en staging.
7. **Concurrencia:** se mencionan 50, 100 y 150 usuarios. Se propone probar 50 concurrentes como objetivo del MVP y registrar 100 como prueba de capacidad, sujeto a infraestructura.
8. **Tecnología UI:** se debe unificar en Angular 14 + Material Dashboard/Angular Material + tokens SCSS canónicos; Tailwind no forma parte del baseline real.
9. **Balance cuatrimestral:** actor y alcance estaban asignados al TD; se corrigen conforme a los arts. 135 y 137.
10. **Circular 001/2026:** se la cita en documentos, pero no está versionada en el repositorio. Cualquier regla que dependa de ella queda marcada `decision-pendiente`.
11. **Enmienda vs. irrevisabilidad:** el diagrama del art. 13 contempla enmienda, mientras la regla sobre gestiones posteriores limita revisar decisiones previas. Se necesita interpretación institucional sobre autoridad, plazo, causales y efecto contable.

## 6. Criterio de granularidad para seis sprints

### Nivel Jira

- **Épica:** capacidad de negocio transversal, no se estima con Story Points.
- **Historia:** corte vertical demostrable por un actor, normalmente 2–5 puntos, con API/UI/reglas/pruebas incluidas en su DoD.
- **Spike:** decisión o investigación con timebox y evidencia concreta; no produce funcionalidad fingida.
- **Tarea:** infraestructura, migración, hardening u homologación que no puede expresarse honestamente como historia.
- **Subtarea:** trabajo de 30 minutos a un día creado durante la planificación del sprint. El requisito de tareas `<30 min` de SDD se conserva en `tasks.md`; no conviene importar cientos de microtareas al Product Backlog antes de planificar.

### Pronóstico

| Sprint | Puntos comprometidos | Stretch | Objetivo |
|---|---:|---:|---|
| 1 | 20 | 0 | Integración, identidad, padrón, ranking y búsqueda sobre datos reales/representativos. |
| 2 | 18 | 0 | Apertura T01, competencias, notificación y máquina de seis estados. |
| 3 | 19 | 0 | Plazos hábiles, T02/T03, evidencia y origen de sanciones. |
| 4 | 22 | 0 | Revisión, conflicto/suplencias, voto nominal y resolución. |
| 5 | 20 | 0 | Firma, emisión, libro mayor, portal y alertas. |
| 6 | 21 | 3 | Balance, reconciliación, calidad, staging y homologación; jurisprudencia como stretch. |
| **Total** | **120** | **3** | Pronóstico inicial; reestimar tras Sprint 1. |

No se recomienda comprometer los 136 puntos del Product Backlog hoy: 120 forman el pronóstico base de seis sprints, 3 son *stretch* y 13 quedan sin calendarizar hasta validar los flujos de los arts. 13–15. El equipo dispone de unas 115,5 horas de foco nominal por sprint según el plan, pero Story Points no equivalen a horas. La decisión de alcance debe basarse en velocidad observada al cerrar Sprint 1. Si la velocidad queda debajo de 20, el orden de recorte sugerido es: jurisprudencia, PDF avanzado del balance y funcionalidades visuales no esenciales, preservando integridad, seguridad, trazabilidad y cumplimiento normativo.

## 7. Definition of Ready y Definition of Done aplicables

Una historia entra a sprint sólo si tiene actor, valor, al menos tres criterios verificables, dependencias resueltas, regla normativa o decisión de producto identificada, mock/contrato cuando corresponda y estimación consensuada.

Se considera terminada únicamente con revisión, pruebas automatizadas, cobertura del dominio ≥80 %, migraciones reversibles, autorización verificada, auditoría de acciones sensibles, responsive 360–414 px, accesibilidad del flujo, contrato OpenAPI actualizado, despliegue en staging y aceptación del Product Owner. Seguridad, documentación y pruebas no son historias que puedan postergarse íntegramente a Sprint 6.

## 8. Riesgos y decisiones bloqueantes

| ID | Riesgo/decisión | Tratamiento |
|---|---|---|
| R-01 | No existe acceso validado a esquema/datos del legado | Spike S1-01 y adaptador de sólo lectura; no crear duplicados productivos. |
| R-02 | Versiones legadas sin soporte | Aislar integración por API/adaptador; no acoplar el frontend nuevo directamente a tablas. |
| R-03 | Clasificación social errónea en documentos actuales | Corregir criterio en código/spec mediante cambio de requisito aprobado antes de T3 de Spec 001. |
| R-04 | Token, claves o passwords expuestos | Rotar secretos compartidos fuera del gestor seguro; `.env.example` sin valores; CI con secret store. |
| R-05 | Datos disciplinarios y médicos sensibles | RBAC por objeto, cifrado en tránsito/reposo, mínimo privilegio, logs sin contenido sensible y política de retención. |
| R-06 | Reglas de firma/custodia digital no aprobadas | ADR y criterio de aceptación firmados por TD/Cómputos antes de Sprint 5. |
| R-07 | Falta Circular 001/2026 | Incorporar copia controlada o acta de decisión; -7 queda configurable/desactivable. |
| R-08 | Eliminación del backlog Jira actual | Exportar/snapshot previo y eliminar sólo issues del proyecto `SCRUM` confirmados; no tocar otros proyectos. |
| R-09 | Flujos de apelación, caso interno y enmienda sin detalle suficiente | Mantener PB-01 a PB-03 fuera de sprint; refinarlos con TD antes de comprometerlos. |

## 9. Artefactos de carga

La propuesta importable está en `docs/gestion-proyecto/jira_backlog_import_v2.csv`. El CSV anterior se conserva sin cambios hasta validar la carga. Antes de importar se deben verificar los nombres reales de los tipos de issue, el campo Story Points, el soporte de Epic Link/Parent y la existencia o creación de los seis sprints.

La importación debe hacerse en dos pasos: primero épicas; luego historias/spikes/tareas enlazadas. Después se valida por muestreo la descripción, prioridad, puntos, etiquetas y épica de al menos un ítem por sprint, y se compara el total importado contra 44 issues: 6 épicas + 38 ítems. PB-01 a PB-03 deben quedar sin sprint.

## 10. Recomendación final

El proyecto es viable en seis sprints sólo como **MVP disciplinario integrado**, con decisiones tempranas y control estricto de alcance. No conviene prometer simultáneamente reemplazo total del legado, migración exhaustiva, jurisprudencia avanzada y todos los refinamientos de reportería. El orden correcto es demostrar un walking skeleton conectado de manera segura, completar el expediente end-to-end y cerrar con reconciliación/homologación. La granularidad v2 permite mover alcance sin romper el valor vertical ni esconder riesgo dentro de historias de 8 puntos.

## 11. Ejecución verificada en Jira (08/09/2026)

Se eliminó exclusivamente el backlog anterior, compuesto por `SCRUM-2` a `SCRUM-27` (26 incidencias). La consulta exacta de esas claves quedó sin resultados después de la operación masiva.

La carga v2 creó y conservó 44 incidencias en el proyecto `SCRUM`:

- 6 épicas: `SCRUM-28` a `SCRUM-33`.
- 35 actividades planificadas: `SCRUM-34` a `SCRUM-68`.
- 3 historias de decisión pendientes sin sprint: `SCRUM-69` a `SCRUM-71`.

La jerarquía, descripción, prioridad, estimación, etiquetas y vínculo con épica se validaron por muestreo. Jira muestra el siguiente calendario y capacidad:

| Sprint | Fechas en Jira | Actividades | Puntos |
|---|---|---:|---:|
| SCRUM Sprint 1 | 09/09/2026–22/09/2026 | 6 | 20 |
| SCRUM Sprint 2 | 23/09/2026–06/10/2026 | 5 | 18 |
| SCRUM Sprint 3 | 07/10/2026–20/10/2026 | 6 | 19 |
| SCRUM Sprint 4 | 21/10/2026–03/11/2026 | 6 | 22 |
| SCRUM Sprint 5 | 04/11/2026–17/11/2026 | 6 | 20 |
| SCRUM Sprint 6 | 18/11/2026–01/12/2026 | 6 | 24, incluidos 3 puntos *stretch* |

La comprobación final `project = SCRUM ORDER BY key ASC` devuelve `44 de 44`, y el backlog sin sprint contiene únicamente las tres historias `PB` por 13 puntos.
