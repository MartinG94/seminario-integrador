# DDL y correspondencias del esquema demo — SCRUM-77

**Fecha inicial:** 11/10/2026; contrato TS77.38, metadato/ORM TS77.40/34 y propiedad/carga TS77.08–19, al 12/10/2026. **Motor:** MySQL 8.0.46. **Estado actual:** core.0001_initial aplicada, 49 tablas/34 migraciones, 16 identidades/162 referencias conciliadas. Cierre legado 27 tablas/39 FKs; 59 FKs totales sin huérfanos. Repetición/persistencia conservan todos los esquemas/filas/conteos/contadores. 1008 backend/222 frontend verdes, build correcto, navegador aprobado; auditoría integral final aprobada sin hallazgos abiertos. [Evidencia](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827). Las cifras/pendientes anteriores son históricos.

El [DDL entregado](../../backend/core/sql/scrum77_legacy_schema.sql) contiene 27 tablas y 39 claves foráneas. Se extrajo el cierre transitivo de las ocho tablas unmanaged consumidas por padrón/ranking desde el [SQL legado](../analisis-proceso-actual/sistema-actual/sistema_actual_legado_schema.sql). Conserva columnas, claves, índices, valores predeterminados, nulabilidad y acciones referenciales de la fuente, salvo tres adaptaciones explícitas: dos precisiones Decimal y anoSocial nullable exclusivo de la demo. El SQL fuente institucional permanece intacto.

TS77.05 entrega el artefacto y su compatibilidad en un esquema temporal. TS77.06 incorpora la [preparación protegida](../../backend/core/management/commands/prepare_demo_schema.py), aplicada y repetida en la base demo, y sus pruebas de rechazo de divergencias. El archivo no se incorpora al directorio de inicialización automática de MySQL.

## Raíces y correspondencias Django

Los modelos [padron.models](../../backend/padron/models.py) y [ranking.models](../../backend/ranking/models.py) conservan managed=False y sus protecciones de lectura. No se habilita `_allow_write`. TS77.34 alinea exclusivamente null=True/blank=True de anoSocial con el DDL demo aplicado, sin migración de padrón ni ALTER físico.

| Modelo | Tabla / identidad física | Correspondencia relevante |
|---|---|---|
| padron.Subcomision | socio_tiposubcomision / codSubcomision | AutoField → INT firmado con AUTO_INCREMENT y PK; nombre VARCHAR(45). |
| padron.Socio | socio_lista / nroSocio | AutoField → INT firmado con AUTO_INCREMENT y PK; nombre/apellido VARCHAR(45); DateField → DATE; BooleanField → TINYINT(1). codSubcomision es NOT NULL: blank=True no equivale a null=True. TS77.38/39 definen/aplican anoSocial nullable en la demo; TS77.34 alinea null=True/blank=True del unmanaged. Fuente institucional intacta. |
| padron.SocioEstudio | socio_estudio / compositeKey | IntegerField PK → INT firmado sin AUTO_INCREMENT; nroLegajo INT, curso/aula VARCHAR(10) nullable. codTurno es nullable, pero su FK requiere socio_tipoEstudioTurno. |
| padron.SocioEmail | socio_email / compositeKey | IntegerField PK → INT firmado sin AUTO_INCREMENT; idEmail INT, email VARCHAR(45), comprobado/habilitado TINYINT(1). |
| padron.SocioEstado | socio_estado / codEstadoSocio | AutoField → INT firmado con AUTO_INCREMENT; nombre/descripcion VARCHAR(45), descripción nullable. |
| padron.SocioEstadoHistorial | socio_estadoHistorial / idEstadoHistorial | AutoField → INT firmado con AUTO_INCREMENT; fechaHora DATETIME(6). Las FKs físicas de grupo, socio, estado y motivo se conservan aunque parte del ORM las represente como IntegerField. |
| ranking.PuntajeAplicado | tribunal_puntajeaplicado / idPuntajeAplicado | AutoField → INT firmado con AUTO_INCREMENT; puntajeAplicado DECIMAL(10,2). socio_id y expediente_id conservan sus FKs físicas, aunque el ORM no genere esas restricciones. |
| ranking.PuntajeGeneral | tribunal_puntajegeneral / idPuntajeGeneral | AutoField → INT firmado con AUTO_INCREMENT; puntos DECIMAL(10,2), contadores INT. socio_id mantiene unicidad y FK, coherentes con OneToOneField. |

