# Auditoría de Discrepancias — Estudio Inicial (SGD-AVEIT)

> **Fecha de auditoría:** 27/11/2026  
> **Alcance:** Entregable **Estudio Inicial** (**NO** incluye la ejecución del Sprint 5).  
> **Fuentes contrastadas:**
> - Entregable presentado: `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Estudio_Inicial.docx` (`v1.5.0`, 18/08/2026).
> - Copia alineada en repositorio: `docs/formales/Estudio_Inicial.docx` (`v1.6.0`, 27/11/2026).
> - Registro canónico y brief común: `auditoria/registro-canonico.md` (§1, §2, §4 y §5) y `auditoria/entregables/_brief-comun.md`.
> - Devoluciones docentes: `retroalimentaciónS0.txt`, `retroalimentaciónS4.txt` y `Notas de Profes-Reuniones.docx`.

---

## a) Qué afirma el documento que el sistema no hace o que no está verificado

| Tema / Afirmación | Presentado (`v1.5.0`) | Corregido en repo (`v1.6.0`) | Aún persiste en `v1.6.0` (o nuevo desvío) |
|---|---|---|---|
| **Votación nominal colegiada** | §1, §3.7.1 (*"registro nominal de votos"*), §3.9 (*"votar y emitir resoluciones"*) y §4.2 (*"emitir votos nominales"*) afirman votación nominal. | Reemplazada en §1, §3.7.1 y §4.2 por redacción unificada y firma electrónica colegiada de 3 integrantes activos (4.º, 5.º y 6.º año), descartada por PO el 07/10/2026. | **Persiste en 3 lugares:** §3.9 (*"revisar descargos, **votar** y emitir resoluciones colegiadas"*), §3.7 Proceso 3 (*"Falta de un registro formal e inalterable de los **votos individuales**"*), y el título de la fila *"Deliberación y **Votación**"* en §3.7.1. |
| **Acrónimo y nombre del sistema** | Ficha de carátula dice `SDG-AVEIT – (Nombre provisional, en discusión)` (error de tipeo `SDG`). | Corregido a `SGD-AVEIT`. | Sin pendientes. |
| **Cómputo algorítmico y triggers MySQL** | Carátula y §1 mencionan *"cómputo algorítmico"*; §3.7.1 afirma *"auditoría inmutable mediante triggers y tabla histórica en MySQL"*. | Reemplazado por cómputo transaccional inmutable mediante libro mayor; eliminada mención a `triggers`. | Sin pendientes en `v1.6.0` respecto a triggers, pero ver fila de contaminación Sprint 5/6 abajo. |
| **Alertas automáticas `-7` y `-10`** | §3.7.1 afirma *"Disparo automatizado de alertas preventivas (-7 pts) y notificación crítica (-10 pts)"*; §4.2 lo presenta como capacidad asegurada. | §1 y §3.7.1 aclaran que quedaron parciales y trasladadas al Sprint 6 (`SCRUM-62`). | **Persiste en §4.2** (*Mitigación de Errores Críticos*), donde sigue asegurando *"advertencia preventiva a los 7 puntos"* sin acotar alcance. En código `ThresholdAlertEngine` no está conectado a `LedgerService`/`emitir_resolucion` ni tiene endpoint/vista. |
| **Balance Cuatrimestral Art. 137 "con un clic"** | §1, §3.4 y §3.7.1 afirman generación y exportación instantánea *"con un clic"* por subcomisión y categoría. | §1 y §3.7.1 acotan que existe en JSON/CSV y que la exportación PDF + cierre RBAC pasan a Sprint 6 (`SCRUM-63/124`). | **Persiste en §3.4** (*"La plataforma SGD-AVEIT automatizará su generación"*) sin acotar formato ni alcance. |
| **Categorías de socios (`Junior/Senior` vs `PASSIVE/ACTIVE`)** | Todo el documento usa `Juniors (1.º–2.º)` y `Seniors (3.º–6.º)` y define `Socio Pasivo` aparte. | Glosario y §3.7.1 agregan equivalencia con código: `PASSIVE` (1.º–3.º) / `ACTIVE` (4.º–6.º). | **Persiste inconsistencia:** el Glosario define `Socio Junior (Pasivo en código: PASSIVE, 1.º a 3.º)` y dos líneas debajo mantiene otra definición de `Socio Pasivo` sin conciliarlas; §1, §2, §3.4, §3.5.6 y §3.7 Proceso 5 siguen usando `1.º–2.º` y `3.º–6.º` sin aclaración. |
| **Firma electrónica con "hash inalterable"** | §3.7.1 afirma *"Firma electrónica interna con sesión autenticada, timestamp, ID de miembro y **hash inalterable**"*. | No modificado. | **Persiste en `v1.6.0`.** En código la firma colegiada se acredita mediante sesión autenticada y registro de los 3 firmantes (`Resolucion.firmantes`), pero **no está verificado** un hash criptográfico inalterable por firma. |
| **Cron/daemon automatizado en producción** | §3.7.1 afirma *"Cron/daemon automatizado con sellado de tiempo y temporizador preclusivo fehaciente e inalterable"*. | No modificado. | **Persiste en `v1.6.0`.** Existe `close_expired_deadlines.py`, pero su ejecución programada en entorno real/staging **no es verificable** desde el repositorio. |
| **Portal "público" de resoluciones** | §3.7.1 (*"Portal responsive público"*), §3.9 y §4.2 (*"consulta pública"*). | No modificado. | **Persiste en `v1.6.0`.** El acceso a resoluciones y saldos requiere autenticación JWT por `numero_socio` (`/mis-expedientes` y publicación oficial protegida con censura médica), no es público anónimo. |
| **Defecto grave en §3.5.3 (*Catálogo de Formularios*)** | §3.5.3 titula *"Catálogo de Formularios Administrativos Oficiales"*, pero **repite textualmente los 6 estados** de §3.5.2 en lugar de listar T01/Anexo/T02/T03. | No modificado. | **Persiste íntegro en `v1.6.0`.** |
| **Nombre de módulo inexistente (`"Justificaciones"`)** | §3.5.2 refiere al módulo `"Justificaciones"` para el estado 3. | No modificado. | **Persiste en `v1.6.0`.** En el sistema ese flujo se opera dentro de `/gestionar-expedientes` (*Gestionar Expedientes*). |
| **Contaminación de alcance Sprint 5/6 y rutas internas** | No presente en `v1.5.0`. | Introducido en `v1.6.0`. | **Desvío nuevo en `v1.6.0`:** §1, §3.7.1 e Historial citan `Sprint 6`, `SCRUM-62`, `SCRUM-63/124`, `auditoria/traspaso-sprint6.md`, `auditoria/registro-canonico.md`, `AsientoLibroMayor` y `Resolucion.firmantes`. Contradice la regla de alcance (**Estudio Inicial NO incluye Sprint 5**) y expone rutas/símbolos internos en un entregable académico. |

