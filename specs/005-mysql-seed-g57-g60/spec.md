# Spec 005 — MySQL y datos sintéticos G57–G60 (SCRUM-77 / S3-PO2)

**Referencia:** [SCRUM-77](https://guillenmartin94.atlassian.net/browse/SCRUM-77).

**Fecha:** 10/10/2026.

**Estado:** SCRUM-77 y ampliación TS77.44–46 completadas y auditadas, sin hallazgos abiertos. 1064 pruebas backend verificadas y 278 frontend verdes (0 errores), cobertura 93,91% en 22 módulos y build b03663973a049f50 correcto. Veinte fichas con cuatro Juniors; 188 referencias, carga aditiva y repetición estable sobre 52 tablas, conservando las altas de UAT. 111 controles HTTP locales y feedback central de PR #49 verificados. Lint mantiene la limitación TSLint heredada. [Evidencia ampliación](tasks.md#verificación-de-ts774446).

## Contexto y objetivo

Las correcciones de saldo, escenas de todos los estados y resoluciones visibles RF77-15–17/CA77-10–12 están en verificación integrada mediante TS77.48–59; conservan el cierre histórico de la implementación y ampliación anteriores.

**Ampliación autorizada el 12/10/2026:** el usuario aprobó la UAT del conjunto original y solicitó sincronizar con `main` (PR #49) e incorporar datos Junior antes de preparar la PR. TS77.01–43 conservan su cierre histórico; TS77.44–46 registran esta ampliación verificada y auditada.

Disponer de un entorno MySQL de demostración identificable, persistente y separado de los entornos existentes. Incorporar datos sintéticos de socios de G57, G58, G59 y G60, subcomisiones y causas testigo para verificar las integraciones actuales de SGD-AVEIT.

La spec se basa en las [Notas del PO](../../docs/gestion-proyecto/notasPO.md), acuerdos del 07/10/2026, sección 7, y el [plan interdisciplinario](../../docs/gestion-proyecto/PLAN_IMPLEMENTACION_SCRUM-77_MYSQL_SEED_G57_G60.md). El usuario confirmó los datos sintéticos y autorizó formalizar la spec e implementar la primera tarea. Posteriormente remitió la [aclaración escrita del PO](aclaraciones-po.md), que cierra DP77-01 y define las nuevas categorías Junior/Senior.

## Aclaración confirmada del PO

| Grupo | Año social del corte actual | Clasificación / condición confirmada |
|---|---:|---|
| G57 | Fuera de la escala | Exviajero; fuera de la clasificación Junior/Senior |
| G58 | 6 | Senior |
| G59 | 5 | Senior |
| G60 | 4 | Senior |
| G63, referencia | 1 | Junior |

Todos los integrantes de un grupo comparten año social, sin excepciones particulares; G57 se contempla fuera de la escala como exviajero. El pase ocurre en la asamblea de recambio de autoridades, con fecha variable; febrero es habitual, no un vencimiento fijo. Junior corresponde a 1.º–2.º y Senior a 3.º en adelante dentro de la escala. Evidencia: RN77-01–04 del registro de aclaraciones.

La nueva clasificación afecta al sistema completo. TS77.31/32/33 implementan EX_TRAVELER/null, Junior 1–2/Senior 3–6 y recálculo local, preservando evidencia y snapshots originales. TS77.40/34/41/42 integran metadato/lectores/T01/JWT; TS77.43/35/36, identidad del legajo y SPA. La adecuación transversal quedó verificada y auditada en TS77.37 antes de aceptar el catálogo TS77.07. G57 no recibe un año ficticio ni se clasifica automáticamente como Senior. La aceptación no acredita carga ni persistencia de los fixtures.

## Historia de usuario y actores

Como integrante del equipo de desarrollo y de Cómputos, quiero comprobar MySQL y disponer de datos representativos de G57–G60, para probar y demostrar los recorridos existentes sin intervenir en información de otros entornos.

Los socios y autoridades de demostración conservan los permisos existentes. Cómputos administra infraestructura; no adquiere facultades para juzgar expedientes ni modificar saldos productivos.

## Requisitos funcionales en notación EARS

| ID | Requisito |
|---|---|
| RF77-01 | CUANDO se resuelve la configuración de demostración, EL SISTEMA utiliza un proyecto, contenedores, puertos publicados, red y volumen MySQL separados de la configuración habitual, y monta el checkout que contiene el archivo de demo, independientemente del directorio de invocación. |
| RF77-02 | MIENTRAS se utiliza la demo, EL SISTEMA configura MySQL y el padrón de base de datos explícitamente; las variables genéricas de otro entorno no cambian su base destino, su host MySQL ni su mecanismo de padrón. Los servicios de la SPA y del backend se comunican dentro de la red demo. |
| RF77-03 | CUANDO se verifica operatividad, EL SISTEMA comprueba por la conexión efectiva de Django el motor MySQL, la identidad de la base, la consulta autenticada, el modo SQL, charset y FKs, y obtiene una respuesta HTTP de salud correcta. La configuración resuelta y mysqladmin ping por sí solos no acreditan este requisito. |
| RF77-04 | SI el entorno, la base destino, el esquema o el perfil de datos no corresponden a la demo habilitada, ENTONCES el comando de carga rechaza la operación antes de insertar datos. |
| RF77-05 | CUANDO se carga el catálogo aprobado, EL SISTEMA incorpora identidades ficticias de G57–G60, subcomisiones válidas y causas testigo, manteniendo explícita la correspondencia entre cuenta, socio operativo y socio institucional. Usa la tabla del corte social confirmado por el PO y su regla Junior/Senior, sin deducir una equivalencia permanente desde el número de grupo. |
| RF77-06 | CUANDO se ejecuta nuevamente el mismo catálogo, EL SISTEMA conserva los identificadores, números de expediente, credenciales, ediciones válidas, relaciones, auditoría y movimientos existentes, y no genera altas duplicadas ni avanza la numeración. |
| RF77-07 | SI se detecta una colisión con datos ajenos o falla una inserción intermedia, ENTONCES EL SISTEMA aborta y revierte la carga transaccional de datos, incluido su registro de propiedad y el contador formal del expediente. |
| RF77-08 | CUANDO se crean causas operativas de demostración, EL SISTEMA usa la numeración y los servicios vigentes, registra actor, fecha y motivo, permite varios involucrados y conserva los seis estados canónicos. La carga inicial sólo puebla Creado y En período de justificaciones, con fechas actuales y plazo hábil vigente; RF77-16 incorpora posteriormente escenas históricas adicionales. |
| RF77-09 | CUANDO se incorporan antecedentes históricos sintéticos con puntos, EL SISTEMA conserva resolución formal, expediente histórico, socio destinatario y asiento individual vinculados de forma consistente. Los puntos solicitados de causas en trámite no se consideran puntos aplicados. |
| RF77-10 | CUANDO se recrea el contenedor MySQL demo conservando su volumen, EL SISTEMA mantiene IDs, relaciones, auditorías y saldos sin volver a ejecutar la carga. |
| RF77-11 | CUANDO se comprueban login, ranking, selector T01, Mis Solicitudes y tablero existentes, EL EQUIPO coteja las respuestas HTTP reales con la base y los identificadores del catálogo; los datos en memoria y las acciones de firma/votación simuladas no constituyen evidencia de persistencia. |
| RF77-12 | MIENTRAS se clasifica a un socio dentro de la escala de años sociales, EL SISTEMA utiliza Junior para años 1–2 y Senior desde el año 3. G57 se representa como socio exviajero fuera de esa escala, sin asignarle un año ficticio para eludir validaciones. La adecuación abarca cálculo, datos, contratos, representación, interfaz y documentación activa. |

**RF77-13:** CUANDO se amplía el catálogo de demostración, EL SISTEMA agrega cuatro identidades Junior y sus cuentas SOCIO habilitadas: dos G62 de 2.º año y dos G63 de 1.º año, conforme a la escala del corte de referencia confirmado. Conserva el perfil de propiedad, las dieciséis identidades originales, sus credenciales, relaciones, escenas, numeración y ocho asientos; los cuatro nuevos socios parten con saldo cero y sin movimientos. La tabla del corte es explícita y no implementa un cálculo permanente desde el número de grupo.

**RF77-14:** CUANDO se sincroniza esta rama con `main`, LA DEMO conserva el feedback central de la PR #49: avisos transitorios de éxito/error/advertencia/información abajo a la derecha, independientes y visibles sobre modales, con cierre accesible y duración de diez segundos. Conserva simultáneamente los contratos de identidad y las correcciones de filtros/accesibilidad de SCRUM-77.

**Ampliación autorizada el 12/10/2026 — saldo en Mis Expedientes:** el usuario solicitó corregir, dentro de la PR #54, la diferencia entre el widget personal y el ranking. El alcance incorpora la lectura del saldo propio; el listado y los descargos conservan su alcance anterior.

**RF77-15:** CUANDO un socio autenticado consulta sus puntos en Mis Expedientes, EL SISTEMA obtiene del servidor su saldo aplicado desde el mismo libro mayor utilizado por el ranking, resolviendo su identidad institucional de forma inequívoca y sin usar coincidencias de nombre, PK local o número académico como número institucional. Los puntos solicitados pendientes y el caché de PuntajeGeneral no integran este saldo. MIENTRAS la lectura está pendiente o no puede acreditarse, EL SISTEMA distingue carga o error de un saldo cero real y descarta respuestas de una sesión anterior. La consulta conserva permisos y no modifica datos.

La aclaración del usuario «todas las inconsistencias» aplica a todos los socios y a las fichas locales/institucionales: sus saldos confirmados usan el mismo lector del libro mayor. Un legajo local sin identidad institucional acreditable conserva sus datos y representa saldo desconocido (`null`); errores de base se informan como fallo de servicio. La ficha prioriza su lectura actual y no utiliza el snapshot del ranking como saldo vigente. Un contrato de saldo propio malformado se trata como error, sin fabricar un valor.

**Ampliación autorizada el 12/10/2026 — todos los estados:** el usuario solicitó agregar tres expedientes En revisión, uno Pendiente de firma, dos Pendientes de envío y cuatro Emitidos, además del trabajo de saldo y CI en curso.

**RF77-16:** CUANDO se amplía la demo con estados avanzados, EL SISTEMA agrega diez escenas históricas sintéticas: tres En revisión, una Pendiente de firma, dos Pendientes de envío y cuatro Emitidos, preservando las causas existentes y sus ediciones de UAT. Cada escena tiene numeración vigente, participantes, fechas pasadas coherentes, plazo hábil vencido e historial completo hasta su estado final. Los cuatro emitidos tienen resolución sintética, respaldo histórico y asiento individual vinculado; las escenas pendientes no aplican puntos. La importación es atómica, protegida e idempotente; no modifica estados, fechas o saldos existentes ni acredita firma/emisión productiva.

El catálogo incorpora un emitido por cada cuenta Junior con puntajes +2, -1, -2 y +1: cuatro asientos adicionales, agregado cero. Las cuatro altas Junior conservaron saldo inicial cero en RF77-13; estos actos sintéticos posteriores explican los nuevos saldos sin cambiar la clasificación social ni los ocho asientos anteriores.

**Ampliación autorizada el 12/10/2026 — resoluciones visibles:** el usuario confirmó la coincidencia de saldo y solicitó poder consultar la resolución que justifica cada puntaje, para todos los socios, incluidos los antecedentes históricos originales.

**RF77-17:** CUANDO un socio consulta el saldo en Mis Expedientes, EL SISTEMA presenta los asientos propios y sus expedientes/resoluciones emitidas reales, con puntos individualizados y texto formal de respaldo. El saldo y el historial corresponden a una misma lectura consistente del libro mayor. Un antecedente histórico sin causa managed se muestra con su identidad histórica; sólo se enlaza una causa operativa cuando la relación está acreditada. Una fila sin respaldo completo o no emitido produce error de servicio, sin inventar resolución ni omitir puntos para aparentar consistencia. La lectura conserva permisos, no duplica causas/asientos y distingue saldo cero confirmado de ausencia de identidad o error.

La misma consulta está disponible desde la ficha de cada socio bajo los permisos actuales del legajo: permite auditar también integrantes sin cuenta o deshabilitados mediante las autoridades ya habilitadas, sin hacer público el documento ni conceder facultades nuevas.

## Requisitos no funcionales e invariantes

- **RNF77-01 — Aislamiento:** la configuración demo se utiliza como archivo autónomo. Sus puertos se publican sólo en loopback; no comparte el volumen MySQL habitual ni las identidades Docker de otros checkouts.
- **RNF77-02 — Seguridad operativa:** los informes y pruebas no imprimen contraseñas, tokens ni claves. Los datos son ficticios y los correos son de prueba. La carga no envía notificaciones externas.
- **RNF77-03 — Integridad:** FKs activas, tablas transaccionales y separación de DDL/grants frente al DML. Ningún saldo o expediente se modifica mediante SQL manual UPDATE/DELETE; no se usan limpiezas destructivas para lograr idempotencia.
- **RNF77-04 — Compatibilidad:** se conserva seed_demo y se planifica la compatibilidad de datos y contratos al adoptar Junior/Senior. Categoría social y vigencia de cuenta son conceptos separados. El cambio de nombres no se realiza mediante una sustitución ciega de valores ni modifica por sí solo roles, facultades o saldos.
- **RNF77-05 — Conformidad:** no se añaden puntos fraccionarios por felicitaciones/llamados, nuevas facultades de Cómputos ni reglas productivas de resolución. Se respeta la acumulación 3:1 documentada por el PO.
- **RNF77-06 — Verificación:** TDD por tarea de código, suite correspondiente en verde, controles aplicables y auditoría independiente. Las pruebas de configuración no sustituyen las consultas de MySQL real ni la demostración de persistencia.

## Criterios de aceptación

| ID | Requisito | Evidencia |
|---|---|---|
| CA77-00 | RF77-01/02, RNF77-01 | Configuración Compose resuelta válida, recursos disjuntos respecto del Compose original, mounts del checkout, publicaciones loopback y destino MySQL/padrón explícitos. Este criterio cierra únicamente la primera tarea de configuración. |
| CA77-01 | RF77-03/04 | MySQL real con consulta autenticada por Django, preflight y health HTTP; esquema y grants verificados. |
| CA77-02 | RF77-05 | Catálogo aprobado con G57 exviajero y G58/G59/G60 en años 6/5/4 del corte confirmado, subcomisiones, identidades y causas; unicidad, referencias completas y manifiesto. La carga depende de DEP77-02. |
| CA77-03 | RF77-06/07 | Segunda ejecución estable, conservación de ediciones/credenciales, colisión sin sobrescritura y rollback completo ante fallo. |
| CA77-04 | RF77-08/09 | Número servidor, estados válidos, plazo actual, auditoría y múltiples socios; antecedentes históricos con resolución y atribución individual correctas. |
| CA77-05 | RF77-10 | Contenedor recreado, mismo volumen y mismos datos comprobados sin reseed. |
| CA77-06 | RF77-11 | Recorridos actuales contrastados contra HTTP/DB en escritorio y móvil; brechas fuera de alcance identificadas expresamente. |
| CA77-07 | RNF77-06 | Pruebas y controles correspondientes en verde, auditoría y chequeo final PO, con trazabilidad de cada criterio. |
| CA77-08 | RF77-12, RNF77-04 | Junior en años 1/2; Senior en 3/4/6 de la escala; G57 identificado como exviajero sin año social ficticio. Representación coherente, datos existentes recalculados conforme a su situación, contratos y filtros compatibles y denominaciones nuevas en la UI/documentación activa. Sin efectos ajenos sobre vigencia, roles ni puntos. Verificado/auditado en TS77.37 mediante oráculos MySQL, frontend y catálogo; la carga posterior G57 quedó verificada en TS77.11/CA77-02. |

**CA77-09 — ampliación:** ranking/padrón contienen veinte identidades: cuatro Junior, doce Senior y cuatro Exviajeros. Las cuatro cuentas Junior ingresan con permisos de SOCIO; sus fichas reflejan 1.º/2.º año y saldo cero. La ampliación sobre la demo existente es aditiva y una segunda carga no cambia filas, IDs ni numeración. Login inválido, validación T01 y error de ficha muestran el feedback de PR #49; las suites, build y auditoría correspondientes deben pasar.

**CA77-10 — saldo propio:** Mis Expedientes y ranking coinciden para socios con saldo positivo, negativo y cero confirmado. La cuenta académica 99077001 se resuelve al socio institucional 770001 y presenta +2; sus causas pendientes no descuentan -6 del saldo. La lectura ignora un caché divergente, individualiza los asientos y rechaza identidades ausentes/ambiguas y errores de base sin fabricar cero. HTTP y DOM acreditan estados de carga/error, permisos, cambio de sesión y ausencia de escrituras; las pruebas, build y auditoría pasan.

La comprobación recorre todas las cuentas habilitadas del catálogo y sus referencias: compara con SQL/ranking y ambos namespaces del legajo cuando hay identidad institucional confirmada, e informa ausencia de identidad cuando corresponde. Las fichas descartan un snapshot de saldo desactualizado; los perfiles locales sin fuente institucional y los payloads inválidos distinguen desconocido/error de cero real.

**CA77-11 — estados avanzados:** el tablero y la colección HTTP contienen las diez nuevas causas con distribución 3/1/2/4 en revisión/firma/envío/emitidos, junto con las causas previas sin cambios. El plazo y cada transición guardan orden temporal y no tienen fechas futuras. Los cuatro nuevos asientos están individualizados y respaldados por resolución/expediente histórico, relacionados con la escena operativa mediante número formal y referencias verificables; no se inventa una FK entre esquemas. Todos los saldos de las cuentas habilitadas coinciden entre widget, fichas, ranking y SQL. Segunda carga, colisión y fallo tardío acreditan preservación, idempotencia y rollback sin avance de numeración. Pruebas, navegador, auditoría y CI pasan.

**CA77-12 — trazabilidad visible:** las nueve cuentas institucionales habilitadas muestran todos sus asientos y respaldos, cuya suma coincide con SQL/ranking/fichas. 99077001 consulta la resolución histórica de su +2; 99077005 consulta +3/-3 con saldo cero; cada Junior consulta su acto individual y referencia operativa emitida acreditada. La atribución compartida +2/+1 conserva el importe propio de cada receptor. Las cinco referencias locales sin vínculo institucional no muestran un historial inventado. DOM/modal, permisos, respuestas inválidas, sesiones y fallas de respaldo se prueban; HTTP/DB acreditan ausencia de escrituras, sin aumentar los cuatro emitidos operativos por duplicar antecedentes.

Una autoridad con el permiso de legajo coteja los veinte historiales institucionales y los doce asientos, incluidos los dos destinatarios sin login habilitado. La ficha representa saldo e historial de una misma consulta actual, con aislamiento ante cambio de sesión; un socio común no consulta actos ajenos por URL.

## Fuera de alcance

Cambios de columnas o DTOs para exponer Gxx, conexión completa del listado y descargos de Mis Expedientes a su API, ampliación del historial de legajo más allá de sus asientos aplicados, renombre general a Revisores, ordenamiento compuesto, reportes, votación nominal compleja, firma/emisión productiva y motor de acumulación 3:1. RF77-15 incorpora el saldo propio y RF77-17 incorpora la consulta de asientos/resoluciones en Mis Expedientes y en las fichas locales/institucionales bajo sus permisos existentes. Las brechas actuales no se ocultan como resultados exitosos; un fallo dentro de un recorrido incluido debe resolverse antes de su aceptación.

Queda fuera retrofechar causas existentes o simular su avance inmediato con fechas futuras. RF77-16 autoriza exclusivamente la importación de nuevas escenas históricas sintéticas con temporalidad y respaldos coherentes.

La administración automática del pase anual en la asamblea no forma parte de esta US. El catálogo registra el corte social al que corresponden sus datos. La adecuación Junior/Senior se incorpora como cambio transversal solicitado por el PO; no debe confundirse con el renombre de roles a Revisores.

## Decisiones pendientes y dependencias

| ID | Decisión | Impacto |
|---|---|---|
| DP77-01 | Cerrado por versión escrita corregida del PO: G57 exviajero fuera de la escala, G58=6, G59=5, G60=4; avance en la asamblea de recambio, grupo sin excepciones y Junior 1–2 / Senior 3+. | Definición y adopción técnica verificadas; DEP77-02 cerrado en TS77.37. |
| DP77-02 | Cerrado: catálogo scrum77-g57-g60-v1 aceptado en TS77.07 tras auditoría TS77.37, con 16 identidades/cuatro por grupo, corte y rangos/referencias en [catálogo](../../docs/gestion-proyecto/CATALOGO_DATOS_DEMO_SCRUM-77.md). | 62 oráculos puros verdes; propiedad/carga/manifiesto/conciliación y persistencia posteriormente verificados en TS77.08–19. Datos sintéticos, sin afirmar representatividad estadística institucional. |
| DEP77-01 | Limitaciones de grupo visible, historial general de legajo, listado/descargos de Mis Expedientes y simulaciones locales. | RF77-15 incorpora el saldo propio y RF77-17 sus asientos/resoluciones visibles en Mis Expedientes/fichas por autorización del usuario; las otras brechas conservan su alcance. Grupo se valida en su catálogo persistido/manifiesto. |
| DEP77-02 | Cerrado en TS77.37: documentación/locales/DDL/transición, metadato/lectores/T01/JWT y legajo/SPA de TS77.30–43 verificados y auditados. CF77-01/02 resueltos en aclaraciones-po.md; CA77-08 verificado. | Prerrequisito resuelto con 932 backend/202 frontend verdes y auditoría sin hallazgos en esa instancia. Carga/conciliación/persistencia acreditadas posteriormente en TS77.08–19; el cierre de la dependencia por sí solo no las acredita. |

El alcance original quedó completado con CA77-00–08 verificados y TS77.01–43 cerradas; la ampliación autorizada completó TS77.44–46 y CA77-09 con carga aditiva, regresiones y auditoría aprobadas. La aceptación se apoya en carga/repetición/persistencia/recorridos reales, suites y auditoría integral; la formalización o CA77-00 por sí solos no la acreditan.
