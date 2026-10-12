# Correcciones y ampliación de la demo — PR #54

Referencias: [PR #54](https://github.com/MartinG94/seminario-integrador/pull/54), spec 005 / RF77-15–17 / CA77-10–12. Fecha: 12/10/2026.

El usuario autorizó corregir los checks de CI, todas las inconsistencias de saldo, agregar diez expedientes en estados avanzados y hacer visibles las resoluciones que respaldan los puntos. La PR continúa abierta hacia main, sin merge. Las Notas del PO y el seguimiento macro se conservan sin cambios.

## Fuente del saldo

Mis Expedientes consultaba un padrón simulado por nombre; la ficha local devolvía cero por defecto, la institucional ocultaba fallas del libro mayor como cero y el modal priorizaba el snapshot del ranking. La corrección consulta el libro mayor individualizado, resuelve la identidad institucional desde el usuario/legajos reales y distingue cero confirmado de carga/error/desconocido.

GET `/api/v1/socios/me/points-balance/` es propio y de sólo lectura. Ambos legajos usan el mismo lector; la ficha local sin vínculo institucional devuelve `null` y una falla de servicio devuelve 503 genérico. Los permisos se verifican antes del saldo. Los DTO inválidos se rechazan, el modal usa la consulta actual y el widget cancela lecturas al cambiar sesión. Los puntos solicitados y el caché PuntajeGeneral mantienen su significado separado.

La verificación HTTP cubre las catorce cuentas habilitadas: nueve vinculadas al catálogo y cinco referencias locales sin contraparte institucional. Las primeras se comparan con SQL/ranking/ambos legajos; las restantes acreditan 404 en el saldo e historial propio y ficha local con saldo desconocido. No se inventan vínculos ni ceros para las referencias externas.

## Resoluciones visibles

GET `/api/v1/socios/me/points-history/` y GET `/api/v1/socios/<pk>/points-history/?identity_source=...` ofrecen asientos individualizados y respaldos emitidos bajo los permisos vigentes. Un SELECT con LEFT JOIN obtiene los movimientos y sus respaldos completos; el saldo se suma en Decimal desde ese mismo listado. Una referencia incompleta/no emitida produce 503, sin omitir movimientos para fabricar consistencia. No hay modelos, migraciones ni asientos nuevos por esta lectura.

Mis Expedientes y la ficha reutilizan tabla/modal de resoluciones y calculan su saldo desde el mismo DTO actual. Los ocho asientos originales muestran su expediente histórico; los cuatro Junior muestran también su causa operativa cuando la cadena de propiedad, M2M y referencia formal coinciden. El texto y los reglamentos almacenados se presentan literalmente; la fecha de registro histórico no se etiqueta como fecha de emisión ni se presenta la PK como número formal.

La autoridad habilitada consulta los veinte historiales, incluidos destinatarios sin cuenta operativa; el socio común sólo consulta el propio. Cambio de sesión y destrucción cancelan HTTP, retiran datos y cierran detalles. Las pruebas rechazan respuestas inválidas, duplicados y sumas divergentes. El navegador confirmó la resolución original DEMO-77-01/2026 de Ámbar (+2) y Félix (+1), los dos actos compensados de Elena (+3/-3), la sanción de Rocío (-1, EXP-0014/2026) y la ficha de Malena (+1) consultada por CD.

## Escenas de todos los estados

El catálogo agrega diez historias sintéticas: tres En revisión, una Pendiente de firma, dos Pendientes de envío y cuatro Emitidos. Importa instancias nuevas validadas con fechas pasadas, calendario y secuencia canónica, sin modificar el reloj ni retrofechar causas previas. Los cuatro emitidos tienen resolución y expediente histórico/asiento individual ligados mediante número formal, texto y referencias; no existe una FK directa entre los dos esquemas.

| Cuenta Junior | Saldo aplicado por el nuevo emitido |
| --- | ---: |
| 99077017 | +2 |
| 99077018 | -1 |
| 99077019 | -2 |
| 99077020 | +1 |

El agregado nuevo es cero. Se conservan los ocho asientos originales y el agregado previo +1. Estas historias expresan su carácter ficticio y no acreditan firma/emisión productiva ni envían notificaciones externas.

La demo efectiva conserva su alta de UAT: 16 expedientes frente a 15 fixtures, con distribución 4 Creado / 2 Justificando / 3 En revisión / 1 Pendiente de firma / 2 Pendiente de envío / 4 Emitidos. El adaptador SPA mantiene las seis claves de la API; antes agrupaba firma en revisión y envío en firma. La corrección sólo cambia la representación.

Primera carga y repetición dejaron 272 referencias, 11 expedientes/resoluciones históricos y 12 movimientos; sus manifiestos comparten SHA-256 `90fd22eaf2758c98d94d695a2c8a4539008630c870aa06049465c3fe45fbb158`. Los 52 esquemas y todas las filas previas se conservaron salvo el avance legítimo del correlativo 2026, de 6 a 16. La repetición conservó todas las filas y el correlativo. [Registro de carga](evidencias/pr54/carga.json).

## Pruebas y auditoría

| Control | Resultado acreditado |
| --- | --- |
| Backend de saldo/identidad/historial | 124 focales MySQL + 2 suplementos aprobados, 0 errores |
| Frontend final | 362 aprobadas, 0 errores; build `c8e0ecb245aa8807`, 11830 ms |
| Catálogo avanzado | 78 aprobadas, 0 errores; TDD previo con 10 fallos esperados |
| Importación avanzada MySQL | 137 aprobadas, 0 errores, 294,68 s |
| HTTP local final | 197 consultas: 154×200, 6×401, 21×403 y 16×404; los 20 historiales/12 asientos coinciden con SQL/ranking; 52 tablas sin cambios |
| Carga/repetición en demo | Preservación e idempotencia verificadas; [registro](evidencias/pr54/carga.json) |
| Navegador | Saldos positivo/negativo/cero, respaldos y fichas, seis columnas, modal y Escape/foco a 360 px verificados |
| Regresión backend final y cobertura | 1155 aprobadas, 0 errores/omisiones, 591,78 s; cobertura 94,17% en 25 módulos (2779 sentencias/162 sin cubrir); usuario CI restringido y ocho controles Compose incluidos |
| Ruff/Django | Lint correcto, 169 archivos formateados; check sin incidencias y sin migraciones nuevas |
| CI de la corrección de permisos | Cuatro checks de fe468b8 verdes; [registro](VERIFICACION_CI_PR54.md) |
| CI del commit definitivo | Pendiente |

TDD reprodujo endpoints ausentes, saldos locales incorrectos, ceros ficticios, lectura previa a permisos, legajos de carreras alternativos, snapshots viejos, respuestas inválidas y errores de carga/propiedad de escenas avanzadas. La lectura de historial se ensayó con respaldos rotos y cadena managed incompleta; el frontend reprodujo 25 fallos propios y 6 de ficha antes de implementar. Auditoría independiente de lectores/SPA, importador y RF77-17 aprobada, sin hallazgos abiertos de código; el cierre integrado depende del CI del commit publicado. [Registro final local](evidencias/pr54/regresion-local.json).

## Evidencia visual

[Saldo y antecedente de Ámbar](evidencias/pr54/saldo-ambar.jpg), [resolución original](evidencias/pr54/resolucion-ambar.jpg), [ficha de Ámbar](evidencias/pr54/ficha-ambar.jpg), [cero compensado de Elena](evidencias/pr54/saldo-elena.jpg), [sanción Junior de Rocío](evidencias/pr54/saldo-rocio.jpg), [ficha autorizada de Malena](evidencias/pr54/ficha-malena.jpg) y [modal móvil](evidencias/pr54/resolucion-movil.jpg).

El tablero usa desplazamiento horizontal a 1140 px: [primeras tres columnas](evidencias/pr54/tablero-seis-estados.jpg) y [etapas finales](evidencias/pr54/tablero-etapas-finales.jpg). El DOM acreditó los seis conteos. El modal móvil tiene x=16/ancho=328 en viewport de 360, sin overflow global; Escape restaura el foco al botón que lo abrió. El viewport se restauró al concluir.

[Smoke HTTP reproducible y conservación](evidencias/pr54/http-local.json); [verificador](evidencias/scrum77-ampliacion/verificar_http.py). Sólo se invocaron GET y POST de login; sus huellas previas/posteriores de las 52 tablas coinciden.

## Límites conservados

La conexión completa del listado/descargos de Mis Expedientes, el historial de legajo más allá de los puntos aplicados, firma productiva y motor 3:1 conservan su alcance anterior. Reportes sigue en pausa por las Notas del PO y mantiene su simulación; no se interviene en esa pantalla. Lint frontend conserva el builder TSLint heredado ausente; los tests y build se informan por separado.