---

## b) Qué hace el sistema que el documento no dice

*(Solo aspectos pertinentes al dominio y alcance de Estudio Inicial, excluyendo la ejecución del Sprint 5.)*

1. **Regla reglamentaria de acumulación 3:1 de llamados de atención:** §3.5.5 menciona llamados de atención, pero omite la regla de negocio por la cual **3 llamados de atención consolidan `-1` punto negativo** (parte del dominio de eventos/asistencia y disciplina implementado antes de Sprint 5).
2. **Apartamiento por conflicto de interés y régimen de suplencias del TD:** §3.5.4 solo señala que el miembro del TD que inicia una acción no puede juzgarla, pero no describe el mecanismo de apartamiento cuando un miembro del TD está involucrado en el expediente ni la convocatoria de suplentes para cubrir la representación colegiada de 4.º, 5.º y 6.º año (`SCRUM-54`).
3. **Instancia previa de apelación y adecuación de solicitudes T01:** §3.5.5 afirma irrecurribilidad general de decisiones del TD, pero omite la instancia operativa previa de apelación/adecuación de una solicitud T01 con plazo parametrizable (`SCRUM-70`).
4. **Protección y confidencialidad de evidencia médica sensible:** El documento menciona adjuntos de certificados médicos (§3.7 Proceso 2) y transparencia de resoluciones (§4.1/§4.2), pero no explicita la necesidad de resguardar/censurar datos médicos sensibles frente a la consulta general de socios.
5. **Calendario institucional propio (feriados y excepciones):** Menciona el plazo de 5 días hábiles (§3.5.2, §3.7 Proceso 2), pero omite la existencia de un calendario institucional específico de AVEIT con feriados y excepciones que gobierna ese cómputo.
6. **Restricción Read-Only sobre el padrón legado MySQL:** §3.8 menciona el servidor y MySQL con el padrón de socios, pero no explicita que las tablas maestras del padrón institucional preexistente son de **solo lectura** (capa anticorrupción).
7. **Gestión de eventos obligatorios y control de asistencia como origen de causas:** §3.5.2 y §3.7 Proceso 1 mencionan de paso el *"cierre de un evento obligatorio/sancionable"*, pero no describen el proceso actual de convocatoria y registro de asistencia a reuniones/asambleas que dispara las sanciones por inasistencia.
8. **Consulta y mantenimiento versionado del reglamento:** El documento trata los reglamentos como textos estáticos, sin mencionar la necesidad operativa de administrar y auditar los artículos reglamentarios vigentes utilizados al tipificar expedientes.

