# Carga, uso y conservación de la demo — SCRUM-77

**Unidad:** TS77.27, [spec 005](../../specs/005-mysql-seed-g57-g60/spec.md).

**Perfil:** `scrum77-g57-g60-v1`. **Corte social:** `PO-SCRUM77-CORTE-01`.

**Estado de esta guía:** procedimiento preparado a partir de la implementación. Las ejecuciones sobre la demo, la persistencia, los recorridos y el cierre de los criterios se registran en la sección de evidencia al final. Este documento por sí solo no acredita una carga ni un criterio cumplido.

El conjunto autorizado está en el [catálogo v1](CATALOGO_DATOS_DEMO_SCRUM-77.md). La [guía de infraestructura](GUIA_ENTORNO_DEMO_SCRUM-77.md) detalla aislamiento, grants, preparación y transición del esquema. El seguimiento y las pruebas de cada unidad se conservan en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

## Preparar el entorno y el esquema

### Inicio recomendado desde una copia limpia

Requiere Git para descargar esta rama y Docker Desktop/Engine con Compose v2 funcionando. No requiere Python ni Node instalados en el host:

```sh
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml --profile frontend up -d --build
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml --profile frontend ps -a
```

El servicio `demo-setup` espera a que el backend esté sano, ejecuta la preparación protegida del esquema y carga el catálogo. La SPA sólo se inicia cuando esa tarea finaliza correctamente (`Exited (0)`). Abrir **http://127.0.0.1:4202** después de que Angular termine de compilar. La primera descarga/compilación puede tardar varios minutos.

Si faltan datos, comprobar que se abrió el puerto **4202**, que el checkout corresponde a la rama de la PR #54 y que `demo-setup` terminó con código cero. `docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml logs demo-setup` muestra el diagnóstico. El Compose habitual y `npm start` usan otro entorno; no cargan automáticamente esta demo.

Una instalación nueva contiene veinte socios institucionales, quince expedientes operativos (3 creados, 2 justificando, 3 en revisión, 1 pendiente de firma, 2 pendientes de envío y 4 emitidos), cuatro solicitudes T01 y doce asientos con respaldo. Las causas o solicitudes agregadas manualmente durante UAT pertenecen al volumen de esa máquina y no se copian como fixtures. Repetir el arranque conserva esos datos; no usar `down -v` para actualizar la rama.

**Dónde verlos:** el ranking contiene los veinte socios y puede tener varias páginas. TD/CD/Admin consultan el conjunto en Gestionar Expedientes. Mis Expedientes muestra únicamente las causas en las que participa la cuenta ingresada; Solicitudes creadas muestra las iniciadas por esa cuenta. Las cuentas clásicas de acceso rápido no reemplazan a las cuentas `99077...` del catálogo y pueden no tener causas propias.

### Angular en el host, como alternativa

Usar Node 18 y las dependencias existentes del proyecto:

```sh
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml up -d --build
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml ps -a
cd frontend
npm install --legacy-peer-deps
npm run start:demo
```

Antes de iniciar Angular, esperar a que `demo-setup` figure como `Exited (0)` en `ps -a`; el comando `up -d` puede retornar mientras termina la carga. El script versionado usa el puerto 4202 y `proxy.scrum77-local.conf.json`, cuyo destino es el backend demo en 8002. No ejecutar a la vez el frontend Docker y el frontend del host sobre el mismo puerto. Las cuentas de prueba se describen más abajo; los accesos rápidos clásicos conservan sus permisos, aunque algunos no tienen ficha institucional y muestran sus puntos como no disponibles.

### Preparación manual para diagnóstico

Ejecutar desde la raíz de este checkout. Usar el archivo demo como único archivo Compose; las credenciales permanecen en la configuración del entorno y no se copian a informes, manifiestos o capturas.

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml config --quiet
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml up -d --build db backend
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml ps
```

Continuar cuando MySQL y backend estén saludables. El destino es `aveit_tribunal_scrum77_demo`, con MySQL en loopback `3307` y backend en `8002`; el backend se conecta internamente a `db:3306`. No reutilizar un servicio montado desde otro checkout.

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py check_demo_mysql
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py prepare_demo_schema
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py check_demo_mysql
```

