# Plan técnico — Spec 004: Calendario institucional de días hábiles

## Modelo y conservación de evidencia

`Holiday` es el registro operativo del calendario único: `date` único, `description`, `created_by` protegido y `created_at` de solo lectura. `origin` distingue internamente USER, SYSTEM y LEGACY; una restricción exige usuario para un registro USER. El timestamp usa `default=timezone.now` para preservar el instante previo durante la importación.

Las migraciones 0009 y 0010 crean la tabla e importan los inhábiles del último calendario activo, conservando las tablas anteriores y las referencias de expedientes. Solo pares fecha/denominación de la carga 0008 y versión 1 son SYSTEM. Otros registros sin evidencia de autor quedan LEGACY. No se usa el creador de la versión como autor de un feriado.

La importación corrige Güemes (17/06 → 15/06) y Soberanía (20/11 → 23/11) exclusivamente en esa carga reconocida. Ante colisión se conserva el registro que ya tenía la fecha correcta. Los registros personalizados posteriores no se trasladan. No se modifican las migraciones aplicadas 0007/0008.

## Cálculo y plazos persistidos

`DbHolidayProvider` consulta exclusivamente `Holiday`. El cálculo puro `compute_business_deadline` mantiene su puerto `HolidayProviderPort` y proveedores aislados de prueba.

Modelo, servicio de notificación y transición a justificaciones usan el proveedor persistido. `iniciar_plazo_descargo` devuelve un vencimiento ya guardado sin recalcularlo. Los plazos nuevos no dependen de una versión. Se preservan inicio, límite y los seis estados procesales.

## API

- `GET /api/v1/expedientes/calendario/feriados/`: cualquier usuario autenticado; lista vacía válida sin inicialización. Parámetros opcionales `year`, `month` y `ordering=fecha|-fecha`, con validación.
- `POST /api/v1/expedientes/calendario/feriados/`: ADMIN, CD o TD; payload `fecha` y `descripcion`. El servidor valida fecha ≥ hoy en Buenos Aires y asigna el usuario autenticado y la hora de creación. La transacción y la unicidad en MySQL resuelven también altas concurrentes con respuesta 400.
- Cada respuesta de feriado contiene `id`, `fecha`, `descripcion`, `creado_por`, `creado_por_nombre` y `created_at`. La consulta precarga usuario/socio para evitar N+1.
- `POST /api/v1/expedientes/calendario/calcular-plazo/`: cualquier usuario autenticado; `start_at` normalizado a Buenos Aires y `business_days` entero positivo. Devuelve vencimiento, días computados y excluidos, sin metadata de versiones.
- Los endpoints de versiones se retiran. Los modelos antiguos permanecen para evidencia; no son calendarios operativos alternativos.

## Angular

Retirar DTOs y diálogo de versiones. Cargar directamente feriados, filtrar localmente por Año/Mes y ordenar por fecha ISO. Mostrar fechas de calendario sin convertirlas a instantes; mostrar timestamps en UTC−3 con segundos.

El formulario restringe el mínimo al día institucional y envía solo fecha/denominación. Al guardar agrega el registro y su auditoría a la tabla. Si hay una simulación visible o pendiente, cancela el cálculo anterior y solicita uno nuevo para impedir resultados obsoletos. Las suscripciones se cancelan al destruir la pantalla.

Usar únicamente tokens canónicos. Mensajes con texto primario y borde semántico para preservar contraste en ambos temas; controles con etiquetas, foco visible, estado de orden accesible y tabla desplazable en móvil.

## Verificación y entorno

TDD en endpoints, migración, reglas de negocio y comportamiento del componente. Ejecutar pytest/MySQL, cobertura del dominio, Karma/ChromeHeadless, compilación Angular, Ruff y detección de migraciones pendientes. Revisar los casos de UTC, duplicados concurrentes, historial, calendarios vacíos y alta durante una simulación pendiente.

El backend local aplica `manage.py migrate --noinput` antes del servidor para evitar el error de tablas faltantes reproducido al ingresar. Levantar MySQL/Django en Docker y Angular con el proxy existente en localhost:4200.

Contrastar el resultado con las notas inmutables del PO, cerrar la auditoría independiente y registrar comprobaciones y pasos UAT.
