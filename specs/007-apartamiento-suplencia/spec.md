# Spec 007 — Gestionar Apartamiento y Suplencia conforme al Estatuto (S4-04)

## Contexto y Objetivo

Constituir correctamente el cuerpo del Tribunal de Disciplina (TD) que interviene en cada expediente cuando un integrante está involucrado o tiene un conflicto de interés, aplicando la suplencia estatutaria o el Tribunal ad hoc, sin admitir recusaciones y dejando la composición inmutable antes de resolver.

- **Referencia Backlog:** S4-04 / SCRUM-54 (EP4, Sprint 4, 3 SP, prioridad Highest) — `docs/gestion-proyecto/jira_backlog_import_v2.csv`.
- **Referencia Normativa:** Estatuto AVEIT Reforma 2026, arts. 92, 93, 95 y 96.
- **Referencia Rectora:** [Notas del PO (27/09/2026 y 07/10/2026)](../../docs/gestion-proyecto/notasPO.md) — Dev 4 "Sala de Tribunal: votación, suplencias y resolución"; bloque "Responsables del Tribunal" y pie de firma `[N° de Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]`.
- **Dependencias:** padrón legado `socio_lista` (cargo en `idTipoSocio`, año social en `anoSocial`) y [Spec 006](../006-resolver-causal-t02/spec.md).
- **Sistema de Diseño:** [DESIGN.md](../../DESIGN.md).

---

## Historia de Usuario

**Como** Tribunal de Disciplina,
**quiero** constituir correctamente el cuerpo cuando un integrante está involucrado,
**para** que la causa la resuelvan miembros habilitados conforme al Estatuto.

---

## Marco normativo aplicado

| Artículo | Regla | Aplicación en el sistema |
| :--- | :--- | :--- |
| Art. 92 | 3 titulares y 3 suplentes, uno de cada por 4.º, 5.º y 6.º año; el suplente reemplaza automáticamente al titular; no pueden ocupar otro cargo. | Nómina leída del padrón legado (`idTipoSocio` 10 = Titular, 11 = Suplente). Un asiento por año social. |
| Art. 93 | Los miembros no pueden ser recusados. | No existe recusación: ningún socio ni otro integrante puede apartar a un miembro. |
| Art. 95 | El titular involucrado se aparta y lo reemplaza su suplente. Si se involucran dos miembros del mismo grupo social o tres o más miembros, se integra un Tribunal ad hoc con miembros de los mismos grupos designados por Asamblea. | Apartamiento automático por involucramiento, suplencia y designación ad hoc. |
| Art. 96 | Decisiones por mayoría absoluta de sus miembros. | El cuerpo constituido tiene siempre tres asientos (mayoría: 2). |

---

## Requisitos en Notación EARS

1. **Ubiquitous (Nómina estatutaria — CA1):**
   El sistema *debe* obtener la nómina vigente del TD del padrón legado (`socio_lista.idTipoSocio` 10 = Titular, 11 = Suplente, sin `fechaBaja`) y agruparla por año social. La nómina es válida sólo si hay exactamente **un titular y un suplente por cada año 4.º, 5.º y 6.º**. SI falta o sobra un integrante en algún año, el sistema *debe* informar la observación y no permitir constituir el cuerpo.

2. **Ubiquitous (Sin recusación — CA2):**
   El sistema *no debe* ofrecer recusación (Art. 93). El único apartamiento voluntario es el que declara el **propio integrante** por conflicto de interés; ningún otro integrante, socio imputado ni autoridad *debe* poder apartar a un miembro. Los socios sin rol TD reciben `403`.

3. **Event-driven (Apartamiento por involucramiento — CA3):**
   CUANDO un integrante de la nómina figure entre los socios involucrados del expediente, el sistema *debe* apartarlo automáticamente con causa `Involucrado en la causa (Art. 95)`.

4. **Event-driven (Apartamiento por conflicto de interés — CA3):**
   CUANDO un integrante declare su apartamiento por conflicto de interés, el sistema *debe* exigir un fundamento de al menos 20 caracteres y registrarlo de forma inmutable con autor y fecha.

