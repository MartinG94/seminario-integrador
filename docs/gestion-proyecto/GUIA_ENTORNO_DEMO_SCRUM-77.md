# Configuración y preflight MySQL de demostración — SCRUM-77

**Alcance actual:** infraestructura/guardias/propiedad/carga verificadas. Demo con 49 tablas/34 migraciones, 16 fichas y 162 referencias; repetición/persistencia sin reseed verificadas. 1008 backend/222 frontend verdes, cobertura 93,91% en 22 módulos y build correcto; 78 controles HTTP reforzados y navegador escritorio/360/414 en ambos temas aprobados. Auditoría integral final aprobada sin hallazgos abiertos; lint heredado ausente clasificado. [Carga/recuperación](GUIA_CARGA_DEMO_SCRUM-77.md) y [resultados](VERIFICACION_CARGA_SCRUM-77.json). Los cierres anteriores son históricos.

## Resolver la configuración

**Arranque automático de la PR #54:** `docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml --profile frontend up -d --build`. `demo-setup` prepara y carga el catálogo después del health del backend; la SPA espera a su finalización exitosa. Comparte la red del backend para conservar la comprobación HTTP local del preflight, sin exponer puertos adicionales. El procedimiento manual de este documento sigue disponible para diagnosticar un rechazo. Ver [guía de carga](GUIA_CARGA_DEMO_SCRUM-77.md#inicio-recomendado-desde-una-copia-limpia).

Usar [docker-compose.scrum77-demo.yml](../../docker-compose.scrum77-demo.yml) como archivo autónomo. El nombre de proyecto se fija con `-p`. Los binds relativos se resuelven desde el directorio del archivo, aunque la terminal esté en otro directorio.

Desde la raíz de este checkout:

```powershell
docker compose -p sgd-aveit-scrum77-demo --profile frontend -f docker-compose.scrum77-demo.yml config --quiet
```

Desde otro directorio, pasar la ruta absoluta del archivo:

```powershell
docker compose -p sgd-aveit-scrum77-demo --profile frontend -f D:/Proyectos/seminario-integrador/docker-compose.scrum77-demo.yml config --quiet
```

`config --quiet` valida sin imprimir credenciales. El perfil `frontend` incluye la SPA; omitirlo deja definidos MySQL y backend. No combinar el archivo demo con el Compose habitual.

## Recursos definidos

| Recurso | Configuración |
|---|---|
| Proyecto | `sgd-aveit-scrum77-demo` |
| MySQL | `sgd_aveit_scrum77_demo_mysql`, `127.0.0.1:3307` |
| Base / usuario | `aveit_tribunal_scrum77_demo` / `aveit_dev`, en el servidor demo |
| Backend | `sgd_aveit_scrum77_demo_backend`, `127.0.0.1:8002` |
| Frontend opcional | `sgd_aveit_scrum77_demo_frontend`, `127.0.0.1:4202` |
| Volumen MySQL | `sgd_aveit_scrum77_demo_mysql_data` |
| Dependencias frontend | `sgd_aveit_scrum77_demo_frontend_node_modules` |
| Red | `sgd-aveit-scrum77-demo_default` |

Backend y frontend montan los directorios del checkout que contiene el archivo. Se reutilizan sus Dockerfiles y el proxy hacia `http://backend:8000`. El backend usa `db:3306`, `USE_SQLITE=False`, `PADRON_ADAPTER=database` y los orígenes CORS de la SPA en puerto 4202.

Las variables genéricas `MYSQL_*`, `USE_SQLITE`, `PADRON_ADAPTER` y `CORS_ALLOWED_ORIGINS` del host no redirigen esta configuración. Las únicas credenciales interpoladas son `SCRUM77_MYSQL_PASSWORD`, `SCRUM77_MYSQL_ROOT_PASSWORD` y `SCRUM77_DJANGO_SECRET_KEY`, con valores por defecto para desarrollo local.

## Pruebas de aislamiento

En un host con Docker CLI y las dependencias Python del proyecto, desde `backend/`:

```powershell
python -m pytest -q tests/infrastructure/test_scrum77_compose.py
```

Las pruebas resuelven los archivos original/demo y vuelven a resolver la demo con variables genéricas conflictivas. Comprueban recursos separados, volumen MySQL propio, puertos loopback, binds del checkout, conexión interna y destino MySQL/padrón explícitos.