En MySQL, las columnas INT y sus destinos FK mantienen tamaño y signo compatibles. Las pruebas comparan COLUMN_TYPE en ambos extremos, incluido user_id → auth_user.id; no se infiere la PK del usuario desde DEFAULT_AUTO_FIELD. La exigencia de compatibilidad está documentada en el [manual de claves foráneas de MySQL](https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html).

## Cierre de dependencias y orden

auth_user es el único destino externo al archivo: lo crean las migraciones reales de Django. La prueba acredita su tipo INT firmado y compara SHOW CREATE TABLE antes y después del DDL, sin redefinir ni alterar esa tabla.

Las 27 creaciones siguen este orden de dependencias:

| Bloque | Tablas incluidas |
|---|---|
| Catálogos societarios previos | socio_tipodocumento, socio_sexo, socio_tiposubcomision, socio_estadocivil, socio_tipoSocio, socio_estado, socio_motivoCambioEstado, socio_especialidad, socio_tipoEstudioTurno, grupo_lista. |
| Padrón y satélites utilizados | socio_lista, socio_estadoHistorial, socio_estudio, socio_email. |
| Catálogos y dependencias del tribunal | tribunal_afectados, tribunal_estadoevento, tribunal_estadoexpediente, tribunal_tiposancion, tribunal_valorsancion, tribunal_tipoevento, tribunal_sancionpersonalizadaeventos. |
| Respaldo histórico y puntos | tribunal_evento, tribunal_solicitud, tribunal_datosresolucion, tribunal_expediente, tribunal_puntajeaplicado, tribunal_puntajegeneral. |

Una relación nullable no permite omitir su tabla destino. Por eso el cierre incluye estado civil, turno, evento, solicitud, datos de resolución, tipos de evento y sanciones personalizadas, aunque los fixtures posteriores puedan dejar algunas referencias sin valor.

El movimiento legado apunta a **tribunal_expediente**, que puede vincular tribunal_datosresolucion. La tabla administrada expedientes_expediente pertenece a otro namespace: no se incorpora al archivo ni se utiliza su PK como sustituto. Las demás tablas del dump quedan fuera porque no pertenecen al cierre requerido.

## Adaptaciones y límites

