# Registro de Cambios — Plan de Proyecto (`SGD-AVEIT`, `v2.1.0`)

> **Fecha de consolidación:** `28/11/2026`  
> **Archivo generado:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\02_Plan_de_Proyecto_SGD_AVEIT.html`  
> **Base visual:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Plantillas\02_Plan_de_Proyecto_SGD_AVEIT.html` y `00_Caratula_General_SGD_AVEIT.html`.  
> **Referencia de decisiones aplicadas:** `DEC-T1`, `DEC-T3`, `DEC-T4`, `DEC-PP1`, `DEC-PP2`, `DEC-PP3`, `PP-01` a `PP-08` (`auditoria/entregables/_aprobacion.md`).

---

## 1. Cambios Aplicados

| ID Decisión / Ítem | Sección afectada | Cambio aplicado | Motivo |
|---|---|---|---|
| **DEC-T1 / PP-08** | Carátula (Pág. 1) | Integración de la Carátula General institucional con título **`Plan de Proyecto`** (en lugar de *"Análisis del Sistema"*), Grupo `13`, Curso `3K2`, N.º de Entrega `Regularidad`, Versión `v2.1.0`, Fecha de Entrega `28/11/2026`, acrónimo `SGD-AVEIT`, nómina docente completa y 7 integrantes con Legajo UTN. Se suprimió el campo *"Fecha de examen"*. | Cumplir formato uniforme de la Guía de Cátedra y unificación transversal de carátulas (obs. #6). |
| **PP-08** | Índice (Pág. 2) y §13 Historial de Cambios (Pág. 17) | Índice regenerado con numeración real de páginas (`Pág. 3` a `Pág. 17`). Se preservaron intactas las 3 filas históricas (`1.0.0` `01/09/2026`, `1.0.1` `02/09/2026`, `2.0.0` `03/09/2026`) y se agregó `2.1.0` (`28/11/2026`). | Regla de inmutabilidad histórica (`AGENTS.md` Regla 13) y trazabilidad editorial. |
| **PP-07 / DEC-T4** | Todo el documento | Eliminación de `"Provicional"` (§2), menciones a skills internas de IA (`systemClassifier`, `/requirementsExtractor`, `useCaseExtractor`), expresiones ambiguas (*"cómputo algorítmico"*), reportes de ejecución del Sprint 5 / traspasos al Sprint 6, tickets `SCRUM-*` y rutas/símbolos internos del repositorio. | Límite temporal estricto del Plan de Proyecto (no incluye Sprint 5) y redacción orientada a lector externo (obs. #6 y #8). |
| **DEC-PP3 / PP-07** | §4 y antigua §12 | Se eliminó **§4.1 (TGS)** (sección vacía) y **§12 (Casos de Uso `CU-01..CU-12` y BCE)** (incompleta y no exigida por la Guía para proyectos Ágiles). Se renumeró la estrategia de entregas y riesgos como §12 e Historial/Glosario como §13. | Evitar secciones vacías o promesas incumplidas en la entrega de regularidad. |
| **PP-01** | §3, §4, §6, §7, §8, §9, §10, §12.1 | Purga definitiva de: (a) votación nominal individual (incluyendo RBAC y trazabilidad), reemplazada por editor unificado y firma colegiada de **3** activos (4.º, 5.º y 6.º año); (b) triggers SQL y tabla `auditoria_puntos`, reemplazados por libro mayor transaccional de solo inserción en capa de dominio; (c) `Tailwind CSS` en §3.1, reemplazado por Angular 14.2+ / TypeScript / Angular Material; (d) *"al menos dos firmas"* en `RNF-03`/`RN-07` → **3 firmas activas**; (e) *"links directos con token"* en `R-04` → autenticación JWT por N.º de Socio. | Coherencia total con el diseño y arquitectura vigentes y cierre de obs. #9, #13, #23 y #31. |
| **PP-02** | §6 Matriz RBAC (Pág. 6) | Alineación a los 5 roles vigentes (`SOCIO`, `FISCALIZADORA`, `CD`, `TD`, `ADMIN`) y categorías `Pasivo` (1.º–3.º) / `Activo` (4.º–6.º). Se habilitó `C/U` para `CD` y `TD` en descargos T02/T03 y apelaciones T01 cuando actúan como socios imputados, explicitando la regla de apartamiento automático por conflicto de interés. | Consistencia con el modelo RBAC real y cierre de obs. #11. |
| **DEC-PP1 / DEC-PP2 / PP-05** | §7 y §8 (Págs. 7–10) | Ampliación del catálogo de `RF-01..RF-15` a **`RF-01..RF-26`** incorporando los módulos omitidos (Autenticación JWT/Padrón Read-Only, Ranking y Legajo, Calendario Institucional, Eventos/Asistencia 3:1, Apelación y Adecuación T01, Apartamiento y Suplencias TD, Visor Autorizado con auditoría, Exclusión fundada y Enmienda con contra-asientos, Censura médica, ABM Reglamentos, Panel Admin, Repositorio de Jurisprudencia y Centro de Notificaciones UI). Repriorización MoSCoW (`Must` / `Should` / `Could`) con entregas incrementales tempranas (**MVP en Sprint 2** + Releases 2, 3 y 4) y actualización completa de la Matriz de Trazabilidad Normativa (§8). | Cierre de obs. #7, #10 y #18 (evitar concentración total de `Must Have` al final). |
| **PP-03** | §9 (`RN-05` y `RN-11..RN-14`, Págs. 11–12) | Alineación de `RN-05` a los 6 nombres canónicos (*Expediente Creado*, *En período de justificaciones*, *Justificaciones en revisión*, *En espera de resolución*, *Pendiente de firma y envío*, *Expedientes ya emitidos*), contemplando Apelación/Adecuación T01 y Enmienda con contra-asientos. Se agregaron `RN-11` (regla 3:1), `RN-12` (apelación T01), `RN-13` (censura médica) y `RN-14` (exclusión y enmienda). | Coherencia con el ciclo procesal real del dominio. |
| **PP-04** | §10 (`RNF-01`, `RNF-04`, `RNF-05`), §11.2 (`RES-04`) y §12.1 (`R-02`) | Reformulación explícita de Lighthouse/SUS (`RNF-01`), prueba de carga de 50 usuarios (`RNF-04`), auditoría OWASP Top 10 (`RNF-05`) y entorno de Staging (`RES-04`/`R-02`) como **criterios objetivo pendientes de verificación**. | Evitar presentar como verificadas métricas o infraestructuras aún no validadas. |
| **PP-06** | §11.1 (Pág. 14) | Ampliación de arquitectura e integración: stack real (Python 3.12 + Django 4.2 LTS + DRF, Angular 14.2+ + TypeScript + Angular Material, MySQL 8.0, Docker Compose), Capa Anticorrupción Read-Only sobre padrón legado, autenticación JWT por N.º de Socio y equivalencia de permisos legados (`tribunal_bajo/medio/alto`). | Cierre de obs. #15. |
| **DEC-T3** | §12 (Pág. 16) | Explicitación en el roadmap del backlog inicial unificado en **116 Story Points** (aclarando el ajuste desde la estimación preliminar de 111 SP) en coherencia con Seguimiento de Proyecto. | Cierre de obs. #16. |

---

## 2. Datos Faltantes Registrados

Los siguientes datos exigidos por la cátedra o referenciados en restricciones institucionales no existen en ninguna fuente verificable y **no fueron inventados**:

1. **Acta de acuerdo formal de despliegue en servidor central de A.V.E.I.T. (`RES-05`):** marcado en el documento como `[DATO FALTANTE: Acta de acuerdo formal de despliegue en servidor central AVEIT]`.
2. **Autor de la versión histórica `1.0.1` (`02/09/2026`):** se conserva `-` por inmutabilidad histórica.
3. **Mediciones ejecutadas de `RNF-01` (Lighthouse/SUS), `RNF-04` (carga 50 usuarios), `RNF-05` (OWASP Top 10) y evidencia de Staging operativo (`RES-04`/`R-02`):** declarados explícitamente como *criterios objetivo pendientes de verificación* (propios de instancias posteriores de prueba/homologación).
4. **Diagramas visuales exportados (3 figuras):** dejados como marcadores `[DIAGRAMA: ...]` y catalogados en `auditoria/entregables/diagramas-plan-de-proyecto.md`.
