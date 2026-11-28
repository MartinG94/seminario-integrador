# Registro de Cambios — Definición del Producto / Solución (`SGD-AVEIT`)

> **Fecha de redacción:** 28/11/2026  
> **Entregable generado:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\04_Definicion_del_Producto_SGD_AVEIT.html`  
> **Archivo de diagramas asociado:** `auditoria/entregables/diagramas-definicion-producto.md`  
> **Base de aprobación aplicada:** `auditoria/entregables/_aprobacion.md` (`DEC-T1`, `DEC-T2`, `DEC-T3`, `DEC-T5`, `DEC-DP1`, `DP-01` a `DP-08`).

---

## 1. Cambios Aplicados y Justificación

| Código | Cambio Aplicado en `04_Definicion_del_Producto_SGD_AVEIT.html` | Motivo / Fuente de Autoridad |
|---|---|---|
| **DEC-T1 / DP-08** | Carátula unificada: **Grupo N° 13** (corrige `Grupo Nº 04` de S4), cátedra `Seminario Integrador — Curso 3K2`, Fecha de Entrega `28/11/2026`, N.º de Entrega `Regularidad`, versión `v2.0.0`, sin campo "Fecha de examen", docentes `Ing. María Irene Mac William`, `Ing. Silvina Arenas`, tutor `Ing. Fernando Sanabria`, acrónimo `SGD-AVEIT`, 7 integrantes con Legajo UTN y logos institucionales UTN/AVEIT. | Unificación transversal aprobada y consistencia con `Carátula gral.docx` y `02_Plan_de_Proyecto_SGD_AVEIT.html`. |
| **DP-01 / Regla 13** | Consolidación en un único documento maestro (`v2.0.0`, `28/11/2026`) preservando intactas en la **Historia de Revisión** las entradas históricas inmutables `v1.0.0` (`08/10/2026` — Sprint 2) y `v1.1.0` (`04/11/2026` — Sprint 4). | `DEC-DP1` y Regla 13 de `AGENTS.md` (inmutabilidad de fechas históricas). |
| **DEC-T2 / DP-08** | Incorporación de la tabla de convención única de calendario Sprints 0–6 (§3.1): Sprint 3 (`07/10–20/10`, aclarando hito PO `07/10` vs Jira `08/10` y cierre administrativo `22/10`), Sprint 4 (`21/10–03/11` con corte real al `03/11` vs integración `SCRUM-56` el `05/11` y `SCRUM-53` el `12/11`) y Sprint 5 Consolidado (`04/11–23/11/2026`). | Obs. docentes #26, #28 y #29; consistencia con Seguimiento de Proyecto. |
| **DEC-T3 / DP-08** | Unificación de Story Points prevaleciendo Seguimiento S4 (`SCRUM-59`: 5, `SCRUM-61`: 2, `SCRUM-64`: 3, `SCRUM-66`: 5, `SCRUM-67`: 5), explicación de `111/116 SP` en Sprint 0 y reporte por historia/PR de los macros del Sprint 5 sin inventar SP retroactivos. | Obs. docente #16 y `DEC-T3`. |
| **DP-02** | Purga total de **votación nominal** en portada, objetivo, roles, backlog, especificaciones de US, matriz de trazabilidad, diagrama de clases y transiciones de estado. *(Nota de alcance de edición: los métodos residuales `+tieneQuorumVotacion()` / `+calcularMayoriaVotacion()` en `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` fueron excluidos del entregable; ese archivo del repo no se modificó por restricción de modo de redacción controlada sobre 3 archivos.)* | Obs. docentes #23, #24 y #31; decisión PO `07/10/2026`. |
| **DP-03** | Corrección técnica integral contra el código real: 6 estados canónicos exactos (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`), resultados reales de Valoración T03 (`ACCEPTED` / `REJECTED`), roles reales (`SOCIO`, `FISCALIZADORA` vigente en S5 con split trasladado a S6, `CD`, `TD`, `ADMIN`), categorías `Pasivo` (`PASSIVE`, 1.º–3.º) y `Activo` (`ACTIVE`, 4.º–6.º), arquitectura **monolito modular** Django 4.2 LTS + DRF / Angular 14.2+ / MySQL 8.0 en Docker Compose, y nombres reales de suites de prueba (`test_t03_valuation_api`, `test_resolution_preview_api`, `test_resolution_api`). | Discrepancias a.2, a.3, a.6, a.7 y a.8 de `definicion-producto-discrepancias.md`. |
| **DEC-DP1 / DP-04** | Agrupación de todas las Historias de Usuario de Sprints 1–5 en **9 Épicas / Módulos** (§6 y §7) incorporando todo el incremento real del Sprint 5 (`MACRO-01..06`, `SCRUM-129`) y los módulos omitidos de S2–S4 (ABM Reglamentos, `puntaje_ratificado`, Calendario, Outbox, `NotificationCenter`, Mis Solicitudes, Urgencia). Retiro definitivo de la sección de Casos de Uso. Listado explícito en §4.1 de los **10 ítems trasladados al Sprint 6** (`auditoria/traspaso-sprint6.md`), corrigiendo el estado de `SCRUM-62` y `SCRUM-63` (PDF y brecha RBAC). | `DEC-DP1`, Regla 12 de `AGENTS.md`, `auditoria/traspaso-sprint6.md` y obs. #28/#29. |
| **DP-05** | Respuesta técnica explícita en §5.1 a las 3 preguntas docentes: **#32** (`IsNotInvolvedInExpediente` HTTP 403 + `ComposicionTribunal` con suplentes 4.º/5.º/6.º), **#33** (editor unificado + 3 firmas electrónicas activas con hash SHA-256 en `Resolucion.firmantes` sin votación nominal) y **#34** (`AdecuacionT01` versionada preservando descargos previos, notificación a solicitante/involucrados y reapertura de `PeriodoApelacion` en días hábiles). | Obs. docentes #32, #33 y #34. |
| **DP-06 / DEC-T5** | Construcción de la **Matriz de Trazabilidad Bidireccional Completa** (§7.2, `RF-01` a `RF-26`, Sprints 1–5) vinculando *Normativa → RF → Épica/US → Cobertura de Pruebas → Estado*. Declaración transparente en §7.3 de la cobertura estática verificada (`114` suites backend / `55` specs frontend) y marcación explícita de la ejecución viva y capturas como `[DATO FALTANTE: ...]`. | Obs. docentes #25 y #27; `DEC-T5`. |
| **DP-07** | Extracción directa desde los modelos Django reales de: Catálogo de Clases (§8), **DER Físico Completo** (§9, **35 tablas** con PK, FK, UK, tipo de dato, longitud y valores posibles/enums) y **Tabla de Transición de Estados** (§10, indicando método, épica/US responsable, estado inicial, estado final y precondiciones). | Requisitos obligatorios de la Guía de Documentación para proyectos Ágiles. |
| **DP-08** | Documentación de Arquitectura, Ambiente de Implementación, Distribución por Nodos en Docker Compose y declaración de Staging/Producción AVEIT como **trasladada al Sprint 6** (§11). Reemplazo de Mermaid crudo por marcadores `[DIAGRAMA: ...]` centralizados en `auditoria/entregables/diagramas-definicion-producto.md`. | Obs. de maquetación (Mermaid crudo en S4) y requisito de despliegue realista sin inventar infraestructura. |
| **Redacción externa** | Eliminación de rutas internas del repositorio (`backend/...`, `frontend/...`, `auditoria/...`, `docs/...`) en el cuerpo del entregable HTML destinado a la cátedra. | Regla 6 de redacción controlada para lector externo. |