Para ejecutar en la imagen backend sin Docker CLI, el orquestador puede proporcionar `SCRUM77_COMPOSE_CONFIG_B64`: JSON saneado, codificado en Base64, generado inmediatamente con Docker CLI. Incluye `base`, `demo`, `demo_conflicting_env`, `repository_root` y `source_sha256` de ambos archivos. Se eliminan campos de entorno cuyo nombre contiene password/secret/token/key; las pruebas cotejan hashes contra el checkout montado y rechazan un snapshot desactualizado. `SCRUM77_REPOSITORY_ROOT` identifica ese mount.

Un contenedor con sólo `/app` y sin snapshot omite esta prueba por falta del checkout completo. Ese resultado no acredita CA77-00; la validación de esta tarea se ejecuta con checkout completo y snapshot recién generado, sin omisiones.

## Arrancar MySQL y backend demo

Desde la raíz del checkout:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml up -d --build db backend
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml ps
```

Estos servicios usan la red y el volumen demo. Para identificar el checkout montado, cotejar los mounts de `sgd_aveit_scrum77_demo_backend` con este directorio; un backend de otro checkout no acredita esta rama. El frontend sigue siendo opcional y no es necesario para este diagnóstico.

## Ejecutar el preflight autenticado

Con ambos servicios saludables:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py check_demo_mysql
```

El [comando check_demo_mysql](../../backend/core/management/commands/check_demo_mysql.py) sólo ejecuta consultas SELECT. Rechaza antes de conectar un perfil distinto: DEBUG desactivado, SQLite, padrón mock, base, usuario, host, puerto o base de pytest ajenos. Comprueba después `SELECT 1`, base y usuario autenticados, MySQL 8.0, modo estricto, charset/collation utf8mb4 y `foreign_key_checks=1`.

Consulta los grants directos del usuario autenticado en `information_schema.SCHEMA_PRIVILEGES`, con el grantee parametrizado. Exige SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX y REFERENCES para la base demo y `test_aveit_tribunal_scrum77_demo`. Los permisos se verifican; el comando no los otorga ni los modifica.

El diagnóstico corresponde al perfil de grants directos de esta demo: requiere `partial_revokes=0` y ningún rol activo. Resuelve `%`, `_` y escapes de los patrones de base, y rechaza patrones superpuestos en lugar de sumar permisos y dar un resultado ambiguo. No acredita configuraciones que dependan de privilegios globales, roles o grants por tabla.

Finalmente consulta `http://127.0.0.1:8000/api/health/` dentro del mismo contenedor, sin proxies ni redirecciones. Exige HTTP 200, URL efectiva exacta y `{"status":"ok","db":"connected"}`. Un servicio sano en otro checkout o una redirección a otro backend no satisface la verificación.

En caso de éxito imprime un JSON con identidad y condiciones verificadas; no incluye contraseñas ni claves. Si falla, termina con código distinto de cero y un mensaje de diagnóstico sin los detalles sensibles de la excepción. El resultado no acredita todavía las tablas del dominio ni la carga de socios.

