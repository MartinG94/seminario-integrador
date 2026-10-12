# Spec 005 — MySQL y datos sintéticos G57–G60 (SCRUM-77 / S3-PO2)

**Referencia:** [SCRUM-77](https://guillenmartin94.atlassian.net/browse/SCRUM-77).

**Fecha:** 10/10/2026.

**Estado:** SCRUM-77 y ampliación TS77.44–46 completadas y auditadas, sin hallazgos abiertos. 1064 pruebas backend verificadas y 278 frontend verdes (0 errores), cobertura 93,91% en 22 módulos y build b03663973a049f50 correcto. Veinte fichas con cuatro Juniors; 188 referencias, carga aditiva y repetición estable sobre 52 tablas, conservando las altas de UAT. 111 controles HTTP locales y feedback central de PR #49 verificados. Lint mantiene la limitación TSLint heredada. [Evidencia ampliación](tasks.md#verificación-de-ts774446).

## Contexto y objetivo

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
| RF77-08 | CUANDO se crean causas operativas de demostración, EL SISTEMA usa la numeración y los servicios vigentes, registra actor, fecha y motivo, permite varios involucrados y conserva los seis estados canónicos. La carga inicial sólo puebla Creado y En período de justificaciones, con fechas actuales y plazo hábil vigente. |
| RF77-09 | CUANDO se incorporan antecedentes históricos sintéticos con puntos, EL SISTEMA conserva resolución formal, expediente histórico, socio destinatario y asiento individual vinculados de forma consistente. Los puntos solicitados de causas en trámite no se consideran puntos aplicados. |
| RF77-10 | CUANDO se recrea el contenedor MySQL demo conservando su volumen, EL SISTEMA mantiene IDs, relaciones, auditorías y saldos sin volver a ejecutar la carga. |
| RF77-11 | CUANDO se comprueban login, ranking, selector T01, Mis Solicitudes y tablero existentes, EL EQUIPO coteja las respuestas HTTP reales con la base y los identificadores del catálogo; los datos en memoria y las acciones de firma/votación simuladas no constituyen evidencia de persistencia. |
| RF77-12 | MIENTRAS se clasifica a un socio dentro de la escala de años sociales, EL SISTEMA utiliza Junior para años 1–2 y Senior desde el año 3. G57 se representa como socio exviajero fuera de esa escala, sin asignarle un año ficticio para eludir validaciones. La adecuación abarca cálculo, datos, contratos, representación, interfaz y documentación activa. |

**RF77-13:** CUANDO se amplía el catálogo de demostración, EL SISTEMA agrega cuatro identidades Junior y sus cuentas SOCIO habilitadas: dos G62 de 2.º año y dos G63 de 1.º año, conforme a la escala del corte de referencia confirmado. Conserva el perfil de propiedad, las dieciséis identidades originales, sus credenciales, relaciones, escenas, numeración y ocho asientos; los cuatro nuevos socios parten con saldo cero y sin movimientos. La tabla del corte es explícita y no implementa un cálculo permanente desde el número de grupo.

**RF77-14:** CUANDO se sincroniza esta rama con `main`, LA DEMO conserva el feedback central de la PR #49: avisos transitorios de éxito/error/advertencia/información abajo a la derecha, independientes y visibles sobre modales, con cierre accesible y duración de diez segundos. Conserva simultáneamente los contratos de identidad y las correcciones de filtros/accesibilidad de SCRUM-77.

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

## Fuera de alcance

Cambios de columnas o DTOs para exponer Gxx, conexión de Mis Expedientes a su API, ampliación del historial de legajo, renombre general a Revisores, ordenamiento compuesto, reportes, votación nominal compleja, firma/emisión productiva y motor de acumulación 3:1. Las brechas actuales no se ocultan como resultados exitosos; un fallo dentro de un recorrido incluido debe resolverse antes de su aceptación.

También queda fuera retrofechar causas recién creadas o avanzar inmediatamente por los seis estados con fechas artificiales. Poblar las etapas restantes de forma inmediata requeriría una ampliación explícita para temporalidad coherente.

La administración automática del pase anual en la asamblea no forma parte de esta US. El catálogo registra el corte social al que corresponden sus datos. La adecuación Junior/Senior se incorpora como cambio transversal solicitado por el PO; no debe confundirse con el renombre de roles a Revisores.

## Decisiones pendientes y dependencias

| ID | Decisión | Impacto |
|---|---|---|
| DP77-01 | Cerrado por versión escrita corregida del PO: G57 exviajero fuera de la escala, G58=6, G59=5, G60=4; avance en la asamblea de recambio, grupo sin excepciones y Junior 1–2 / Senior 3+. | Definición y adopción técnica verificadas; DEP77-02 cerrado en TS77.37. |
| DP77-02 | Cerrado: catálogo scrum77-g57-g60-v1 aceptado en TS77.07 tras auditoría TS77.37, con 16 identidades/cuatro por grupo, corte y rangos/referencias en [catálogo](../../docs/gestion-proyecto/CATALOGO_DATOS_DEMO_SCRUM-77.md). | 62 oráculos puros verdes; propiedad/carga/manifiesto/conciliación y persistencia posteriormente verificados en TS77.08–19. Datos sintéticos, sin afirmar representatividad estadística institucional. |
| DEP77-01 | Limitaciones de grupo visible, historial de legajo, Mis Expedientes y simulaciones locales. | Se registran; no se amplía esta US para corregir pantallas no incluidas. Grupo se valida en su catálogo persistido/manifiesto. |
| DEP77-02 | Cerrado en TS77.37: documentación/locales/DDL/transición, metadato/lectores/T01/JWT y legajo/SPA de TS77.30–43 verificados y auditados. CF77-01/02 resueltos en aclaraciones-po.md; CA77-08 verificado. | Prerrequisito resuelto con 932 backend/202 frontend verdes y auditoría sin hallazgos en esa instancia. Carga/conciliación/persistencia acreditadas posteriormente en TS77.08–19; el cierre de la dependencia por sí solo no las acredita. |

El alcance original quedó completado con CA77-00–08 verificados y TS77.01–43 cerradas; la ampliación autorizada completó TS77.44–46 y CA77-09 con carga aditiva, regresiones y auditoría aprobadas. La aceptación se apoya en carga/repetición/persistencia/recorridos reales, suites y auditoría integral; la formalización o CA77-00 por sí solos no la acreditan.