La preparación aplica las migraciones managed pendientes, incluida [core.0001_initial](../../backend/core/migrations/0001_initial.py), que incorpora el registro técnico de propiedad. Después verifica el cierre legado. No carga personas, causas o movimientos. Sobre un esquema compatible ya preparado, repetir debe informar cero migraciones y cero tablas nuevas.

Si una demo antigua conserva `socio_lista.anoSocial NOT NULL`, corresponde el procedimiento protegido de transición de la guía de infraestructura antes de preparar. No ejecutar ALTER manual ni marcar migraciones como aplicadas para eludir una divergencia.

## Cargar y guardar el manifiesto

El [comando seed_expedientes](../../backend/core/management/commands/seed_expedientes.py) exige el perfil aprobado, DEBUG habilitado, padrón de base de datos y destino MySQL demo explícito. Comprueba la conexión efectiva, grants, FKs, tablas InnoDB, migraciones y esquema. No prepara ni migra mientras carga.

```powershell
$scrum77ManifestPath = Join-Path $env:TEMP 'scrum77-manifest-first.json'
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py seed_expedientes --profile scrum77-g57-g60-v1 | Out-File -Encoding utf8 $scrum77ManifestPath
if ($LASTEXITCODE -ne 0) {
    throw 'La carga fue rechazada. Conservá la demo y revisá el diagnóstico antes de reintentar.'
}
$scrum77Manifest = Get-Content -Raw -LiteralPath $scrum77ManifestPath | ConvertFrom-Json
$scrum77Manifest | Select-Object status, profile, social_cycle
```

La salida estándar contiene un JSON con `status=ok`, perfil, corte, referencias e identidades. No contiene contraseñas, hashes de credenciales ni JWT. Conservar ese archivo fuera del repositorio como evidencia técnica, junto con la fecha y la versión del checkout utilizada.

La carga mantiene una sola transacción para datos, propiedad y numeración, bajo el bloqueo compartido con la preparación/transición. Las causas usan los servicios vigentes; los antecedentes se insertan con respaldo resolutivo y atribución individual. No se despachan notificaciones externas.

## Leer las identidades sin equiparar números

| Campo del manifiesto | Significado |
|---|---|
| `fixtures[].fixture_key` | Clave estable del catálogo o de un componente generado |
| `fixtures[].namespace` | Tabla física correspondiente a esa referencia |
| `fixtures[].object_key` | PK real, expresada como cadena; puede ser un UUID |
| `fixtures[].owned` | Alta propia o referencia explícita a un objeto compartido/preexistente |
| `mappings` | Diccionarios por tipo: usuarios, socios locales/institucionales, cuentas, grupos, subcomisiones, causas, T01 y antecedentes |
| `identities[].institutional_number` | `socio_lista.nroSocio`; no es la PK local ni el legajo académico |
| `identities[].academic_number` | Legajo académico real de `socio_estudio` |
| `identities[].user_id` / `local_socio_id` / `local_legajo` | Correspondencia efectiva con cuenta y socio operativo, o null cuando no existe una cuenta local |
| `identities[].group` | Grupo institucional confirmado mediante su historial |
| `institutional_subcommission` / `local_subcommission_id` | Código legado y PK local separados; el centinela institucional 99 no inventa una subcomisión local |

Por ejemplo, buscar `member.g57.01` en `identities` permite obtener su identidad institucional y su socio local resuelto; no se calcula ninguna PK a partir de `770001`.

```powershell
$scrum77Manifest.identities | Where-Object fixture_key -eq 'member.g57.01'
$scrum77Manifest.fixtures | Where-Object fixture_key -eq 't01.cd.issued.multi'
$scrum77Manifest.mappings.issued_causes
```

Las cuatro T01 tienen UUID propio. Una solicitud emitida conserva un número `T01-…` y vincula un expediente con número formal `EXP-…/AAAA`, asignado por el servidor. Son identificaciones distintas: al cotejar tablero o detalle de causa, usar el expediente vinculado; para Mis Solicitudes, usar la T01 y su UUID. Los IDs de antecedentes legados tampoco se sustituyen por PKs de expedientes managed.

## Cuentas y clasificación del conjunto

