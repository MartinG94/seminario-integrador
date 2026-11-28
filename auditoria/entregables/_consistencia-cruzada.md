# Reporte de Consistencia Cruzada — 4 Entregables Formales (`SGD-AVEIT`)

> **Fecha de verificación:** 28/11/2026  
> **Modo:** Comparación objetiva de los 4 HTML generados en `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\`. **Solo reporte de consistencia y diferencias (sin aplicar correcciones).**

---

## 1. Matriz Comparativa General

| Dimensión | `01_Estudio_Inicial` (`v1.6.0`) | `02_Plan_de_Proyecto` (`v2.1.0`) | `03_Seguimiento` (`v1.5.0`) | `04_Definicion_Producto` (`v2.0.0`) | Consistencia |
|---|---|---|---|---|---|
| **Acrónimo** | `SGD-AVEIT` (0 `SDG-AVEIT`) | `SGD-AVEIT` (0 `SDG-AVEIT`) | `SGD-AVEIT` (0 `SDG-AVEIT`) | `SGD-AVEIT` (0 `SDG-AVEIT`) | **Consistente** |
| **Grupo / Curso / Cátedra** | Grupo 13 · 3K2 · Seminario Integrador | Grupo N° 13 / Grupo 13 · 3K2 · Seminario Integrador | Grupo N° 13 / Grupo 13 · 3K2 · Seminario Integrador | Grupo N° 13 / Grupo 13 · 3K2 · Seminario Integrador | **Consistente** *(variante menor: `Grupo 13` vs `Grupo N° 13` en ficha de portada)* |
| **Docentes e Integrantes** | Mac William, Arenas, Sanabria · 7 integrantes (Legajo UTN) | Mac William, Arenas, Sanabria · 7 integrantes (Legajo UTN) | Mac William, Arenas, Sanabria · 7 integrantes (Legajo UTN) | Mac William, Arenas, Sanabria · 7 integrantes (Legajo UTN) | **Consistente** |
| **Fecha / N.º Entrega** | `28/11/2026` · `Regularidad` (sin *Fecha de examen*) | `28/11/2026` · `Regularidad` (sin *Fecha de examen*) | `28/11/2026` · `Regularidad` (sin *Fecha de examen*) | `28/11/2026` · `Regularidad` (sin *Fecha de examen*) | **Consistente** |
| **Historial inmutable** | `v1.0.0`–`v1.5.0` (15–18/08) + `v1.6.0` (28/11) | `v1.0.0`–`v2.0.0` (01–03/09) + `v2.1.0` (28/11) | `v1.0.0`–`v1.4.0` (01/09–04/11) + `v1.5.0` (28/11) | `v1.0.0` (08/10), `v1.1.0` (04/11) + `v2.0.0` (28/11) | **Consistente** |
| **Alcance Sprint 5** | **Excluido** (0 menciones a S5/S6/`SCRUM-*`) | **Excluido** (0 menciones a S5/S6/`SCRUM-*`) | **Incluido** (9 bloques ejecutados `04/11`–`23/11`) | **Incluido** (9 Épicas/Módulos S1–S5 + DER 35 tablas) | **Consistente** |
| **Traslado Sprint 6** | No aplica (0 menciones) | No aplica (0 menciones) | **10 ítems** alineados a `traspaso-sprint6.md` | **10 ítems** alineados a `traspaso-sprint6.md` | **Consistente** |
| **Catálogo RF** | No aplica | `RF-01` a `RF-26` (26 RF) | Referencia a Backlog / Épicas / US | Matriz bidireccional `RF-01` a `RF-26` (26 RF) | **Consistente** |
| **6 Estados canónicos** | 6 estados Art. 12 alineados | 6 estados canónicos alineados | 6 estados canónicos alineados | 6 estados canónicos (`EstadoExpedienteEnum`) | **Consistente** |
| **Votación nominal** | Eliminada (1 mención solo en historial de cambios) | Eliminada (4 menciones en negativo/historial) | Eliminada (10 menciones en negativo/historial) | Eliminada (10 menciones en negativo/historial) | **Consistente** |
| **Roles RBAC** | Órganos estatutarios (Comisión Fiscalizadora) | 5 roles (`SOCIO`, `FISCALIZADORA`, `CD`, `TD`, `ADMIN`) | `FISCALIZADORA` vigente en S5; split trasladado a S6 | `FISCALIZADORA` vigente en S5; split trasladado a S6 | **Consistente** |
| **Categorías de socios** | `Juniors (1.º–2.º)` / `Seniors (3.º–6.º)` + nota de equivalencia operativa (`Pasivo 1.º–3.º` / `Activo 4.º–6.º`) | `Pasivo` (1.º–3.º) / `Activo` (4.º–6.º) | `Pasivo` (1.º–3.º) / `Activo` (4.º–6.º) | `Pasivo` (`PASSIVE`, 1.º–3.º) / `Activo` (`ACTIVE`, 4.º–6.º) | **Diferencia controlada (`DEC-EI2`)** |
| **Stack tecnológico** | Sin prescripción en cuerpo AS-IS | Django 4.2 + DRF · Angular 14.2 + Material · MySQL 8.0 · Docker Compose | Django 4.2 + DRF · Angular 14.2 + Material · MySQL 8.0 · Docker Compose | Monolito modular Django 4.2 + DRF · Angular 14.2 + Material · MySQL 8.0 · Docker Compose | **Consistente** |
| **Rutas internas repo** | 0 (`backend/`, `frontend/`, `auditoria/`, `docs/`) | 0 | 0 | 0 | **Consistente** |
| **Marcadores `[DIAGRAMA]`** | 3 (`diagramas-estudio-inicial.md`) | 3 (`diagramas-plan-de-proyecto.md`) | 4 (`diagramas-seguimiento.md`) | 5 (`diagramas-definicion-producto.md`) | **Consistente (15 total)** |
| **Marcadores `[DATO FALTANTE]`** | 3 | 1 | 13 | 11 | **Consistente (28 total)** |

---

## 2. Diferencias Detectadas (Solo Reporte — Sin Corregir)

1. **Formato de rótulo de grupo en carátula (`Grupo 13` vs `Grupo N° 13`):**
   - `01_Estudio_Inicial` muestra `Grupo 13` en portada y encabezados.
   - `02_Plan_de_Proyecto`, `03_Seguimiento` y `04_Definicion_Producto` muestran `Grupo N° 13` en la ficha de portada y `Grupo 13` en los encabezados de página.
2. **Orden de *Tabla de Contenido* e *Historia de Revisión*:**
   - `01_Estudio_Inicial` y `02_Plan_de_Proyecto` colocan *Tabla de Contenido* al principio e *Historia de Revisión* al final (respetando sus respectivas plantillas HTML).
   - `03_Seguimiento` y `04_Definicion_Producto` colocan *Historia de Revisión* al inicio antes de la *Tabla de Contenido*.
3. **Nomenclatura `Junior/Senior` en `01_Estudio_Inicial` vs `Pasivo/Activo` en `02`/`03`/`04`:**
   - Coherente con lo aprobado en `DEC-EI2`: `01_Estudio_Inicial` conserva el lenguaje estatutario del dominio AS-IS (`Juniors 1.º–2.º` / `Seniors 3.º–6.º`) acompañado de la nota de equivalencia operativa (`Pasivo 1.º–3.º` / `Activo 4.º–6.º`), mientras los otros 3 documentos operan directamente con `Pasivo` / `Activo`.
4. **Presencia de nombres de tablas/servicios técnicos en `04_Definicion_Producto`:**
   - `04_Definicion_Producto` incluye nombres de tablas físicas MySQL (`expedientes_asiento_libro_mayor`, `tribunal_evento`, etc.) y nombres de servicios/clases (`IsNotInvolvedInExpediente`, `T01AppealService`, `Resolucion.firmantes`) requeridos por el DER físico y las respuestas a las observaciones docentes #32–#34. `01`, `02` y `03` no exponen símbolos de implementación (ni ninguno de los 4 expone rutas de archivos del repositorio).
5. **Desfase de fecha entre HTML en `Entregables/` (`28/11/2026`) y archivos ya commiteados en el repo (`27/11/2026`):**
   - Los 4 HTML generados hoy en `Documentación Actual Humana\Entregables\` reflejan las decisiones aprobadas el `28/11/2026` (incluyendo `DEC-T4`, `DEC-EI1`, `DEC-PP1..3`, `DEC-DP1`), mientras que `docs/formales/Estudio_Inicial.docx` (`v1.6.0`), `docs/formales/Plan_de_Proyecto.docx` (`v2.1.0`), `docs/gestion-proyecto/Seguimiento de Proyecto.md` (`v1.5.0`) y `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` (con 2 métodos residuales de votación) permanecen en el estado del `27/11/2026` porque esta fase indicó explícitamente **no tocar el repositorio**.
6. **Story Points y calendario entre `03_Seguimiento` y `04_Definicion_Producto`:**
   - Ambos aplican la convención única de calendario (`DEC-T2`: S3 `07/10–20/10` / Jira `08/10`; S4 `21/10–03/11` / cierre S3 `22/10`; S5 `04/11–23/11`), el corte real del `03/11` (`SCRUM-56` el `05/11`, `SCRUM-53` el `12/11`), los mismos 10 ítems trasladados al Sprint 6 y los mismos SP unificados (`DEC-T3`: `SCRUM-59`: 5, `61`: 2, `64`: 3, `66`: 5, `67`: 5). **Sin discrepancias.**

---

## 3. Verificación de Integridad del Repositorio

- `git status --short` confirma que **ningún archivo del repositorio ni de `Plantillas\` fue modificado** fuera de `auditoria/entregables/`.
- Los únicos cambios previos en el working tree siguen siendo los dos archivos preexistentes de backend (`backend/core/sql/03-scrum50-eventos-asistencias-apercibimientos.sql` y `backend/expedientes/migrations/0033_drop_legacy_socio_fks_eventos.py`).
