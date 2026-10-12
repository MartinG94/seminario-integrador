# Plan técnico — Spec 005 / SCRUM-77

**Fuente:** [plan interdisciplinario](../../docs/gestion-proyecto/PLAN_IMPLEMENTACION_SCRUM-77_MYSQL_SEED_G57_G60.md).

**Spec:** [requisitos y criterios](spec.md).

**Estado actual:** SCRUM-77 y ampliación TS77.44–46 completadas y auditadas, sin hallazgos abiertos. 1064 pruebas backend verificadas y 278 frontend verdes (0 errores), cobertura 93,91% en 22 módulos y build b03663973a049f50 correcto. Veinte fichas con cuatro Juniors; 188 referencias, carga aditiva y repetición estable sobre 52 tablas, conservando las altas de UAT. 111 controles HTTP locales y feedback central de PR #49 verificados. Lint mantiene la limitación TSLint heredada. [Seguimiento](tasks.md#verificación-de-ts774446).

**Antecedente cerrado TS77.43/35/36/37/07:** 932 pruebas backend y 202 frontend verdes (0 errores), cobertura backend 94,72%, build correcto y auditoría integral aprobada sin hallazgos pendientes. Catálogo v1/DP77-02 aceptado con 62 oráculos; CA77-08/DEP77-02 cerrados. Esa instancia conservó 48 esquemas, filas/conteos y contador, sin carga. [Evidencia histórica](tasks.md#verificación-de-ts774335363707).

**Aclaración posterior del PO:** [versión corregida](aclaraciones-po.md). G57 es exviajero fuera de la escala; G58/G59/G60 corresponden a años 6/5/4. Junior abarca 1–2 y Senior desde 3. DP77-01 y DEP77-02 cerrados; adopción verificada en TS77.37 antes de aceptar el catálogo, sin cargarlo.

## Ampliación autorizada después de UAT — TS77.44–46

Sincronizar por fast-forward con `origin/main` (PR #49, 73a2d8a), preservando cambios locales mediante zip y stash antes de combinar archivos solapados. Conservar el centro global de notificaciones y las validaciones de calendario, junto con identidad institucional, filtros confirmados y accesibilidad de SCRUM-77. Aplicar las migraciones nuevas a la demo mediante el comando protegido de preparación; no tocar el volumen ni resembrar para resolver conflictos.

Extender aditivamente `scrum77-g57-g60-v1`, sin cambiar el namespace de propiedad ni las dieciséis referencias existentes. Agregar `group.g62` (año 2) y `group.g63` (año 1), cuatro fichas de órdenes 17–20 y cuatro cuentas SOCIO habilitadas. Los loaders genéricos continúan resolviendo propiedad/PK bajo la transacción y el bloqueo existentes. No agregar causas ni asientos; el saldo histórico total sigue siendo +1.

TDD: alta nueva y ampliación de una carga de dieciséis, conservación de credenciales/filas originales, rollback ante colisión Junior y repetición estable. Verificar MySQL real/HTTP, filtro Junior/fichas/permisos y feedback global en la SPA. La UAT original aprobada no acredita automáticamente estos cambios posteriores; registrar su verificación separada.

## Configuración original

Crear docker-compose.scrum77-demo.yml como archivo autónomo, sin combinarlo con docker-compose.yml. Se reutilizan Dockerfiles y proxy existentes; se evita heredar listas de ports/volumes o nombres globales del Compose habitual.

| Recurso | Identidad propuesta |
|---|---|
| Proyecto | sgd-aveit-scrum77-demo, especificado también con -p en los comandos documentados. |
| MySQL | Contenedor sgd_aveit_scrum77_demo_mysql; base aveit_tribunal_scrum77_demo; puerto 127.0.0.1:3307 → 3306. |
| Backend | Contenedor sgd_aveit_scrum77_demo_backend; puerto 127.0.0.1:8002 → 8000. |
| SPA | Contenedor sgd_aveit_scrum77_demo_frontend; perfil opcional frontend; puerto 127.0.0.1:4202 → 4200. |
| Volumen MySQL | sgd_aveit_scrum77_demo_mysql_data. |
| Red | Red default exclusiva del proyecto demo. |
| Mounts | ./backend → /app, ./docs → /docs:ro y ./frontend → /app, resueltos respecto del archivo en este checkout. Dependencias de la SPA en volumen independiente. |

Los servicios conservan sus nombres db/backend/frontend para reutilizar el proxy frontend existente. MySQL host=db y puerto interno=3306; la SPA mantiene target=http://backend:8000. CORS permite los orígenes demo localhost/127.0.0.1:4202.

Configurar USE_SQLITE=False y PADRON_ADAPTER=database explícitamente. La base/usuario y los puertos del demo no consumen variables genéricas MYSQL_* de otros entornos. Las contraseñas y clave Django usan variables SCRUM77_* con defaults exclusivamente de desarrollo; no se imprimen en las verificaciones.

Reutilizar usuario aveit_dev en el servidor demo independiente y su init SQL existente; esto no comparte conexiones ni datos con el servidor habitual. Verificar grants y consultas reales en TS77.04. La primera tarea sólo entrega configuración: no levanta servicios, aplica migraciones o siembra datos.

## TDD y oráculos de aislamiento

Las pruebas de infraestructura consumirán el modelo resuelto por docker compose config --format json. Validarán recursos disjuntos, binds del checkout correcto, publicación loopback, comunicación interna y resistencia a variables genéricas conflictivas. No analizarán el YAML con regex ni añadirán librerías de YAML.

En un host/CI con Docker CLI, pytest resolverá los archivos directamente. En el contenedor backend sin Docker CLI, la verificación generará inmediatamente un snapshot de las configuraciones base/demo y demo con variables conflictivas, eliminará campos de secretos y lo pasará a pytest por un canal de entorno; no se guardará una fixture estática ni se imprimirá el modelo con credenciales.

La ausencia del archivo demo debe hacer fallar las pruebas antes de implementarlo. Ejecutar después pruebas enfocadas, suite backend y Ruff. La prueba de configuración no demuestra conexión MySQL demo.

La [guía de configuración y verificación](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md) documenta el archivo entregado, los recursos y las condiciones necesarias para ejecutar las pruebas dentro o fuera del contenedor.

## Preflight implementado — TS77.04

El comando `core.management.commands.check_demo_mysql` comprueba el perfil demo antes de abrir el cursor. Consulta identidad y condiciones de la sesión por Django, y verifica grants directos mediante `information_schema.SCHEMA_PRIVILEGES` con grantee parametrizado. Resuelve patrones de base MySQL sin sumar grants superpuestos; rechaza roles activos y partial_revokes para mantener una acreditación inequívoca del perfil entregado. Sólo ejecuta SELECT y devuelve un JSON sin credenciales.

La salud HTTP se consulta en loopback dentro del mismo contenedor mediante un opener sin proxies, con rechazo de redirecciones y URL efectiva exacta. Las pruebas incluyen un servidor HTTP real y la verificación final usa MySQL demo con una base de pytest separada. Los mounts, red y volumen se cotejan por metadatos Docker saneados. Evidencia y límites en [tasks.md](tasks.md) y en la guía de ejecución. El esquema físico y las guardias del comando de carga corresponden a tareas posteriores.

## Arquitectura por tarea

1. TS77.04, completada: preflight de conexión Django real y grants, con identificación de motor/base/mounts; no confiar sólo en mysqladmin ping.
2. TS77.05/06, completadas: [DDL mínimo](../../backend/core/sql/scrum77_legacy_schema.sql), [correspondencias](../../docs/gestion-proyecto/MAPEO_ESQUEMA_DEMO_SCRUM-77.md) y [preparación protegida](../../backend/core/management/commands/prepare_demo_schema.py), 27 tablas/39 FKs con cierre completo. auth_user externo creado por migraciones; puntos y puntajeAplicado en DECIMAL(10,2), acorde con el ORM. Validación previa de tablas/historial, migraciones Django sólo si hay plan pendiente, CREATE de faltantes y verificación final con FKs activas. Demo preparada y repetida sin destrucción ni seed; no importar el dump destructivo ni helpers de tests.
3. DEP77-02 resuelto antes de TS77.07/10/11 mediante TS77.29–43: revisión de impacto y compatibilidad, documentación rectora, representación de exviajeros, cálculo, migración, evolución demo, condición institucional, T01, JWT, identidad de legajo, consumidores y auditoría. No inventar año 7 para G57 ni ampliar el rango como atajo.
4. TS77.07: catálogo sintético determinista y mapa de identidades según el corte confirmado. G57 exviajero se mantiene dentro de la cobertura pedida por Jira; G58/G59/G60 usan 6/5/4. Versionar el corte, sin una fórmula perpetua ni avance fijo por calendario.
5. TS77.08/09 implementadas: seed_expedientes protegido y DemoFixtureOwnership, con UNIQUE(profile, fixture_key) y UNIQUE(namespace, object_key), PK canónica y validación explícita de destinos managed/legacy, sin FK polimórfica inventada. El bloqueo se comparte por base con prepare/transition.
6. TS77.10–17 implementadas: loaders de miembros/escenas dentro de una sola transacción DML; coexistencia con seed_demo, servicios workflow/T01, causas actuales en dos etapas y antecedentes legados individualizados. Pruebas de conservación, colisiones y rollback preceden a la carga real.
7. TS77.18–27 integradas: oráculos SQL/API/manifiesto, persistencia sin reseed, correcciones mínimas del modal/filtro de socio, regresión y runbook. Carga/repetición/HTTP/persistencia, suites y navegador verificados; auditoría documental/integral final aprobada sin hallazgos abiertos.

## Adecuación transversal Junior/Senior y exviajeros

El cambio afecta a la clasificación y a su denominación, no sólo a etiquetas. La migración deberá recalcular por año y situación: traducir todos los antiguos PASSIVE a Junior dejaría incorrectamente a los socios de 3.º. TS77.29 define la compatibilidad de valores persistidos, payloads y filtros a partir de los consumidores relevados.

La [revisión TS77.29](../../docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md) fija representación explícita EX_TRAVELER/año nulo y códigos JUNIOR/SENIOR; UNKNOWN queda separado para lecturas anómalas. TS77.31 amplía category a 12 y admite año nulo mediante una migración managed nueva; TS77.33 recalcula datos por año/situación. La condición institucional se registra mediante metadato propio por nroSocio con fuente/corte y asociación validada, sin reutilizar cargo/estado ni incorporar una FK hacia una tabla ausente durante migrate. No equivale a deshabilitación, no cambia roles por defecto y no omite G57 del seed.

La nulabilidad nueva de anoSocial sólo se adapta en el DDL demo y requiere transición protegida del contrato físico anterior; dump/base institucional no se modifican. Filtros admiten aliases históricos de entrada con semántica nueva; respuestas canónicas y SPA se liberan de forma coordinada. El perfil cacheado se obtiene nuevamente de me, refresh lee categoría del socio actual y T01 transmite el año nulo sin usar or 1 ni equiparar namespaces de identidad. Inventario, alternativas, límites y oráculos en la revisión; su existencia no acredita implementación.

La secuencia de adecuación es TS77.30 → 31 → 32 → 33 → 38 → 39 → 40 → 34 → 41 → 42 → 43 → 35 → 36 → 37 → 07. TS77.38–43 separan el trabajo descubierto: contrato y transición completados en TS77.38/39; metadato/lectores/T01/JWT en TS77.40/34/41/42. TS77.43 resuelve la fuente explícita del legajo; TS77.35/36 integran contratos, perfil cacheado, UI y datos demo existentes. La verificación TS77.37 precede a aceptar el catálogo TS77.07, preparado en paralelo por autorización del usuario. La autorización global posterior permite completar TS77.09–27 e integrar previamente las guardias TS77.08 sin otra confirmación por unidad. Firma/elegibilidad requieren regla propia en sus US; no se deducen desde la nueva categoría ni bloquean clasificación.

Las pruebas cubren años 1, 2 y 3 en el límite de categoría, años 4 y 6, representación de G57, conservación de credenciales/vigencia/roles/saldos y compatibilidad de filtros. Los cambios de documentación activa se realizan en su unidad; las Notas del PO y el seguimiento macro permanecen inalterados. Para el cierre autorizado, los agentes preparan unidades independientes en paralelo, integrando propiedad/miembros antes de escenas y ejecución live; las pruebas reales se serializan desde root.

Separar DDL/grants de DML por los commits implícitos de MySQL. No usar update_or_create, REPLACE, limpieza del volumen ni UPDATE/DELETE manuales de saldos/expedientes. No confundir la PK de expedientes_expediente con la FK del libro mayor a tribunal_expediente.

## Representación local implementada — TS77.31

El [modelo Socio](../../backend/socios/models.py) admite EX_TRAVELER únicamente con social_year nulo. Las restantes clasificaciones requieren año entre 1 y 6. Al cerrar TS77.31 se conservaban el enum y corte anteriores; TS77.32 los adecua conforme al apartado siguiente. clean/save rechazan combinaciones inválidas antes de persistir. Cuando update_fields selecciona categoría o año, save incluye ambos para conservar el par; una actualización de nombre no incorpora una clasificación que no fue seleccionada. Rol, habilitación, usuario e identidad permanecen independientes.

La [migración 0002](../../backend/socios/migrations/0002_ex_traveler_representation.py) amplía category a 12, permite año nulo y agrega un CHECK. En MySQL el marcador se compara mediante regex sensible a mayúsculas y longitud exacta; la rama de la escala exige IS NOT NULL y rango 1–6. Esto rechaza variantes del marcador y combinaciones inconsistentes aunque se omita save.

Una precondición de lectura consulta el alias recibido y rechaza años históricos fuera de la escala antes del primer DDL. La última operación tiene una guardia de reversión que se ejecuta antes de quitar el CHECK: rechaza años nulos o categorías que excedan la longitud anterior. No recategoriza, completa años ni modifica filas para habilitar la reversión. MySQL conserva su limitación de commits implícitos; las guardias previenen las incompatibilidades ensayadas y no prometen rollback integral del esquema.

Las [pruebas del modelo](../../backend/tests/test_socios_ex_traveler.py) y de [migración/retroceso](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) verifican persistencia, errores, escrituras parciales y conservación de credenciales, expedientes y sus relaciones. El comando protegido aplicó una migración en la demo y su repetición aplicó cero. Evidencia y límites de integración en [tasks.md](tasks.md); TS77.38/39/40 mantienen separados el esquema y la condición institucionales.

## Clasificación local implementada — TS77.32

SocialCategory usa JUNIOR/SENIOR/EX_TRAVELER. El helper category_for_social_year acepta enteros 1–6: devuelve Junior para 1/2 y Senior para 3–6. Rechaza None, booleanos, valores no enteros y años fuera de escala con ValidationError asociado al año, sin deducir exviajero desde un dato inválido. save continúa validando los campos mediante Django antes de clasificar; se conserva su coerción de campo previa.

save deriva la categoría del año para los socios de la escala, incluso ante una etiqueta proporcionada o un cambio de 2↔3 mediante update_fields. El par categoría/año se mantiene completo cuando se selecciona uno; un update_fields ajeno a ambos no recategoriza el dato histórico persistido. Un save completo incluye la clasificación y la deriva del año. EX_TRAVELER/null, rol, habilitación, usuario, identidad y relaciones mantienen las reglas de TS77.31.

La [migración 0003](../../backend/socios/migrations/0003_local_social_categories.py) contiene un AlterField de choices: sqlmigrate informa no-op físico. Conserva columnas, CHECK, FKs y filas; el recálculo histórico permanece en TS77.33. La reversión de 0003 sólo restaura opciones del estado Django y conserva los códigos almacenados, incluidos posibles JUNIOR/SENIOR. No restaura por sí sola los nombres o la semántica del corte anterior.

Las [pruebas locales](../../backend/tests/test_socios.py) y el [ensayo de transición/reversión](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) cubren reglas, escrituras parciales y conservación del historial. Nuevos socios o escrituras explícitas de clasificación usan los códigos canónicos; al cerrar TS77.32 las filas antiguas podían conservar PASSIVE/ACTIVE hasta TS77.33. Padrón, filtros, snapshots institucionales, tokens históricos y SPA conservan sus unidades pendientes; la liberación transversal depende de TS77.37. Evidencia atómica en [tasks.md](tasks.md).

## Migración histórica local — TS77.33

La [migración de datos 0004](../../backend/socios/migrations/0004_recalculate_social_categories.py) usa modelos históricos y el alias del editor. Contiene sólo RunPython; el cuerpo abre transaction.atomic y bloquea las filas con select_for_update antes de validar el conjunto completo. Acepta los códigos exactos PASSIVE/ACTIVE/JUNIOR/SENIOR con año entero 1–6, o EX_TRAVELER con año nulo. Un código desconocido, variante del marcador o combinación inconsistente aborta antes de cualquier UPDATE; no inventa años ni deduce la condición desde una anomalía.

El avance calcula JUNIOR para 1/2 y SENIOR para 3–6, aunque la etiqueta anterior no coincidiera con su año. Se actualiza únicamente category de las filas que cambian; EX_TRAVELER/null se conserva. Repetir el cuerpo sobre datos canónicos no emite UPDATE. Las dos agrupaciones de cambios se escriben dentro de la misma transacción y un fallo posterior a la primera escritura revierte ambas. La regla queda congelada en la migración, sin importar el modelo ni el clasificador vigente.

La reversión semántica utiliza el año conservado para restaurar PASSIVE en 1–3 y ACTIVE en 4–6; mantiene EX_TRAVELER/null porque 0003 ya admite esa representación. No recupera etiquetas arbitrarias anteriores ni deshace ediciones posteriores. Retroceder luego hasta 0001 sigue sujeto a la guardia de compatibilidad de 0002, que rechaza exviajeros antes de alterar columnas. No se incorpora una tabla de respaldo ni se mezclan DDL y DML.

Los [ensayos MySQL](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) comparan filas completas salvo category y definiciones físicas salvo el registro de migraciones: usuarios/credenciales/grupos, roles/vigencia, subcomisión, expediente/M2M, descargo, auditoría, T01 y snapshots con códigos históricos. Incluyen movimientos no cero vinculados a una resolución y expediente institucionales, con identidad distinta de la PK local. También verifican rechazo previo en ambas direcciones y fallo después de un UPDATE efectivamente ejecutado, con historial de migraciones sin avance parcial y reintento correcto. Evidencia de cierre en [tasks.md](tasks.md).

## Contrato DDL demo nullable — TS77.38

El [DDL demo](../../backend/core/sql/scrum77_legacy_schema.sql) declara socio_lista.anoSocial como INT firmado DEFAULT NULL. Es la tercera adaptación respecto del SQL institucional fuente, junto con las dos precisiones DECIMAL(10,2). Se conservan íntegramente las restantes definiciones, nombres, tipos, defaults, PKs, índices, FKs y acciones referenciales: 27 tablas legadas/39 FKs, InnoDB y utf8mb4_unicode_ci. El fuente institucional permanece intacto.

La comparación de [DDL contra fuente y MySQL](../../backend/tests/infrastructure/test_scrum77_legacy_ddl.py) permite sólo esas tres adaptaciones. El oráculo ORM conserva una excepción exacta para la nulabilidad de socio_lista.anoSocial en la demo: el modelo unmanaged sigue con null=False hasta su integración en TS77.34. Los restantes campos y restricciones siguen comparándose sin excepciones nuevas. El cierre vacío se prueba en esquemas MySQL temporales propios, sin filas de negocio. El ensayo de repetición incorpora luego un usuario y grupo propios, y comprueba que sus filas/identidades se conservan sin nuevas creaciones o migraciones.

El bootstrap y su comando mantienen la validación íntegra, sin cambios. Con el nuevo DDL rechazan una tabla socio_lista que conserve anoSocial NOT NULL; la [prueba de rechazo](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) combina ese contrato anterior con una migración managed pendiente, una tabla legada faltante y filas sintéticas previas. Exige cero DDL/DML y conservación de datos, definiciones e historial. La base demo ya preparada conserva NOT NULL en TS77.38: su transición protegida corresponde exclusivamente a TS77.39. No se altera esa base ni se presenta la nueva definición como transición ya aplicada.

NULL físico no acredita condición exviajero. El metadato explícito y su coherencia permanecen en TS77.40; clasificación/consumidores institucionales en TS77.34 y posteriores. Las condiciones del PO, la escala y el criterio de asamblea no cambian. Evidencia atómica en [tasks.md](tasks.md).

## Transición protegida de una demo preparada — TS77.39

El [comando transition_demo_schema](../../backend/core/management/commands/transition_demo_schema.py) reutiliza el preflight de configuración, identidad/base real, sesión/grants y salud HTTP. No admite otra base ni opciones para omitir guardias. Delega en [transition_social_year_schema](../../backend/core/demo_schema.py), entrada interna que exige MySQL/autocommit/FKs activas y usa el mismo GET_LOCK por base que prepare_demo_schema. Los modelos, migraciones, DDL TS77.38 y fuente institucional se conservan.

La versión anterior se deriva del contrato actual cambiando únicamente la nulabilidad de anoSocial en una copia del mapa de columnas; no modifica el contrato nuevo compartido. Reconocer el campo anterior o actual sólo selecciona la comparación: se exige el cierre completo de 27 tablas/39 FKs y auth_user compatible, con todas sus definiciones, orden de columnas, tipos, defaults, claves, opciones y acciones referenciales. Un faltante o divergencia adicional aborta antes de escribir, tanto en la rama anterior como en la que ya está actualizada.

Después de validar se leen las filas completas de socio_lista ordenadas por nroSocio y su contador AUTO_INCREMENT, sólo para comparar en memoria. La rama anterior ejecuta una sola sentencia ALTER de anoSocial a INT NULL DEFAULT NULL; la actual no emite DDL ni DML. Ambas verifican el contrato nuevo íntegro, sesión/FKs y conservación de filas/IDs/contador, sin imprimir registros ni secretos. El comando informa columnas alteradas, cantidad de filas verificadas y cierre/FKs. No ejecuta migraciones, CREATE, seed, limpieza o DML de saldos/expedientes; prepare_demo_schema sigue rechazando el contrato anterior.

La lectura del contador omite las estadísticas cacheadas: guarda information_schema_stats_expiry de la sesión, lo fija en cero para consultar el valor vigente del motor y restaura el valor previo en finally, incluso si falla la consulta. No modifica la variable global ni ejecuta ANALYZE. La prueba calienta la caché antes de insertar una identidad sintética y contrasta el contador con SHOW CREATE TABLE; otra fuerza un error de lectura y exige restauración. Referencia: [estadísticas dinámicas de MySQL](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_information_schema_stats_expiry).

El bloqueo coordina los comandos de preparación/transición. No bloquea escrituras o cambios de esquema externos: su coordinación sigue siendo una precondición operativa. MySQL puede confirmar DDL antes de un error posterior; no se promete rollback ni se modifica la base para aparentarlo. Si el contrato ya quedó actualizado, un reintento acredita el conjunto nuevo y devuelve cero columnas alteradas. Un resultado discrepante posterior rechaza la acreditación de éxito y conserva la base para diagnóstico.

Los [ensayos MySQL](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) conservan cuentas/credenciales, local EX_TRAVELER/null, roles/vigencia, vínculos, T01/snapshots, descargo/auditoría y libro mayor institucional no cero; fijan un contador reservado mayor a MAX(nroSocio)+1. Verifican un solo ALTER, repetición vacía, dos versiones con divergencias rechazadas, cierre incompleto, guardias/bloqueo y fallo después de DDL real con reintento sin escrituras. Metadato institucional y consumidores permanecen en TS77.40 y posteriores. Evidencia atómica en [tasks.md](tasks.md).

Después del fallo posterior al ALTER, una conexión distinta debe adquirir el mismo GET_LOCK para demostrar su liberación. Reintentar desde la conexión original no acredita este punto porque MySQL permite adquisiciones repetidas en la misma sesión. Referencia: [bloqueos cooperativos MySQL](https://dev.mysql.com/doc/refman/8.0/en/locking-functions.html).

## Metadato e integración backend — TS77.40/34/41/42

El 12/10/2026 el usuario confirmó TS77.40 y autorizó expresamente tres subagentes para implementar TS77.34, TS77.41 y TS77.42 en paralelo. Esta autorización aplica a esas cuatro unidades: la integración respeta metadato → lector institucional → T01; JWT trabaja sobre el modelo local ya adecuado. Las pruebas MySQL se ejecutan por turnos para no compartir simultáneamente la base de pytest. La autorización posterior para TS77.43/35/36/37/07 se registra en los apartados siguientes.

### Asociación institucional de TS77.40

[InstitutionalMembershipCondition](../../backend/socios/institutional_conditions.py), exportado desde socios.models, usa el nroSocio real como PK IntegerField institutional_number, condition=EX_TRAVELER, source_reference y social_cycle obligatorios. Es un modelo managed separado de socio_lista, sin FK física hacia el legado. La [migración nueva 0005](../../backend/socios/migrations/0005_institutional_membership_condition.py) crea sólo su tabla/PK/CHECK; no ejecuta consultas al padrón. El bootstrap puede aplicar todas las migraciones managed antes de crear las 27 tablas legadas, demostrado con un esquema UUID propio.

El escritor register_ex_traveler requiere una instancia institucional persistida de la conexión seleccionada; verifica su número, existencia y año nulo. Nunca deduce la condición desde NULL, idTipoSocio, cargo, baja o estado. La fuente y el corte provienen del llamador que acredita la evidencia. La propiedad del fixture, namespace, pertenencia a G57 y manifiesto se validarán en TS77.09/11; este servicio no declara implementadas esas guardias del seed.

Dentro de atomic, escritor y save bloquean primero la fila institucional y después el marcador. La referencia sigue validándose en la misma conexión. Un registro idéntico repite sin DML; una fuente/corte diferente o una identidad duplicada se rechaza sin sobrescribir. El modelo bloquea modificaciones y las operaciones masivas que omiten esa asociación. La PK y un CHECK de identidad positiva, código exacto y textos no vacíos refuerzan la integridad física. No se promete una FK virtual frente a modificaciones externas: corresponde conciliación posterior del padrón/metadatos.

La aplicación protegida en la demo agrega la tabla vacía y el registro de migración. post_migrate genera el content type y cuatro permisos de catálogo estándar del modelo, sin asignarlos a usuarios/grupos. Se verifican exactamente esas altas y sus contadores, junto con conservación de todas las filas previas y relaciones. La preparación repetida no aplica migraciones ni genera altas adicionales.

### Proyección y filtros de TS77.34

[querysets.py](../../backend/padron/querysets.py) anota Exists por institutional_number=OuterRef(nroSocio) y condición EX_TRAVELER; se reutiliza en padrón y ranking antes de count y LIMIT. El marcador confirmado prevalece y excluye a su titular de Junior/Senior/UNKNOWN. Sin marcador, años 1–2 producen Junior, 3–6 Senior y anomalías UNKNOWN. EX/UNKNOWN proyectan social_year=null, con etiquetas propias. El DTO y los serializers aceptan ese año nulo; el unmanaged anoSocial se alinea con el DDL ya aplicado, sin migración/ALTER institucional. Se retira la excepción ORM temporal de TS77.38.

Los filtros admiten únicamente aliases de entrada PASSIVE/PASIVO→JUNIOR y ACTIVE/ACTIVO→SENIOR; mantienen HTTP 400 para valores desconocidos. Omitir is_active no aplica filtro de vigencia; los valores True/False explícitos siguen funcionando. Las pruebas SQL verifican conteos, páginas y resultados coincidentes, con cuatro consultas del adaptador y una del ranking para listas de distintos tamaños, sin consulta por socio.

### Materialización T01 de TS77.41

El [servicio T01](../../backend/expedientes/services/solicitud_t01_service.py) valida el ID seleccionado contra el DTO, el par EX_TRAVELER/null y la escala por año. Resuelve la persona mediante user_id institucional real único o legajo real corroborado, sin equiparar PK local/nroSocio. Un legajo institucional debe identificar un único nroSocio mediante DISTINCT: varias carreras de la misma persona no producen una falsa colisión. Referencias contradictorias, cuentas ajenas y clasificación no confirmada abortan la emisión.

La emisión transaccional reutiliza DTOs validados y sincroniza exclusivamente categoría/año de perfiles existentes, conservando IDs, credenciales, rol, vigencia, otros campos y relaciones. Los perfiles nuevos usan la identidad acreditada y cuentas con contraseña inutilizable cuando se deben crear. Los snapshots nuevos se construyen con clasificación canónica; los históricos permanecen intactos. Un fallo tardío de identidad o apertura revierte materialización, sincronizaciones y emisión; no se absorbe el error de workflow. No cambia estados, firma, facultades ni puntos.

### Tokens y perfil de TS77.42

[CurrentSocioRefreshToken](../../backend/accounts/serializers.py) verifica primero con la implementación JWT instalada, valida la identidad configurada y relee category del socio vigente al emitir access. El serializer hereda validate y conserva rotación, blacklist, vidas útiles y USER_ID_FIELD/CLAIM. Se prueba SimpleJWT 5.5.1 instalado, incluido un proceso aislado con token_blacklist habilitado antes de django.setup; no se modifica settings ni se agregan dependencias.

Login/me conservan sus claves y leen el perfil vigente; refresh sólo actualiza category y conserva role/legajo/identidad. Los tokens anteriores no se reescriben, y la autorización continúa leyendo rol/vigencia en servidor. La hidratación SPA y la identidad explícita del legajo se implementan en TS77.35/43 según los apartados siguientes.

## Contratos y perfil SPA — TS77.35

[AuthService](../../frontend/src/app/services/auth.service.ts) conserva la sesión y el rol válidos del perfil almacenado, pero vacía su etiqueta/categoría hasta recibir auth/me confirmado. El perfil pendiente es nullable; la respuesta confirmada sólo admite códigos canónicos. La petición se difiere a una microtarea para evitar el ciclo con AuthInterceptor, mantiene el flujo 401 y se cancela/descarta por generación/token al cerrar sesión o ingresar otra cuenta. Un error HTTP/red mantiene la sesión actual sin inventar categoría. No se interpreta el claim category de un JWT histórico.

Los DTOs de legajo admiten año/legajo nulos y las cuatro categorías; el servicio transporta identity_source sin fallback. Padrón conserva is_active como vigencia independiente y DTOs de snapshots T01 antiguos que omiten clasificación. El ranking usa códigos canónicos para filtrar, etiquetas institucionales para mostrar y fuente institutional para abrir una ficha. No se modifica el contrato de puntos ni se agrega año social a una respuesta de ranking que no lo expone.

## Etiquetas y demo existente — TS77.36

Ranking/modal muestran Junior, Senior, Exviajero y Sin clasificación. El modal limpia resultados al recargar/fallar, reintenta con la misma fuente y muestra Sin legajo cuando falta el legajo real. Sólo muestra años 1–6; null/0/7 no se presentan como escala válida. El badge usa --color-surface-elevated, --color-text-primary y --color-border-main definidos en DESIGN.md; los controles estáticos de contraste no acreditan toda la accesibilidad de la SPA.

El mock conserva sus 33 identidades y saldos, con clasificación basada en un corte sintético explícito. seed_demo ya deriva la categoría por año/situación; sus cambios son ayuda/docstrings/type hints. Ocho pruebas verifican clasificación, cuentas/credenciales/roles, idempotencia, DEBUG y rollback. Durante el cierre TS77.36 no se ejecutó seed_demo ni se crearon sus cinco cuentas en la demo; su integración posterior corresponde a TS77.10.

## Catálogo y validación transversal — TS77.07/37

[demo_catalog](../../backend/socios/demo_catalog.py) es un módulo puro de dataclasses congeladas y tuplas, sin SQL/Django/reloj/azar. Define versión scrum77-g57-g60-v1, corte PO-SCRUM77-CORTE-01, 16 identidades/cuatro por grupo y seis cuentas nuevas, junto con las cinco referencias existentes de seed_demo. Cantidades, rangos candidatos, asignación de subcomisiones y escenas futuras se detallan en el [catálogo](../../docs/gestion-proyecto/CATALOGO_DATOS_DEMO_SCRUM-77.md). No reserva PKs managed ni afirma ausencia de colisiones contra una base real.

La validación exige referencias internas, namespace/tipo/rango correcto, fuente/corte de los exviajeros y roles separados de categoría/vigencia. Tres causas/cuatro T01 y ocho asientos con siete respaldos forman un conjunto futuro de saldo esperado +1; no se carga ni se modifica la puntuación de nadie. Los solicitantes CD/FISCALIZADORA usan roles que el permiso T01 existente ya admite.

TS77.37 audita la integración y precede a aceptar TS77.07/DP77-02. Los 932 casos backend y 202 frontend, build y preservación exacta de demo respaldan ese cierre; lint frontend registra su builder TSLint ausente. Al cerrar esas unidades, guardias/propiedad/carga/conciliación seguían en TS77.08–18 y persistencia/recorridos/cierre en TS77.19–27; su implementación posterior se describe abajo. [Evidencia y límites históricos](tasks.md#verificación-de-ts774335363707).

## Identidad del legajo — TS77.43

La autorización del 12/10/2026 comprende TS77.43 y agentes distintos para TS77.35/36/37/07. Se preparan artefactos en paralelo; CA77-08/DEP77-02 y aceptación del catálogo sólo se cierran después de integrar y verificar las dependencias. TDD y ejecución real de pruebas se coordinan desde root, con una base MySQL y un runner Karma por vez. Las Notas del PO, fuentes, migraciones aplicadas y seguimiento macro permanecen protegidos.

El parámetro opcional identity_source admite exactamente local o institutional, una sola vez; valor inválido/vacío/repetido devuelve 400. Con fuente explícita la ruta identifica la PK local o nroSocio institucional exclusivamente: no se reutiliza el número como legajo alternativo ni se consulta otro namespace si falta el ID. El ranking enviará institutional. Las llamadas anteriores sin parámetro pueden resolver por ID o legajo, conservando casos inequívocos: si los candidatos alcanzan personas distintas dentro de un namespace o entre ambos, se devuelve el mismo 404 genérico que ante ausencia. Un vínculo confirmado que demuestra la misma persona permite conservar la llamada antigua, sin equiparar PKs.

Los rangos respetan cada contrato físico: PK local BIGINT hasta 9223372036854775807, nroSocio/legajo académico institucional INT firmado hasta 2147483647. Dos ensayos en schemas UUID propios cubren la PK local 2147483648 con fuente explícita y llamada antigua; no elevan el AUTO_INCREMENT de la base padre de pytest. Un hallazgo del auditor detectó el límite INT aplicado inicialmente a ambos namespaces y se corrigió con ese TDD, sin alterar esquemas ni migraciones.

La propiedad institucional exige user_id real y único o legajo académico real de asociación institucional inequívoca mediante DISTINCT nroSocio. Varias carreras de la misma persona no constituyen colisión. Un user_id ajeno prevalece sobre un legajo coincidente; un vínculo ambiguo o ausencia de evidencia no otorga acceso de propietario. El correo coincidente no determina dueño ni rol. TD/CD/ADMIN habilitados conservan acceso; rol, vigencia y permisos se consultan en servidor y no dependen de categoría.

El adaptador devuelve legajo=null cuando la ficha no tiene uno real, retirando str(nroSocio) artificial; mantiene claves/rutas y año nulo institucional. Las interfaces Angular admiten ese null y muestran Sin legajo. GET no crea/sincroniza cuentas o socios ni cambia credenciales, evidencias, saldos o estados. Ante fallo de consulta institucional, una llamada sin fuente explícita no elige un candidato local que no pudo desambiguar; se falla con 404 genérico y sin detalles sensibles. La fuente local explícita no consulta el padrón.

## Carga protegida integrada — TS77.08–18

La entrada [seed_expedientes](../../backend/core/management/commands/seed_expedientes.py) realiza el preflight de configuración, MySQL/grants y salud HTTP. Delega en cuatro módulos separados: [demo_seed](../../backend/core/demo_seed.py) orquesta guardias/manifiesto/transacción; [demo_fixtures](../../backend/core/demo_fixtures.py) resuelve propiedad y bloqueo; [demo_members](../../backend/core/demo_members.py) carga cuentas/padrón; [demo_scenes](../../backend/core/demo_scenes.py) carga causas/T01/antecedentes. No importa utilidades de tests ni agrega dependencias.

### Guardias y propiedad física

Se exige el perfil exacto scrum77-g57-g60-v1, DEBUG y padrón database; conexión MySQL 8.0 con base/usuario/host/puerto demo, identidad real, grants, modo estricto, FKs activas y tablas InnoDB. La validación del esquema comprueba el contrato de las 27 tablas legadas, historial managed consistente, ausencia de migraciones pendientes, presencia de tablas/M2M requeridas y las dos UNIQUE físicas del registro. El seed no aplica DDL ni grants y rechaza una invocación dentro de otra transacción.

[DemoFixtureOwnership](../../backend/core/models.py) se incorpora mediante [core.0001_initial](../../backend/core/migrations/0001_initial.py), preparada por el comando de esquema antes del DML. Sus campos son profile, fixture_key, namespace, object_key y owned, con collation utf8mb4_bin en los textos. UNIQUE(profile, fixture_key) impide reasignar una clave; UNIQUE(namespace, object_key) impide doble propiedad del mismo destino, incluso entre perfiles. No contiene entity_type, fingerprint o timestamp ni declara una FK genérica hacia tablas heterogéneas.

La PK se normaliza mediante el campo real de su namespace: variantes numéricas/UUID no producen identidades alternativas. Modelos managed, through automáticos y las 27 tablas legadas poseen resolutores explícitos de existencia. ensure_model/ensure_legacy reutilizan únicamente referencias registradas; una identidad natural ajena, duplicada o que contradiga la referencia aborta. Las referencias compartidas de catálogo y seed_demo se aceptan de forma explícita, sin reparar sus datos. export verifica nuevamente todos los destinos registrados, incluidos componentes de auditoría/M2M; un destino perdido no se recrea.

### Bloqueo, generación y transacción

demo_fixture_lock adquiere GET_LOCK para scrum77-schema:<base>, antes de abrir atomic, y comparte nombre con prepare_demo_schema/transition_demo_schema. Cada escritura del registro verifica configuración/base, atomic activo y que IS_USED_LOCK corresponda a CONNECTION_ID. El contexto genera un token privado por adquisición, asociado a la conexión. El resultado del chequeo de esquema sólo se cachea dentro de esa generación: liberar/reobtener obliga a validar nuevamente; un lock manual sin token no habilita reutilizar el cache. Un ensayo MySQL altera una unicidad física entre adquisiciones y exige rechazo posterior antes de escribir.

run_demo_seed valida otra vez el esquema bajo el lock y abre una única transacción para cuentas, padrón, condiciones, causas, antecedentes, propiedad y contador formal. Liberación del lock ocurre en finally. Las colisiones y fallos tardíos revierten el DML completo; no se promete reutilización de PKs autoincrementales consumidas por MySQL ni rollback de una preparación DDL. La repetición conserva datos propios editados, sin update_or_create, REPLACE, limpieza ni UPDATE/DELETE manuales de puntos/expedientes.

### Loaders y documentos

demo_members comprueba usernames, legajos, correos, documentos y vínculos institucionales antes de cargar sus referencias. Crea seis cuentas/perfiles del catálogo y conserva las cinco cuentas seed_demo mediante su comando vigente. Resuelve subcomisiones de los dos padrones por sus referencias, grupos/historial/satélites del esquema real y user_id institucional por auth_user.id. Conserva credenciales, roles, habilitación y ediciones válidas; rechaza contradicciones de identidad/corte. G57 recibe marcador explícito EX_TRAVELER/null con fuente/ciclo, sin inferirlo desde un NULL aislado.

demo_scenes usa ExpedienteWorkflowService.open_expediente para tres causas en Creado y SolicitudT01Serializer/EmitirT01Serializer para cuatro T01 de dos solicitantes. Dos emitidas vinculan expedientes y abren el plazo con iniciar_plazo_descargo y reloj actual; cinco expedientes managed pueblan sólo Creado/Justificaciones, con urgencia heredada. Registra cada causa, solicitud, M2M y auditoría; el contador anual es una referencia compartida. No despacha SMTP ni avanza por las restantes etapas con fechas artificiales.

El antecedente sintético usa INSERT parametrizado protegido para siete respaldos/resoluciones y expedientes legados, y ocho asientos individuales. La tabla resolutiva conserva número/fecha y texto VISTO/CONSIDERANDO/SE RESUELVE en consideracion, identificando su carácter ficticio y destinatarios/puntos. No acredita firmas ni facultades. Cada asiento mantiene resolución → expediente legacy → socio/puntos exactos; una inconsistencia aborta sin sobrescribir. El mérito compartido aplica +2/+1 individualmente; el agregado inicial esperado es +1. No se crea PuntajeGeneral ni se computan pedidos pendientes como saldo ni se habilita _allow_write productivo.

### Manifiesto y conciliación

La salida JSON contiene status, profile, social_cycle, fixtures, mappings e identities; nunca credenciales, hashes de contraseña o JWT. fixtures conserva clave/tabla/PK canónica/propiedad; mappings agrupa IDs resueltos por tipo y admite null en la subcomisión local del centinela 99. identities distingue nroSocio, nroLegajo académico, auth_user.id, socio local/legajo, grupo y ambos namespaces de subcomisión. Las fichas sin cuenta conservan user_id/local_socio_id/local_legajo nulos; no se materializan por coincidencia numérica.

T01 conserva UUID y número T01 propio; su expediente posee número EXP servidor distinto. Los antecedentes conservan PKs legadas reales, sin reutilizar PKs managed. Los oráculos de [integración](../../backend/tests/infrastructure/test_scrum77_seed_integration.py) y [HTTP/BD](../../backend/tests/infrastructure/test_scrum77_demo_http.py) contrastan referencias, destinatarios y sumas; el smoke por identifier mantiene el login de prueba existente y no acredita contraseña validada.

## Verificación y entrega integradas — TS77.19–27

El protocolo de persistencia conserva el volumen demo fijo y compara contenedor nuevo, referencias, filas, vínculos, auditoría y saldos, sin ejecutar seed entre mediciones. El [runbook](../../docs/gestion-proyecto/GUIA_CARGA_DEMO_SCRUM-77.md) separa preflight/preparación/carga de ese ensayo y documenta recuperación sin reset. La ejecución real aplicó una migración core.0001 y dejó 49 tablas/34 registros de migración; sólo agregó el registro y sus metadatos Django estándar, conservando las 27 tablas legadas vacías/contador 1 antes del seed.

La carga inicial registró 162 referencias, 16 fichas institucionales, 11 cuentas/perfiles locales, cuatro marcadores EX_TRAVELER, cinco causas, cuatro T01, siete expedientes/resoluciones históricos y ocho asientos, con saldo agregado +1. La segunda salida JSON fue idéntica, y se conservaron exactamente los 49 hashes de esquema/filas/conteos y el contador institucional 770017. El smoke HTTP realizó 78 controles antes y después de recrear MySQL. Los prefijos de ID cambiaron 5b793d5 → e5e7116 sobre sgd_aveit_scrum77_demo_mysql_data, con las 49 comparaciones físicas/de datos iguales y sin ejecutar seed ni preparación entre mediciones. El registro detallado de cierre corresponde a tasks.md.

Los recorridos de login/permisos, ranking/legajo, T01/Mis Solicitudes y tablero se cotejan contra HTTP y MySQL; mocks o capturas por sí solos no acreditan cumplimiento. La corrección frontend TS77.23 conserva el filtro de socio confirmado por servidor: evita recortar una causa cuyo destinatario buscado es secundario, aunque el DTO compacto muestre al principal. TS77.24 mejora el modal de detalle existente con role=dialog, aria-modal/título, Escape, FocusTrap CDK, foco inicial en Cerrar y restauración. No crea un componente Socios ni amplía el DTO.

El frontend host usa proxy.scrum77-local.conf.json desde 4202 hacia 8002; el perfil Docker conserva el proxy backend:8000. La regresión final acreditó 1008 backend/222 frontend verdes, cobertura 93,91% (2331 sentencias, 142 sin cubrir, 22 módulos) y build 6fae4265931dc3f8 en 7854 ms; Ruff y controles Django/migraciones están correctos. Lint heredado ausente se clasifica separado. Se mantienen DEP77-01, facultades/firma/votación y motor 3:1 fuera de alcance. El navegador real aprobó desktop/360/414, ambos temas y teclado; CA77-06 verificado. La revisión documental independiente final aprobó CA77-07 y el cierre de la US, sin repetir confirmación por unidad.

## Alternativas descartadas

- Cambiar únicamente -p sobre el Compose habitual: conserva nombres globales de contenedores y volumen MySQL.
- Override combinado sin sustituir íntegramente ports/volumes: puede mantener publicaciones y mounts habituales.
- Reutilizar el backend activo de calendario: monta otro checkout y no acredita esta rama.
- Cargar los seis estados managed pasando fechas futuras: el reloj de apertura y las fechas automáticas del historial no siguen ese parámetro.
- SQLite o capturas del mock para cerrar la US: no prueban conectividad, FK física ni persistencia MySQL.

La precedencia del nombre de proyecto y el modelo resuelto se respaldan en la documentación oficial de [nombres de proyecto](https://docs.docker.com/compose/how-tos/project-name/) y [docker compose config](https://docs.docker.com/reference/cli/docker/compose/config/).

### Lectura y presentación verificadas en los recorridos

Mis Solicitudes conserva snapshots y resuelve IDs de borradores desde el puerto de padrón, sin PK local, materialización o legajo inventado. Las fallas de base devuelven 503 genérico; roles y aislamiento se mantienen. El DTO de involucrados admite legajo null.

Las correcciones de presentación usan tokens en superficies/textos/badges y flex/scroll en toolbar, ficha y detalle T01. MatDialog mantiene campos y lector; agrega título/nombre de cierre/foco y tabla desplazable enfocables. Los oráculos DOM usan temas reales y composición RGBA; las geometrías de overlay se complementan con navegador real a 360/414/escritorio. No se declara accesibilidad global de toda la SPA. [Evidencia](../../docs/gestion-proyecto/VERIFICACION_UI_SCRUM-77.md).

## Corrección de saldo — TS77.48–51

GET `/api/v1/socios/me/points-balance/` autenticado y de sólo lectura devuelve `{ points_balance: number }`. Reutiliza la resolución de propiedad institucional desde el usuario y agrega los asientos de PuntajeAplicado para ese socio, con el mismo criterio del ranking. Conserva los permisos vigentes. Identidad ausente/ambigua devuelve error genérico y una falla de repositorio devuelve error de servicio; cero sólo corresponde a una identidad confirmada sin saldo. No requiere tablas, migraciones ni cambios del caché PuntajeGeneral.

MisExpedientesComponent consulta ese contrato mediante SocioApiService cuando recibe el perfil de sesión. Cancela la lectura previa ante cambio de sesión o destrucción y limpia el valor antes de consultar; muestra carga/error en lugar de cero inventado. El número y los estilos de saldo confirmados conservan el diseño existente. Los puntos de las causas pendientes mantienen su significado y no se suman al widget.

Los legajos institucionales y los locales con vínculo inequívoco usan un lector común del libro mayor. Un perfil local sin fuente institucional devuelve `points_balance: null` conservando sus datos; en el modo de padrón simulado el saldo institucional no se presume disponible. Una falla de base devuelve 503. El modal presenta la lectura actual del legajo y no antepone el snapshot que recibió desde el ranking. SocioApiService valida el número finito del contrato de saldo propio; un payload inválido sigue el estado de error.

TDD cubre fuente de saldo, individualización, identidades, permisos, errores, cambios de sesión y snapshots de ficha. El oráculo HTTP MySQL recorre todas las cuentas habilitadas del catálogo y sus referencias: compara el nuevo GET y ambos legajos con ranking y SQL donde existe identidad confirmada y acredita errores/valores desconocidos donde no existe. El navegador reproduce saldo positivo y cero. Se preservan todas las filas de la demo. La auditoría revisa implementación y evidencia antes de publicar la corrección y comprobar el CI del último commit.

Se descartan sumar puntos solicitados, copiar el caché divergente o buscar al socio por nombre/igualdad de números de namespaces distintos. La conexión completa del listado y los descargos continúa fuera de esta ampliación.

## Escenas históricas en todos los estados — TS77.52–56

Un catálogo `advanced_causes` separado agrega diez fixtures: `revision_resolucion` ×3, `espera_resolucion` ×1, `pendiente_correos` ×2 y `emitido` ×4. Conserva las escenas, T01, referencias y asientos previos. Fechas aware pasadas, plazo calculado con DbHolidayProvider e historial canónico validado hasta el estado final; todo timestamp debe ser anterior o igual al momento de importación.

Los servicios actuales no permiten importar coherentemente apertura e historial históricos y no hay un modelo managed de firma/resolución. Un importador exclusivo de demo valida las nuevas instancias con `full_clean` y sólo inserta mediante `save_base(raw=True, force_insert=True)` para conservar fechas explícitas. Usa ExpedienteNumberSequence y el registro de propiedad/auditoría/M2M existentes, bajo el lock y la transacción del seed. No cambia el reloj global ni avanza causas existentes. Los registros y textos expresan su carácter histórico ficticio; no acreditan facultades o firma productiva.

Los cuatro emitidos incorporan cuatro resoluciones y expedientes históricos y cuatro asientos individuales mediante el loader legado protegido, en un namespace propio. Se comprueba destinatario, importe y número formal de la causa managed mediante textos y referencias del manifiesto; ambos esquemas carecen de FK directa. Los Juniors reciben +2/-1/-2/+1 y el agregado nuevo es cero, conservando los ocho asientos anteriores. Las causas pendientes sólo tienen puntaje solicitado.

TDD cubre referencias/distribución, calendario/cronología/historial, número servidor, vínculo de puntos y upgrade aditivo. El ensayo de catálogo anterior excluye `advanced_causes` para conservar el escenario original; las pruebas de ampliación comprueban el upgrade real sobre una demo con altas/ediciones de UAT. Repetición estable, colisiones, pérdida de referencias y fallo tardío no se resuelven con limpieza ni sobrescritura. HTTP y navegador contrastan los seis estados y los nuevos saldos contra SQL, con auditoría independiente.

TS77.56 preserva las seis claves del contrato en el adaptador SPA. La verificación real detectó una conversión heredada que agrupaba `espera_resolucion` en revisión y `pendiente_correos` en firma; los contadores del navegador deben coincidir con la API, también en tabla y detalle. La corrección actúa sobre la representación y no modifica estados persistidos ni el flujo productivo.

## Resoluciones aplicadas visibles — TS77.57–59

GET `/api/v1/socios/me/points-history/` propio y sin escritura devuelve `{ points_balance, entries }`. Cada entrada contiene `movement_id`, `applied_points`, `historical_case` (id/número/fecha de registro/estado emitido), `resolution` (id/texto/reglamentos) y `managed_case` (id/número/estado emitido) o null. No se extraen números o fechas ficticios del texto: la fecha histórica de registro conserva ese significado y el documento formal se presenta tal como está almacenado.

GET `/api/v1/socios/<pk>/points-history/?identity_source=...` usa el mismo contrato y resolución/RBAC de legajo para consultar cualquier ficha autorizada. SOCIO conserva acceso propio; TD/CD/Admin conservan el acceso a otros legajos vigente, sin ampliar permisos. El modal de ficha usa saldo e historial de esa lectura actual y permite abrir el mismo detalle resolutivo; las veinte identidades y todos los asientos quedan auditables aun cuando no existe login del destinatario.

La identidad/permisos se reutilizan del saldo propio. Un SELECT enlaza libro mayor, expediente y resolución; verifica respaldo completo y emisión y calcula el total decimal del mismo listado. Los enlaces managed se acreditan exclusivamente mediante referencias de propiedad coincidentes y número formal/texto/participante; los ocho antecedentes originales conservan managed_case null. Una transacción de lectura consistente evita mezclar snapshots. Errores de respaldo o base devuelven 503 genérico, sin omitir entradas.

El widget y la nueva sección de resoluciones aplicadas usan el mismo DTO, con cancelación por sesión y validación de contrato. La tabla muestra importes individuales y expediente histórico/operativo acreditado; el detalle presenta texto y reglamentos con modal accesible. Cero sin movimientos se distingue del saldo cero compensado con +3/-3, y de desconocido/error. No se modifica ni duplica el listado operativo, ni se añade un motor de firma/emisión.

TDD, HTTP/SQL y navegador verifican los doce asientos del conjunto por destinatario: +2 original, mérito compartido, compensación cero y cuatro actos Junior nuevos. Se conservan todas las filas y los cuatro emitidos operativos. Regresión de identidad BIGINT declara fuente mock explícita cuando acredita un perfil exclusivamente local, con saldo desconocido en el nuevo contrato.