| Legajo de ingreso de cuenta nueva | Referencia institucional | Rol inicial | Habilitación inicial |
|---|---|---|---|
| 99077001 | G57 / 770001 | SOCIO | Habilitada |
| 99077002 | G57 / 770002 | SOCIO | Deshabilitada |
| 99077005 | G58 / 770005 | CD | Habilitada |
| 99077006 | G58 / 770006 | SOCIO | Habilitada |
| 99077009 | G59 / 770009 | FISCALIZADORA | Habilitada |
| 99077013 | G60 / 770013 | SOCIO | Habilitada |
| 99077017 | G62 / 770017 | SOCIO | Habilitada |
| 99077018 | G62 / 770018 | SOCIO | Habilitada |
| 99077019 | G63 / 770019 | SOCIO | Habilitada |
| 99077020 | G63 / 770020 | SOCIO | Habilitada |

El código FISCALIZADORA conserva el RBAC existente; SCRUM-77 no implementa el renombre general de roles. Las cinco cuentas de `seed_demo` se conservan por sus legajos `74907`, `85194`, `87414`, `408917` y `403655`; si faltan, se crean mediante ese comando original. Las credenciales, roles y ediciones de cuentas existentes no se sobrescriben ni se publican en el manifiesto.

El ingreso vigente envía `identifier` —legajo o correo— a `/api/v1/auth/login/`. Conserva el acceso de prueba sin contraseña cuando se omite ese campo; si se suministra una contraseña no vacía, el servidor la valida. Un smoke por identificador acredita el contrato existente, la sesión y los permisos, **sin acreditar una prueba de contraseña**. La cuenta nueva deshabilitada debe recibir el rechazo genérico del servidor. No mostrar tokens, contraseñas o hashes en capturas o resúmenes.

Junior corresponde a años 1–2; Senior a 3–6 dentro de la escala operativa. Este catálogo contiene G58=6, G59=5 y G60=4 como Senior; los cuatro G57 son Exviajeros con año nulo y marcador explícito. La ampliación autorizada agrega dos G62 de 2.º año y dos G63 de 1.º año, cuatro Juniors con cuenta SOCIO habilitada y saldo cero. La categoría no otorga rol, habilitación, firma ni saldo. El pase de año corresponde a la asamblea de recambio, sin fecha fija ni cálculo automático en este seed.

## Abrir la SPA contra esta demo

Para usar dependencias ya instaladas en el host, desde `frontend/`:

```powershell
npm start -- --host 127.0.0.1 --port 4202 --proxy-config proxy.scrum77-local.conf.json
```

El [proxy local](../../frontend/proxy.scrum77-local.conf.json) dirige `/api` a `http://127.0.0.1:8002`. Abrir `http://127.0.0.1:4202`. Para la alternativa Docker, desde la raíz:

```powershell
docker compose -p sgd-aveit-scrum77-demo --profile frontend -f docker-compose.scrum77-demo.yml up -d --build frontend
```

Esta alternativa utiliza el proxy interno hacia `backend:8000` y publica igualmente `4202`. Elegir una alternativa para evitar ocupar ese puerto con dos servidores.

Los recorridos previstos incluyen ranking y filtros, detalle institucional de legajo, selector T01 con búsqueda reactiva/múltiples destinatarios, Mis Solicitudes de cada solicitante y tablero/listado. Contrastar IDs, estados y saldos con el manifiesto y MySQL; una tabla vacía, un fallback en memoria o un HTTP distinto del esperado requieren diagnóstico.

El detalle de legajo acepta la fuente explícita: `/api/v1/socios/770001/legajo/?identity_source=institutional`. Para una ficha local, usar su PK real y `identity_source=local`. El ranking transporta la fuente institucional. Una fuente inválida devuelve 400; referencias ausentes o ambiguas no habilitan elegir otra persona. El rol/vigencia del servidor sigue controlando el acceso.

## Repetir sin reconstruir los fixtures

Repetir el mismo comando y perfil, guardando la segunda salida en otro archivo:

```powershell
$scrum77RepeatPath = Join-Path $env:TEMP 'scrum77-manifest-repeat.json'
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py seed_expedientes --profile scrum77-g57-g60-v1 | Out-File -Encoding utf8 $scrum77RepeatPath
if ($LASTEXITCODE -ne 0) {
    throw 'La repetición fue rechazada. No se deben reconstruir ni reasignar los fixtures.'
}
```