---

## c) Correcciones de los profesores sin aplicar (cita breve)

| Obs. # | Fuente | Cita breve de la observación docente | Estado real (`v1.5.0` → `v1.6.0`) | Evidencia concreta |
|---|---|---|---|---|
| **#1** | `retroalimentaciónS0.txt` / `Notas de Profes-Reuniones.docx` | *"Reformular los procesos afectados describiendo primero el proceso actual (AS-IS), sin SGD-AVEIT."* / *"En el estudio inicial revisar la parte que hablan de una solución demasiado definida dentro del propio Estudio."* | **Parcial** (en `v1.5.0` y `v1.6.0`) | §3.7 describe los 5 procesos AS-IS, pero el documento mantiene una solución altamente predefinida antes y durante el Estudio: carátula (*Objetivo*, *Metodología: Scrumban*), §1 (*"plataforma 100% web y responsive mobile..."*), §3.4, §3.5.2 (describe los 6 estados como funciones automáticas del sistema), §3.7.1 (Matriz TO-BE con detalles técnicos) y §3.8/§3.9 (*"requerimiento mandatorio... 100% Web y Responsive Mobile-First"*). |
| **#2** | `Notas de Profes-Reuniones.docx` | *"Documentar técnicas y fuentes del relevamiento: entrevistados, roles, documentos y sistemas analizados."* | **Parcial** (en `v1.5.0` y `v1.6.0`) | Se agregó §3.5.6 con técnicas, fuentes documentales, sistemas y rol del PO (Diego G. Sánchez), pero **faltan los nombres/cargos concretos de los entrevistados del TD y Cómputos, las fechas de entrevistas/talleres** y las instancias de refinamiento. Además, el párrafo introductorio de §3.5.6 está mal estilado como `Heading 3`. |
| **#3** | `Notas de Profes-Reuniones.docx` | *"Aclarar quién valida institucionalmente la utilización del procedimiento 2026, dado que el documento indica que 2018 sería el último formalmente aprobado."* | **Parcial** (en `v1.5.0` y `v1.6.0`) | §3.5.1 agrega una fundamentación estatutaria (Arts. 94–96) indicando que el TD dicta la Circular Normativa 001/2026, pero **no identifica autoridades firmantes, fecha de aprobación ni respaldo formal de CD/Asamblea** que cierre la brecha con el reglamento 2018 aprobado por Asamblea. |
| **#4** | `Notas de Profes-Reuniones.docx` | *"Separar oportunidades/necesidades de las decisiones de solución tecnológica."* | **Parcial** (en `v1.5.0` y `v1.6.0`) | §4.2 está orientada a beneficios de negocio, pero sigue anclada en *"La incorporación del sistema SGD-AVEIT..."* e incluye decisiones de diseño (`v1.6.0`: *"redactar la resolución unificada y formalizar la firma electrónica colegiada..."*); además §3.7.1, §3.8 y §3.9 siguen mezclando contexto con decisiones tecnológicas. |
| **#5** | `Notas de Profes-Reuniones.docx` | *"Revisar el nivel de detalle del ámbito físico, conservando solamente aquello relevante para el proyecto."* | **Aplicada** (con detalle menor) | §3.9 ya acotó el ámbito físico a servidor central, PCs administrativas, red UTN FRC, archivo histórico y trabajo remoto del TD. *Menor:* el último párrafo reintroduce prescripciones de solución TO-BE (incluido *"votar"*). |
| **#23** | `Notas de Profes-Reuniones.docx` (28/10/2026) | *"Evaluar si corresponde que la votacion nominal y su modificacion corresponde con la modificacion del plan de proyecto y estudio inicial, y otros."* | **Sin aplicar** (`v1.5.0`) / **Parcial** (`v1.6.0`) | `v1.5.0` mantiene votación nominal en todo el texto. `v1.6.0` la corrigió en §1, §3.7.1 y §4.2, pero dejó 3 residuos (§3.9 *"votar"*, §3.7 Proceso 3 *"votos individuales"*, título *"Deliberación y Votación"* en §3.7.1). |
| **#31** | `retroalimentaciónS4.txt` | *"¿Qué documentos y modelos generales fueron actualizados para reflejar definitivamente la eliminación de la votación nominal?"* | **Sin aplicar** (`v1.5.0`) / **Parcial** (`v1.6.0`) | El Estudio Inicial presentado (`v1.5.0`) nunca se actualizó; `v1.6.0` en repo tiene actualización parcial con los 3 residuos de #23 y sin fecha de entrega formal. |

---

## d) Datos que la cátedra o la plantilla exigen y no existen en ninguna fuente