El endpoint también se puede consultar desde el host en [salud de la demo](http://127.0.0.1:8002/api/health/).

## Pruebas del preflight

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend pytest -q tests/infrastructure/test_mysql_demo_preflight.py
```

Las pruebas cubren identidades/configuración inválidas, sesiones incompatibles, errores sin secretos, grants insuficientes o ambiguos y HTTP inválido. Un servidor HTTP loopback real comprueba respuesta directa, rechazo de redirecciones e independencia de proxies del entorno. Estas pruebas automatizadas se complementan con la ejecución autenticada anterior contra MySQL real.

## Transicionar una demo preparada — TS77.39

Este procedimiento corresponde a una demo con el cierre legado completo, preparada antes de TS77.38 con socio_lista.anoSocial INT NOT NULL. Una base vacía se prepara directamente mediante el procedimiento siguiente. Coordinar previamente las escrituras y cambios de esquema externos: el bloqueo cooperativo compartido serializa los comandos de preparación/transición, sin bloquear otros clientes.

Con MySQL y backend demo saludables, ejecutar desde este checkout:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py transition_demo_schema
```

El [comando transition_demo_schema](../../backend/core/management/commands/transition_demo_schema.py) acredita configuración, identidad/base/grants y salud HTTP con el preflight existente. Exige autocommit, FKs activas y el mismo GET_LOCK por base que la preparación. Compara el contrato anterior o actual completo de las 27 tablas legadas/39 FKs, con auth_user compatible; un faltante o divergencia adicional aborta antes de escribir. No admite otra base ni controles omitidos.

Sobre el contrato anterior ejecuta únicamente ALTER TABLE de anoSocial a INT NULL DEFAULT NULL. Sobre el actual devuelve altered_columns vacío. Ambas ramas verifican el contrato nuevo, las filas completas/IDs y el contador AUTO_INCREMENT sin imprimir registros. El contador se lee sin estadísticas cacheadas, guardando/restaurando information_schema_stats_expiry de la sesión aun ante error; no cambia la variable global ni ejecuta ANALYZE. Referencia: [estadísticas MySQL](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_information_schema_stats_expiry).

No aplica migraciones Django, crea tablas ni carga datos. Si falla después del ALTER, el DDL puede estar aplicado: conservar la base, corregir la causa y reintentar para verificar el contrato actual. No se promete rollback de DDL ni se ejecutan limpiezas para aparentarlo. Referencias: [commits implícitos](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html) y [GET_LOCK/RELEASE_LOCK](https://dev.mysql.com/doc/refman/8.0/en/locking-functions.html).

Al cerrar TS77.39 en esta demo, la primera ejecución informó una columna alterada y cero filas institucionales; la segunda, cero columnas alteradas. Se conservaron las huellas de datos, IDs, conteos y contador: 47 tablas, 32 registros de migración y 39 FKs. prepare_demo_schema posterior informó cero creaciones/migraciones; ambas repeticiones conservaron los 47 hashes de esquema y todas las huellas de datos. La preservación con datos vinculados, credenciales, snapshots y libro mayor no cero se acredita mediante scratch propios. [Evidencia histórica TS77.39](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7739); la tabla de metadatos posterior se registra al final de esta guía.

Las 26 pruebas nuevas de transición están en [test_scrum77_schema_bootstrap.py](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py). Incluyen caché caliente/restauración ante error, ambas versiones con divergencias, cierre incompleto, sesiones inválidas, bloqueo concurrente y fallo posterior a DDL real. Una conexión distinta comprueba la liberación del bloqueo antes del reintento. El cierre histórico de TS77.39 acredita 670 pruebas verdes (0 errores) y auditoría integral aprobada. NULL físico no clasifica por sí solo a G57; el metadato explícito y los lectores posteriores están documentados en el apartado TS77.40/34/41/42.

## Preparar el esquema demo — TS77.06

Desde TS77.38, el DDL demo exige socio_lista.anoSocial nullable. Si la base ya fue preparada con el contrato anterior NOT NULL, este comando la rechaza por divergencia de socio_lista antes de escribir. Primero se debe usar la [transición protegida TS77.39](#transicionar-una-demo-preparada--ts7739); después se puede repetir esta preparación. La demo de este checkout ya completó ambas ejecuciones, con datos conservados. El procedimiento siguiente permite preparar una base vacía o repetir sobre el contrato nuevo compatible.

Con MySQL y backend demo saludables, ejecutar desde este checkout:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py prepare_demo_schema
```

El [comando prepare_demo_schema](../../backend/core/management/commands/prepare_demo_schema.py) acredita primero las mismas condiciones de configuración, identidad efectiva, grants y HTTP que el preflight. No admite destinos alternativos ni opciones para omitir controles. Requiere autocommit y FKs activas; adquiere un bloqueo MySQL por base para impedir preparaciones concurrentes del mismo comando.

La [preparación](../../backend/core/demo_schema.py) compara todas las tablas legadas presentes contra el DDL aprobado antes de ejecutar migraciones o crear faltantes. Verifica columnas y orden, tipos/signo/precisión, nulabilidad, valores predeterminados, autoincremento, charset/collation efectivos, PK, unicidad, índices, destinos de FKs y acciones ON DELETE/ON UPDATE. Una vista, definición desconocida o referencia a otra base produce rechazo. Sólo normaliza diferencias de representación equivalentes de MySQL, como el ancho de visualización de INT, defaults numéricos y el contador AUTO_INCREMENT de la tabla.

También exige una PK INT firmada compatible en auth_user si ya existe. Revisa el historial Django y detecta tablas managed o M2M automáticas que una migración pendiente intentaría crear, tanto mediante CreateModel como mediante AddField. Una tabla copiada sin su historial no se adopta mediante fake-initial: el comando rechaza la preparación antes de escribir.

Si hay migraciones pendientes y ningún conflicto detectable, las aplica mediante Django. Después valida auth_user y crea exclusivamente las tablas legadas faltantes, en orden y sin desactivar FKs. Finalmente verifica el cierre completo. El JSON de salida informa tablas creadas/existentes, 27 tablas legadas, 39 FKs y cantidad de migraciones aplicadas; no contiene credenciales.

Repetir el mismo comando acredita la preparación sobre esquema compatible: debe informar created_tables vacío y migrations_applied igual a cero. No ejecuta migrate cuando no hay plan pendiente, no inserta datos de negocio, no reemplaza tablas ni corrige divergencias. Las pruebas conservan filas propias e identidades de usuario entre ejecuciones.

MySQL realiza commits implícitos de DDL. Si un fallo de infraestructura deja una preparación parcial, se conserva la base; después de corregir la causa se puede reintentar el cierre legado compatible. Una migración Django parcial o un esquema divergente requieren diagnóstico y recuperación, sin limpieza ni marcación ficticia del historial. El comando no promete rollback del esquema. El bloqueo protege contra otra instancia del mismo comando; cambios externos de esquema deben coordinarse fuera de esa ejecución. Referencias: [SHOW CREATE TABLE](https://dev.mysql.com/doc/refman/8.0/en/show-create-table.html), [GET_LOCK](https://dev.mysql.com/doc/refman/8.0/en/locking-functions.html) y [commits implícitos](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html).

Las [pruebas de bootstrap](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) se ejecutan con:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml run --rm --no-deps -T backend pytest -q tests/infrastructure/test_scrum77_schema_bootstrap.py
```

Cada ensayo MySQL crea un esquema propio test_scrum77_bootstrap_ seguido de diez caracteres hexadecimales, separado de aplicación y pytest, y elimina únicamente ese esquema creado por la fixture. Los ALTER utilizados para introducir divergencias pertenecen a esos ensayos temporales. El aplicador crea exclusivamente las tablas legadas faltantes y deja la evolución managed a las migraciones Django.

El [aislamiento de migraciones en pruebas](../../backend/tests/infrastructure/scratch_routing.py) dirige temporalmente el alias default al esquema propio del ensayo. Esto incluye las operaciones RunPython históricas que usan ese alias en lugar del recibido por migrate. Restaura el alias al salir y bloquea consultas de expedientes contra la conexión padre de pytest durante la preparación. Los ensayos de TS77.05/06 verifican el contador técnico inicial en su propia base; las migraciones existentes permanecen intactas.

## Verificación posterior

TS77.05 entrega el [DDL mínimo](../../backend/core/sql/scrum77_legacy_schema.sql) y su [mapeo con Django](MAPEO_ESQUEMA_DEMO_SCRUM-77.md): 27 tablas, 39 FKs y auth_user externo creado por migraciones. TS77.06 lo aplica mediante el comando protegido: la demo pasó de cero a 47 tablas totales, con 29 migraciones Django y 27 tablas legadas. La segunda ejecución creó cero tablas y aplicó cero migraciones; los hashes de SHOW CREATE TABLE y de cantidades de filas permanecieron iguales. Las 27 tablas legadas siguen vacías y sus 39 FKs están activas, con destinos dentro de la misma base y tipos compatibles.

`mysqladmin ping` y la configuración resuelta por sí solos no acreditan operatividad autenticada. check_demo_mysql conserva su alcance de diagnóstico; prepare_demo_schema aplica el esquema. Las tareas de carga/conciliación y persistencia deben verificar los datos después. La evidencia atómica figura en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

La correspondencia ya está confirmada en la [aclaración corregida del PO](../../specs/005-mysql-seed-g57-g60/aclaraciones-po.md): G57 exviajero; G58/G59/G60 en años 6/5/4. La adecuación Junior/Senior y la representación de exviajeros preceden al seed.

## Evolución local de exviajeros — TS77.31

La [migración socios 0002](../../backend/socios/migrations/0002_ex_traveler_representation.py) amplía la categoría local a 12 caracteres y admite año nulo únicamente para EX_TRAVELER explícito. El CHECK de MySQL rechaza pares inválidos y variantes del marcador. Al cerrar TS77.31 se conservaba transitoriamente el corte anterior de la escala; TS77.32 lo adecua. Roles, habilitación e identidades permanecen independientes.

Antes del primer ALTER, una consulta por el alias de la migración rechaza socios históricos con años fuera de 1–6. La reversión comienza con otra comprobación: si hay años nulos o categorías que no caben en la longitud anterior, se rechaza antes de quitar el CHECK o reducir columnas. Estas guardias no corrigen datos ni prometen rollback integral de DDL; se mantienen los límites de MySQL descritos arriba.

TS77.31 se aplicó mediante prepare_demo_schema después de 594 pruebas backend verdes. La demo conserva 47 tablas, ahora con 30 migraciones registradas; las 27 tablas legadas siguen vacías y sus 39 FKs se mantienen. Sólo cambia la definición de socios_socio; django_migrations registra la operación y avanza su contador. Repetir el comando devuelve cero tablas creadas y cero migraciones aplicadas, con los 47 hashes de SHOW CREATE y todas las cantidades de filas idénticos.

Al cerrar TS77.31, socio_lista.anoSocial seguía siendo NOT NULL. TS77.38 evoluciona el DDL demo a nullable; la transición de la base preparada sigue en TS77.39 y el metadato institucional en TS77.40. Esta unidad no carga G57 ni acredita CA77-08 completo. Evidencia del modelo y las migraciones en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

## Cálculo local Junior/Senior — TS77.32

El modelo deriva JUNIOR para años 1/2 y SENIOR para 3–6; EX_TRAVELER/null mantiene su condición explícita. El helper de clasificación requiere un entero de la escala. Una escritura de clasificación conserva el par categoría/año y su independencia de roles/vigencia. Guardar sólo el nombre mediante update_fields no recategoriza filas históricas; un save completo sí incluye la clasificación y la deriva del año.

La [migración socios 0003](../../backend/socios/migrations/0003_local_social_categories.py) sólo cambia las opciones de categoría en el estado Django: sqlmigrate informa no-op físico. prepare_demo_schema la registró después de 621 pruebas verdes. La demo conserva 47 tablas, ahora con 31 migraciones registradas; sólo cambia el registro/contador de django_migrations. Los esquemas de negocio, las 27 tablas legadas y sus 39 FKs permanecen iguales. La repetición aplica cero migraciones/creaciones y conserva los 47 hashes de SHOW CREATE y todos los conteos.

Al cerrar TS77.32, las filas antiguas podían conservar PASSIVE/ACTIVE hasta TS77.33 o una escritura explícita de clasificación. Revertir 0003 restaura las opciones del estado, sin recodificar lo almacenado ni restaurar automáticamente la semántica anterior. Las credenciales y vínculos se conservan en los ensayos de avance/reversión. Tokens históricos, padrón/contratos institucionales y SPA siguen pendientes en sus tareas; CA77-08 y DEP77-02 continúan abiertos. La liberación transversal se verifica en TS77.37.

## Migración histórica local — TS77.33

La [migración socios 0004](../../backend/socios/migrations/0004_recalculate_social_categories.py) recalcula categorías de filas locales por año/situación: Junior 1/2, Senior 3–6 y EX_TRAVELER/null conservado. Usa modelos históricos, alias explícito y bloqueo/validación dentro de la transacción DML. Rechaza anomalías antes de actualizar; un fallo luego de una escritura revierte el conjunto. Sólo modifica category, sin cambios de año, credenciales, roles, vigencia, vínculos, evidencia o puntos. Repetir su cuerpo sobre datos canónicos no emite UPDATE.

Después de 642 pruebas backend verdes, prepare_demo_schema aplicó una migración y creó cero tablas. La demo conserva 47 tablas y tiene 32 registros de migración; los esquemas/conteos de negocio y 39 FKs legadas siguen iguales. Sólo cambia el registro/contador de django_migrations. La segunda preparación aplicó cero migraciones/creaciones y conservó los 47 hashes y todos los conteos. La demo sigue sin usuarios/socios ni datos legados; los casos no vacíos se verificaron en bases MySQL temporales.

La reversión semántica de 0004 usa el año conservado: PASSIVE 1–3 / ACTIVE 4–6, manteniendo EX_TRAVELER/null porque 0003 lo admite. No recupera etiquetas arbitrarias originales ni ediciones posteriores. Volver además a 0001 sigue bloqueado por la guardia de 0002 ante exviajeros. El padrón institucional, tokens históricos, filtros, T01 institucional y SPA mantienen sus tareas; CA77-08 y DEP77-02 permanecen abiertos. La próxima unidad es TS77.38, evolución del DDL demo, previa confirmación.

## Contrato DDL demo nullable — TS77.38

El [DDL](../../backend/core/sql/scrum77_legacy_schema.sql) conserva 27 tablas/39 FKs y admite anoSocial INT firmado DEFAULT NULL. Es la tercera adaptación exclusiva de la demo frente al SQL fuente, junto con las dos precisiones Decimal. Las otras definiciones siguen idénticas. El fuente institucional, el modelo unmanaged, el bootstrap y las migraciones no se modifican; la excepción física respecto del campo ORM queda documentada hasta TS77.34.

Las pruebas verifican el cierre MySQL vacío y una repetición posterior que conserva un usuario y grupo propios sobre el contrato nuevo. El contrato anterior se rechaza antes de migrar o crear, con datos previos y una tabla faltante; no se incorpora una tolerancia genérica a la nulabilidad. En la demo existente, prepare_demo_schema produjo el CommandError esperado por socio_lista: los 47 esquemas y todos los conteos permanecieron idénticos, con 32 registros de migración, 39 FKs legadas y anoSocial todavía NOT NULL.

Al cierre de TS77.38, la transición real quedó pendiente para TS77.39. Esta unidad ya la aplicó y repitió mediante el [procedimiento protegido](#transicionar-una-demo-preparada--ts7739), conservando datos y referencias. NULL no identifica por sí solo a un exviajero: metadato y coherencia pertenecen a TS77.40, y los consumidores conservan sus unidades. CA77-08 y DEP77-02 siguen abiertos; no se siembra ni se cambia la base institucional.

## Metadato y consumidores backend — TS77.40/34/41/42

TS77.40 incorpora [InstitutionalMembershipCondition](../../backend/socios/institutional_conditions.py) y la [migración 0005](../../backend/socios/migrations/0005_institutional_membership_condition.py). Es una tabla managed por nroSocio real, con condición EX_TRAVELER, referencia de fuente y corte obligatorios, PK/CHECK y sin FK física al legado. El escritor valida la ficha institucional persistida de la misma conexión y su año nulo; repite un registro idéntico sin DML y rechaza contradicciones, huérfanos o mutaciones. La pertenencia/propiedad de fixtures y manifiesto se implementarán en el seed; NULL por sí solo no clasifica a nadie.

Para una demo con el contrato nullable ya acreditado por TS77.39, usar el mismo prepare_demo_schema protegido del apartado TS77.06. En la aplicación de TS77.40 informó una migración aplicada y cero creaciones legadas. La migración creó socios_institutionalmembershipcondition vacía; el cierre pasó de 47/32 a **48 tablas / 33 registros de migración**. Django post_migrate agregó un content type y cuatro permisos de catálogo del modelo, sin asignarlos a grupos/usuarios. Las filas anteriores se conservaron y los únicos cambios de definición preexistentes fueron los tres contadores de esos catálogos/historial. Todas las otras definiciones/filas y el contador institucional permanecieron idénticos.

La preparación repetida informó **0 migraciones / 0 creaciones**; los 48 hashes de esquema, huellas de filas/conteos y contador coinciden con la primera preparación. Continúan 27 legadas vacías/39 FKs activas, anoSocial nullable, cero usuarios/socios locales y metadato vacío. Se verificó también migrate anterior a las tablas legadas en un esquema MySQL propio. Estas comprobaciones no cargan G57 ni acreditan persistencia del seed.

TS77.34 proyecta Junior 1–2, Senior 3–6, EX_TRAVELER explícito/null y UNKNOWN para anomalías sin marcador. Padrón y ranking comparten Exists y filtros antes de contar/paginar; no consultan el metadato por persona. Los aliases PASSIVE/PASIVO y ACTIVE/ACTIVO se aceptan sólo como filtros de entrada, con salida canónica; valores desconocidos devuelven 400. Omitir is_active no aplica filtro de vigencia. El unmanaged anoSocial admite null y se retiró la excepción temporal de la comparación ORM, sin ejecutar un ALTER ni modificar la fuente.

TS77.41 materializa T01 con identidad institucional inequívoca, EX_TRAVELER/null y snapshots nuevos canónicos. Rechaza legajos compartidos entre distintas fichas; varias carreras de una misma persona siguen válidas. Una emisión fallida revierte todos sus cambios; perfiles existentes conservan datos/credenciales/rol/vigencia e historial. TS77.42 relee la categoría vigente al renovar access, delegando firma, rotación, blacklist y duración a SimpleJWT; los otros claims se preservan y RBAC sigue leyendo DB. Login/me conservan sus claves. No cambia configuración JWT ni dependencias.

Las cuatro unidades cuentan con **827 pruebas backend verdes, 0 errores y sin omisiones**, cobertura combinada 94,64%, checks Django/migraciones y Ruff correctos. Tres variantes de rotación pasan además con blacklist real habilitada únicamente en un proceso de pruebas aislado. Revisiones cruzadas de código aprobadas; auditoría integral aprobada sin hallazgos pendientes. [Evidencia y límites](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142). TS77.43, TS77.35–37 y seed conservan sus tareas; CA77-01/08 y DEP77-02 permanecen abiertos.

## Legajo, SPA y catálogo — TS77.43/35/36/37/07

La fuente explícita del legajo se consulta como /api/v1/socios/ID/legajo/?identity_source=local o institutional. ID representa únicamente la PK del namespace elegido; una fuente inexistente no reintenta otra ni transforma ID en legajo. Sin parámetro, la llamada anterior se conserva sólo cuando ID/legajo identifican inequívocamente a la misma persona; ante ausencia/ambigüedad devuelve 404 genérico. Fuentes inválidas, vacías o repetidas devuelven 400. Estos ejemplos describen consultas, no crean fichas.

La propiedad institucional requiere user_id único confirmado o legajo real corroborado; no basta una PK coincidente, email o número convertido en legajo. La respuesta conserva sus claves, permite legajo/año nulos y no escribe ni sincroniza un perfil. Las PK locales usan rango BIGINT; los números institucionales/legajos académicos conservan INT. Dos pruebas MySQL propias verifican el límite 2147483648 local sin elevar contadores de la demo.

La SPA restaura identidad/rol/sesión válidos y confirma categoría desde auth/me, sin reinterpretar etiquetas históricas ni JWT. Mientras espera o ante fallo HTTP/red no muestra una categoría inventada. Ranking abre el modal con fuente institutional; la ficha conserva fuente al reintentar y muestra Sin legajo o la categoría Exviajero/Sin clasificación sin año ficticio. Vigencia, roles y puntos conservan sus significados. Badge y contraste usan tokens canónicos; UI manual/responsive sigue en sus pruebas futuras.

**932 pruebas backend y 202 frontend verdes, 0 errores**, cobertura backend **94,72%**, build de producción final correcto; Ruff/formato, Django y ausencia de cambios de modelo que requieran nuevas migraciones correctos. npm run lint registra el builder @angular-devkit/build-angular:tslint ausente, sin agregar dependencias/configuración. [Evidencia, auditoría y límites](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).

La comparación de la demo antes/después conserva exactamente las **48 definiciones/huellas de filas/conteos y el contador institucional**, con 33 registros de migración/27 legadas vacías/39 FKs activas y cero usuarios/socios locales/metadatos. En estas unidades no se ejecutan bootstrap, migraciones ni seed. El [catálogo v1](CATALOGO_DATOS_DEMO_SCRUM-77.md) puro de 16 identidades y referencias/rangos fue aceptado tras auditoría TS77.37; DP77-02/DEP77-02 y CA77-08 cerrados. CA77-02 aún requiere manifiesto/carga/conciliación, y CA77-01 las guardias TS77.08. La próxima unidad autorizable es TS77.08; la US sigue en curso.