El registro resuelve por propiedad y PK efectiva, conservando credenciales, ediciones válidas, números, vínculos y auditoría. No adopta una fila ajena por coincidir en sus datos visibles; tampoco recrea una referencia registrada que perdió su destino. Los asientos mantienen su socio, respaldo y puntos individuales inmutables. Repetir no debe avanzar el contador formal ni insertar movimientos adicionales.

El conjunto ampliado esperado comprende 20 fichas institucionales, diez cuentas del catálogo y las cinco referencias de `seed_demo`; los fixtures conservan tres causas en Creado, dos en Justificaciones y cuatro T01, dos por solicitante. RF77-16 agrega tres En revisión, una Pendiente de firma, dos Pendientes de envío y cuatro Emitidos: quince causas fixtures y doce asientos vinculados a once expedientes/resoluciones históricos, con suma **+1**. Las altas manuales durante UAT se conservan y pueden aumentar los totales de causas/T01. Los puntos solicitados de causas pendientes no forman el saldo. Los cuatro Juniors reciben +2/-1/-2/+1 por sus nuevos actos sintéticos, conservando los ocho asientos anteriores; una resolución original compartida atribuye +2 y +1 a destinatarios distintos, sin duplicar su total.

## Conservar datos al recrear MySQL

El volumen fijo es `sgd_aveit_scrum77_demo_mysql_data`. Antes de recrear, registrar el ID del contenedor, el mount efectivo y una lectura de referencias/filas/relaciones/saldos. Conservar también el manifiesto de la carga aceptada. Coordinar el ensayo para que no haya escrituras externas concurrentes.

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml stop backend db
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml up -d --force-recreate db
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml up -d backend
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml ps
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py check_demo_mysql
```

Esperar nuevamente la salud de ambos servicios. El contenedor MySQL debe tener un ID distinto y el mismo volumen. Verificar después las referencias, filas, relaciones y saldos mediante lecturas, **sin ejecutar seed ni preparación entre las dos mediciones**. El registro puede consultarse sin cargar datos:

```powershell
docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python manage.py shell -c "import json; from core.demo_fixtures import DemoFixtureRegistry; print(json.dumps(DemoFixtureRegistry('scrum77-g57-g60-v1').export(), sort_keys=True))"
```

La comparación del registro es una parte del ensayo; completar también la comparación de datos y saldos. No usar `down -v`, eliminar el volumen ni resembrar para aparentar persistencia. Detener contenedores conserva el volumen; borrar ese volumen elimina los datos que este criterio busca verificar.

## Diagnosticar un rechazo y recuperar

| Situación | Acción |
|---|---|
| Perfil, base, host, usuario, DEBUG o padrón incorrectos | Corregir la configuración de la demo y volver a verificar `check_demo_mysql`; no redirigir la carga a otro entorno. |
| Migración pendiente o tablas compatibles faltantes | Ejecutar `prepare_demo_schema` antes del seed y revisar su resultado. La carga no aplica DDL. |
| Esquema divergente, historial inconsistente o unicidad física ausente | Conservar la base y diagnosticar la diferencia contra las migraciones/DDL aprobados. No usar fake, reset ni reparación SQL ad hoc. |
| Otro proceso posee el bloqueo compartido | Esperar su finalización y reintentar. No quitar el bloqueo a la fuerza ni ejecutar un loader por fuera del comando. |
| Identidad natural ajena, duplicada o referencia de propiedad contradictoria | Revisar catálogo, namespace y referencia en modo lectura. No adoptar, borrar ni sobrescribir la fila; una colisión requiere resolver su causa antes de reintentar. |
| Asiento o respaldo inconsistente | Conservar el libro mayor y diagnosticar la atribución. No editar el saldo ni reemplazar el asiento. |
| Excepción durante el DML | El comando rechaza la carga y revierte datos, propiedad y numeración de esa transacción. Corregir la causa y repetir el mismo perfil; no limpiar para conseguir una ejecución verde. |
| Fallo durante preparación DDL | MySQL puede haber confirmado cambios de esquema. Conservar e inspeccionar el estado; la preparación y el seed tienen garantías distintas. |

No imprimir secretos ni el contenido de excepciones SQL en el informe. Registrar etapa, código de salida, diagnóstico saneado y las comprobaciones de conservación realizadas.

## Límites del recorrido

DEP77-01 conserva las brechas fuera de alcance: columna visible de grupo, historial general de legajo más allá de los puntos aplicados, conexión completa del listado/descargos de Mis Expedientes, ordenamiento compuesto y simulaciones de firma/votación. RF77-15 incorpora el saldo propio y coherencia de las fichas; RF77-17 permite consultar sus asientos/resoluciones bajo los permisos existentes. El grupo se comprueba en catálogo, historial y manifiesto.

Las cinco escenas managed originales conservan Creado y Justificaciones con fechas actuales y plazo hábil vigente. RF77-16 importa diez historias nuevas temporalmente coherentes hasta las cuatro etapas restantes, con auditoría y respaldos sintéticos. No modifica fechas ni estados previos, ni acredita firmas productivas o facultades nuevas. Los antecedentes contienen textos resolutivos y referencias individuales; no se implementa el motor 3:1 mediante movimientos fraccionarios.

El lint frontend permanece clasificado como limitación heredada por el builder `@angular-devkit/build-angular:tslint` ausente. La evidencia de pruebas y build debe registrarse por separado; no presentar ese lint como aprobado ni ampliar dependencias para ocultarlo.

## Evidencia de ejecución y cierre

La coordinación registró estos resultados reales el 12/10/2026 en [VERIFICACION_CARGA_SCRUM-77.json](VERIFICACION_CARGA_SCRUM-77.json). Carga, repetición, persistencia y HTTP reforzado se contrastaron con MySQL; recorridos reales de escritorio/360/414, ambos temas y teclado aprobados. Los hallazgos de identidad, filtros, contraste y modales quedaron corregidos. La auditoría integral final aprobó el cierre sin hallazgos abiertos.

| Control | Resultado y estado de verificación |
|---|---|
| Guardias reales | Perfil inválido y migración pendiente: salida 1, con conservación de los 48 esquemas/filas previos. |
| Preparación y preflight demo | core.0001_initial aplicada: una migración, 49 tablas y 34 registros de migración. Se conservó el cierre legado de 27 tablas/39 FKs, vacío antes de cargar. Repetición de preparación: cero migraciones y cero tablas legadas nuevas. |
| Carga inicial y manifiesto | Perfil/corte v1 confirmado: 162 referencias, 16 fichas institucionales, seis cuentas nuevas más cinco seed_demo, 11 usuarios/perfiles, cuatro marcadores EX_TRAVELER; tres causas Creado/dos Justificaciones, cuatro T01, siete expedientes/resoluciones históricos y ocho asientos con suma +1. Outbox vacío; sin notificaciones externas. |
| Repetición y recuperación | Manifiestos inicial/repetido idénticos: SHA-256 `b5d6fce4594c743926ae76f2c1703cc234edd8b305d4d250dba89b7b68a28eb8`. Los 49 hashes de esquema, filas y conteos permanecieron iguales; contador institucional 770017 y contador formal 2026=5. Ediciones/credenciales, colisiones y rollback se ensayaron en schemas MySQL UUID; la comparación live conservó las filas completas sin editar fixtures. |
| Persistencia sin reseed | MySQL cambió de contenedor, prefijos `5b793d5` → `e5e7116`, sobre `sgd_aveit_scrum77_demo_mysql_data`. Los 49 esquemas/filas/conteos coincidieron exactamente, sin ejecutar seed ni preparación entre mediciones. IDs completos y controles en el registro JSON. |
| Conciliación y HTTP | Cuatro integrantes por G57–G60 con NULL/6/5/4; cuatro condiciones explícitas, ocho asientos/+1, sin huérfanos y 59 restricciones FK revisadas. HTTP: 78 controles antes y 78 después de recrear; login por identifier, sin acreditar contraseña ni publicar secretos. |
| Regresión backend | **1008 pruebas verdes, 0 errores**, 618,46 s; cobertura 93,91% en 22 módulos, 2331 sentencias/142 sin cubrir. Ruff global y formato de 15 Python nuevos + serializer correctos; Django check y makemigrations sin cambios. |
| Navegador y frontend final | Login/RBAC, ranking 10+6/legajos, T01/aislamiento y board/tabla verificados en escritorio y 360/414, claro/oscuro y teclado. Modales contienen contenido y permiten scroll/Cerrar/Escape. **222 pruebas verdes, 0 errores**, 0,907 s; build 6fae4265931dc3f8, 7854 ms. [Evidencia UI](VERIFICACION_UI_SCRUM-77.md). |
| Auditoría y PO | Código/manifiestos/correcciones aprobados sin hallazgos; auditoría documental integral final aprobada sin hallazgos abiertos. CA77-00–08 verificados, categoría/rol/vigencia/facultades independientes. Quince protegidos conservados y comprobados por el auditor. Lint frontend exit 1 por builder TSLint heredado ausente, clasificado. |

Registro rector: [verificación de TS77.08–27](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827). Navegador y suites/build finales aprobados; CA77-07 cerrado por auditoría integral aprobada sin hallazgos abiertos.

## Ampliación posterior a UAT — TS77.44–46

UAT original aprobada por el usuario; main 73a2d8a integrado con las notificaciones centrales de PR #49. La preparación protegida aplicó cinco migraciones de calendario y conservó los datos previos (52 tablas finales). El seed del mismo perfil agregó cuatro Juniors G62/G63 de años 2/1: veinte fichas, quince cuentas/perfiles y 188 referencias. Las seis causas/cinco T01 observadas incluyen el alta de UAT; los cinco/cuatro fixtures originales y los ocho asientos/+1 se conservaron. La repetición produjo idénticos manifiestos, esquemas, filas y conteos.

Regresiones: 1064 backend verificados y 278 frontend verdes, cero errores; los ocho controles Compose se ejecutaron aparte con las configuraciones reales saneadas. Cobertura 93,91% en 22 módulos, build b03663973a049f50 correcto, Ruff/formato/Django/migraciones correctos. HTTP local: 111 controles esperados sin mutación. Navegador: filtro Junior, fichas años 1/2, permisos y feedback en login/T01/modales, teclado y 360 px verificados; auditoría final aprobada sin hallazgos. Lint conserva el builder TSLint heredado ausente. [Registro](VERIFICACION_AMPLIACION_SCRUM-77.json), [HTTP](evidencias/scrum77-ampliacion/http-local.json) y [capturas](VERIFICACION_UI_SCRUM-77.md#verificación-posterior-a-uat--ts774446).

## Correcciones y ampliación de PR #54 — TS77.47–59

La misma carga protegida incorpora diez historias avanzadas, conserva UAT y repite sin cambios: 272 referencias, quince causas fixture/dieciséis efectivas, once respaldos históricos y doce asientos con suma +1. Distribución efectiva: 4 Creado / 2 Justificando / 3 En revisión / 1 Pendiente de firma / 2 Pendiente de envío / 4 Emitidos. Los cuatro nuevos emitidos Junior aplican +2/-1/-2/+1; los ocho movimientos originales se conservan.

Mis Expedientes ofrece **Resoluciones aplicadas**, debajo del listado operativo, con **Ver resolución** para abrir el texto y los reglamentos persistidos. La ficha ofrece la misma consulta bajo los permisos vigentes. Saldo e historial provienen de la misma lectura del libro mayor; los antecedentes originales conservan su identidad histórica y los actos nuevos muestran su vínculo operativo acreditado. La fecha de registro histórico conserva su significado.

Resultado final: 1155 backend MySQL y 362 frontend verdes, 0 errores/omisiones; cobertura local 94,17% en 25 módulos y build local c8e0ecb245aa8807 correcto. HTTP local: 197 controles sobre veinte historiales y doce asientos, con las 52 tablas intactas. Navegador de escritorio/móvil y auditoría integral aprobados. El código 4b2f077 aprobó cuatro checks CI, cada evento con 1155 backend/362 frontend y build f650aba676820783. PR #54 abierta sin merge. [Evidencia y recuperación](VERIFICACION_CORRECCIONES_PR54.md).
