# Spec 007 — Gestionar Apartamiento y Suplencia conforme al Estatuto (S4-04)

## Contexto y Objetivo

Garantizar que la causa la juzguen sólo miembros habilitados del Tribunal de Disciplina (TD): ningún socio involucrado interviene, el suplente asume automáticamente y, cuando el Tribunal ordinario no puede integrarse, la causa se deriva a la Asamblea sin trámites manuales.

- **Referencia Backlog:** S4-04 / SCRUM-54 (EP4, Sprint 4, 3 SP, prioridad Highest) — `docs/gestion-proyecto/jira_backlog_import_v2.csv`.
- **Referencia Normativa:** Estatuto AVEIT Reforma 2026, arts. 92, 93, 95 y 96; Reglamento Procesal 2026, arts. 7, 12 y 24.
- **Referencia Rectora:** [Notas del PO (27/09/2026 y 07/10/2026)](../../docs/gestion-proyecto/notasPO.md) — pie de firma `[N° de Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]` al emitir resolución.
- **Revisión del PO sobre el PR #63 (23/10/2026 y 25/10/2026):** simplificación KISS: remoción total del panel visual 'Responsables del Tribunal' en el detalle del expediente; inhibición estricta de involucrados (imputado o solicitante) en backend (403) y UI; suplencia automática transparente; aviso por correo a CD (`cd@aveit.org`) por mayoría de TD o ambos miembros del año involucrados; y formalización de la relación Promociones vs. Años Sociales mediante $\text{Año Social} = (\text{Año Actual} - 1962) - \text{Número de Grupo}$ (fundación 1965, en 2026 G58 es 6.º año social Seniors y en 2027 viaja a Europa como exviajero).
- **Decisión del PO (31/10/2026):** sin acta de Asamblea en el sistema: la Asamblea designa a los integrantes ad hoc y se les asigna el rol TD por fuera del flujo; los casos críticos ya no inmovilizan la causa y la nómina incompleta no bloquea la resolución.
- **Dependencias:** padrón legado `socio_lista` (cargo en `idTipoSocio`, año social en `anoSocial`), [Spec 006](../006-resolver-causal-t02/spec.md) y Outbox de correos (`notifications`).
- **Sistema de Diseño:** [DESIGN.md](../../DESIGN.md).

---

## Historia de Usuario

**Como** Tribunal de Disciplina,
**quiero** que el cuerpo que resuelve cada causa se integre automáticamente sin sus partes interesadas,
**para** que la causa la resuelvan miembros habilitados conforme al Estatuto.

---

## Marco normativo aplicado

| Artículo | Regla | Aplicación en el sistema |
| :--- | :--- | :--- |
| Art. 92 | 3 titulares y 3 suplentes, uno de cada por 4.º, 5.º y 6.º año; el suplente reemplaza automáticamente al titular; no pueden ocupar otro cargo. | Nómina leída del padrón legado (`idTipoSocio` 10 = Titular, 11 = Suplente). Un asiento por año social. |
| Art. 93 | Los miembros no pueden ser recusados. | No existe recusación ni apartamiento voluntario: el apartamiento es objetivo y automático. |
| Art. 95 / Art. 24 RPD | Ningún involucrado interviene; el titular involucrado lo reemplaza su suplente. Si se involucran titular y suplente de un mismo año o tres o más miembros, interviene un Tribunal ad hoc / Asamblea. | Inhibición (403), suplencia automática y aviso a CD para convocar a Asamblea General. |
| Art. 96 | Decisiones por mayoría absoluta de sus miembros. | El cuerpo efectivo tiene siempre tres asientos. |

---

## Requisitos en Notación EARS

1. **Ubiquitous (Nómina estatutaria — CA1):**
   El sistema *debe* obtener la nómina vigente del TD del padrón legado (`socio_lista.idTipoSocio` 10 = Titular, 11 = Suplente, sin `fechaBaja`) y agruparla por año social. La nómina es válida sólo si hay exactamente **un titular y un suplente por cada año 4.º, 5.º y 6.º**, sin cargos incompatibles (Art. 92). SI no lo es, la resolución *puede* adoptarse igualmente con los asientos disponibles (decisión del PO, 31/10/2026).

