# Plan de implementación — SCRUM-77 / S3-PO2

**US:** [Corroborar base de datos MySQL y ampliar seed data con grupos G57 a G60](https://guillenmartin94.atlassian.net/browse/SCRUM-77).

**Fecha:** 10/10/2026.

**Rama:** feature/US-S3-PO2-mysql-seed-g57-g60.

**Base:** main actualizada desde origin/main, commit 0596c64a1002fd06f135733c7090ae4480f7351f.

**Estado actual:** SCRUM-77 completada: TS77.01–43 verificadas y cerradas, con auditoría integral aprobada sin hallazgos abiertos. 1008 backend y 222 frontend verdes (0 errores), cobertura 93,91% en 22 módulos y build 6fae4265931dc3f8 correcto. Catálogo cargado, repetición y persistencia sin reseed verificadas; 78 controles HTTP reforzados y recorridos reales de escritorio/360/414 px en ambos temas. Lint frontend mantiene el builder TSLint heredado ausente. [Seguimiento](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827) y [runbook](GUIA_CARGA_DEMO_SCRUM-77.md).
**Participantes:** PM, desarrollador frontend senior, desarrollador backend senior y DBA senior.

## 1. Objetivo y decisiones confirmadas

Corroborar que Django utiliza MySQL en Docker y que los datos sobreviven a la recreación de los contenedores. Preparar socios de G57, G58, G59 y G60, subcomisiones y causas testigo para comprobar las integraciones actuales de la UI con datos identificables y persistidos.

El usuario confirmó usar **datos sintéticos representativos**. El conjunto cubrirá situaciones de prueba; no se presentará como una reproducción estadística del padrón institucional ni reutilizará nombres, documentos o legajos reales de las notas del PO.

La [aclaración corregida del PO](../../specs/005-mysql-seed-g57-g60/aclaraciones-po.md) confirma **G57 exviajero fuera de la escala; G58=6.º, G59=5.º y G60=4.º**, con G63=1.º como referencia. Junior abarca 1.º–2.º y Senior desde 3.º dentro de la escala. Todos los socios del mismo grupo comparten año social; el avance ocurre en la asamblea de recambio, sin fecha fija. La versión previa que asignaba 7.º a G57 queda descartada. Categoría social y vigencia de la cuenta se mantienen separadas.

El cambio de denominaciones y clasificación se solicita para todo el sistema. DEP77-02 y TS77.29–43 cubren representación, cálculo, datos, contratos, UI y documentación activa. La [revisión de impacto](IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md) define las decisiones, implementadas en TS77.30–43. TS77.43/35/36 resuelven identidad del legajo, caché/contratos y UI; TS77.37 verifica transversalmente antes de aceptar el catálogo TS77.07. No se convierte exviajero en cuenta inactiva por defecto; la carga G57 quedó verificada en TS77.11, con cuatro marcadores explícitos y año nulo.

La entrega inicial fue exclusivamente de planificación. Las autorizaciones posteriores y evidencias por unidad figuran en tasks.md de la spec 005. El cierre TS77.43/35/36/37/07 acreditó 932 backend/202 frontend verdes (0 errores), cobertura 94,72%, build y auditoría integral aprobados, catálogo aceptado con 62 oráculos y CA77-08/DEP77-02/DP77-02 cerrados. Esa instancia conservó 48 esquemas/huellas/conteos/contador, 33 migraciones/27 legadas vacías/39 FKs y metadato vacío, sin seed. La implementación posterior de guardias/propiedad/loaders/manifiesto ya se ejecutó sobre la demo y completó repetición/persistencia; TS77.08–27 cerradas y auditadas sin hallazgos abiertos.

## 2. Fuentes y alcance

| Fuente | Definición aplicable |
|---|---|
| Jira SCRUM-77 | Verificación de operatividad y persistencia de MySQL; datos de G57–G60, subcomisiones y antecedentes para probar la UI. No contiene criterios de aceptación adicionales ni comentarios. |
| [Notas del PO](notasPO.md), acuerdos del 07/10, sección 7 | Conectividad MySQL en Docker y ampliación representativa de los datos de prueba. |
| [Notas del PO](notasPO.md), decisiones generales y sección 6 | Expedientes con varios socios, resultado individual y acumulación 3:1 de felicitaciones/llamados sin fracciones. |
| [Aclaración escrita corregida del PO](../../specs/005-mysql-seed-g57-g60/aclaraciones-po.md), RN77-01–04 | G57 exviajero; corte 6/5/4 para G58–G60; Junior 1–2 / Senior 3+; pase efectivo en la asamblea de recambio. |
| [Constitución](../constitution.md), puntos 1–8 | Spec previa, integridad, pruebas, dominio desacoplado, terminología y permisos institucionales. |
| [Spec 001](../../specs/001-walking-skeleton/spec.md) | Autenticación, padrón, ranking, legajo único, agregación de puntos y categoría separada de vigencia. |
| [Spec 002](../../specs/002-expediente-trazabilidad/spec.md) | Numeración del servidor, seis estados, auditoría secuencial y múltiples involucrados. |
| [Spec 003](../../specs/003-monitorear-solicitudes-t01/spec.md) | Borradores/emitidas T01, aislamiento del solicitante y confidencialidad del TD. |
| [Spec 004](../../specs/004-clasificador-urgencia/spec.md) | Baja/Normal/Urgente, urgencia en origen y contratos vigentes del tablero. |
| [AGENTS.md](../../AGENTS.md), secciones 4–5 | TDD, unidades verificables y límites de edición. La autorización global posterior permite terminar TS77.09–27 e integrar TS77.08 sin confirmaciones individuales. |

El alcance recomendado comprende configuración de demostración aislada, preparación del esquema requerido, catálogo de fixtures, comando de seed, pruebas de integridad/idempotencia, protocolo de persistencia y comprobación de las integraciones existentes.

Los cambios de columna Grupo, ordenamiento compuesto, conexión de Mis Expedientes, historial completo del legajo, renombre de roles y emisión productiva de resoluciones se registran como dependencias. Incorporarlos a esta US exige definir expresamente el alcance en la spec. Reportes, votación nominal compleja y motor productivo 3:1 quedan fuera de esta planificación.

## 3. Diagnóstico de la planificación inicial

Los siguientes hallazgos corresponden al baseline 0596c64 de esta planificación; conservan su procedencia y no describen el estado de implementación posterior.

| Hallazgo comprobado | Consecuencia para la implementación |
|---|---|
| No existe seed_expedientes en main. [seed_demo.py](../../backend/socios/management/commands/seed_demo.py), línea 28, crea cinco cuentas demo, exige DEBUG y evita recrearlas por legajo. | Crear el comando solicitado y conservar la compatibilidad con seed_demo. |
| [socios.Socio](../../backend/socios/models.py), línea 36, y [padron.Socio](../../backend/padron/models.py), línea 90, corresponden a tablas e identidades distintas. | Registrar la correspondencia explícita entre cuenta, socio local, número institucional y legajo académico. No asumir igualdad de PK. |
| El legado contiene grupo_lista y socio_estadoHistorial.idGrupo; este último está mapeado en [padron/models.py](../../backend/padron/models.py), línea 196. El [DTO institucional](../../backend/padron/domain.py), línea 59, no expone Gxx. | Sembrar grupos en su catálogo real. Mostrar el grupo por API/UI requiere una decisión de alcance adicional; social_year no sirve como reemplazo. |
| [PuntajeAplicado](../../backend/ranking/models.py), línea 35, es managed=False y de lectura. El DDL vincula su expediente_id a tribunal_expediente, que referencia tribunal_datosresolucion. | Los antecedentes del ranking necesitan sus relaciones legadas. La PK de expedientes_expediente no puede utilizarse como FK del libro mayor legado. |
| El [SQL fuente](../analisis-proceso-actual/sistema-actual/sistema_actual_legado_schema.sql) sólo incluye G53–G56 y tres socios sanitizados. Contiene USE, DROP y desactivación de FKs. [load_legacy_schema](../../backend/ranking/management/commands/load_legacy_schema.py) admite limpieza y continúa tras errores. | Extraer un bootstrap específico de demo. No ejecutar el dump completo ni reutilizar el cargador como motor del nuevo seed. |
| [ExpedienteWorkflowService](../../backend/expedientes/services/workflow_service.py), líneas 42 y 76, asigna número, registra involucrados y audita cada transición; no permite salir del descargo antes de cinco días hábiles. | Usar los servicios y sus validaciones. No asignar números manuales ni forzar estados para llenar el tablero. |
| Mis Expedientes consume colecciones en memoria; el tablero conserva datos locales ante errores HTTP. La firma y votación actuales tienen mutaciones locales. | Una captura de pantalla no acredita integración MySQL. Exigir HTTP exitoso e IDs cotejados; no usar firma/votación simulada para producir antecedentes. |
| El legajo local puede devolver saldo cero y el modal mostrar el saldo recibido del ranking. | Comparar el payload de legajo, el de ranking y el agregado SQL; documentar la diferencia existente sin ocultarla. |
| [docker-compose.yml](../../docker-compose.yml) fija nombres de contenedores y el volumen global sgd_aveit_mysql_data. | Cambiar sólo el nombre de proyecto Compose no aísla los recursos. Definir nombres, puertos y volumen propios para demo. |

La inspección del entorno encontró MySQL y backend saludables, frontend Docker detenido y el backend montado desde el worktree calendario-pr49. Ese servicio no acredita el código de esta rama. No se recrearon los servicios existentes ni se alteró su volumen para planificar.

## 4. Solución técnica implementada

### 4.1. Entorno de demostración

La configuración Compose demo usa MySQL 8.0, volumen exclusivo, nombres de contenedores y puertos separados, con mounts del checkout de SCRUM-77. Resuelve también el destino de la SPA y del proxy hacia ese backend. La alternativa host inicia en 4202 con proxy.scrum77-local.conf.json hacia 8002; el perfil frontend Docker usa backend:8000.

La comprobación inicial registrará commit, mounts, base y volumen, sin contraseñas. Exigirá USE_SQLITE=False y PADRON_ADAPTER=database en el entorno destinado a demostrar la integración. El health HTTP se complementará con una consulta autenticada por Django: mysqladmin ping puede indicar éxito aunque el servidor rechace credenciales. [Referencia oficial](https://dev.mysql.com/doc/refman/8.0/en/mysqladmin.html).

Los grants de pruebas se revisarán con el usuario efectivo. El script [01-test-db-grants.sql](../../docker/mysql/init/01-test-db-grants.sql) usa aveit_dev de forma fija; cambiar MYSQL_USER no actualiza esa concesión.

### 4.2. Esquema y separación de responsabilidades

prepare_demo_schema aplica las migraciones managed de Django y prepara por separado el cierre de tablas legadas para padrón, grupos, historial, resoluciones y movimientos. Conserva auth_user y valida los tipos/destinos de FKs. La nueva core.0001_initial incorpora únicamente el registro de propiedad del seed; las migraciones previas y el SQL institucional fuente se conservan.

El bootstrap exige la base demo, valida tablas existentes y aborta frente a incompatibilidades, con FKs activas/InnoDB. DDL y grants permanecen separados de la carga DML por los commits implícitos de MySQL. [Referencia oficial](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html).

El esquema construido por [tests/legacy_schema.py](../../backend/tests/legacy_schema.py) sirve para las pruebas actuales, pero no sustituye la validación física de las FKs del esquema de demostración.

### 4.3. Catálogo e identidad persistente

El catálogo puro v1 conserva claves estables, corte del PO y nombres/correos/documentos ficticios. Los rangos candidatos se comprueban contra restricciones e identidades ajenas durante la carga; no se afirma que sean una reserva global. Una edición de un título o motivo no sustituye la clave de propiedad.

El [modelo DemoFixtureOwnership](../../backend/core/models.py), creado por [core.0001_initial](../../backend/core/migrations/0001_initial.py), implementa el siguiente contrato físico:

| Campo | Propósito |
|---|---|
| profile | Identifica el conjunto de demostración y su versión. |
| fixture_key | Clave estable de la escena o identidad del catálogo. |
| namespace | Tabla física managed/legacy, incluida una through automática o auditoría registrada. |
| object_key | PK canónica del destino como cadena, incluido UUID cuando corresponde. |
| owned | Distingue alta propia y referencia explícita compartida/preexistente. |

UNIQUE(profile, fixture_key) impide reasignar claves; UNIQUE(namespace, object_key) impide registrar dos propietarios del mismo destino entre perfiles. Los textos usan utf8mb4_bin. La validación normaliza PKs numéricas/UUID mediante el campo real, rechazando aliases que eludirían unicidad. El modelo no contiene entity_type, fingerprint o timestamp ni inventa una FK polimórfica: verifica cada referencia contra el resolutor managed o el contrato de las 27 tablas legadas.

El manifiesto JSON contiene status/profile/social_cycle, fixtures, mappings e identities, sin contraseñas, hashes o JWT. Las identidades distinguen institutional_number, academic_number, user_id, local_socio_id/local_legajo, group y ambas subcomisiones. Las fichas sin cuenta conservan campos locales nulos; mappings admite null para la subcomisión local del centinela 99. T01 tiene UUID/número T01 propio y expediente EXP asociado; los antecedentes poseen PKs legacy reales. Los nombres de personas no son claves de vinculación.

### 4.4. Comando y transacciones

El [comando seed_expedientes](../../backend/core/management/commands/seed_expedientes.py) exige perfil scrum77-g57-g60-v1, DEBUG, padrón database y conexión efectiva MySQL 8.0 demo por nombre/usuario/host/puerto. Reutiliza preflight/grants/salud HTTP y verifica modo estricto, FKs e InnoDB. El esquema debe acreditar contrato legado completo, tablas managed/M2M, historial consistente sin migraciones pendientes y las dos UNIQUE físicas del registro; el seed no migra ni prepara.

Cuatro módulos separan responsabilidades: [demo_seed](../../backend/core/demo_seed.py) orquesta guardias/transacción/manifiesto, [demo_fixtures](../../backend/core/demo_fixtures.py) resuelve propiedad/bloqueo, [demo_members](../../backend/core/demo_members.py) carga las cuentas/padrones y [demo_scenes](../../backend/core/demo_scenes.py) causas/T01/antecedentes. Una sola atomic abarca datos, propiedad y contador formal. No se importan helpers de tests ni se agrega un framework de seed.

El bloqueo GET_LOCK para scrum77-schema:<base> se adquiere antes de atomic y comparte nombre con prepare/transition. Cada escritura verifica identidad efectiva, transacción y propiedad del lock en la conexión. Una generación privada de ContextVar identifica cada adquisición: sólo se cachea el chequeo de esquema dentro de esa generación; liberar/reobtener exige revisar el contrato. Un GET_LOCK manual sin token no reutiliza el cache. export vuelve a validar todos los destinos registrados, incluidos vínculos/auditorías; pérdida de referencia produce rechazo, sin recreación.

La repetición resuelve filas propias por PK registrada y conserva IDs, numeración, credenciales, ediciones válidas, vínculos y auditorías. Las referencias compartidas seed_demo/catálogo son explícitas y no se reparan. Una coincidencia natural ajena, duplicada o contradictoria aborta; no se usa update_or_create, REPLACE, limpieza ni UPDATE/DELETE manual de puntos/expedientes. Una asociación persistida no autoriza adoptar otra persona por coincidencia visible.

El rollback debe abarcar también el registro de fixtures y el contador formal del expediente. No se exige reutilizar PK autoincrementales consumidas por MySQL tras una transacción fallida.

### 4.5. Causas y antecedentes

demo_members carga seis cuentas/perfiles nuevos y conserva las cinco referencias seed_demo mediante el comando existente. Resuelve grupos, subcomisiones, historial y satélites institucionales, con user_id real de auth_user y año/condición del corte. Las guardias de identidad y clasificación rechazan contradicciones sin recategorizar ni reasignar credenciales/roles/ediciones.

demo_scenes abre tres causas managed mediante ExpedienteWorkflowService y crea/emite cuatro T01 mediante sus serializers vigentes. Dos emitidas vinculan causas y usan iniciar_plazo_descargo con reloj actual; tres causas quedan en Creado y dos en Justificaciones. Se registran solicitante, relaciones M2M, auditoría y contador anual compartido. Los pedidos pendientes no se computan como saldo aprobado y no se despachan notificaciones externas.

El fixture implementa RF77-09 mediante INSERTs parametrizados exclusivos de la demo protegida: siete resoluciones → siete expedientes legacy → ocho asientos individuales. consideracion conserva número/fecha y VISTO/CONSIDERANDO/SE RESUELVE ficticios, sin acreditar firmantes/facultades. El asiento verifica socio, expediente y puntos exactos; una divergencia aborta sin sobrescribir. ReadOnlyModel permanece intacto y no se habilita _allow_write productivo.

No fabricar PuntajeGeneral para disimular un historial vacío. Verificar el agregado de movimientos y su respaldo resolutivo. Cómputos conserva su función técnica; los fixtures no amplían permisos para juzgar ni alterar puntos en el producto.

La carga inicial puebla exclusivamente **Creado** y **En período de justificaciones**, con apertura/plazo/auditoría actuales. Se conserva el workflow de seis estados; las cuatro etapas restantes no se pueblan artificialmente. Los antecedentes legados no avanzan esas causas ni implementan el motor 3:1. El saldo sintético inicial esperado es +1; la resolución compartida atribuye +2/+1 a socios distintos.

### 4.6. Recorridos, regresión y entrega

Los oráculos SQL/API/manifiesto verifican namespaces, identidades, relaciones y suma de asientos; los HTTP de prueba y el smoke live mantienen contratos actuales. La autenticación por identifier conserva el acceso de prueba sin contraseña: ese recorrido acredita sesión/permisos, sin afirmar validación de contraseña. No se publican tokens o secretos.

Dos correcciones mínimas resuelven recorridos incluidos: el filtro de socio del tablero recuerda la búsqueda confirmada por servidor y evita descartar una causa cuando el buscado es involucrado secundario; el DTO compacto sigue mostrando al principal. El modal de detalle existente incorpora role=dialog, aria-modal/título, Escape, FocusTrap CDK, foco inicial en Cerrar y restauración. No se crea un componente Socios ni se amplía la API.

El [runbook](GUIA_CARGA_DEMO_SCRUM-77.md) separa configuración/preflight/preparación/carga, manifiesto, repetición, recuperación y persistencia sin reseed. La preparación real aplicó una migración core.0001, con 49 tablas/34 registros de migración; sólo agregó registro/metadatos Django, preservando las 27 legadas vacías/contador 1 antes de cargar. El seed registró 162 referencias, 16 fichas, 11 cuentas/perfiles, cuatro EX_TRAVELER, cinco causas, cuatro T01, siete expedientes/resoluciones y ocho asientos con suma +1. La segunda salida JSON y los 49 hashes de esquemas/filas/conteos/contador 770017 fueron idénticos.

La persistencia cambió el ID MySQL (prefijos 5b793d5 → e5e7116) conservando sgd_aveit_scrum77_demo_mysql_data y las 49 comparaciones exactas, sin seed/preparación entre mediciones. HTTP acreditó 78 controles antes y después. La regresión final cerró 1008 backend/222 frontend verdes, cobertura 93,91% (2331 sentencias/142 sin cubrir, 22 módulos) y build 6fae4265931dc3f8 en 7854 ms; Ruff y controles Django/migraciones correctos. Navegador real desktop/360/414, temas y teclado aprobados; CA77-06 verificado. Revisión documental independiente TS77.27 en curso. Lint frontend heredado se clasifica separado, sin aceptar mocks como prueba live.

transition(ahora=...) controla la validación y el plazo, pero no las fechas automáticas de creación e historial; open_expediente tampoco recibe un reloj. Pasar fechas futuras para avanzar inmediatamente fabricaría una cronología incoherente. Si el PO exige poblar los seis estados managed en una sola ejecución, deberá definir una ampliación de spec para un reloj coherente en apertura, numeración e historial. Esa ampliación no es necesaria para el alcance recomendado.

## 5. Matriz de datos y comprobación

TS77.07 concreta el conjunto de **16 socios institucionales, cuatro por grupo**, con seis cuentas nuevas y cinco referencias seed_demo conservadas, en el [catálogo v1](CATALOGO_DATOS_DEMO_SCRUM-77.md). Cantidades/rangos y referencias verificados por 62 oráculos; aceptado tras auditoría TS77.37 y DP77-02 cerrado. Los loaders y la carga live se contrastaron con manifiesto/MySQL/HTTP; el navegador está aprobado y la revisión documental independiente final sigue en curso. El reparto es una cobertura de prueba, sin significado estadístico institucional.

| Escenario | Fixture del catálogo | Evidencia a conciliar |
|---|---|---|
| Cohortes | G57 exviajero y G58/G59/G60 en 6/5/4, con pertenencia societaria persistida. | Catálogo grupo_lista, último historial aplicable y manifiesto del corte confirmado; G57 sin año ficticio. |
| Subcomisiones | Tres asignadas y centinela institucional 99 para la ficha sin asignación; socio local conserva NULL. | FK y nombres consistentes entre los dos padrones, sin inventar una subcomisión local para 99. |
| Categoría y vigencia | Junior 1–2, Senior desde 3 en la escala y G57 exviajero; cuentas con vigencia independiente. | Clasificación nueva contrastada con el PO; los grupos objetivo G58–G60 son Senior. No forzar un Junior en esas cohortes para cubrir pruebas. |
| Roles | Cuentas existentes de demo y dos autoridades solicitantes distintas. | Perfil, acceso servidor y aislamiento; nomenclatura Revisores registrada como dependencia del cambio general de rol. |
| Búsqueda/paginación | Tildes, nombres extensos, coincidencias parciales, texto sin coincidencias y más de diez socios visibles. | Ranking con segunda página, búsqueda T01 desde tres caracteres, selección múltiple y estados vacíos. |
| Antecedentes | Sin movimientos, saldo positivo, negativo, compensado en cero y empate entre socios. | Resolución + FK legada + suma SQL = payload ranking; contraste separado con legajo. |
| Multisocio | Causa creada y T01 emitida multisocio; antecedente compartido con +2/+1 individuales. | M2M, solicitante y auditoría; ningún saldo atribuido automáticamente a todos. |
| T01 | Borrador incompleto, retomable y emitida para dos creadores. | Snapshot, urgencia, expediente vinculado, inmutabilidad e aislamiento de mis-solicitudes. |
| Estados y urgencia | Causas en Creado y En período de justificaciones; Baja, Normal y Urgente distribuidas. Conservar los seis estados y columnas. | Workflow y fechas; board/tabla cotejados con DB. No avanzar hasta estados posteriores antes de vencer el plazo; registrar desvíos UI existentes. |
| Felicitaciones/llamados | Escenas sin impacto fraccionario; casos 2/3 sólo cuando exista soporte de contador aprobado. | No introducir ±0,33 o ±0,5 ni implementar el motor 3:1 para completar fixtures. |

## 6. Criterios de aceptación propuestos

Estos criterios originales concretan Jira y las notas del PO. Se formalizaron posteriormente en la spec 005, que agrega CA77-00 para verificar por separado la primera tarea de configuración.

| ID | Criterio y evidencia de cierre |
|---|---|
| CA77-01 | Django conecta al MySQL correcto; SELECT 1 y consulta de identidad/version/modo SQL exitosos; health HTTP 200 con status=ok y db=connected. Checkout y mounts comprobados. |
| CA77-02 | G57–G60, subcomisiones, identidades y causas del catálogo aprobado están persistidos y son consistentes; cero duplicados u huérfanos. |
| CA77-03 | Segunda ejecución sin altas duplicadas ni avance del contador del expediente; se conservan las ediciones y credenciales existentes. Colisión y fallo intermedio revierten el DML completo. |
| CA77-04 | Causas con estados permitidos, numeración del servidor, involucrados, fechas y auditoría válidos. Cada movimiento histórico tiene respaldo resolutivo y atribución individual en su namespace. |
| CA77-05 | Recrear el contenedor MySQL demo preservando el volumen conserva IDs, relaciones, auditorías y saldos, sin ejecutar nuevamente el seed. |
| CA77-06 | Login, ranking, selector T01, Mis Solicitudes y tablero existentes se contrastan con respuestas HTTP reales e IDs del manifiesto, en escritorio y móvil. Limitaciones de grupo, historial y Mis Expedientes se documentan y se decide explícitamente su alcance antes del cierre de la US. |
| CA77-07 | Pruebas nuevas y suites correspondientes en verde, controles de migraciones/lint aplicables y revisión final frente al PO. Los resultados del baseline no se usan como pruebas del seed futuro. |

## 7. Secuencia de tareas propuesta

El usuario autorizó globalmente terminar TS77.09–27 con los subagentes necesarios, sin confirmaciones individuales; TS77.08 se integra antes de cargar como prerrequisito de guardias. Cada unidad de código conserva TDD y verificación pertinente. El paralelismo distribuye ownership/loaders/escenas/UI/documentación por archivos, respetando integración y runners centralizados; no exige una nueva pausa entre estas tareas autorizadas. La tabla conserva el desglose original, mientras tasks.md/TASK.md registran el cierre efectivo.

| ID | Responsable | Minutos | Trabajo y evidencia de terminación |
|---|---|---:|---|
| 77.01 | PM + PO | 20 | Ratificar alcance, grupo/año social, antecedentes y CA; autorizar expresamente la formalización de la spec de esta US. |
| 77.02 | PM | 25 | Con autorización, registrar requisitos EARS y tareas trazables en los artefactos SDD y TASK.md; dejar sin completar las tareas de código. |
| 77.03 | DBA | 20 | Precisar contenedores, puertos, mounts, base y volumen del entorno demo; comprobar que no colisionan con el entorno actual. |
| 77.04 | Backend + DBA | 25 | Con pruebas de preflight, preparar configuración demo y validar MySQL, adapter, usuario y grants. |
| 77.05 | DBA | 25 | Extraer el DDL requerido y su cierre de FKs; documentar correspondencias de tipos con Django. |
| 77.06 | DBA | 25 | Verificar bootstrap en demo vacía y segunda preparación sin destrucción; comprobar esquema físico/FKs activas. |
| 77.07 | Backend + DBA | 20 | Fijar catálogo sintético y mapa de identidades con oráculos de conteos, relaciones y saldo. |
| 77.08 | Backend | 25 | TDD de guardias del comando: entorno/base inválidos sin escrituras; mensajes claros. |
| 77.09 | Backend | 25 | TDD del registro de propiedad y su unicidad; ejecución serializada por perfil y colisiones ajenas. |
| 77.10 | Backend | 25 | TDD de usuarios/socios locales y coexistencia con seed_demo; conservar contraseñas y permisos existentes. |
| 77.11 | Backend + DBA | 25 | TDD de grupos, socios institucionales, subcomisiones e historial; identificar cada vínculo sin equiparar PK. |
| 77.12 | Backend | 25 | TDD de causas simples y multisocio mediante workflow; correlativo y auditoría. |
| 77.13 | Backend | 25 | TDD de borradores/emitidas T01 de dos solicitantes; aislamiento y urgencia heredada. |
| 77.14 | Backend | 25 | TDD de plazos actuales y urgencias de las dos etapas seed; reusar la regresión de los seis estados sin poblar etapas posteriores artificialmente. |
| 77.15 | Backend + DBA | 25 | TDD del respaldo resolutivo histórico de demo y atribución individual, según alcance aprobado. |
| 77.16 | Backend | 25 | TDD de segunda ejecución: mismos IDs, numeración, relaciones e historial; preservar ediciones posteriores. |
| 77.17 | Backend | 25 | TDD de colisión y fallo intermedio: rollback de todo el DML y del contador formal. |
| 77.18 | Backend + DBA | 20 | Cotejar endpoints, manifiesto y suma SQL; registrar diferencias preexistentes de legajo. |
| 77.19 | DBA | 25 | Capturar estado, recrear sólo el MySQL demo sobre el mismo volumen y comparar sin reseed. |
| 77.20 | Frontend | 20 | Smoke login/permisos con cuentas demo; HTTP y perfiles reales. |
| 77.21 | Frontend | 25 | Smoke ranking/legajo: filtros, empate, segunda página y contraste de ambos saldos. |
| 77.22 | Frontend | 25 | Smoke selector T01 y Mis Solicitudes: varias selecciones, borradores/emitidas y aislamiento. |
| 77.23 | Frontend | 25 | Smoke board/tabla: GET 200, IDs, filtros y estados contra MySQL; detectar fallback en memoria. |
| 77.24 | Frontend | 25 | Verificar 360/414 px, escritorio y teclado con nombres largos, tildes, modales y badges. |
| 77.25 | Backend | 25 | Ejecutar suite backend con MySQL real, cobertura de negocio exigida, lint/formato y controles de migraciones. |
| 77.26 | Frontend | 25 | Ejecutar suite y build con dependencias del proyecto; clasificar fallos y no aceptar mocks como evidencia. |
| 77.27 | PM + equipo | 20 | Documentar uso, respaldo/recuperación y CA→evidencia; chequeo final PO y estado explícito de dependencias. |

Las estimaciones son orientativas para dividir trabajo, no compromisos de Sprint ni asignación de Story Points. El bootstrap y los antecedentes pueden requerir subdivisión una vez definida la spec. Este listado inicial no registra avances; el estado efectivo se mantiene en tasks.md y TASK.md.

La aclaración posterior agrega TS77.28–37 y la revisión de impacto TS77.38–43, detalladas en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md). Secuencia cumplida: 30 → 31 → 32 → 33 → 38 → 39 → 40 → 34 → 41 → 42 → 43 → 35 → 36 → 37 → 07. El usuario autorizó esos grupos paralelos con runners centralizados; su cierre histórico acreditó 932 backend/202 frontend verdes, cobertura 94,72%, build y auditoría TS77.37 aprobados, catálogo TS77.07 aceptado y CA77-08/DEP77-02/DP77-02 cerrados. La autorización global posterior integra guardias TS77.08 y finaliza TS77.09–27 sin nueva confirmación por unidad. No se programa avance anual por una fecha supuesta.

## 8. Protocolo de prueba y persistencia

1. Comprobar rama/commit, mounts, labels Compose y volumen real. Registrar el backend al que apunta la SPA.
2. Consultar por Django vendor, DATABASE(), CURRENT_USER(), VERSION(), modo SQL, charset, collation y foreign_key_checks; confirmar MySQL, InnoDB y FKs activas.
3. Revisar showmigrations --plan, migrate --check, makemigrations --check --dry-run y esquema legado físico. Mantener DDL/grants fuera del atomic de datos.
4. Ejecutar el seed sólo en la demo preparada. Verificar unicidad, relaciones y respaldo resolutivo mediante consultas de lectura y manifiesto.
5. Ejecutar nuevamente y comparar IDs, conteos, auditorías y contador. Probar preservación de una edición válida, colisión ajena y fallo a mitad de carga.
6. Capturar filas propias ordenadas y hashes de contenido, IDs de contenedor y nombre del volumen. Recrear únicamente MySQL demo, conservar el volumen y comprobar que cambió el contenedor.
7. Sin reseed, repetir consultas SQL/Django/API y comparar IDs, hashes, relaciones y saldos. Un simple reinicio no alcanza para demostrar reutilización del volumen.
8. Comprobar UI con respuestas HTTP y datos del manifiesto. No usar la firma simulada ni los datos en memoria como prueba de antecedentes o persistencia.
9. Conservar un respaldo consistente de demo. Un fallo de DML debe revertirse; ante un fallo de DDL, conservar el volumen/estado y diagnosticar el contrato antes de reintentar el procedimiento protegido. No ejecutar reset, down -v ni UPDATE/DELETE manuales de saldos o expedientes para aparentar recuperación.

Pruebas prioritarias: guardias, dos ejecuciones, conservación de credenciales, colisiones, rollback, identidades separadas, multisocio, atribución individual, respaldo de saldo, plazos y persistencia real. SQLite y el esquema simplificado de tests no cierran la verificación MySQL de esta US.

## 9. Decisiones y dependencias antes de implementar

| Decisión | Estado y consecuencia |
|---|---|
| Datos sintéticos representativos | Confirmado por el usuario. TS77.07 fija 16 identidades/cuatro por grupo y rangos en el [catálogo v1](CATALOGO_DATOS_DEMO_SCRUM-77.md), con 62 oráculos verdes; aceptado tras auditoría TS77.37, DP77-02 cerrado. Distribución sintética, sin afirmar representatividad estadística institucional. |
| Correspondencia cohorte/año social | Cerrada por versión escrita corregida del PO: G57 exviajero fuera de la escala; G58/G59/G60 en 6/5/4. No utilizar el año 7 de la versión retirada. |
| Clasificación transversal | Junior 1–2 / Senior 3–6 y exviajero explícito/null implementados en TS77.30–43, incluidos legajo y SPA. 932 backend/202 frontend verdes, sin efectos sobre roles/vigencia/saldos; auditoría TS77.37 aprobada y DEP77-02/CA77-08 cerrados. |
| Representación de exviajeros | EX_TRAVELER/null local y DDL/transición implementados. TS77.40 agrega metadato por nroSocio/fuente/corte, con lector TS77.34/T01 TS77.41; cierre previo sin hallazgos y tabla demo vacía en esa instancia. TS77.11 cargó cuatro marcadores G57 con corte/propiedad/manifiesto validados, sin perder acceso/permisos por condición. |
| Spec de SCRUM-77 | TS77.08–27 integrado por autorización global; suites/build/carga/repetición/HTTP/persistencia ya verificados. Navegador aprobado/CA77-06 verificado; auditoría integral final aprobada sin hallazgos abiertos antes del cierre CA77-07. |
| Antecedentes históricos | RF77-09 implementado y cargado: siete respaldos/expedientes y ocho asientos individuales con suma +1 conciliada, sin habilitar escritura del ORM lector. |
| Poblar los seis estados managed inmediatamente | Extensión opcional de alcance. El plan recomendado sólo carga dos etapas con fechas actuales; llenar las restantes exige una spec adicional para temporalidad coherente. |
| Registro auxiliar de propiedad | TS77.09 implementa DemoFixtureOwnership/core.0001, dos UNIQUE físicas, resolución de PKs/destinos y bloqueo compartido con validación por generación. No adopta/recrea filas ajenas o referencias perdidas. |
| Grupo visible por API/UI | La spec verifica grupo persistido y manifiesto; ampliar contratos o columnas de UI queda fuera de esta US. |
| Mis Expedientes e historial de legajo | Integración incompleta. Resolver en sus US o ampliar expresamente el alcance; no declarar aceptación de esas pantallas usando mocks. |

Las brechas existentes de UI se clasifican con evidencia. RF77-11 y CA77-06 de la spec formalizada delimitan las integraciones incluidas; un fallo dentro de ese alcance se corrige antes del cierre. Documentar una brecha no convierte automáticamente en aprobada la aceptación.

## 10. Verificaciones realizadas durante la planificación

| Comprobación | Resultado |
|---|---|
| Git | main actualizada con pull --ff-only; nueva rama creada desde 0596c64. |
| Backend de esta rama | **490 passed en 104,33 segundos; 0 errores.** Contenedor temporal con mount explícito del checkout actual, MySQL real y base de tests separada. |
| Frontend | Se intentó npm test -- --watch=false --browsers=ChromeHeadless. No inició la suite: Angular CLI no disponible porque faltan dependencias locales. No se instalaron paquetes para esta planificación. |
| Entorno activo | MySQL/backend saludables; backend de otro worktree y frontend Docker detenido. No constituye evidencia de aceptación de SCRUM-77. |
| PO y alcance | Durante la planificación inicial: notas del 27/09 y 07/10, constitución y cuatro specs leídas; datos sintéticos confirmados y grupo/año social aún pendiente. La aclaración corregida posterior cierra DP77-01. |
| Archivos rectores | Durante esta planificación previa, notasPO.md, Seguimiento de Proyecto.md, specs y TASK.md se conservaron sin ediciones. La formalización posterior autorizada se registra en la spec 005. |

Comando de baseline utilizado, limitado a una base temporal de pytest y sin reemplazar los servicios activos:

~~~powershell
docker compose run --rm --no-deps -T --volume D:/Proyectos/seminario-integrador/backend:/app --env DATABASE_NAME=scrum77_baseline --env USE_SQLITE=False backend pytest -q
~~~

La primera suite lanzada en el contenedor existente correspondía al worktree de calendario. Sus resultados y migraciones se excluyeron de la validación de esta rama al comprobar el mount. La suite de 490 pruebas es el baseline correcto; no valida funciones del seed que todavía no fueron implementadas.

Los cambios locales anteriores de docs/seguimiento-sprints-1-2 quedaron conservados en stash@{0}, hash 01b62051787149e27e3f5d8fafcd2495b0b62bd4, mensaje «pre-SCRUM-77: preserve docs-seguimiento-sprints-1-2 local work».

## 11. Aportes de los cuatro perfiles

| Perfil | Responsabilidad en el plan | Skill aplicada |
|---|---|---|
| PM | Alcance, fuentes, criterios de aceptación, vacíos y secuencia SDD. | requirementsExtractor, modo extracción/normalización. |
| Frontend senior | Contratos reales, datos necesarios, límites de mocks y matriz de QA. | designUxUi, modo auditoría. |
| Backend senior | Comando inexistente, workflow, idempotencia, propiedad de fixtures y TDD. | backendTesting, modo estrategia. |
| DBA senior | Esquema legado, identidades, FKs, aislamiento Docker y persistencia. | ormMaster, modo auditoría. |

Los cuatro aportes se consolidaron en este documento. La capacidad de la sesión permitió tres subagentes simultáneos; el DBA se incorporó al terminar el aporte inicial del PM y coordinó las relaciones de grupo/antecedentes con ambos desarrolladores.

## Verificación definitiva de recorridos y calidad

El navegador real acreditó roles/permisos, ranking/legajo, T01/Mis Solicitudes/aislamiento y tablero/tabla en escritorio, 360 y 414 px, con teclado y temas claro/oscuro. Las correcciones incluidas resolvieron filtro de involucrado secundario, fuente de IDs de borradores, contraste, scroll/contención y foco de modales; no amplían grupo/historial/firma/votación ni alteran fixtures.

La suite definitiva acredita 1008 backend/222 frontend verdes, cobertura 93,91% en 22 módulos y build 6fae4265931dc3f8. Ruff/migraciones correctos; lint heredado ausente clasificado. [Evidencia UI](VERIFICACION_UI_SCRUM-77.md), [registro de resultados](VERIFICACION_CARGA_SCRUM-77.json) y [aceptación](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827).
