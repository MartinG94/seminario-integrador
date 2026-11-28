# Registro de Cambios — Seguimiento de Proyecto (`v1.5.0`)

> **Entregable redactado:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\03_Seguimiento_de_Proyecto_S0_S5_SGD_AVEIT.html`  
> **Fecha de consolidación:** 28/11/2026  
> **Base aprobada:** `auditoria/entregables/_aprobacion.md` (`DEC-T1`, `DEC-T2`, `DEC-T3`, `DEC-T5`, `DEC-SG1`, `SG-01` a `SG-08`).

---

## 1. Cambios Aplicados y Motivo

| Código | Sección(es) afectada(s) | Cambio aplicado | Motivo / Referencia |
| :--- | :--- | :--- | :--- |
| **DEC-T1 / SG-08** | Carátula (Pág. 1) y §2.1.2 (Pág. 6) | Carátula unificada con `Grupo N° 13`, `Curso 3K2`, `N.º de Entrega: Regularidad`, `Versión v1.5.0`, `Fecha de Entrega: 28/11/2026`, sin campo "Fecha de examen", nómina docente correcta (`Ing. María Irene Mac William`, `Ing. Silvina Arenas`, tutor `Ing. Fernando Sanabria`), acrónimo `SGD-AVEIT` y rótulo **"Legajo UTN"** en lugar de "Número de Socio". Logos institucionales UTN y AVEIT embebidos igual que en `02_Plan_de_Proyecto_SGD_AVEIT.html`. | Homogeneidad institucional entre los 4 entregables y corrección del error de rotulado de legajos. |
| **SG-01 (Regla 13)** | Historia de Revisión (Pág. 2) | Se conservaron intactas las 5 filas históricas (`v1.0.0` `01/09`, `v1.1.0` `02/09`, `v1.2.0` `07/10`, `v1.3.0` `22/10` y `v1.4.0` `04/11/2026` con su redacción original de cierre S4 + apertura S5 Consolidado) y se agregó `v1.5.0` con fecha **`28/11/2026`**. | Respeto estricto a la inmutabilidad de versiones y fechas ya presentadas (`AGENTS.md`, Regla 13). |
| **SG-02** | Índice (Pág. 3), §2.1.6 (Pág. 8), §2.1.7 (Pág. 9), §2.7.3 (Pág. 15) y §2.8.1 (Pág. 16) | Se corrigieron las regresiones de la copia previa del repo: `US-13` y Story Map actualizados a **Editor Unificado de Resolución Oficial + Firma Colegiada sin votación nominal**; se recuperó la Retrospectiva completa del Sprint 4 (`03/11/2026`) y la apertura de Sprint 5 Consolidado; se corrigió la numeración y el Índice completo (Págs. 2–18). | Consistencia con la directiva del PO del `07/10/2026` y completitud documental. |
| **SG-05 / Obs. #16–#20** | §2.1.1 A (Pág. 4), §2.1.6 (Pág. 8) y §2.1.7 (Pág. 9) | 1) Sustitución de *"Velocidad Promedio Proyectada"* por **"Carga promedio planificada"** (`~19,3 SP/Sprint`). 2) Conversión del calendario en **"Roadmap inicial adaptable"** sujeto a velocidad real y feedback. 3) Formalización del **corte horizontal de MVP en Sprint 2 (Release R1)** y **Releases R0–R5** (sin "MVP por sprint"). 4) Conciliación explícita de `116 SP` frente a `111 SP` (exclusión preliminar de `US-19`). 5) Repriorización MoSCoW (`16 Must`, `2 Should` en `US-17`/`US-18`, `1 Could` en `US-19`). | Cumplimiento integral de las observaciones docentes #16, #17, #18, #19 y #20. |
| **SG-07** | §2.1.1 D (Pág. 5), §2.1.5 (Pág. 7) y §2.5 (Pág. 12) | Alineación del stack real (**Python 3.12 + Django 4.2 LTS + DRF**, **Angular 14.2+ + TypeScript + Angular Material**, **MySQL 8.0**, **Docker Compose**), DoD sobre integración directa en **`main`** (sin `develop`, aclarando Staging y OpenAPI/Swagger en S6) y vigencia del rol **`FISCALIZADORA`** en Sprint 5 (partición trasladada a S6). | Fidelidad al código real y decisión D-02. |
| **DEC-T2 / SG-06** | Índice (Pág. 3), §2.1.1 A (Pág. 4) y §§2.2–2.8 | Aplicación de la convención única de calendario: Sprint 1 (`08/09–21/09`), Sprint 2 (`22/09–06/10`), Sprint 3 (`07/10–20/10`, hito PO `07/10` / Jira `08/10` / cierre `22/10`), Sprint 4 (`21/10–03/11`, apertura operativa `22/10`) y Sprint 5 Consolidado (`04/11–23/11/2026`). | Resolución de la observación docente #26. |
| **SG-03 / Obs. #28–#29** | §2.7.1–§2.7.2 (Págs. 14–15) | Explicitación del corte real del Sprint 4 al `03/11/2026`: integradas al corte `SCRUM-70` (`25/10`), `SCRUM-51` (`26/10`), `SCRUM-54` (`02/11`) y ABM Reglamentos (`03/11`); integradas post-corte `SCRUM-56` (`05/11`) y `SCRUM-53` (`12/11`); adelantos `SCRUM-63` (`04/11`) y `SCRUM-62` (`05/11`) aclarados como parciales. | Resolución de las observaciones docentes #28 y #29. |
| **SG-04 / DEC-T3 / Obs. #30** | §2.8.1–§2.8.3 (Págs. 16–18) | Documentación del cierre formal del Sprint 5 Consolidado (`04/11–23/11/2026`): 1) Valores unificados de SP de Seguimiento S4 (`SCRUM-59`: 5, `61`: 2, `64`: 3, `66`: 5, `67`: 5). 2) Explicación de viabilidad (obs. #30). 3) Detalle de los **9 bloques implementados** reportando macros por historia/PR sin inventar SP. 4) Tabla de los **10 ítems trasladados al Sprint 6** con estado real y motivo en una línea según `auditoria/traspaso-sprint6.md`. | Trazabilidad real del incremento y cumplimiento de la Regla 12 de `AGENTS.md`. |
| **DEC-T5** | §2.8.2 (Pág. 17) | Declaración de cobertura estática verificada (`114` archivos de prueba backend / `55` archivos de prueba frontend) y marca explícita de ejecución viva final como pendiente. | Resolución de la observación docente #27 sin invocar cifras desactualizadas de S4. |
| **DEC-SG1** | §2.1.2 (Pág. 6), §2.1.4 (Pág. 7), §2.7.2 (Pág. 15), §2.8.2–§2.8.3 (Págs. 17–18) | Inserción de marcadores explícitos `[DATO FALTANTE: ...]` en lugar de inventar métricas, fechas o actas no existentes. | Rigor documental y transparencia académica. |
| **Redacción externa y diagramas** | Todo el documento | Eliminación de rutas internas del repositorio y menciones a `auditoria/`; inserción de 4 marcadores `[DIAGRAMA: ...]` inventariados en `auditoria/entregables/diagramas-seguimiento.md`. | Presentación profesional para lector externo (cátedra y autoridades de A.V.E.I.T.). |

---

## 2. Listado Consolidado de `[DATO FALTANTE: ...]` en el Entregable

1. **`[DATO FALTANTE: horas reales dedicadas por integrante en los Sprints 1 a 5]`** — Págs. 6 y 18 *(solo existe la capacidad nominal planificada en Sprint 0: 154 hs/sprint)*.
2. **`[DATO FALTANTE: gráficos reales de Burndown, Diagrama de Flujo Acumulado (CFD), Lead Time y Cycle Time exportados de Jira para los Sprints 1 a 5]`** — Págs. 7 y 18.
3. **`[DATO FALTANTE: acta o constancia formal de aceptación del PO y autoridades de A.V.E.I.T. al corte del 03/11/2026]`** — Págs. 15 y 18.
4. **`[DATO FALTANTE: resultado de ejecución viva actualizada de pytest y Angular Karma al cierre del 23/11/2026]`** — Págs. 17 y 18 *(solo se certifica cobertura estática de 114/55 archivos)*.
5. **`[DATO FALTANTE: fecha real, técnica y acta de la Sprint Review y Retrospectiva del Sprint 5]`** — Pág. 18.
6. **`[DATO FALTANTE: actas formales de aceptación del Product Owner y homologación UAT de autoridades de A.V.E.I.T. al cierre del Sprint 5 (23/11/2026)]`** — Pág. 18.
7. **`[DATO FALTANTE: Story Points formales en Jira para los macros ejecutados en Sprint 5 (SCRUM-86, 87, 89/101–103, 91, 93/114–115 y 129)]`** — Pág. 18.
