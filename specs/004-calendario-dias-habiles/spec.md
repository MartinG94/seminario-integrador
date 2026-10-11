# Spec 004 — Calendario institucional de días hábiles (SCRUM-45 / S3-01)

## Contexto y alcance

Mantener un único calendario institucional de días inhábiles para calcular los plazos procesales de AVEIT. El alta de un feriado impacta directamente en los cálculos nuevos; los vencimientos ya persistidos se conservan.

La [revisión del PO del PR #49](https://github.com/MartinG94/seminario-integrador/pull/49#pullrequestreview-5477670411), autorizada para implementación, reemplaza los requisitos anteriores de versiones operativas, tipificación y condición laborable. Referencia: [SCRUM-45](https://guillenmartin94.atlassian.net/browse/SCRUM-45), épica SCRUM-30.

## Historia de usuario

**Como** autoridad habilitada (ADMIN, CD o TD), **quiero** registrar feriados institucionales con fecha, denominación y auditoría, **para que** los plazos se calculen con los días inhábiles vigentes.

**Como** usuario autenticado, **quiero** consultar el calendario y simular un plazo, **para que** pueda conocer los días computados y el vencimiento.

## Criterios de aceptación (EARS)

- **CA1 — Calendario único:** Cuando se calcula un plazo nuevo o una simulación, el sistema excluye sábados, domingos y los feriados del calendario institucional único. Cuando se registra un feriado, el sistema lo aplica inmediatamente a los cálculos siguientes y actualiza una simulación visible o pendiente.
- **CA2 — Auditoría:** Cuando se registra un feriado, el servidor persiste su fecha única, denominación, usuario creador e instante exacto de creación. El cliente no puede asignar la autoría ni el timestamp. La tabla muestra quién lo creó y la fecha/hora con segundos.
- **CA3 — Vencimientos persistidos:** Cuando ya existe un vencimiento guardado, el sistema conserva su fecha/hora de inicio y límite aunque cambie el calendario. Las referencias históricas de expedientes se preservan como evidencia.
- **CA4 — Zona institucional:** Cuando el sistema interpreta fechas y horas, usa `America/Argentina/Buenos_Aires`. El cálculo conserva la hora, minutos y segundos del inicio. La fecha de un feriado se exhibe como día de calendario independientemente de la zona del navegador.
- **CA5 — Acceso:** Cuando cualquier usuario autenticado consulta el calendario o simula un plazo, el sistema permite la lectura, también con calendario vacío y sin versiones inicializadas. Cuando se intenta registrar un feriado, solo ADMIN, CD y TD tienen autorización en servidor. Los usuarios anónimos no pueden consultar.
- **CA6 — Interfaz:** La tabla muestra Fecha, Denominación, Creado por y Creado el. Fecha permite alternar ascendente/descendente. Los únicos filtros son Año y Mes, en la misma fila y alineados con Crear Feriado/Cancelar. No hay selector de versiones, búsqueda textual, tipo ni condición. El alta se integra en un contenedor blanco con radio de 8 px, elevación suave y separación entre campos; Guardar conserva el estilo primario institucional y un icono claro. Simular plazo se abre desde un botón junto a Crear Feriado en un modal accesible, con inputs y botón alineados. Al cerrar por X, Escape, fondo o navegación se cancela cualquier cálculo pendiente y se reinician campos y resultados; al reabrir no aparece información anterior. Los estados vacíos y las acciones de recuperación permanecen centrados. La vista consume los tokens de `DESIGN.md`, es responsive y accesible.
- **CA7 — Validaciones:** Cuando se registra un feriado, su fecha debe ser mayor o igual a hoy en la zona institucional y su denominación debe estar completa. El servidor rechaza fechas pasadas o duplicadas; la interfaz aplica las mismas restricciones. Ante dos altas concurrentes de la misma fecha, el sistema informa el conflicto sin error 500.
- **CA8 — Actualización de entornos:** Cuando se aplican 0009 y 0010 sobre una base existente, el calendario queda disponible para lectura autenticada, con los feriados importados o una lista vacía válida. Cuando se vuelve a aplicar la importación, el sistema conserva los feriados ya registrados y su auditoría, sin duplicarlos ni impedir el arranque.
- **CA9 — Notificaciones globales:** Cuando cualquier pantalla o modal de la aplicación informa un éxito, error, advertencia o información transitoria, el sistema muestra una notificación abajo a la derecha durante 10 segundos, con desvanecimiento final y cierre manual accesible. Cada aviso tiene su propio temporizador, sobrevive a la navegación y se ve y anuncia también sobre modales. No se duplica un mismo aviso ni se inserta HTML o información técnica de errores. Las ayudas, estados vacíos, resultados y datos permanentes siguen en la vista. La regla queda establecida en `AGENTS.md`.

## Migración y datos existentes

El calendario único importa los días inhábiles del último calendario activo. Los modelos y referencias anteriores se conservan únicamente como evidencia histórica, sin endpoints de publicación o selección de versiones. La lectura nunca inicializa datos.

La segunda revisión del PM en [PR #49](https://github.com/MartinG94/seminario-integrador/pull/49#issuecomment-6101450538), autorizada por el usuario, incorpora la verificación de actualización/reaplicación de migraciones y los ajustes de alineación, formulario y estados de tabla de CA6/CA8.

El usuario autorizó el 10/10/2026 dos cambios adicionales solicitados por el PM fuera de los comentarios y del backlog original: el simulador en modal y las notificaciones globales de CA6/CA9. Se implementan en la misma rama del PR #49 sin cambiar las reglas de negocio, las notas del PO ni la gobernanza del Sprint.

La carga inicial reconocida se identifica como Sistema. Los registros previos que no guardaron autor por feriado se muestran como Autor no registrado (registro previo); no se atribuyen al creador de una versión.

El usuario autorizó corregir la carga oficial de 2026: Güemes al 15/06 y Soberanía al 23/11. La corrección afecta solamente los pares fecha/denominación reconocidos de la carga inicial de la versión 1; no reclasifica registros institucionales posteriores. Fuente: [Cancillería — feriados 2026](https://clond.cancilleria.gob.ar/es/node/1986).

## Finalización

1. Modelo operativo con fecha única, auditoría protegida y migración que conserva evidencia y timestamps anteriores.
2. API autenticada, creación por roles habilitados, validación retroactiva y conflictos controlados.
3. Simulación y apertura de plazos mediante el mismo proveedor de feriados persistidos.
4. Interfaz simplificada con autoría y timestamp, filtros Año/Mes y orden de Fecha.
5. Regresión backend y frontend, compilación, chequeo de migraciones y linters disponibles; registrar cualquier limitación preexistente con su evidencia.
6. Revisión independiente y contraste final con `docs/gestion-proyecto/notasPO.md`, sin modificar ese documento.
7. Entorno localhost disponible y guía UAT para la validación del usuario.
