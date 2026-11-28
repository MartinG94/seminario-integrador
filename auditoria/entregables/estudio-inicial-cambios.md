# Registro de Cambios Aplicados — Estudio Inicial (`SGD-AVEIT`)

> **Entregable generado:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\01_Estudio_Inicial_SGD_AVEIT.html`  
> **Versión consolidada:** `v1.6.0` (`28/11/2026`)  
> **Aprobaciones aplicadas:** `DEC-T1`, `DEC-T4`, `DEC-EI1`, `DEC-EI2`, `EI-01` a `EI-08` (según `auditoria/entregables/_aprobacion.md`).

---

## 1. Resumen de Cambios Aplicados

| Código | Sección afectada | Cambio aplicado | Motivo / Fuente |
|---|---|---|---|
| **DEC-T1 / EI-08** | Carátula (Pág. 1) e Índice (Pág. 2) | Se integró la carátula institucional unificada (`Grupo N.º 13`, `Curso 3K2`, `N.º de Entrega: Regularidad`, `Fecha de Entrega: 28/11/2026`, `Versión: v1.6.0`, acrónimo `SGD-AVEIT`, docentes `Ing. María Irene Mac William` e `Ing. Silvina Arenas`, tutor `Ing. Fernando Sanabria`), suprimiendo el campo `Fecha de examen`. Se generó la Tabla de Contenido completa con numeración exacta de páginas (1 a 15). | Alinear carátula al estándar transversal aprobado y corregir fecha/acrónimo (`xx/xx/2026`, `SDG-AVEIT`). |
| **EI-08** | §7.1 Historial de Cambios (Pág. 14) | Se conservaron **intactas** las 6 filas históricas (`v1.0.0` 15/08/2026 a `v1.5.0` 18/08/2026) y se agregó `v1.6.0` con fecha `28/11/2026`. | Regla de inmutabilidad de fechas históricas (`AGENTS.md`, Regla 13). |
| **DEC-T4 / EI-04** | Todo el documento | Se eliminó toda mención a Sprint 5, Sprint 6, tickets `SCRUM-*` y rutas o símbolos internos del repositorio (`auditoria/...`, `backend/...`, `AsientoLibroMayor`, `Resolucion.firmantes`, etc.). | Alcance estricto del Estudio Inicial (no incluye Sprint 5) y redacción orientada a lector externo. |
| **DEC-EI1 / EI-05** | Secciones 1–5 y Sección 6 (Págs. 3–13) | Se depuró el cuerpo principal (Secciones 1 a 5) para mantenerlo 100% **AS-IS + Problemas y Oportunidades**, retirando prescripciones tecnológicas anticipadas. La Matriz Comparativa y las definiciones tecnológicas iniciales se reubicaron al final en la **Sección 6: Expectativas Iniciales del Usuario** (§6 y §6.1). | Observaciones docentes #1 y #4 (`retroalimentaciónS0.txt` / `Notas de Profes-Reuniones.docx`). |
| **EI-01** | §3.7 Proceso 3, §3.9, §5.2 y §6.1 | Se eliminaron los 3 residuos de votación nominal (`"votar"` en §3.9, `"votos individuales"` en §3.7 Proceso 3 y título `"Deliberación y Votación"` en la matriz, renombrado a `"Deliberación y dictamen colegiado"`). Se conservó únicamente la referencia a la votación verbal real del proceso AS-IS en Proceso 3 y se expresó la validación colegiada mediante firma de 3 integrantes activos (4.º, 5.º y 6.º año). | Eliminación de votación nominal decidida por el PO (07/10/2026) y observaciones docentes #23 y #31. |
| **EI-02** | §3.5.3 Catálogo de Formularios (Pág. 6) | Se reconstruyó íntegramente §3.5.3 (que antes repetía los 6 estados de §3.5.2), incorporando una tabla AS-IS de los cuatro instrumentos oficiales: **Formulario T01**, **Anexo T01**, **Formulario T02 (Justificación)** y **Formulario T03 (Descargo)**. | Corrección de defecto grave detectado en `v1.5.0`. |
| **EI-03** | §1, §3.4, §3.5.2, §5.2 y §6.1 | Se retiraron afirmaciones no verificadas o inexactas: `"cómputo algorítmico"`, `"triggers MySQL"`, `"hash inalterable"`, `"cron/daemon automatizado"`, `"portal público"` anónimo (reemplazado por acceso autenticado por número de socio con censura de datos médicos), módulo inexistente `"Justificaciones"`, balance `"con un clic"` y promesas absolutas de alertas automáticas `-7/-10`. | Alineación a la realidad verificable y depuración de sobrepromesas técnicas. |
| **DEC-EI2 / EI-05** | §3.4 (Pág. 4) y §7.2 Glosario (Pág. 15) | Se mantuvo la clasificación estatutaria (`Juniors 1.º–2.º` / `Seniors 3.º–6.º`) incorporando una **nota única de equivalencia operativa** (`Pasivo 1.º–3.º` / `Activo 4.º–6.º`). En el Glosario se eliminó la doble definición contradictoria de `Socio Pasivo`. | Conciliación terminológica entre Estatuto Social 2026 y operación del padrón. |
| **EI-06** | §3.5.2, §3.5.4, §3.5.5, §3.7 y §3.8 | Se incorporaron al dominio AS-IS los 8 aspectos omitidos: regla **3:1** de llamados de atención (`3 llamados = -1 pto`), **apartamiento y suplencias** del TD, instancia previa de **apelación/adecuación T01**, **resguardo de evidencia médica sensible**, **calendario institucional** propio, restricción de **solo lectura sobre el padrón legado MySQL**, proceso de **eventos obligatorios y asistencia**, y **administración/consulta de reglamentos vigentes**. | Completitud del dominio AS-IS relevado (`estudio-inicial-discrepancias.md`, sección b). |
| **EI-07** | §3.5.1, §3.5.6, §3.9 y §4 | Se corrigió el formato de §3.5.6 (párrafo introductorio en texto normal en lugar de encabezado), se agregaron marcadores explícitos `[DATO FALTANTE: ...]` para los datos no disponibles (ver Sección 2), y se redactó la **nota explícita de no aplicabilidad** en §4 (*Antecedentes / Competencia*) por tratarse de un sistema institucional a medida para A.V.E.I.T. | Observaciones docentes #2, #3, #5 y Guía de Documentación de la cátedra. |
| **Regla 7 (Diagramas)** | §3.1, §3.6 y §3.9 | Se colocaron marcadores `[DIAGRAMA: Organigrama Institucional de A.V.E.I.T.]`, `[DIAGRAMA: Mapa Global de Procesos de AVEIT]` y `[DIAGRAMA: Lay-Out Físico de la Sede AVEIT]` sin SVG/Mermaid inline ni ASCII, documentados en `auditoria/entregables/diagramas-estudio-inicial.md`. | Separación limpia entre redacción HTML y generación/inserción de gráficos finales. |

---

## 2. Datos Faltantes Marcados en el Documento (Sin Inventar)

Los siguientes datos exigidos por la cátedra o señalados en devoluciones docentes no constan en ninguna fuente auditada y quedaron señalizados explícitamente con `[DATO FALTANTE: ...]` en el HTML:

1. **Aval institucional del procedimiento 2026 (§3.5.1, Pág. 5 — Obs. docente #3):**
   - `[DATO FALTANTE: acta, fecha de emisión y autoridades firmantes de la convalidación institucional de la Circular Normativa 001/2026 y del Reglamento Procesal Disciplinario 2026 respecto del texto 2018 aprobado por Asamblea General]`
2. **Entrevistados y fechas reales del relevamiento (§3.5.6, Pág. 7 — Obs. docente #2):**
   - `[DATO FALTANTE: nómina completa con nombres y cargos de las personas entrevistadas del Tribunal de Disciplina y de la Subcomisión de Cómputos, junto con las fechas reales de realización de las entrevistas y talleres de relevamiento]`
3. **Plano / esquema gráfico del Lay-Out físico (§3.9, Pág. 10 — Obs. docente #5):**
   - `[DATO FALTANTE: plano o esquema gráfico oficial de distribución física (Lay-Out) de la Sede Social A.V.E.I.T.]`
