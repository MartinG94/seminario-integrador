# Spec 008 — Tramitar Apelación y Adecuación del T01 (PB-02)

## Contexto y Objetivo

Permitir que cada socio involucrado en un expediente originado en un Formulario T01 apele por el canal formal dentro de un plazo parametrizado, y que el Tribunal de Disciplina (TD) debata y adecúe puntos e involucrados comunicando los motivos, sin perder la versión original y respetando el derecho de defensa.

- **Referencia Backlog:** PB-02 — Tramitar apelación y adecuación del T01.
- **Referencia Normativa:** Reglamento Procesal Disciplinario 2026, art. 12 (5 días hábiles para el descargo de los T01 "por el medio comunicado por el Tribunal") y diagrama del art. 14.
- **Referencia Rectora:** [Notas del PO](../../docs/gestion-proyecto/notasPO.md) — expedientes multi-socio con resolución individualizada, descargo editable mientras el plazo esté abierto, notificaciones centrales.
- **Sistema de Diseño:** [DESIGN.md](../../DESIGN.md).

### Diagrama del art. 14 y su correspondencia

| Operación | Art. 14 | Estado (art. 12) | En el sistema |
| :--- | :--- | :--- | :--- |
| OP 10 | Generación del expediente | Expediente Creado | Emisión del T01 (ya existente). |
| OP 20 | Período de apelación (apelación vía mail) | En período de justificaciones | Apelación desde "Mis Expedientes" con constancia por mail. |
| OP 30 | Debate y adecuación: puntos e involucrados (mail con motivos al solicitante y solicitado) | Justificaciones en revisión | Adecuación versionada y mail con motivos. |
| OP 40 | Generación de resolución | En espera de resolución | Fuera de alcance (otra historia). |
| OP 50 | Firma Tribunal | Pendiente de firma y envío | Fuera de alcance. |
| OP 60 | Emitido (mail con resolución final) | Expedientes ya emitidos | Conserva el historial de apelaciones y adecuaciones (CA4). |

### Decisiones del equipo (22/10/2026)

- **Canal:** el socio apela desde el sistema ("Mis Expedientes") y el sistema envía la constancia por mail al socio y al TD.
- **Plazo:** parámetro global, 5 días hábiles por defecto (art. 12), editable por TD o Administración; cada período congela el valor vigente al abrirse.
- **T02/T03:** en expedientes originados en un T01 la apelación reemplaza al descargo T02/T03.
- **Derecho de defensa:** al adecuar, el TD decide si abre un nuevo período de apelación para los socios afectados; si lo abre, el expediente vuelve a "En período de justificaciones".

---

## Historia de Usuario

**Como** involucrado,
**quiero** apelar el T01 por el canal formal,
**para** que el TD debata y comunique cualquier adecuación.

---

## Requisitos en Notación EARS

1. **Event-driven (Apertura del período — CA1):**
   CUANDO un expediente originado en un T01 ingrese a `En período de justificaciones`, el sistema *debe* abrir un período de apelación por cada socio involucrado con el plazo en días hábiles vigente en ese momento, calculado con el calendario institucional.

2. **Ubiquitous (Plazo parametrizado — CA1):**
   El sistema *debe* conservar el plazo de apelación como parámetro global (por defecto 5 días hábiles, entre 1 y 30). Sólo TD y Administración *pueden* modificarlo; cada cambio *debe* quedar registrado con autor y fecha y no *debe* alterar los períodos ya abiertos.

3. **State-driven (Apelación en plazo — CA1):**
   MIENTRAS el período del socio esté abierto y el expediente esté en `En período de justificaciones`, el socio involucrado *debe* poder presentar y corregir su apelación (texto de 20 a 5.000 caracteres). Cada presentación *debe* crear una versión inmutable con fecha del servidor y enviar la constancia por mail al socio y al TD. Fuera de plazo o de etapa, el sistema *debe* responder `409`; un socio ajeno a la causa recibe `403`.

4. **Ubiquitous (Reemplazo de T02/T03):**
   En expedientes originados en un T01 el sistema *debe* rechazar descargos T02/T03 indicando que corresponde apelar.

5. **Event-driven (Adecuación versionada — CA2):**
   CUANDO el TD adecúe un expediente en `Justificaciones en revisión`, el sistema *debe* registrar una versión inmutable con puntos e involucrados anteriores y nuevos, motivos (mínimo 20 caracteres), autor y fecha, y aplicar los nuevos valores al expediente. La solicitud T01 emitida y las versiones previas *no deben* modificarse ni eliminarse. Debe quedar al menos un involucrado y el signo de los puntos debe respetar el tipo de acción (sanción negativa, mérito positivo).

6. **Event-driven (Notificación de motivos — CA3):**
   CUANDO se registre una adecuación, el sistema *debe* encolar un mail con los motivos al socio solicitante y a cada socio solicitado (incluidos los quitados de la causa).

7. **Event-driven (Derecho de defensa — CA5):**
   CUANDO el TD indique al adecuar que abre un nuevo período, el sistema *debe* abrir un período de apelación para los socios afectados (agregados y, si los puntos se agravan, todos los involucrados) y devolver el expediente a `En período de justificaciones` registrando el cambio de estado. SI no hay afectados, *debe* rechazar la apertura con `400`. El pase a `Justificaciones en revisión` *debe* esperar al vencimiento del último período abierto.

8. **Ubiquitous (Trazabilidad — CA4):**
   El sistema *debe* exponer el historial del T01 (versión original emitida, períodos, apelaciones y adecuaciones) a TD, CD y Administración, y al socio involucrado sólo sus propias apelaciones y las adecuaciones comunicadas. Ningún registro del historial *debe* poder modificarse ni eliminarse.

---

## Criterios de Aceptación (DoD)

- [ ] **CA1 (Canal y plazo):** Apelación desde el sistema con constancia por mail, dentro del plazo parametrizado por socio.
- [ ] **CA2 (Adecuación sin borrar el original):** Puntos e involucrados se adecúan en versiones inmutables; el T01 emitido no cambia.
- [ ] **CA3 (Motivos notificados):** Mail con motivos a solicitante y solicitados.
- [ ] **CA4 (Trazabilidad):** Historial completo consultable e inmutable hasta la resolución final.
- [ ] **CA5 (Estados y defensa):** Nuevo período aprobado por el TD con retorno a `En período de justificaciones`.
- [ ] **CA6 (Suites en verde):** `pytest` y `Karma` sin regresiones.

---

## Fuera de alcance

- Adjuntos en la apelación (se puede sumar reutilizando la evidencia protegida de la Spec 005).
- Generación, firma y envío de la resolución (OP 40 a OP 60).
