# Spec 006 — Resolver Causal T02 con Fundamento Trazable (S4-02)

## Contexto y Objetivo

Permitir que un miembro del Tribunal de Disciplina (TD) acepte o rechace cada causal tipificada presentada mediante Formulario T02, dejando una decisión auditable, versionada y vinculada a la evidencia valorada, sin alterar el descargo presentado por el socio.

- **Referencia Backlog:** S4-02 (EP4, Sprint 4, 3 SP, prioridad Highest) — `docs/gestion-proyecto/jira_backlog_import_v2.csv`.
- **Referencia Rectora:** [Notas del PO (27/09/2026 y 07/10/2026)](../../docs/gestion-proyecto/notasPO.md).
- **Dependencias:** S3-03 (T02 tipificado) y [Spec 005](../005-evidencia-protegida/spec.md) (evidencia protegida).
- **Sistema de Diseño:** [DESIGN.md](../../DESIGN.md).

---

## Historia de Usuario

**Como** miembro del Tribunal de Disciplina,
**quiero** aceptar o rechazar cada causal tipificada con fundamento,
**para** producir una decisión auditable.

---

## Requisitos en Notación EARS

1. **Ubiquitous (Decisión individualizada por causal):**
   El sistema *debe* registrar la decisión (`Aceptada` o `Rechazada`) sobre la causal de cada descargo T02 de forma individual por socio, ya que la resolución se individualiza (Notas del PO, 27/09/2026).

2. **Event-driven (Evidencia valorada):**
   CUANDO un miembro del TD registre una decisión, el sistema *debe* vincularla a los comprobantes vigentes valorados del descargo, conservando su identificador y hash SHA-256. SI se indica un comprobante ajeno al descargo o no vigente, el sistema *debe* rechazar la decisión con HTTP `400`.

3. **Ubiquitous (Regla sugerida):**
   El sistema *debe* calcular la regla sugerida para cada causal T02: `Aceptada` si el descargo tiene al menos un comprobante vigente (Spec 005, T02 exige comprobante) y `Rechazada` en caso contrario. La regla es orientativa y no reemplaza la decisión del miembro del TD.

4. **Event-driven (Fundamento obligatorio):**
   CUANDO la decisión sea `Rechazada` O difiera de la regla sugerida, el sistema *debe* exigir un fundamento escrito de al menos 20 caracteres y rechazar la decisión con HTTP `400` si falta.

5. **Event-driven (Autoría, fecha y versión):**
   CUANDO se registre una decisión, el sistema *debe* conservar el autor (usuario, N° de socio y rol), la fecha y hora del servidor y un número de versión correlativo por descargo. Una nueva decisión sobre la misma causal *debe* crear una versión nueva y conservar las anteriores sin modificarlas ni eliminarlas.

6. **Ubiquitous (Descargo inalterado):**
   El registro de decisiones *no debe* modificar el descargo presentado (tipo, causal, texto, fecha de presentación) ni sus comprobantes. La decisión *debe* guardar una copia fiel del descargo valorado.

7. **State-driven (Etapa procesal):**
   MIENTRAS el expediente no esté en `Justificaciones en revisión` o `En espera de resolución`, el sistema *debe* rechazar decisiones con HTTP `409`. SI el descargo no es T02, el sistema *debe* rechazarlo con HTTP `400` (el T03 se valora por S3-05).

8. **Ubiquitous (Acceso):**
   Sólo integrantes habilitados del TD *deben* poder registrar decisiones; TD, CD y Administrador *pueden* consultarlas. El socio imputado no *debe* ver decisiones antes de la emisión de la resolución (confidencialidad de la deliberación). Anónimos reciben `401`; otros roles, `403`.

---

## Criterios de Aceptación (DoD)

- [ ] **CA1 (Decisión por causal y evidencia):** Una decisión por descargo T02 y socio, vinculada a los comprobantes vigentes valorados con su hash.
- [ ] **CA2 (Fundamento obligatorio):** Se exige fundamento al rechazar o al apartarse de la regla sugerida.
- [ ] **CA3 (Autor, fecha y versión):** Cada decisión conserva autor, fecha y versión; las anteriores se preservan inmutables.
- [ ] **CA4 (Descargo inalterado):** El descargo y sus comprobantes no se modifican; la decisión guarda una copia del descargo valorado.
- [ ] **CA5 (Suites en verde):** `pytest` y `Karma` en verde sin regresiones.