2. **Ubiquitous (Involucrados — CA2):**
   Son partes interesadas del expediente los socios imputados (`expediente.socio` y `expediente.socios`) y quien solicitó la apertura o la sanción (`SolicitudT01.solicitante`, Art. 24 RPD).

3. **Event-driven (Inhibición estricta — CA2):**
   CUANDO una parte interesada intente evaluar justificativos T02/T03 (`POST /descargos/<id>/decisiones/`), transicionar el expediente (`POST /estado/` o `POST /transicionar/`), o emitir o firmar la resolución, el sistema *debe* responder `403 Forbidden`.

4. **State-driven (Aviso en la interfaz — CA2):**
   MIENTRAS el usuario de TD visualice un expediente en el que es parte interesada, el sistema *debe* ocultar las acciones de decisión de justificativos y de transición y mostrar el aviso: *"⚠️ Participación restringida: Sos parte interesada en este expediente (imputado o solicitante). Tu lugar lo ocupa automáticamente tu suplente conforme al Art. 95 del Estatuto y Art. 24 del Reglamento Procesal."*

5. **State-driven (Suplencia automática — CA3):**
   MIENTRAS el titular de un año esté involucrado, el sistema *debe* asignar ese asiento a su suplente. La composición se calcula en tiempo real; no existe botón de constitución ni formulario de apartamiento.

6. **Event-driven (Estampado inmutable — CA4):**
   CUANDO el expediente pase de `En espera de resolución` a `Pendiente de firma y envío`, el sistema *debe* estampar de forma inmutable los integrantes efectivos (hasta tres) (año, condición Titular/Suplente, N° de socio, nombre, grupo y a quién reemplaza) y los integrantes apartados. El panel y la resolución muestran el pie de firma `[N° de Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]`.

7. **State-driven (Casos A y B del Art. 95 — CA5):**
   MIENTRAS el titular y el suplente de un mismo año estén involucrados (Caso A) o tres o más integrantes de la nómina lo estén (Caso B), el sistema *debe*:
   - permitir que los imputados sigan presentando T02/T03 durante los 5 días hábiles reglamentarios;
   - mostrar un aviso sutil de causa derivada a Comisión Directiva para su tratamiento en Asamblea General, sin inmovilizar la causa: la resuelven los integrantes TD no involucrados, incluidos los que designe la Asamblea (decisión del PO, 31/10/2026).

8. **Event-driven (Aviso a Comisión Directiva — CA5):**
   CUANDO se cree el expediente o se vincule su solicitante y se detecte el Caso A o B, el sistema *debe* encolar en el Outbox, una única vez por expediente, un correo a Comisión Directiva (`COMISION_DIRECTIVA_EMAIL`, por defecto `cd@aveit.org`) para que convoque de inmediato a Asamblea General.

9. **Ubiquitous (Acceso):**
    TD, CD y Administrador *pueden* consultar los responsables de la causa. Los socios sin rol de autoridad reciben `403` y los anónimos `401`.

---

## Criterios de Aceptación (DoD)

- [x] **CA1 (Nómina 3 + 3):** Tres titulares y tres suplentes, uno de cada por 4.º, 5.º y 6.º año; las nóminas incompletas, duplicadas o con cargos incompatibles no bloquean la resolución (decisión del PO, 31/10/2026).
- [x] **CA2 (Inhibición):** Imputados y solicitantes reciben `403` al evaluar justificativos, transicionar, emitir o firmar; la interfaz oculta esas acciones y muestra el aviso de participación restringida.
- [x] **CA3 (Suplencia automática):** El suplente asume el asiento del titular involucrado, sin trámites manuales.
- [x] **CA4 (Estampado inmutable):** Los responsables se fijan al adoptar la resolución, con pie de firma institucional.
- [x] **CA5 (Casos A y B):** Se avisa a CD por Outbox y se muestra el aviso de derivación a Asamblea, sin inmovilizar la causa (decisión del PO, 31/10/2026).
- [x] **CA6 (Suites en verde):** `pytest` y `Karma` sin regresiones.

---

## Fuera de alcance

- Gestión de integrantes ad hoc designados por Asamblea: la Asamblea los designa fuera del sistema y se les asigna el rol TD; no se carga acta (decisión del PO, 31/10/2026).
- Irregularidades en funciones de los miembros (Art. 95, último párrafo) y votación nominal (decisión del PO, 07/10/2026).