---

## 2. Listado Consolidado de `[DATO FALTANTE: ...]` en el Entregable

Los siguientes datos exigidos por la cátedra o la plantilla no constan verificados en el repositorio actual y se dejaron marcados explícitamente sin inventar información:

1. **Capturas actualizadas de interfaz de usuario (Sección 7, Págs. 7–11):**
   - E1: `[DATO FALTANTE: Capturas actualizadas de Login por N.º de Socio, Ranking de Socios paginado y Legajo Integral en vista desktop/mobile]`
   - E2: `[DATO FALTANTE: Capturas actualizadas de formulario Crear Expediente T01, Mis Solicitudes y Tablero Kanban/Tabla de 6 estados]`
   - E3: `[DATO FALTANTE: Capturas de Calendario Institucional y NotificationCenter accesible]`
   - E4: `[DATO FALTANTE: Capturas de carga responsive de Formulario T02/T03, historial de versiones y adjuntos]`
   - E5: `[DATO FALTANTE: Capturas del Visor Autorizado, valoración T02/T03 con precedentes, composición TD y panel de apelación T01]`
   - E6: `[DATO FALTANTE: Capturas de Editor de Resolución, vista previa PDF, panel de firmas colegiadas y flujo de Enmienda]`
   - E7: `[DATO FALTANTE: Capturas de Portal Mis Expedientes, saldo individual y vista de publicación oficial con censura médica]`
   - E8: `[DATO FALTANTE: Capturas de Eventos y Asistencia rediseñado y panel de Reportes / Balance Art. 137]`
   - E9: `[DATO FALTANTE: Capturas actualizadas de módulo Reglamentos y Panel de Administración /admin/parametros]`
2. **Evidencia de ejecución viva de pruebas automatizadas (Sección 7.3, Pág. 13):**
   - `[DATO FALTANTE: Log de ejecución viva final de pytest y Karma/Jasmine con fecha, cantidad exacta de casos aprobados y evidencia específica en permisos RBAC, vencimientos de plazos y transacciones del libro mayor]`
3. **Infraestructura física / cloud de A.V.E.I.T. (Sección 11.3, Pág. 21):**
   - `[DATO FALTANTE: Especificación física/cloud del servidor central y equipamiento de red de A.V.E.I.T. — Despliegue en Staging/Producción trasladado al Sprint 6 (SCRUM-66)]`
4. **Actas UAT firmadas por autoridades institucionales:** declaradas como no verificables y formalmente **trasladadas al Sprint 6** (`SCRUM-67`, §§4.1 y 7).

---

## 3. Marcadores de Diagramas Incorporados

Todos los diagramas gráficos se dejaron como marcadores `[DIAGRAMA: ...]` en el HTML y cuentan con su fuente Mermaid/especificación en `auditoria/entregables/diagramas-definicion-producto.md`:
1. `[DIAGRAMA: Diagrama de Clases de Dominio SGD-AVEIT]` (Pág. 14)
2. `[DIAGRAMA: Diagrama Entidad-Relación (DER) Físico SGD-AVEIT]` (Pág. 15)
3. `[DIAGRAMA: Diagrama de Transición de Estados del Expediente Disciplinario]` (Pág. 20)
4. `[DIAGRAMA: Diagrama de Despliegue — Contenedores Docker Compose y Nodos]` (Pág. 21)
5. `[DIAGRAMA: Lay-Out de Equipamiento — Topología de Despliegue]` (Pág. 21)