1. **Fecha real de entrega en Carátula (`Carátula gral.docx`):** figura `xx/xx/2026` en `v1.5.0` y `v1.6.0` → **`dato faltante`**.
2. **Fecha de examen en tabla de Carátula (`Carátula gral.docx`):** figura `DD/MM/AAAA` en `v1.5.0` y `v1.6.0` → **`dato faltante`**.
3. **N.º de Entrega definitivo de la versión revisada:** figura `N° de Entrega: 1` (entrega inicial de Sprint 0); no consta el número de entrega correspondiente a la presentación de regularidad/final → **`dato faltante`**.
4. **Nómina de entrevistados (TD y Subcomisión de Cómputos) y fechas reales de entrevistas/talleres (Obs. #2):** no constan en el repositorio ni en las fuentes documentales auditadas → **`dato faltante`**.
5. **Acta, fecha y autoridades firmantes de la convalidación institucional del Reglamento Procesal 2026 / Circular Normativa 001/2026 (Obs. #3):** no existe documento probatorio ni referencia de fecha/firmantes en las fuentes auditadas → **`dato faltante`**.
6. **Antecedentes de Productos Similares / Análisis de Competencia (`Seminario-Guia de Documentación.pdf`):** sección exigida por la guía para proyectos de producto; no existe relevamiento ni justificación explícita de no aplicabilidad → **`dato faltante`**.
7. **Esquema gráfico / plano simplificado del Lay-Out físico (§3.9):** existe solo descripción textual; no existe diagrama/plano en ninguna fuente → **`dato faltante`** *(si la cátedra requiere representación visual)*.

*(Nota de formato verificada: el encabezado `ÍNDICE` aparece sin entradas generadas en el texto plano del `.docx`; deberá actualizarse el campo de Tabla de Contenido al regenerar el archivo.)*

---

## e) Cambios que dependen de una decisión del usuario (alcance, traslados, criterios)

1. **Limpieza de alcance en `v1.6.0` (retirar Sprint 5/6 y referencias internas del repo):** Confirmar si se eliminan del Estudio Inicial las menciones a `Sprint 6`, `SCRUM-62`, `SCRUM-63/124`, `auditoria/traspaso-sprint6.md`, `auditoria/registro-canonico.md`, `AsientoLibroMayor` y `Resolucion.firmantes` introducidas en `v1.6.0`, para respetar estrictamente que este entregable **no incluye la ejecución del Sprint 5** ni rutas internas.
2. **Grado de depuración de solución TO-BE dentro del Estudio Inicial (Obs. #1 y #4):** Decidir si la Matriz Comparativa TO-BE (§3.7.1) y las definiciones tecnológicas en §1, §3.4, §3.5.2, §3.8 y §3.9 se **eliminan** (dejando el documento 100% AS-IS + necesidades/oportunidades) o si se **reubican al cierre** bajo un apartado explícito de *"Expectativas iniciales del usuario"* (como sugirió `retroalimentaciónS0.txt`).
3. **Metadatos de Carátula y número de versión:** Definir valores reales de **Fecha de Entrega**, **N.º de Entrega** y **Fecha de Examen** (o supresión del campo), y decidir si la versión definitiva reemplaza `v1.6.0` (con fecha real) o avanza a `v1.7.0` manteniendo inmutables `v1.0.0`–`v1.5.0` (`AGENTS.md`, Regla 13).
4. **Criterio terminológico para categorías de socios (`Junior/Senior` vs `Pasivo/Activo`):** Definir si el Estudio Inicial adopta el criterio estatutario (`Juniors 1.º–2.º / Seniors 3.º–6.º`) con una nota única de aclaración frente al modelo operativo (`1.º–3.º / 4.º–6.º`) y cómo resolver la doble definición actual de `Socio Pasivo` en el Glosario.
5. **Reconstrucción de §3.5.3 (*Catálogo de Formularios Administrativos Oficiales*):** Aprobar el reemplazo del bloque duplicado de los 6 estados por la descripción AS-IS de los formularios `T01`, `Anexo T01`, `T02` y `T03`.
6. **Inclusión de aspectos de dominio omitidos (sección b):** Decidir cuáles de los puntos omitidos (regla 3:1, apartamiento/suplencias del TD, apelación/adecuación T01, confidencialidad médica, calendario institucional, padrón Read-Only, eventos/asistencia, ABM reglamentos) se incorporan al Estudio Inicial y cuáles se reservan para Plan de Proyecto / Definición del Producto.
7. **Provisión de datos faltantes (sección d):** Confirmar si el usuario suministrará (a) entrevistados y fechas de relevamiento (Obs. #2), (b) fecha/firmantes o aval institucional del procedimiento 2026 (Obs. #3), y (c) si se agrega una nota de no aplicabilidad para *Antecedentes / Competencia* por ser un sistema institucional a medida para AVEIT.
