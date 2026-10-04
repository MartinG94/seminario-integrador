# Spec 002 — Apertura y trazabilidad del expediente (S2-01)

## Contexto y objetivo
Permitir que integrantes habilitados abran expedientes con número correlativo y consulten su recorrido procesal auditado, respetando los seis estados del Art. 12 del Reglamento Procesal 2026. La spec se basa en S2-01 del backlog y en las reglas rectoras de `docs/gestion-proyecto/notasPO.md`.

## Historia de usuario
Como integrante habilitado quiero abrir y seguir un expediente con trazabilidad completa.

## Criterios de aceptación
- **CA1:** Cada expediente nuevo recibe un número único, correlativo y asignado por el servidor.
- **CA2:** El expediente sólo puede usar los seis estados canónicos, en orden: Creado → En período de justificaciones → Justificaciones en revisión → En espera de resolución → Pendiente de firma y envío → Emitido.
- **CA3:** La apertura y cada transición guardan actor, fecha/hora y motivo. Se rechaza toda transición que saltee o revierta un estado.
- **CA4:** La asignación concurrente de números no genera duplicados.
- Un expediente admite múltiples socios implicados, conforme a las Notas del PO.
- Sólo cuentas habilitadas con rol TD, CD o autoridad de subcomisión/equipo pueden abrir expedientes. Las transiciones manuales quedan reservadas al TD; los procesos automáticos transicionan mediante servicios del sistema.
- Un socio implicado puede consultar el expediente y presentar su propio descargo; se conserva el contrato de respuesta existente durante la transición del modelo.

## Fuera de alcance
Carga completa del T01, validación de competencias de Arts. 21–26, notificaciones, tablero visual, resolución individual por socio y firma colegiada.

## Criterios de finalización
Pruebas de dominio y API para numeración, autorización, historial, progresión secuencial, concurrencia y participación de varios socios; migraciones aplicables; suite backend verde.