| Decisión | Evidencia y alcance |
|---|---|
| DOUBLE → DECIMAL(10,2) en tribunal_puntajeaplicado.puntajeAplicado y tribunal_puntajegeneral.puntos | Los dos campos vigentes son DecimalField(max_digits=10, decimal_places=2). Se adapta únicamente la creación de estas tablas nuevas; no se convierte información existente. DECIMAL representa valores exactos, conforme al [manual de MySQL](https://dev.mysql.com/doc/refman/8.0/en/fixed-point-types.html). |
| INT NOT NULL → INT DEFAULT NULL en socio_lista.anoSocial, sólo demo | Tercera adaptación D77-03/TS77.38: permite representar un exviajero sin año ficticio. Conserva tipo firmado, columna, PKs/FKs y demás contratos. NULL por sí solo no acredita condición exviajero; el metadato explícito corresponde a TS77.40. No modifica el fuente ni la base institucional. |
| Conservar tribunal_valorsancion.valor como DOUBLE | No existe un campo DecimalField equivalente en los modelos consumidos que justifique cambiar este catálogo. Se mantiene la fuente. |
| Conservar tipos y nombres legados | No se renombran columnas ni tablas del esquema institucional. Las PK/FK firmadas, compositeKey y acciones ON DELETE son las documentadas por la fuente. |
| Sin cambio de reglas de puntos | La precisión física no autoriza impactos fraccionarios ni implementa el motor 3:1. No se cargan movimientos, saldos o expedientes. |
| Sin carga de clasificación institucional | El contrato vacío no clasifica filas ni siembra G57. TS77.40/34/41 incorporan metadato y consumidores backend, con tabla vacía en la demo; propiedad/carga del seed y SPA pendientes. DEP77-02 permanece abierto. No se deduce exviajero desde NULL ni se inventa un año. |
| CREATE TABLE sin IF NOT EXISTS | El archivo no oculta una tabla existente incompatible. TS77.06 valida todo lo existente antes de crear, omite tablas compatibles y permite completar un cierre legado parcial válido. No corrige divergencias ni migra por fuera de Django. |

Todas las tablas usan InnoDB, utf8mb4 y utf8mb4_unicode_ci. El archivo contiene exclusivamente CREATE TABLE: no incluye CREATE DATABASE, USE, SET, DROP, ALTER, TRUNCATE, DML, grants, datos de conexión ni desactivación de FKs.

El nuevo contrato es válido para una base demo vacía. Una demo preparada con anoSocial NOT NULL diverge de esta versión: el bootstrap conserva su comparación estricta y la rechaza antes de migrar o crear faltantes. TS77.39 incorpora un [comando separado de transición protegida](../../backend/core/management/commands/transition_demo_schema.py) que exige el contrato anterior o actual íntegro. En la demo existente ya se aplicó el único ALTER de anoSocial; se repitieron transición y bootstrap estricto sin alteraciones adicionales, creaciones ni migraciones. No se incorpora un ALTER al archivo DDL ni se relaja la comparación del bootstrap.

Las precondiciones del aplicador son: perfil/base demo acreditados, historial managed sin colisiones, identidad/PK compatibles en auth_user, autocommit y FKs activas. Verifica el contrato íntegro de todas las tablas legadas presentes antes de migrar/crear; controla por separado la identidad de auth_user y el historial/colisiones managed. Aplica migraciones pendientes mediante Django y omite tablas legadas compatibles. No compara íntegramente los contratos de las demás tablas managed. El archivo SQL por sí solo no garantiza el destino; no se presenta como comando manual de preparación. MySQL hace commits implícitos de DDL: se conserva un cierre parcial ante un fallo y se distingue su recuperación de la carga transaccional del seed. Proceso, límites y pruebas en la [guía de demo](GUIA_ENTORNO_DEMO_SCRUM-77.md#preparar-el-esquema-demo--ts7706).

## Pruebas y oráculos

Desde la raíz del checkout, con MySQL demo activo:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml run --rm --no-deps -T backend pytest -q tests/infrastructure/test_scrum77_legacy_ddl.py
```

Las [pruebas](../../backend/tests/infrastructure/test_scrum77_legacy_ddl.py) usan primero la base separada de pytest y crean después un esquema propio de nombre aleatorio test_scrum77_ddl_ seguido por diez caracteres hexadecimales. Aplican allí las migraciones reales y el DDL, y eliminan únicamente ese esquema cuyo CREATE fue satisfactorio. Durante migrate, default apunta al esquema propio para incluir sus RunPython históricos; un guardia impide consultas de expedientes contra la conexión padre y se comprueba el contador técnico local. No importan helpers de esquema reducido para preparar el ensayo ni relajan codSubcomision a NULL.

| Riesgo | Oráculo |
|---|---|
| Operaciones destructivas o inclusión de datos/auth simplificado | Todas las sentencias son creaciones completas; auth_user y expedientes_expediente quedan fuera. |
| Cierre incompleto u orden inválido | Conjunto exacto derivado de las ocho raíces y FKs del SQL fuente; todos los destinos se crean antes que sus referencias. |
| Pérdida de definición del legado | Comparación íntegra de cada CREATE contra la fuente, permitiendo únicamente las dos adaptaciones Decimal y anoSocial nullable. |
| SQL inválido, FKs ausentes o tipos incompatibles | Ejecución MySQL real; catálogo físico con 39 relaciones y tipos iguales en ambos extremos, FK checks activos e InnoDB/utf8mb4. |
| Desvío frente al ORM | Tipos, longitudes, precisión, nulabilidad, autoincremento, PK y unicidad comparados con los ocho modelos vigentes. TS77.34 cierra la diferencia temporal de anoSocial y retira la excepción; no quedan tolerancias especiales para esa columna. |
| Cierre vacío nuevo | MySQL acredita INT firmado, IS_NULLABLE=YES y DEFAULT NULL; las 27 tablas legadas sin filas y FKs activas. Bootstrap desde vacío y repetición sobre contrato compatible conservados. |
| Adopción accidental del contrato anterior | Migración managed pendiente, socio/cuenta/grupo previos y socio_email faltante: rechazo con cero DDL/DML, datos/SHOW CREATE/historial intactos. |
| Restricciones existentes sólo en texto | INSERT de movimiento huérfano rechazado con error 1452; el libro mayor temporal queda vacío. |

TS77.06 demuestra 30 pruebas adicionales: guardias del comando y ensayos MySQL temporales de preparación desde vacío, segunda ejecución con filas/IDs propios conservados, cierre parcial compatible, divergencias de columnas/PK/índices/FKs, referencia a otra base, auth_user incompatible o tablas sin historial —incluido el through M2M de un AddField— y bloqueo concurrente. Un fallo simulado de CREATE conserva lo ya creado y una repetición completa el cierre sin limpieza. El aplicador compara también charset/collation efectivos por columna y rechaza cláusulas físicas desconocidas. Las 36 pruebas combinadas de DDL y preparación pasan sin errores.

En TS77.06 se aplicaron 29 migraciones y 27 creaciones legadas en la demo (47 tablas totales); al repetir no se crearon tablas ni se aplicaron migraciones. SHOW CREATE TABLE y cantidades de filas conservaron sus hashes; las 39 FKs legadas apuntan a la misma base con tipos compatibles y las tablas legadas continúan vacías. La evidencia histórica se conserva en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

En TS77.38 se comprobó el rechazo esperado de prepare_demo_schema por socio_lista en la demo con contrato anterior. Antes/después, los 47 hashes de SHOW CREATE y todos los conteos eran idénticos: 32 registros de migración, 39 FKs legadas y anoSocial todavía NOT NULL. El contrato nullable se probó en esquemas temporales propios; la transición real quedó pendiente para TS77.39. Esta evidencia histórica se conserva.

En TS77.39, el comando protegido alteró únicamente socio_lista.anoSocial a INT DEFAULT NULL. Conservó todas las huellas de filas, conteos, IDs y contador; los otros 46 esquemas no cambiaron. Transición repetida: cero columnas alteradas. Bootstrap estricto posterior: cero creaciones/migraciones. Los 47 hashes y huellas de filas coinciden entre esas repeticiones; 32 registros de migración, 27 tablas legadas vacías y 39 FKs activas. La preservación con datos y un contador reservado se verifica en scratch propios, incluyendo libro mayor no cero y snapshots históricos. 670 pruebas backend verdes (0 errores), código/oráculos auditados y auditoría integral aprobada sin hallazgos pendientes. [Evidencia TS77.39](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7739). CA77-01/02/08 y DEP77-02 conservan sus pendientes; NULL físico no acredita la condición institucional, pendiente en TS77.40.

## Metadato managed separado del cierre legado — TS77.40

La [migración nueva 0005](../../backend/socios/migrations/0005_institutional_membership_condition.py) crea socios_institutionalmembershipcondition; no modifica ninguna de las 27 definiciones del DDL ni incorpora una FK al legado. Puede migrar antes de crear socio_lista, sin consultarla. El [modelo/escritor](../../backend/socios/institutional_conditions.py) verifica después la existencia y nulabilidad de la referencia institucional en la misma conexión.

| Campo / restricción | Mapeo y garantía |
|---|---|
| institutional_number | IntegerField PK, INT firmado sin AUTO_INCREMENT; nroSocio real, positivo hasta 2147483647. No representa PK local, legajo ni grupo. |
| condition | VARCHAR(12), valor único permitido EX_TRAVELER; collation utf8mb4_bin y longitud exacta en CHECK. |
| source_reference / social_cycle | VARCHAR(200) / VARCHAR(80), NOT NULL y no vacíos tras TRIM en CHECK. Fuente/corte explícitos provistos por el llamador. |
| Asociación | Sin FK física. El escritor/save validan ficha persistida y anoSocial NULL con bloqueo institucional antes del marcador; repetición idéntica sin DML y contradicción/duplicado rechazado. Las mutaciones externas requieren conciliación; propiedad/manifiesto del seed siguen en TS77.09/11. |

En la demo, prepare_demo_schema aplicó una migración y creó cero tablas legadas: **48 tablas / 33 registros de migración**, metadato vacío. Django post_migrate agregó un content type y cuatro permisos de catálogo, sin asignaciones; el historial agregó su registro. Todas las filas previas se conservaron, con cambios de SHOW CREATE limitados a los tres contadores de esos catálogos/historial. Las otras definiciones y el contador institucional permanecieron idénticos. Repetición: cero migraciones/creaciones, 48 hashes y todas las huellas de datos/conteos/contador iguales; 27 legadas vacías/39 FKs activas y cero usuarios/socios locales, sin seed.

TS77.34 alinea la nulabilidad del unmanaged y retira la excepción del oráculo ORM; el DDL y el SQL fuente permanecen intactos. Padrón/ranking proyectan y filtran mediante Exists del metadato antes de count/LIMIT, sin N+1. **827 pruebas backend verdes, 0 errores/sin omisiones**, incluidas las 37 del metadato y el bootstrap anterior al legado; cobertura combinada 94,64%. Revisiones de código aprobadas; auditoría integral aprobada sin hallazgos pendientes. [Evidencia TS77.40/34/41/42](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142). CA77-01/02/08 y DEP77-02 siguen abiertos por guardias de carga, identidad del legajo, SPA y seed.

## Namespaces y catálogo — TS77.43/07

PK local, nroSocio y nroLegajo académico conservan su tipo/namespace propio. La PK local de la consulta con identity_source=local admite BigAutoField/BIGINT positivo hasta 9223372036854775807; el campo legajo local conserva VARCHAR(20). nroSocio/nroLegajo institucional son INT firmado positivo hasta 2147483647. [Dos oráculos MySQL nativos](../../backend/tests/infrastructure/test_scrum77_legajo_bigint.py) verifican PK local 2147483648 en esquemas UUID propios. No se agrega ALTER, migración ni cambio del contador compartido. legajo faltante se transmite como null, sin fabricar un valor desde otra identidad.

El [catálogo v1](CATALOGO_DATOS_DEMO_SCRUM-77.md) fija rangos candidatos disjuntos para sus 16 identidades, estudio/email/DNI, grupos y referencias futuras. Son compatibles con tipos/longitudes del DDL fuente y los modelos actuales; no quedan reservados contra datos reales. La ausencia de colisiones/propiedad se verificará en TS77.08/09/11 y las PK managed se resolverán al cargar.

Antes/después de TS77.43/35/36/37/07: 48 hashes de SHOW CREATE y todas las huellas de filas/conteos idénticos; 33 migraciones, 27 legadas vacías/39 FKs, anoSocial nullable, contador institucional=1 y metadato/usuarios/socios locales vacíos. Sin nueva preparación ni seed. Implementación transversal verificada/auditada, CA77-08/DEP77-02 cerrados; CA77-01/02 conserva guardias/carga/manifiesto/conciliación. DDL demo, SQL fuente y migraciones 0001–0005 intactos.

## Propiedad, carga y conservación — TS77.08–19

core.0001_initial incorpora core_demofixtureownership, con profile/fixture_key y namespace/object_key únicos físicamente; las referencias genéricas se validan por tabla/PK existente. Preparación protegida: una migración, 49 tablas/34 registros. Su repetición no agrega migraciones ni tablas legadas; el SQL fuente/demo y las migraciones socios 0001–0005 quedan intactos.

La demo contiene 16 fichas/cuatro por grupo, cuatro marcadores G57 EX_TRAVELER/null, 11 cuentas/perfiles locales, cinco causas, cuatro T01 y 162 referencias. Los namespaces de usuario, socio local, nroSocio y legajo académico permanecen separados. El centinela institucional 99 conserva subcomisión local null. Siete resoluciones/expedientes legados respaldan ocho asientos, total +1,00; cero huérfanos en las 59 FKs totales (39 legadas).

La segunda carga conserva exactamente manifiesto, 49 esquemas/huellas/conteos y contadores institucional 770017/formal2026=5. La recreación MySQL mantiene esas comparaciones sobre el mismo volumen sin reseed. Los GET posteriores, incluida la reparación de Mis Solicitudes que resuelve el proveedor sin PK local, conservan todas las huellas. [Resultados](VERIFICACION_CARGA_SCRUM-77.json) y [seguimiento](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827).
