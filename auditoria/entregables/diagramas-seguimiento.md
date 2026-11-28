# Diagramas del Entregable — Seguimiento de Proyecto (`SGD-AVEIT`)

> **Entregable destino:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\03_Seguimiento_de_Proyecto_S0_S5_SGD_AVEIT.html`  
> **Fecha:** 28/11/2026  
> **Versión:** `v1.5.0`

---

## 1. Inventario de Marcadores `[DIAGRAMA: ...]`

| # | Marcador en el HTML | Ubicación (Sección / Página) | Tipo sugerido | Fuente de datos verificada |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `[DIAGRAMA: Roadmap inicial adaptable S0-S6 con corte de MVP y Releases]` | §2.1.1 A · Página 4 (Figura 1) | Línea temporal / Flowchart horizontal (`flowchart LR`) | `auditoria/entregables/_aprobacion.md` (`DEC-T2`, `SG-05`), `auditoria/entregables/_brief-comun.md` (§1.4) y `auditoria/traspaso-sprint6.md`. |
| **2** | `[DIAGRAMA: User Story Map con corte horizontal de MVP en Sprint 2 y Releases]` | §2.1.7 · Página 9 (Figura 2) | Mapa bidimensional Backbone × Releases (matriz visual / Mermaid / Figma) | `docs/gestion-proyecto/Seguimiento de Proyecto.md` (§2.1.6–§2.1.7), `auditoria/entregables/_aprobacion.md` (`SG-02`, `SG-05`, obs. #18 y #20) y `auditoria/traspaso-sprint6.md`. |
| **3** | `[DIAGRAMA: Evolución de Velocidad por Sprint (S1-S5) y Traspaso a Sprint 6]` | §2.8.2 · Página 17 (Figura 3) | Gráfico de barras comparativo (`xychart-beta` o SVG/PNG) | `docs/gestion-proyecto/Seguimiento de Proyecto.md` (S1: 20/20 SP, S2: 23/23 SP, S3: 36/36 SP), `auditoria/entregables/seguimiento-discrepancias.md` (S4: 13 SP al 03/11 y 19/19 SP totales; S5: 9 bloques integrados + 10 ítems a S6) y `DEC-T3`. |
| **4** | `[DIAGRAMA: Flujo de integración real vs. planificación en Sprint 4 y Sprint 5 Consolidado]` | §2.8.3 · Página 18 (Figura 4) | Línea temporal comparativa (Planificado vs. Merge real en `main`) | `auditoria/entregables/seguimiento-discrepancias.md` (§a.1, §b), `auditoria/traspaso-sprint6.md` y fechas reales de PRs `#63`–`#79` y commit `6a60167`. |

---

## 2. Especificación Breve para Producción de Cada Diagrama

### Figura 1 — Roadmap inicial adaptable S0–S6 con corte de MVP y Releases
- **Eje temporal:** S0 (`18/08–08/09`), S1 (`08/09–21/09`, Release R0), S2 (`22/09–06/10`, **Corte de MVP · Release R1**), S3 (`07/10–20/10`, Jira `08/10`, cierre `22/10`, Release R2), S4 (`21/10–03/11`, apertura operativa `22/10`, Release R3), S5 Consolidado (`04/11–23/11`, Release R4), S6 (Post-Regularidad, Release R5).
- **Anotación obligatoria:** Indicar explícitamente que es un roadmap adaptable sujeto a velocidad real y feedback del PO/AVEIT, y destacar visualmente la línea de corte horizontal de **MVP en Sprint 2**.

### Figura 2 — User Story Map con corte horizontal de MVP en Sprint 2 y Releases
- **Backbone (6 columnas):** 1. Acceso y Padrón → 2. Apertura T01 → 3. Descargos y Plazos → 4. Sala TD y Firma Colegiada → 5. Libro Mayor y Portal → 6. Balances y Cierre.
- **Cortes horizontales (6 filas):** Release R0 (S1), **MVP · Release R1 (S2)** (resaltado con línea de corte horizontal), Release R2 (S3), Release R3 (S4), Release R4 (S5 Consolidado), Release R5 (Sprint 6).
- **Regla de consistencia:** `US-13` debe figurar como *Editor Unificado de Resolución Oficial (sin votación nominal)* y `US-14` como *Firma Colegiada de Activos (4.º/5.º/6.º)*.

### Figura 3 — Evolución de Velocidad por Sprint (S1–S5) y Traspaso a Sprint 6
- **Series por sprint:**
  - **S1:** 20 SP comprometidos / 20 SP integrados (100%).
  - **S2 (MVP):** 23 SP comprometidos (18 + 5 emergente) / 23 SP integrados (100%).
  - **S3:** 36 SP comprometidos (19 + 17 refinamiento) / 36 SP integrados (100%).
  - **S4:** 19 SP comprometidos / 13 SP integrados al corte `03/11` (+6 SP integrados al `12/11`, 19/19 SP totales).
  - **S5 Consolidado:** 44 SP base + 3 SP Stretch planificados → representar 9 bloques integrados (sin inventar SP para los macros) y 10 ítems trasladados al Sprint 6.

### Figura 4 — Flujo de integración real vs. planificación en Sprint 4 y Sprint 5 Consolidado
- **Carril superior (Planificado):** Corte S4 `03/11/2026` (19 SP + 8 SP adelanto) y cierre S5 Consolidado `18/11/2026` (44 SP).
- **Carril inferior (Real en `main`):**
  - Al `03/11`: `SCRUM-70` (`25/10`), `SCRUM-51` (`26/10`), `SCRUM-54` (`02/11`), ABM Reglamentos (`03/11`).
  - `04/11–12/11`: `SCRUM-63` parcial (`04/11`), `SCRUM-56` (`05/11`), `SCRUM-62` parcial (`05/11`), `SCRUM-53` (`12/11`).
  - `16/11–23/11`: PRs `#74–#75` (`16/11`), PR `#76` (`16/11`), PR `#77` (`17/11`), PRs `#78–#79` y `SCRUM-129` (`23/11`).
  - **Salida al Sprint 6:** 10 ítems parciales, no implementados o no verificables.