5. **State-driven (Suplencia — CA3):**
   MIENTRAS el titular de un año esté apartado, el sistema *debe* asignar ese asiento a su suplente (Art. 92 y 95).

6. **State-driven (Tribunal ad hoc — CA3):**
   MIENTRAS haya dos miembros involucrados del mismo año social, tres o más miembros involucrados, o un asiento sin titular ni suplente habilitado, el sistema *debe* marcar el caso como **Tribunal ad hoc** y exigir que cada miembro involucrado (y cada asiento vacante) se cubra con un integrante designado por Asamblea del **mismo año social**, indicando el acta de la Asamblea. La designación la registra TD o CD.

7. **Event-driven (Incompatibilidad de cargos — CA5):**
   CUANDO se evalúe la nómina o se designe un integrante ad hoc, el sistema *debe* rechazar a quien ocupe otro cargo en la Asociación (Art. 92): en la nómina, un integrante con rol de Comisión Directiva, Autoridad de Subcomisión o Administrador; en la designación ad hoc, además, quien en el padrón tenga un cargo distinto de Socio Ordinario (`idTipoSocio` ≠ 12). También *debe* rechazar al designado que no sea socio Activo del mismo año, esté involucrado en la causa, no esté habilitado o ya integre el cuerpo.

8. **Event-driven (Constitución inmutable — CA4):**
   CUANDO el TD constituya el cuerpo, el sistema *debe* guardar de forma inmutable los tres integrantes efectivos (año, condición Titular/Suplente/Ad hoc, N° de socio, nombre, grupo y a quién reemplaza) y la causa de cada apartamiento. Una vez constituido, *no debe* admitir nuevos apartamientos, designaciones ni una segunda constitución (`409`).

9. **State-driven (Antes de resolver — CA4):**
   MIENTRAS el cuerpo no esté constituido, el sistema *debe* rechazar el pase de `En espera de resolución` a `Pendiente de firma y envío`. La composición sólo puede gestionarse antes de ese pase.

10. **Ubiquitous (Acceso y apartados):**
    TD, CD y Administrador *pueden* consultar la composición; sólo TD constituye y declara apartamientos; TD o CD registran designaciones ad hoc. Un integrante apartado *no debe* constituir el cuerpo ni designar reemplazos en esa causa. Anónimos reciben `401`.

---

## Criterios de Aceptación (DoD)

- [ ] **CA1 (Nómina 3 + 3):** Tres titulares y tres suplentes, uno de cada por 4.º, 5.º y 6.º año; las nóminas incompletas o duplicadas se informan y bloquean la constitución.
- [ ] **CA2 (Sin recusación):** No existe recusación; sólo el propio integrante declara su apartamiento por conflicto.
- [ ] **CA3 (Apartamiento, suplencia y ad hoc):** Apartamiento automático del involucrado, suplencia por año y Tribunal ad hoc del Art. 95 con designación por Asamblea.
- [ ] **CA4 (Inmutable antes de resolver):** Composición y causas quedan inmutables al constituir; sin cuerpo constituido no se pasa a `Pendiente de firma y envío`.
- [ ] **CA5 (Incompatibilidad de cargos):** Se rechaza a quien ocupa otro cargo, en la nómina y en la designación ad hoc.
- [ ] **CA6 (Suites en verde):** `pytest` y `Karma` en verde sin regresiones.

---

## Interpretaciones a validar con el PO

- **Orden de cobertura del asiento en el caso ad hoc:** titular → su reemplazo ad hoc → suplente → su reemplazo ad hoc. El Estatuto no fija el orden cuando conviven suplencia y Tribunal ad hoc.
- **Asiento vacante por conflicto:** si el titular y el suplente de un mismo año quedan apartados (aunque sea por conflicto y no por involucramiento), se trata como Tribunal ad hoc por imposibilidad de integrar el cuerpo (Art. 92).
- **Fuera de alcance:** las irregularidades en funciones de los miembros (Art. 95, último párrafo) las sustancia la Asamblea fuera del sistema; la votación nominal queda fuera por decisión del PO (07/10/2026).
