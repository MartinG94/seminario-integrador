# Plan técnico — Spec 002: Apertura y trazabilidad del expediente

## Diseño
- Crear expedientes dentro de una transacción. El número (`EXP-NNNNNN`) sale de una tabla contador de una sola fila (`expedientes_numero_secuencia`) bloqueada con `SELECT ... FOR UPDATE`, y queda protegido además por la restricción `UNIQUE` de `numero`. La migración siembra el contador a partir del mayor número existente.
- Alternativa descartada: derivar el número del ID autoincremental. InnoDB no devuelve los valores consumidos por transacciones revertidas, por lo que la secuencia quedaría con huecos y dejaría de ser correlativa (CA1).
- Centralizar transiciones en un servicio de dominio/aplicación que bloquea la fila, valida el siguiente estado exacto y persiste el cambio y su auditoría en la misma transacción.
- Mantener los seis valores existentes de `EstadoExpedienteEnum` y alinear sus etiquetas con el texto del Art. 12. Las tareas de vencimiento y apertura del plazo usan el mismo servicio.
- Agregar una relación muchos-a-muchos para socios implicados y migrar los socios de expedientes ya existentes. Se conserva temporalmente el FK `socio` como referencia primaria de compatibilidad con clientes y datos actuales; la colección `socios` es la relación completa.
- Exponer creación y listado de expedientes para autoridades, transición manual sólo para TD, historial en las respuestas, y consulta de expedientes propios por los socios implicados.
- La autorización se decide en servidor usando rol y habilitación actuales de S1-03; no se confía en claims del cliente.

## Verificación
Tests API/domain bajo `backend/tests/expedientes`; comprobar migraciones con `makemigrations --check` y ejecutar la suite backend. La protección ante concurrencia se verifica con un test multihilo contra MySQL que exige números únicos y consecutivos (CA4).