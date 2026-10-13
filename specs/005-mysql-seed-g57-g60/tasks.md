# Tareas — SCRUM-77 / S3-PO2

Referencia: [spec](spec.md), [plan técnico](plan.md) y [plan interdisciplinario](../../docs/gestion-proyecto/PLAN_IMPLEMENTACION_SCRUM-77_MYSQL_SEED_G57_G60.md). IDs TS77.01–43 conservados y TS77.44–46 agregados por autorización posterior a UAT. SCRUM-77 y ampliación TS77.44–46 completadas y auditadas, sin hallazgos abiertos. 1064 pruebas backend verificadas y 278 frontend verdes (0 errores), cobertura 93,91% en 22 módulos y build b03663973a049f50 correcto. Veinte fichas con cuatro Juniors; 188 referencias, carga aditiva y repetición estable sobre 52 tablas, conservando las altas de UAT. 111 controles HTTP locales y feedback central de PR #49 verificados. Lint mantiene la limitación TSLint heredada. [Registro de ampliación](../../docs/gestion-proyecto/VERIFICACION_AMPLIACION_SCRUM-77.json).

Tareas de 20–25 minutos. Cadencia general: una unidad por vez, TDD y pruebas pertinentes en verde. Después de autorizar los grupos TS77.40/34/41/42 y TS77.43/35/36/37/07, el usuario autorizó expresamente terminar TS77.09–27 con los subagentes necesarios y sin confirmaciones individuales; TS77.08 se incorpora como prerrequisito de carga. Se respetan dependencias y TDD; una ejecución MySQL y un runner Karma por vez. Esta autorización reemplaza la pausa por unidad de AGENTS.md para el cierre de SCRUM-77.

## Formalización autorizada

## Ampliación posterior a UAT — autorización del 12/10/2026

El usuario aprobó las pruebas UAT del conjunto original y pidió sincronizar con `main` e incorporar Juniors antes de preparar la PR. Se autoriza realizar ambas operaciones y su validación conjunta; se conserva el cierre histórico de TS77.01–43. Las evidencias previas de dieciséis socios no se atribuyen a la ampliación.

- [x] **TS77.44 Sincronizar main y preservar feedback PR #49 (25 min):** Respaldo recuperable, combinación de cambios sin pérdida de identidad/filtros/accesibilidad, migraciones protegidas y notificaciones centrales funcionales en local.
- [x] **TS77.45 Ampliar catálogo con Juniors (25 min):** Dos G62 de año 2 y dos G63 de año 1, cuatro cuentas SOCIO habilitadas, saldo cero; TDD de ampliación aditiva, conservación, colisión y repetición sobre MySQL.
- [x] **TS77.46 Verificar ampliación y auditar (25 min):** Regresión backend/frontend, build, HTTP/navegador, conciliación y repetición; documentación/cuentas actualizadas, chequeo PO y auditoría independiente sin hallazgos abiertos.

## Formalización original

- [x] **TS77.01 Registrar alcance autorizado y pendientes (20 min):** Datos sintéticos, límites de UI, antecedentes auditables y DP77-01/02 visibles. Mapa inicialmente pendiente y cerrado posteriormente mediante aclaración del PO.
- [x] **TS77.02 Formalizar spec, plan y seguimiento atómico (25 min):** RF/RNF en EARS, CA trazables y tareas registradas aquí y en TASK.md, sin editar notasPO ni Seguimiento de Proyecto.

## Implementación

- [x] **TS77.03 Configuración Docker demo aislada (20 min; CA77-00):** Archivo standalone con nombres, puertos loopback, mounts del checkout y volumen propio; MySQL/padrón explícitos. **Hecho cuando:** pruebas sobre configuración resuelta acreditan aislamiento frente al Compose habitual y variables genéricas, suite backend y auditoría verdes. No incluye arrancar servicios ni preflight MySQL autenticado.
- [x] **TS77.04 Preflight MySQL y grants (25 min; CA77-01):** Identificación del entorno, consulta autenticada por Django, health y permisos sobre base demo/tests, con pruebas. Evidencia detallada al final; las guardias de carga TS77.08 mantienen abierto CA77-01.
- [x] **TS77.05 DDL y cierre de FKs (25 min; CA77-01/02):** Bootstrap mínimo legado con tipos compatibles y sin operaciones destructivas. 27 tablas/39 FKs; evidencia al final. Aplicación protegida/repetición verificadas posteriormente en TS77.06.
- [x] **TS77.06 Verificar bootstrap vacío y repetido (25 min; CA77-01/02):** Aplicador protegido y esquema físico compatible; 30 pruebas de bootstrap (36 combinadas con DDL)/568 backend verdes. Demo preparada y repetida con FKs activas, sin creaciones ni migraciones al repetir. Evidencia al final.
- [x] **TS77.07 Catálogo y mapa de identidades (20 min; CA77-02):** [Catálogo v1](../../docs/gestion-proyecto/CATALOGO_DATOS_DEMO_SCRUM-77.md) puro aceptado tras TS77.37, con 16 identidades/cuatro por grupo, rangos/referencias/corte PO-SCRUM77-CORTE-01 y 62 oráculos verdes. G57 exviajero y G58/G59/G60 6/5/4, sin reservas managed ni carga. DP77-02/DEP77-02 cerrados; CA77-02 sigue abierto por manifiesto/carga/conciliación. [Evidencia](#verificación-de-ts774335363707).
- [x] **TS77.08 Guardias del seed (25 min; CA77-01/03):** Rechazar entorno/base/perfil/esquema inválidos sin escrituras.
- [x] **TS77.09 Propiedad de fixtures (25 min; CA77-03):** Registro persistente, referencias/namespace, unicidad y ejecución serializada.
- [x] **TS77.10 Usuarios y socios locales (25 min; CA77-02/03):** Coexistencia con seed_demo y conservación de credenciales/permisos.
- [x] **TS77.11 Grupos y socios institucionales (25 min; CA77-02):** G57–G60, subcomisiones e historial, sin equiparar PK; depende de DEP77-02 y del mapa aprobado.
- [x] **TS77.12 Causas simples y multisocio (25 min; CA77-04):** Workflow, número servidor y auditoría.
- [x] **TS77.13 T01 de dos solicitantes (25 min; CA77-04/06):** Borradores/emitidas, aislamiento y urgencia heredada.
- [x] **TS77.14 Plazos actuales y urgencias (25 min; CA77-04):** Dos etapas seed con fechas coherentes y regresión de los seis estados.
- [x] **TS77.15 Antecedentes históricos legados (25 min; CA77-04):** Resolución, expediente y movimientos individuales trazables.
- [x] **TS77.16 Segunda ejecución (25 min; CA77-03):** IDs/contador estables y ediciones conservadas.
- [x] **TS77.17 Colisión y fallo intermedio (25 min; CA77-03):** Rollback integral del DML, registro y contador formal.
- [x] **TS77.18 Conciliar SQL/API/manifiesto (20 min; CA77-02/04):** Relaciones y suma de puntos; límites de legajo explícitos.
- [x] **TS77.19 Persistencia sin reseed (25 min; CA77-05):** Nuevo contenedor, mismo volumen y mismos datos.
- [x] **TS77.20 Smoke login/permisos (20 min; CA77-06):** HTTP y perfiles reales de cuentas demo.
- [x] **TS77.21 Smoke ranking/legajo (25 min; CA77-06):** Filtros, empate, segunda página y saldos cotejados.
- [x] **TS77.22 Smoke T01/Mis Solicitudes (25 min; CA77-06):** Selección múltiple, borradores/emitidas y aislamiento.
- [x] **TS77.23 Smoke board/tabla (25 min; CA77-06):** HTTP 200, IDs y filtros contra DB, detectando fallbacks locales.
- [x] **TS77.24 Responsive y teclado (25 min; CA77-06):** Escritorio, 360/414 px, nombres largos, modales y badges.
- [x] **TS77.25 Regresión backend (25 min; CA77-07):** MySQL, cobertura de negocio exigida, Ruff y migraciones.
- [x] **TS77.26 Regresión frontend (25 min; CA77-07):** Suite/build con dependencias disponibles y fallos clasificados.
- [x] **TS77.27 Cierre documental y PO (20 min; CA77-07):** CA→evidencia, uso/recuperación y pendientes resueltos dentro del alcance.

## Adecuación por aclaración posterior del PO

TS77.28 registra la definición; TS77.29–43 resuelven DEP77-02 antes de TS77.07/10/11. Estas unidades no se declaran implementadas por recibir la respuesta. Secuencia definida por la revisión de impacto: 30 → 31 → 32 → 33 → 38 → 39 → 40 → 34 → 41 → 42 → 43 → 35 → 36 → 37 → 07.

- [x] **TS77.28 Registrar aclaración corregida y sincronizar SDD (20 min):** Fuentes, cierre DP77-01, G57 exviajero, Junior 1–2 / Senior 3+, evento de asamblea y diferencias frente al baseline; auditoría documental aprobada sin hallazgos abiertos.
- [x] **TS77.29 Revisar impacto y compatibilidad (25 min; CA77-08):** [Inventario y decisiones](../../docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md) de modelos, contratos, datos, permisos y pantallas; representación explícita de exviajeros, nulabilidad, transición demo e identidad de legajo. 568 pruebas de baseline verdes (0 errores) y auditoría independiente aprobada sin hallazgos pendientes. No implementa todavía CA77-08.
- [x] **TS77.30 Alinear documentación activa (20 min; CA77-08):** Reglas rectoras y referencias pertinentes alineadas con Junior/Senior y exviajeros, con antecedentes y facultades independientes preservados. 568 pruebas backend verdes (0 errores), controles documentales y auditoría aprobados; notasPO y seguimiento macro intactos. La implementación de CA77-08 sigue pendiente.
- [x] **TS77.31 Representar exviajeros (25 min; CA77-08):** Modelo local EX_TRAVELER/año nulo explícito, longitud 12, CHECK y migración managed nueva con guardias de avance/reversión. 594 pruebas backend verdes (0 errores) y auditoría integral aprobada. Migración demo aplicada/repetida, sin año ficticio ni deshabilitación automática; esquema legado y metadato institucional separados en TS77.38/39/40.
- [x] **TS77.32 Clasificación de socios operativos (25 min; CA77-08):** Junior en 1/2 y Senior en 3–6, independiente de vigencia/roles y con EX_TRAVELER/null conservado. Migración nueva sólo de choices, aplicada/repetida sin recategorizar filas históricas. 621 pruebas verdes (0 errores), cobertura local 97% y auditoría integral aprobada.
- [x] **TS77.33 Migrar categorías existentes (25 min; CA77-08):** Migración histórica por año/situación, incluido PASSIVE de 3.º→SENIOR, con validación previa, bloqueo y rollback DML en ambas direcciones. Conserva identidades, credenciales, vínculos, snapshots y saldos. 642 pruebas verdes (0 errores), cobertura de migración 100%, demo aplicada/repetida y auditoría integral aprobada; sin SQL manual de puntos.
- [x] **TS77.34 Alinear padrón/ranking y filtros backend (25 min; CA77-08):** Implementada; DTOs, mock/DB, proyección de legajo y ranking canónicos, EX_TRAVELER explícito/UNKNOWN separados, aliases sólo de entrada y filtros/count/paginación SQL sin N+1. Unmanaged nullable alineado con DDL ya aplicado, sin ALTER; excepción ORM temporal retirada. 53 casos propios incluidos en 827 pruebas verdes; cierre integral aprobado sin hallazgos pendientes. [Evidencia](#verificación-de-ts7740344142).
- [x] **TS77.35 Alinear contratos y filtros frontend (25 min; CA77-08):** Cuatro categorías canónicas y nulos, servicios/filtros y caché confirmado por me, sin reinterpretar JWT/aliases. Errores HTTP/red y sesiones tardías controlados; ranking abre legajo institucional. Incluida en 202 pruebas frontend verdes, con auditoría cruzada e integral aprobadas. Requiere TS77.42/43, completadas. [Evidencia](#verificación-de-ts774335363707).
- [x] **TS77.36 Actualizar etiquetas y datos demo existentes (25 min; CA77-08):** Ranking/selectores/modal/badges y mock canónicos, legajo nulo sin año ficticio; tokens DESIGN y 33 identidades/saldos mock conservados. seed_demo mantiene flujo/cuentas/credenciales/roles con ayuda/tipos ajustados y 8 casos verdes. 202 frontend verdes, build correcto y auditorías aprobadas; sin seed en demo real. [Evidencia](#verificación-de-ts774335363707).
- [x] **TS77.37 Verificar adecuación transversal (25 min; CA77-07/08):** 932 backend/202 frontend verdes (0 errores), cobertura 94,72%, build/checks correctos; lint heredado registrado. verify_ts7737 aprueba código/oráculos/diez documentos/PO sin hallazgos pendientes; CA77-08/DEP77-02 y CF77-01/02 cerrados. Preservación demo/protegidos comprobada; CA77-07 de toda la US permanece abierto. [Evidencia](#verificación-de-ts774335363707).
- [x] **TS77.38 Evolucionar contrato DDL demo (25 min; CA77-01/08):** anoSocial nullable sólo en el DDL demo; comparación íntegra con fuente permite exactamente tres adaptaciones. Cierre MySQL vacío/repetición y rechazo previo del contrato anterior, sin relajar bootstrap. 644 pruebas verdes (0 errores), auditoría integral aprobada; demo preparada, modelos, bootstrap y fuente intactos.
- [x] **TS77.39 Transicionar demo preparada (25 min; CA77-01/08):** Guardias/bloqueo, contrato anterior íntegro y ALTER acotado hacia el nuevo, preservando filas/IDs/contador/FKs. Repetición vacía y rechazo de divergencias; sin reset, limpieza ni DML de puntos/expedientes. 670 pruebas verdes (0 errores), demo aplicada/repetida y auditoría integral aprobada sin hallazgos pendientes. [Evidencia](#verificación-de-ts7739). Requiere TS77.38.
- [x] **TS77.40 Condición institucional explícita (25 min; CA77-08):** Implementada; metadato managed por nroSocio real, fuente/corte, PK/CHECK y escritor transaccional idempotente sin FK hacia socio_lista. 37 casos y bootstrap anterior al legado incluidos en 827 pruebas verdes; 0005 aplicada/repetida. Huérfanos, referencia ajena, contradicciones, duplicados y mutaciones masivas rechazados; propiedad/manifiesto del seed siguen en TS77.09/11. Cierre integral aprobado sin hallazgos pendientes. [Evidencia](#verificación-de-ts7740344142).
- [x] **TS77.41 Integrar clasificación en T01 (25 min; CA77-04/08):** Implementada; EX_TRAVELER/null sin año ficticio, identidad institucional inequívoca mediante user_id único o legajo real corroborado, sin atajo por PK local. Conserva datos, credenciales/rol/vigencia y snapshots históricos; rollback integral de emisión y rechazo de legajo ambiguo. 36 casos incluidos en 827 pruebas verdes; cierre integral aprobado sin hallazgos pendientes. [Evidencia](#verificación-de-ts7740344142).
- [x] **TS77.42 Actualizar claims y perfil servidor (25 min; CA77-08):** Implementada; refresh relee categoría del socio actual y conserva otros claims y opciones JWT, con login/me canónicos y RBAC independiente. 30 casos incluidos en 827 pruebas verdes; 3 rotaciones adicionales con blacklist real en proceso aislado, sin cambiar settings/dependencias. SPA completada posteriormente en TS77.35; cierre integral aprobado sin hallazgos pendientes. [Evidencia](#verificación-de-ts7740344142).
- [x] **TS77.43 Resolver identidad del legajo (25 min; CA77-06/08):** identity_source explícito sólo identifica PK local/nroSocio institucional, sin fallback por otra fuente/legajo. Fuente inválida/repetida 400, ambigüedad sin fuente 404 genérico y llamadas antiguas inequívocas conservadas. Propiedad institucional real, legajo ausente null, lectura sin sincronizar/cambiar roles/vigencia/saldos. 33 casos nuevos y dos BIGINT incluidos en 932 pruebas verdes, auditoría integral aprobada. Requiere TS77.34, completada. [Evidencia](#verificación-de-ts774335363707).

## Verificación de la primera tarea

Completada TS77.03 el 10/10/2026. Artefactos: [Compose demo](../../docker-compose.scrum77-demo.yml), [pruebas](../../backend/tests/infrastructure/test_scrum77_compose.py) y [guía](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Control | Evidencia |
|---|---|
| TDD rojo | 8 errores por ausencia del archivo demo antes de implementarlo, 0,44 s. |
| Compose resuelto | config --quiet correcto; modelos base/demo/demo con variables conflictivas generados inmediatamente por Docker Compose 2.40.3 y saneados antes de inyectarlos. |
| Pruebas enfocadas | **8 passed, 0 errores**, 0,20 s; sin omisiones. |
| Suite backend | **498 passed, 0 errores**, 104,00 s; MySQL real y base de pytest separada, backend montado desde este checkout, snapshot y checkout completo en la misma ejecución. |
| Ruff | ruff check . correcto; ruff format --check tests/infrastructure/test_scrum77_compose.py correcto. |
| Auditoría independiente | audit_scrum77_implementation: sin hallazgos P1/P2 abiertos. Corregida la omisión condicionada para contenedores sin checkout completo; éstos no acreditan CA77-00 por sí solos. |
| Consistencia PO | En el cierre inicial de TS77.03, comprobadas notas del 07/10, sección 7, y límites de infraestructura; DP77-01 aún estaba pendiente. Se cierra posteriormente en TS77.28. Sin cambios a notasPO ni Seguimiento de Proyecto. |

La suite se ejecutó en un contenedor temporal de pruebas con mount explícito, sin reemplazar los servicios activos. Al cerrar TS77.03, CA77-00 quedó verificado; CA77-01–08, TS77.04–27 y la adecuación TS77.29–37 seguían abiertos, sin arranque de demo, preflight, bootstrap ni seed. El avance posterior del preflight se registra en el cierre de TS77.04.

TS77.04 fue autorizada posteriormente por el usuario; su cierre se registra a continuación.

## Verificación de la aclaración corregida

TS77.28 completada: versión definitiva del PO registrada, DP77-01 cerrado y adecuación técnica DEP77-02 pendiente. Verificadas 43 referencias locales, los 37 IDs/estados de tareas sincronizados y git diff --check correcto. Auditoría independiente audit_scrum77_implementation aprobada, sin hallazgos abiertos; corregida la tabla para no confundir condición exviajero con una decisión de enum técnico.

Esta revisión es documental. No se modificó código ni se ejecutó una nueva suite; la evidencia de 498 pruebas corresponde al cierre previo de TS77.03 y no acredita CA77-08. TS77.29–37 siguen sin implementar; las Notas del PO, la constitución y el seguimiento macro permanecen inalterados en esta revisión.

## Verificación de TS77.04

Completada el 10/10/2026, por autorización del usuario. Artefactos: [comando](../../backend/core/management/commands/check_demo_mysql.py), [pruebas](../../backend/tests/infrastructure/test_mysql_demo_preflight.py) y [guía de ejecución](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Control | Evidencia |
|---|---|
| TDD inicial | 30 errores por ausencia del comando antes de implementarlo, 1,09 s. |
| TDD de corrección auditada | 3 fallos y 1 caso verde antes de impedir proxies/redirecciones y rechazar una URL efectiva ajena; servidor HTTP loopback real. |
| Pruebas enfocadas | **34 passed, 0 errores**, 1,91 s. |
| MySQL real | `SELECT 1` por Django; base `aveit_tribunal_scrum77_demo`, usuario `aveit_dev@%`, servidor MySQL 8.0.46, STRICT_TRANS_TABLES, utf8mb4/utf8mb4_0900_ai_ci, FKs activas y grants demo/tests acreditados. |
| HTTP real | Endpoint loopback del mismo contenedor y puerto host 8002: HTTP 200, status ok/db connected. Preflight también correcto con HTTP_PROXY conflictivo y NO_PROXY vacío en una invocación efímera. |
| Rechazos reales | Credencial de prueba inválida y base ajena: exit 1, mensajes de diagnóstico sin contraseñas ni detalles de conexión. No se cambiaron variables del servicio activo. |
| Aislamiento | Docker inspect confirma mounts de este checkout, red `sgd-aveit-scrum77-demo_default` y volumen `sgd_aveit_scrum77_demo_mysql_data`; recursos habituales de otro checkout siguen saludables. |
| Suite backend final | **532 passed, 0 errores**, 85,41 s, sin omisiones. MySQL demo real y base `test_aveit_tribunal_scrum77_demo` separada; snapshot Compose saneado recién generado y checkout completo en la misma ejecución. |
| Sin bootstrap/seed | Tras pytest, la base demo conserva 0 tablas y la base temporal de pruebas ya no existe. El comando sólo consulta; la carga y el esquema siguen pendientes. |
| Ruff | ruff check . correcto; ruff format --check core/management tests/infrastructure correcto, 5 archivos. |
| Auditoría independiente | audit_scrum77_implementation: revisión final favorable; P2 de HTTP corregido y verificado, y P3 documental corregido en el cierre de TS77.03 de TASK.md. Sin hallazgos abiertos. |
| Consistencia PO | Verificadas notas del PO, sección 7, RF77-03/RNF77-01/02/03/06 y aclaración corregida. La tarea verifica conectividad Docker/MySQL sin modificar clasificación, socios, saldos ni expedientes; notasPO, constitución y seguimiento macro intactos. |

TS77.04 queda completada. CA77-01 continúa abierto: faltan esquema físico y guardias de carga de las tareas correspondientes. No se declara listo el seed ni se cierra la US completa. DEP77-02 y TS77.29–37 siguen pendientes.

TS77.05 fue autorizada posteriormente por el usuario; su cierre se registra a continuación.

## Verificación de TS77.05

Completada el 11/10/2026 por autorización del usuario. Artefactos: [DDL](../../backend/core/sql/scrum77_legacy_schema.sql), [mapeo y decisiones](../../docs/gestion-proyecto/MAPEO_ESQUEMA_DEMO_SCRUM-77.md), [pruebas](../../backend/tests/infrastructure/test_scrum77_legacy_ddl.py) y [guía](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Control | Evidencia |
|---|---|
| TDD rojo | 1 fallo y 5 errores por ausencia del DDL antes de crearlo, 0,59 s. |
| Cierre mínimo | 27 CREATE TABLE y 39 FKs: ocho raíces unmanaged de padrón/ranking y todos sus destinos transitivos. auth_user queda externo, creado por migraciones Django. Incluye destinos de relaciones nullable. |
| Adaptación documentada | Sólo puntos y puntajeAplicado pasan de DOUBLE fuente a DECIMAL(10,2), conforme a sus modelos vigentes. No se altera información existente ni se cambian reglas de puntos. |
| Pruebas enfocadas | **6 passed, 0 errores**, 8,52 s. Fuente/orden/creación exclusiva, FKs físicas, tipos compatibles, nulabilidad, precisión, autoincremento, PK/unicidad y rechazo de movimiento huérfano con error MySQL 1452. |
| Ensayo MySQL aislado | Esquema aleatorio propio test_scrum77_ddl_<10 hex>, separado de aplicación y pytest. Migraciones reales y SHOW CREATE TABLE auth_user idéntico antes/después. InnoDB/utf8mb4 y FK checks activos, sin helpers de esquema reducido en el ensayo. |
| Suite backend final | **538 passed, 0 errores**, 107,80 s, sin omisiones. MySQL real, base de pytest separada, checkout completo y snapshot Compose saneado recién generado. |
| Limpieza y demo | SELECT posterior: 0 tablas en la base demo y ningún esquema temporal de DDL/pytest restante. Preflight autenticado y health continúan correctos en MySQL 8.0.46. |
| Controles | ruff check . correcto; ruff format --check core/management tests/infrastructure correcto (6 archivos); makemigrations --check --dry-run sin cambios; git diff --check correcto. |
| Auditoría independiente | audit_scrum77_implementation: código, SQL y correspondencias revisados; sin hallazgos. |
| Consistencia PO | Contraste inicial, durante la extracción y final con notasPO, sección 7, RF77-03/04/09 y RNF77-01/02/03/06. Sin datos, permisos nuevos, cambios societarios, saldos o expedientes. NotasPO, constitución, seguimiento macro, SQL fuente, modelos y dependencias intactos. |

Esta tarea entrega el DDL revisable y su evidencia de compatibilidad. No incluye aplicar migraciones/DDL a la demo, preparar una segunda ejecución o implementar su aplicador: TS77.06 continúa pendiente. CA77-01/02 y la US completa siguen abiertos; seed, DEP77-02 y TS77.29–37 no se iniciaron.

TS77.06 fue autorizada posteriormente por el usuario; su cierre se registra a continuación.

## Verificación de TS77.06

Completada el 11/10/2026 por autorización del usuario. Artefactos: [comando protegido](../../backend/core/management/commands/prepare_demo_schema.py), [contrato y aplicador](../../backend/core/demo_schema.py), [pruebas](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py), [aislamiento de migraciones en pruebas](../../backend/tests/infrastructure/scratch_routing.py), [guía](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md) y [mapeo](../../docs/gestion-proyecto/MAPEO_ESQUEMA_DEMO_SCRUM-77.md).

| Control | Evidencia |
|---|---|
| TDD inicial | 21 fallos y 5 errores por ausencia del comando/aplicador, 7,49 s. |
| Correcciones auditadas | P2: tablas sin historial Django causaban error 1050 después de iniciar migraciones; pruebas rojas para auth_user y el through expedientes_expediente_socios. Validación de historial y colisiones CreateModel/AddField M2M antes de migrate; snapshot intacto al rechazar, sin fake-initial. |
| Aislamiento de RunPython | Oráculo rojo: contador técnico ausente en el esquema propio pese a migrate satisfactorio. Corregidas las fixtures TS77.05/06 para dirigir default temporalmente al esquema del ensayo y bloquear fugas de consultas de expedientes a la conexión padre. Restauración en finally; contador local last_value=0 acreditado, sin modificar migraciones existentes. |
| Pruebas enfocadas finales | **36 passed, 0 errores**, 45,58 s: 30 de bootstrap y 6 de DDL. Desde vacío/repetido, filas e IDs conservados, parcial compatible, once divergencias físicas, FKs/acciones/unicidad/precisión, referencia a otra base, auth externo, colisión M2M, bloqueo concurrente y fallo intermedio recuperable. |
| Validación previa | Todas las tablas legadas presentes comparadas íntegramente contra el DDL: columnas/orden, tipos/signo, null/defaults/autoincremento, charset/collation efectivos, PK/índices/unicidad y FKs/acciones. Identidad/PK de auth_user e historial/colisiones managed controlados por separado; no se acredita el contrato íntegro de las demás tablas managed. Definiciones desconocidas, vistas y referencias ajenas rechazadas sin reparación. Autocommit y FKs activas; preparación serializada mediante GET_LOCK. |
| Demo vacía → preparada | MySQL 8.0.46, base aveit_tribunal_scrum77_demo, mount de este checkout y volumen propio. Antes: 0 tablas. Primera ejecución del comando: 29 migraciones Django y 27 creaciones legadas; después: 47 tablas totales y 39 FKs legadas físicas con tipos compatibles y destinos dentro de la base. |
| Segunda preparación real | created_tables vacío, migrations_applied=0, 27 tablas existentes compatibles. SHOW CREATE TABLE y cantidades de todas las tablas conservaron los hashes de la primera preparación; django_migrations mantiene 29 filas. |
| Huellas de la repetición final | Esquema: 3dc1dda89d35ee1d972cd190e48370d96abfaa0579493066e750b04a3bac6e80. Cantidades: 147866e3ad633e59cd582a1dd6454d87f640af13aaf0a8bc478e41295d7d885c. Comparación íntegra de SHOW CREATE TABLE y cantidades por tabla antes/después de repetir: sin cambios. |
| Sin catálogo fixture | 27 tablas legadas vacías; auth_user, socios, expedientes, solicitudes y notificaciones sin filas. Las migraciones normales crean sus metadatos/permisos y el contador técnico inicial mediante expedientes.0005; no se ejecutó seed, no se emitieron causas ni movimientos. |
| Suite backend final | **568 passed, 0 errores**, 147,25 s, sin omisiones. MySQL real, base de pytest separada, checkout completo y snapshot Compose saneado recién generado. |
| Limpieza y diagnóstico final | Ningún esquema temporal test_scrum77_bootstrap, test_scrum77_ddl o pytest restante. Nueva repetición final con created_tables vacío y migrations_applied=0, 47 tablas y 0 filas de usuarios/socios/expedientes/legado; contador técnico inicial en cero. Contratos legados y PK auth correctos, migrate --check sin pendientes y preflight/health correctos; FKs activas, modo estricto y grants demo/tests vigentes. |
| Controles | ruff check . correcto; ruff format --check core/demo_schema.py core/management tests/infrastructure correcto (10 archivos); makemigrations --check --dry-run sin cambios; git diff --check correcto. |
| Auditoría independiente | audit_scrum77_implementation: cierre integral aprobado, sin hallazgos abiertos. Corregidos P2 de colisiones managed/M2M y aislamiento de RunPython, junto con ajustes documentales. Revisados código, evidencia final y sincronización de seguimiento; auditoría en lectura, sin ejecutar pruebas ni mutaciones. |
| Consistencia PO | Contraste inicial, durante implementación y final con notasPO sección 7 y RF77-03/04, RNF77-01/02/03/06. Sin clasificaciones nuevas, datos ficticios, facultades, saldo o expediente modificado manualmente. NotasPO, constitución, seguimiento macro, SQL fuente, modelos, migraciones y dependencias intactos. |

TS77.06 queda completada. El esquema ya está preparado, pero CA77-01 conserva pendientes las guardias de carga TS77.08 y CA77-02 depende del catálogo/seed y DEP77-02. La repetición probada es del bootstrap de esquema; la idempotencia del catálogo sigue en TS77.16. No se cierra la US completa ni se inicia la carga o la adecuación societaria.

Antes de TS77.07 hay que resolver DEP77-02, comenzando por TS77.29 (impacto y compatibilidad). Se requiere confirmación para esa próxima unidad según AGENTS.md.

TS77.29 fue autorizada posteriormente por el usuario; su cierre se registra a continuación.

## Verificación de TS77.29

Revisión completada el 11/10/2026 por autorización del usuario. Artefacto: [impacto y decisiones de compatibilidad](../../docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md). Se conservan los requisitos de negocio aprobados; las decisiones técnicas se sincronizan en plan y seguimiento, sin implementar las unidades dependientes.

| Control | Evidencia |
|---|---|
| Descubrimiento | Índice seminario-integrador del checkout correcto, search_graph/get_code_snippet/trace_path/search_code y contraste de fuentes. Inventario de modelos, migraciones, DTOs, JWT/perfil/caché, roles/vigencia, SQL, filtros, T01, mocks, seed, UI y documentación. |
| Representación decidida | JUNIOR/SENIOR/EX_TRAVELER, UNKNOWN sólo para lectura institucional anómala; exviajero explícito/año nulo y category ampliado a 12. Metadato institucional por nroSocio con procedencia y asociación verificadas; cargo/estado/año inválido no identifican exviajero. |
| Compatibilidad decidida | Datos recalculados por año/situación, aliases sólo en consultas con semántica nueva, SPA/backend coordinados, perfil antiguo consultado mediante me y refresh desde servidor. Legajo con fuente explícita y rechazo genérico de ambigüedad; snapshots históricos conservados. Roles/vigencia/saldos separados. |
| Dependencias descubiertas | anoSocial NOT NULL requiere contrato/transición demo; modelo unmanaged no lo migra. EX_TRAVELER excede longitud 10. T01 usa año or 1; legajo prioriza PK local ante un ID institucional y usa legajo artificial si falta el real. La caché no contiene año y un JWT viejo puede mantener el claim anterior. TS77.38–43 desglosan esas dependencias y quedan pendientes. |
| MySQL físico, sólo lectura | Demo conserva 47 tablas. socio_lista.anoSocial INT NOT NULL; socios_socio.social_year SMALLINT UNSIGNED NOT NULL; category VARCHAR(10) NOT NULL. auth_user, socios_socio, socio_lista y socio_tipoSocio sin filas. No quedan esquemas temporales de pytest/DDL/bootstrap. No se ejecuta ALTER ni carga en esta tarea. |
| Suite backend | **568 passed, 0 errores**, 147,19 s, sin omisiones. Nueva ejecución MySQL con pytest separado, checkout completo y snapshot Compose saneado recién generado. Verifica baseline conservado, no la clasificación futura de CA77-08. |
| TDD | No corresponde agregar pruebas de comportamiento futuro en una tarea de revisión documental. Cada unidad de código pendiente mantiene TDD y sus oráculos explícitos. No se modifican código ni tests en TS77.29. |
| Auditoría independiente | audit_scrum77_implementation: cierre documental aprobado, sin hallazgos pendientes. Incorporadas identidad explícita de legajo, excepción de snapshots históricos y corrección de su enlace de propiedad. Auditoría en lectura, sin ejecutar pruebas ni mutaciones. |
| Control documental | Referencias locales existentes, 43 IDs/estados sincronizados entre tasks.md y TASK.md, y git diff --check correcto. Sólo TS77.29 se cierra en esta unidad; TS77.30–43 siguen pendientes. |
| Consistencia PO | Junior 1/2, Senior desde 3 dentro de la escala y G57 exviajero explícito; grupos del corte confirmado, asamblea variable y ninguna atribución nueva por clasificación. Firma/elegibilidad requieren fuente propia en sus US, fuera de este alcance; no bloquean clasificación. NotasPO, constitución, seguimiento macro, código, SQL, modelos, migraciones y dependencias intactos en esta unidad. |

DEP77-02 y CA77-08 siguen abiertos: TS77.29 decide el cómo, no implementa la adecuación ni habilita el seed. La próxima unidad es TS77.30, con confirmación antes de iniciarla.

TS77.30 fue autorizada posteriormente por el usuario; su cierre se registra a continuación.

## Verificación de TS77.30

Actualización documental autorizada el 11/10/2026 y completada el 12/10/2026. Alcance y documentos en el [informe de impacto actualizado](../../docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md). No se modifican código, modelos, migraciones, DDL ni dependencias.

| Control | Evidencia |
|---|---|
| Reglas vigentes | Constitución, spec 001, ADR, ERS, modelo, actores y referencias activas usan Junior 1.º–2.º / Senior desde 3.º dentro de la escala y G57 exviajero fuera de ella. Corte 6/5/4 y referencia G63=1, mismo año por grupo y asamblea variable conservados; sin avance anual automático. |
| Facultades independientes | DP77-FAC-01 registra elegibilidad/firma del TD y presidencia de subcomisiones en sus US. No se asigna una facultad por ser Senior o exviajero; roles, vigencia y saldo permanecen separados. |
| Antecedentes | SRC77-BASE-01 referencia el commit/antecedente de la constitución. Plan/tareas de Sprint 1, §6 del ADR, backlog anterior y legado están delimitados como históricos; citas del relevamiento, historial de versiones y exportaciones binarias conservados. |
| TDD / alcance | Unidad exclusivamente documental: sin tests nuevos de comportamiento futuro. Las unidades TS77.31–43 mantienen TDD y sus oráculos; no se declara implementada la adecuación por cambiar estos documentos. |
| Suite backend | **568 passed, 0 errores**, 153,85 s, sin omisiones. Nueva ejecución con MySQL real, base de pytest separada, checkout completo y snapshot Compose recién generado/saneado. Acredita el baseline conservado, no la clasificación futura de CA77-08. |
| Control documental | 197 referencias locales existentes y 43 IDs/estados sincronizados; git diff --check correcto. 394 archivos backend/frontend y notasPO/Seguimiento/AGENTS conservan los hashes del inicio. Normas fuente y exportaciones binarias sin diff. Referencias absolutas antiguas a DESIGN reparadas en la ERS del Tribunal y los escenarios de calidad; vistas Mermaid/PlantUML y diccionario coherentes, citas originales e historial preservados. |
| Auditoría independiente | audit_scrum77_implementation: cierre aprobado sin hallazgos pendientes, en lectura y con umlConsistency para modelo/diccionario/trazabilidad. Corregidas las dos filas de denominacion de faltas/causales alcanzadas accidentalmente por un selector amplio y las referencias/figura del TPI; sólo CategoriaSocio conserva la descripción nueva. No se ejecutaron pruebas ni mutaciones desde el auditor. |
| Consistencia PO | RN77-01–04 y notasPO, sección 7, contrastadas al inicio/durante/cierre. Notas del PO, seguimiento macro, normas fuente y exportaciones históricas conservan su contenido. |

CA77-08 y DEP77-02 permanecen abiertos. La próxima unidad es TS77.31, representación local de exviajeros con TDD, previa confirmación según AGENTS.md.

## Verificación de TS77.31

Completada el 12/10/2026 por confirmación expresa del usuario, con auditoría integral aprobada sin hallazgos pendientes. Artefactos: [modelo](../../backend/socios/models.py), [migración managed nueva](../../backend/socios/migrations/0002_ex_traveler_representation.py), [pruebas del modelo](../../backend/tests/test_socios_ex_traveler.py), [ensayos de migración](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) y [guía demo](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Riesgo / regla | Nivel y oráculo verificable |
|---|---|
| RN77-01: exviajero fuera de la escala | Modelo + MySQL: EX_TRAVELER/null explícito, etiqueta Exviajero; rechazar año ficticio o null sin condición. |
| Vigencia y rol independientes | Persistencia de exviajeros habilitados/deshabilitados y roles distintos; conversión conserva cuenta, credenciales, identidad y subcomisión. |
| Escrituras parciales inconsistentes | save(update_fields): categoría/año se guardan juntos cuando se selecciona uno; modificar nombre conserva la clasificación persistida no seleccionada. |
| Eludir save / comparación tolerante | CHECK físico: rechazar año 0/7, null fuera del marcador, marcador con año, minúsculas y espacio final; refresh confirma la fila anterior intacta. |
| Historia o reversión incompatibles | MigrationExecutor + SHOW CREATE: precondición rechaza años 0/7 antes de DDL; retroceso rechaza null y categoría larga antes de quitar CHECK/reducir columnas. Reversión compatible conserva filas y vuelve a nulabilidad/longitud previas. |
| Pérdida de identidad o relaciones | Migración 0001→0002 sobre filas previas: igualdad de datos del socio/usuario, credenciales, expediente y vínculos M2M; permite luego persistir EX_TRAVELER/null. |

| Control | Evidencia |
|---|---|
| TDD inicial del modelo | **11 failed / 17 passed**, 8,82 s, antes de implementar: año nulo rechazado, marcador sobrescrito y rango 0/7 permitido al omitir save. Casos adicionales del marcador exacto agregados antes de la restricción. |
| TDD de migración | La prueba de conservación y dos casos históricos 0/7 fallaron por ausencia de la migración nueva antes de crearla. Sólo se agrega 0002; la migración aplicada 0001 permanece intacta. |
| TDD de reversión | **2 failed**, 6,31 s: MySQL fallaba por NULL/truncamiento después de comenzar el retroceso. Guardia de lectura agregada antes de toda operación inversa; ambos rechazos quedan verdes conservando SHOW CREATE y filas. |
| Casos enfocados | 72 casos de socios, exviajeros, bootstrap y DDL incluidos en la suite final verde. Ejecución enfocada inicial: 71 passed/1 fallo de fixture; referencia entre versiones históricas de Subcomision corregida usando su PK, caso aislado **1 passed**, 6,83 s. |
| Suite backend final | **594 passed, 0 errores**, 153,15 s, sin omisiones. MySQL 8.0.46, base de pytest separada y ensayos UUID propios, checkout completo y snapshot Compose recién generado/saneado. 26 casos nuevos frente al baseline de 568. |
| Ruff / Django | ruff check . correcto; check y format --check sobre los cuatro archivos modificados/nuevos correctos. makemigrations --check --dry-run: sin cambios detectados; manage.py check: 0 problemas. |
| Demo física | Preflight autenticado correcto y prepare_demo_schema aplica **1 migración**, crea **0 tablas** y conserva las **27 tablas legadas/39 FKs**. 47 tablas totales, 30 registros de migración; category VARCHAR(12), social_year nullable y CHECK enforced. 0 usuarios/socios locales y tablas legadas vacías, sin seed. |
| Conservación / repetición | Hashes de las 27 tablas legadas intactos; cambios de definición sólo en socios_socio y contador AUTO_INCREMENT del nuevo registro en django_migrations. Cantidades de filas iguales salvo el historial de migraciones. Segunda preparación: 0 migraciones/0 tablas, los 47 hashes y todas las cantidades idénticos. |
| Alcance | De 394 archivos backend/frontend preexistentes, cambian únicamente socios/models.py y el archivo de ensayos de bootstrap; se agregan la migración 0002 y las pruebas de exviajeros. Sin cambios a padrón, DTOs, T01, JWT, frontend, DDL legado ni migraciones aplicadas. NotasPO, seguimiento macro y AGENTS conservan sus hashes. |
| Control documental | 222 referencias locales válidas, 43 IDs/estados sincronizados y git diff --check correcto; 396 archivos backend/frontend después de agregar los dos archivos de la unidad. Fuentes normativas y exportaciones históricas sin diff. |
| Auditoría independiente | audit_scrum77_implementation: cierre integral aprobado sin hallazgos pendientes. Revisión en lectura de modelo, CHECK, migración, oráculos y evidencia; control independiente de 43 IDs/estados y 10 hashes protegidos de notas, normas y exportaciones. P3 de estados en alcance/secuencia/tabla del plan corregidos y revisados; el auditor no ejecutó pruebas ni mutaciones. |
| Consistencia PO | RN77-01–04, principio 8 y notasPO §7 contrastados al inicio/durante/cierre. Exviajero explícito fuera de la escala, sin año 0/7 ni deshabilitación o facultad automática. La representación institucional y el nuevo cálculo mantienen sus unidades propias. |

El enum/corte PASSIVE/ACTIVE se conserva transitoriamente para los socios de la escala hasta TS77.32; esta unidad no recategoriza datos existentes. socio_lista.anoSocial sigue NOT NULL; su evolución, transición demo y metadato institucional permanecen en TS77.38/39/40. CA77-08 y DEP77-02 continúan abiertos. La siguiente unidad es TS77.32, previa confirmación según AGENTS.md.

## Verificación de TS77.32

Completada el 12/10/2026 por confirmación expresa del usuario, con auditoría integral aprobada sin hallazgos pendientes. Artefactos: [modelo](../../backend/socios/models.py), [migración de opciones 0003](../../backend/socios/migrations/0003_local_social_categories.py), [pruebas locales](../../backend/tests/test_socios.py), [exviajeros](../../backend/tests/test_socios_ex_traveler.py), [ensayo de migración](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) y [guía demo](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Riesgo / origen | Nivel y oráculo verificable |
|---|---|
| RN77-04 / CA77-08: corte por año | Helper sin I/O y persistencia MySQL: 1/2→JUNIOR, 3/4/5/6→SENIOR, con etiquetas Junior/Senior. |
| D77-01: clasificación fuera de escala | Helper rechaza None, -1/0/7, bool, float y cadena con ValidationError por año. Modelo conserva validación/coerción Django; un año inválido no determina EX_TRAVELER. |
| RNF77-04: roles/vigencia independientes | Socios con años, roles y habilitaciones distintos conservan esos atributos. Cambio 2↔3 mantiene IDs, credenciales, usuario y subcomisión. |
| D77-01: escritura parcial o etiqueta proporcionada | Seleccionar sólo categoría o año guarda el par completo en ambas direcciones 2↔3; el año prevalece sobre una etiqueta. Guardar únicamente nombre mediante update_fields no recategoriza un PASSIVE histórico persistido; un save completo incluye clasificación. |
| RN77-01: condición exviajero | 20 casos de TS77.31 conservados y adecuados al enum local canónico: EX_TRAVELER/null persiste y sus combinaciones inválidas siguen rechazadas. |
| D77-04: confundir choices con recálculo histórico | MigrationExecutor 0002→0003 mantiene PASSIVE3/ACTIVE6/EXnull, filas exactas, usuarios/credenciales, expediente/M2M y SHOW CREATE salvo historial. Un save seleccionado posterior usa SENIOR; revertir choices conserva los códigos persistidos. |

| Control | Evidencia |
|---|---|
| TDD rojo del modelo | **29 failed / 7 passed**, 8,10 s, antes de implementar el enum/corte/validación. Casos fallan por nomenclatura anterior, corte de año 3 e interpretación de entradas fuera de escala. |
| TDD de migración | **1 failed**, 7,15 s, por ausencia de 0003 antes de crearla. Se genera una nueva migración sólo de choices; 0001/0002 aplicadas permanecen intactas. |
| Pruebas enfocadas / cobertura | **109 passed, 0 errores**, 72,48 s, sin omisiones. socios.models: **97%** de cobertura de sentencias, 68 sentencias/2 sin cubrir correspondientes a __str__; las reglas y guardias de clasificación se ejecutan. |
| Regresión y corrección | Primera regresión: 620 passed/1 fallo, 150,06 s, por expectativa ACTIVE/Activo en un legajo local de año 5. Corregida a SENIOR/Senior; caso aislado **1 passed**, 4,42 s. Las expectativas del padrón institucional se conservan para su tarea. |
| Suite backend final | **621 passed, 0 errores**, 155,30 s, sin omisiones. MySQL 8.0.46 real, base separada de pytest y scratch UUID propios, checkout completo y snapshot Compose recién generado/saneado. 27 casos adicionales frente a TS77.31. |
| Ruff / Django / SQL de migración | ruff check . correcto; check/format --check de los siete archivos cambiados/nuevo correctos. makemigrations --check --dry-run sin cambios; manage.py check sin problemas. sqlmigrate socios 0003 informa **no-op físico**. |
| Demo / repetición | Preflight autenticado correcto; prepare_demo_schema aplica **1 migración** y crea **0 tablas**. 47 tablas y 31 registros de migración; sólo cambia registro/contador de django_migrations. Hashes de todos los esquemas de negocio iguales y conteos sin cambios; 27 tablas legadas vacías/39 FKs conservadas, 0 usuarios/socios locales y sin seed. Segunda ejecución: 0 migraciones/creaciones, 47 hashes y todos los conteos idénticos. |
| Alcance | De 396 archivos backend/frontend preexistentes, cambian el modelo y cinco archivos de pruebas; se agrega únicamente la migración 0003. Sin cambios al código de padrón, cuentas, T01, frontend, DDL legado ni migraciones aplicadas. Constitución, notasPO, seguimiento macro y AGENTS conservan sus hashes. |
| Control documental | 236 referencias locales válidas, 43 IDs/estados sincronizados y git diff --check correcto. 397 archivos backend/frontend al cierre; 390 preexistentes mantienen sus hashes. Sólo TS77.32 pasa a completada; TS77.33–43 y tareas del seed siguen pendientes. |
| Auditoría independiente | audit_scrum77_implementation: cierre integral aprobado sin hallazgos pendientes. Revisión de código, oráculos, evidencia y documentación; 43 estados coincidentes y 10 hashes protegidos conservados. Auditoría en lectura, sin pruebas ni mutaciones propias. |
| Consistencia PO | RN77-01/04, constitución ppio. 8 y notasPO §7 contrastados al inicio/durante/cierre. Junior 1–2, Senior 3–6 dentro de escala, exviajero explícito fuera de ella; sin derivar vigencia, cargo, facultades o saldo desde la categoría. |

Las filas históricas pueden mantener PASSIVE/ACTIVE hasta TS77.33 o una escritura explícita de clasificación. La reversión de 0003 sólo restaura opciones del estado Django: conserva códigos almacenados y no promete restaurar automáticamente nomenclatura/corte anteriores. La integración de padrón/ranking/filtros, snapshots institucionales, tokens históricos y SPA mantiene sus unidades; CA77-08 y DEP77-02 siguen abiertos hasta la adecuación transversal. Próxima unidad TS77.33, previa confirmación según AGENTS.md.

## Verificación de TS77.33

Completada el 12/10/2026 por confirmación expresa del usuario, con auditoría integral aprobada sin hallazgos pendientes. Artefactos: [migración histórica nueva 0004](../../backend/socios/migrations/0004_recalculate_social_categories.py), [ensayos MySQL](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py), [estrategia técnica](plan.md#migración-histórica-local--ts7733), [compatibilidad](../../docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md) y [guía demo](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Riesgo / origen | Nivel y oráculo verificable |
|---|---|
| RN77-04 / D77-04: recálculo por año | MigrationExecutor 0003→0004 sobre códigos antiguos, actuales y etiquetas conocidas discordantes: años 1/2→JUNIOR, 3–6→SENIOR; PASSIVE de año 3 pasa a SENIOR. |
| RN77-01: condición fuera de escala | EX_TRAVELER/null exacto se conserva en avance y reversión. No se deduce desde una anomalía ni se inventa año 0/7. |
| D77-04: anomalía tardía | 18 casos en ambas direcciones: UNKNOWN, vacío, minúsculas, año nulo fuera de condición, 0/7, marcador con año y variantes del marcador. Validación del conjunto bloqueado antes de todo UPDATE; filas y SHOW CREATE intactos. |
| RNF77-03/04: pérdida de evidencia o datos ajenos | Filas completas de todas las tablas de negocio salvo category: usuarios/contraseñas/grupos, PKs, roles/vigencia, subcomisión, expediente/M2M, descargo, auditoría y T01/snapshots no vacíos con códigos históricos. Movimientos/saldo institucional de 2,5 puntos vinculados a resolución/expediente, nroSocio distinto de PK local. |
| D77-04: repetición engañosa | Se ejecuta directamente el cuerpo sobre datos canónicos y se comprueba cero UPDATE; no basta con repetir migrate sobre una migración registrada. |
| RNF77-03 / D77-04: fallo tras una escritura | Avance y reversión por MigrationExecutor: inyección después de ejecutar realmente un UPDATE, comprobación del cambio dentro de la transacción, rollback exacto de filas/esquema y estado de migraciones, reintento correcto. |
| D77-04: reversión con corte incorrecto | Retorno semántico por año: PASSIVE 1–3 / ACTIVE 4–6 y EX_TRAVELER/null conservado. No reproduce etiquetas arbitrarias originales; reavance devuelve códigos canónicos. La guardia de 0002 sigue rechazando exviajeros si se intenta volver a 0001. |

| Control | Evidencia |
|---|---|
| TDD inicial | **1 failed**, 9,92 s, por NodeNotFoundError de 0004 antes de crear la migración. Los datos y vínculos históricos ya estaban preparados. Sólo se agrega 0004; 0001/0002/0003 aplicadas permanecen intactas. |
| Pruebas enfocadas | **21 passed, 0 errores**, 81,58 s: conservación/repetición/reversión, 18 anomalías y dos fallos después de UPDATE. 37 casos previos del módulo quedan fuera sólo de esta ejecución enfocada y se incluyen en la regresión. |
| Suite backend final / cobertura | **642 passed, 0 errores**, 251,68 s, sin omisiones. MySQL 8.0.46 real, base separada de pytest y scratch UUID propios, checkout completo y snapshot Compose recién generado/saneado. 21 casos nuevos frente a TS77.32. Migración 0004: **100%**, 28 sentencias/0 sin cubrir; socios.models: **97%**, 68/2 sin cubrir (__str__). Cobertura combinada **97,92%**, umbral 80% cumplido. |
| Ruff / Django | ruff check . correcto; format --check de los dos archivos de TS77.33 correcto. makemigrations --check --dry-run sin cambios; manage.py check: 0 problemas. |
| Demo / repetición | Preflight autenticado correcto. prepare_demo_schema aplica **1 migración**, crea **0 tablas**; 47 tablas y 32 registros de migración. Sólo cambian el registro/contador de django_migrations; todos los esquemas de negocio y conteos restantes son iguales. 27 tablas legadas vacías/39 FKs conservadas y 0 usuarios/socios locales, sin seed. Segunda ejecución: 0 migraciones/creaciones, los 47 hashes y todos los conteos idénticos. El recálculo sobre filas no vacías queda probado en scratch. |
| Alcance / archivos protegidos | De 397 archivos backend/frontend preexistentes sólo cambia el ensayo de bootstrap; se agrega 0004 (398 archivos al cierre). Los otros 396 conservan sus hashes. Modelo, código de padrón/cuentas/T01, frontend, DDL legado, migraciones aplicadas, constitución, notasPO, seguimiento macro y AGENTS intactos respecto del inicio de TS77.33. |
| Control documental | 249 referencias locales válidas, 43 IDs/estados sincronizados y git diff --check correcto. Sólo TS77.33 pasa a completada; TS77.34–43 y tareas del seed siguen pendientes. Próxima unidad TS77.38, sin iniciarla. |
| Auditoría independiente | audit_scrum77_implementation aprobó el cierre integral sin hallazgos pendientes: implementación, oráculos, regresión/cobertura, aplicación/repetición demo y documentación. Confirmó transacción interna, bloqueo/validación, alias/modelos históricos, códigos exactos y reversión por año; 43 estados coincidentes y archivos protegidos intactos. Auditoría en lectura, sin pruebas ni mutaciones propias. |
| Consistencia PO | RN77-01/04, constitución ppio. 8 y notasPO §7 contrastados al inicio/durante/cierre. Junior 1–2 / Senior 3–6 en escala; condición exviajero explícita fuera de ella, sin modificar rol, vigencia, saldo, facultades, grupo o año. Snapshots y evidencia histórica conservan sus códigos originales. |

CA77-08 y DEP77-02 continúan abiertos: integración institucional, contratos, tokens históricos y SPA conservan sus tareas. La próxima unidad de la secuencia es TS77.38, evolución del contrato DDL demo, previa confirmación según AGENTS.md; no se inicia en esta tarea.

## Verificación de TS77.38

Completada el 12/10/2026 por confirmación del usuario, con auditoría integral aprobada sin hallazgos pendientes. Artefactos: [DDL demo](../../backend/core/sql/scrum77_legacy_schema.sql), [oráculos DDL/ORM/MySQL](../../backend/tests/infrastructure/test_scrum77_legacy_ddl.py), [rechazo y repetición del bootstrap](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py), [mapa de correspondencias](../../docs/gestion-proyecto/MAPEO_ESQUEMA_DEMO_SCRUM-77.md) y [guía](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md).

| Riesgo / origen | Nivel y oráculo verificable |
|---|---|
| RN77-01 / D77-03: año ficticio para exviajeros | Contrato vacío: anoSocial INT firmado DEFAULT NULL, IS_NULLABLE=YES en MySQL. No se introducen filas ni se infiere condición desde NULL; metadato explícito pendiente en TS77.40. |
| D77-03: cambios no autorizados al fuente | Comparación íntegra de los 27 CREATE sólo admite dos precisiones Decimal y nulabilidad de anoSocial. Conserva tipos/signo, defaults restantes, PKs/índices, orden y 39 FKs/acciones; fuente institucional con hash intacto. |
| RNF77-03: cierre físico inconsistente | Compilación MySQL real con 39 FKs, tipos iguales en ambos extremos, InnoDB/utf8mb4_unicode_ci y FKs activas. Las 27 tablas legadas están vacías; bootstrap vacío y repetición sobre nuevo contrato pasan. |
| D77-03: relajar nulabilidad del ORM o bootstrap | Oráculo ORM permite sólo la diferencia física temporal de socio_lista.anoSocial; todos los otros campos/restricciones mantienen sus comparaciones. Modelos y bootstrap no cambian. |
| D77-03: adopción silenciosa del contrato anterior | Scratch con anoSocial NOT NULL, migración 0004 pendiente, socio PASSIVE3/cuenta/grupo previos y socio_email faltante: rechazo por socio_lista antes de cualquier DDL/DML. Filas completas protegidas, socio, SHOW CREATE e historial pendiente intactos. |
| TS77.39: transicionar por adelantado la demo preparada | Comando protegido sobre la demo devuelve CommandError esperado por socio_lista. Los 47 hashes y todos los conteos antes/después son idénticos; anoSocial sigue NOT NULL. No se ejecuta ALTER real ni se reinicia volumen. |

| Control | Evidencia |
|---|---|
| TDD rojo | **4 failed / 4 passed**, 12,98 s, antes de cambiar SQL: tercera adaptación, nulabilidad física/ORM y rechazo del contrato anterior fallan por la definición previa. |
| Pruebas enfocadas | **66 passed, 0 errores**, 140,14 s: siete casos DDL y 59 de bootstrap, incluidos los dos nuevos de TS77.38. Conservación/repetición/guardias de las unidades anteriores incluidas. |
| Suite backend / cobertura | **644 passed, 0 errores**, 252,14 s, sin omisiones. MySQL 8.0.46 real, base de pytest separada y scratch UUID propios, checkout completo y snapshot Compose recién generado/saneado. core.demo_schema: **91%**, 185 sentencias/17 sin cubrir; socios.models: **97%**, 68/2 sin cubrir (__str__). Combinada **92,49%**, umbral 80% cumplido. No cambia lógica de negocio. |
| Ruff / Django | ruff check . y format --check de los dos archivos de pruebas correctos; makemigrations --check --dry-run sin cambios y manage.py check: 0 problemas. No se agrega una migración Django ni se cambia el unmanaged en esta unidad. |
| Demo preparada | Rechazo esperado por divergencia de socio_lista antes de escribir. 47 esquemas y todos los conteos idénticos, 32 registros de migración y 39 FKs legadas; 0 usuarios/socios locales y tablas legadas vacías. anoSocial físico sigue NOT NULL: transición real pendiente en TS77.39. |
| Alcance / archivos protegidos | De 398 archivos backend/frontend sólo cambian el DDL demo y los dos archivos de pruebas; sin archivos nuevos, 395 hashes restantes iguales. Bootstrap/comando, modelos, migraciones, consumidores y frontend intactos. Constitución, notasPO, seguimiento macro, AGENTS, SQL fuente y ambos Compose conservan sus hashes. |
| Control documental | 269 referencias locales válidas, 43 IDs/estados sincronizados y git diff --check correcto. Sólo TS77.38 pasa a completada; próxima unidad TS77.39 pendiente. Evidencia histórica conservada y límites de la demo preparada explícitos en guía/mapa/plan. |
| Auditoría independiente | audit_scrum77_implementation aprobó el cierre integral sin hallazgos pendientes: código, oráculos, regresión/cobertura, demo y documentación. Comparación propia confirma 27/39, sólo tres adaptaciones, excepción ORM acotada, 43 estados y 13 hashes protegidos coincidentes. Corregida la precisión documental que distingue cierre vacío de repetición con usuario/grupo propios conservados. Auditoría en lectura, sin pruebas ni mutaciones propias. |
| Consistencia PO | RN77-01–04, constitución ppio. 8 y notasPO §7 contrastados al inicio/durante/cierre. Exviajero fuera de escala sin año ficticio; NULL físico no otorga condición, rol, vigencia, facultades o puntos. Fuente/base institucional y reglas no modificadas. |

CA77-01/08 y DEP77-02 continúan abiertos por transición/integración y guardias de carga. La próxima unidad es TS77.39, transición protegida de la demo preparada, previa confirmación según AGENTS.md; no se inicia aquí.

## Verificación de TS77.39

Completada el 12/10/2026 por confirmación expresa del usuario, con auditoría integral aprobada sin hallazgos pendientes. Artefactos: [comando protegido](../../backend/core/management/commands/transition_demo_schema.py), [transición interna](../../backend/core/demo_schema.py), [pruebas MySQL](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py), [diseño técnico](plan.md#transición-protegida-de-una-demo-preparada--ts7739) y [procedimiento](../../docs/gestion-proyecto/GUIA_ENTORNO_DEMO_SCRUM-77.md#transicionar-una-demo-preparada--ts7739).

| Riesgo / requisito | Oráculo verificable |
|---|---|
| D77-03 / RNF77-03: adoptar una divergencia | Selección del contrato anterior/actual sólo por anoSocial; validación íntegra de 27 tablas/39 FKs y auth_user antes del único ALTER. Ocho casos de default, nulabilidad ajena, precisión y FK ausente en ambas versiones exigen cero DDL/DML; base vacía/cierre incompleto también rechazados. |
| RNF77-04: perder datos, identidades o contador | Scratch con datos históricos y contador reservado 880033, mayor que MAX(nroSocio)+1. Conserva cuentas/credenciales, socios locales Junior/Senior/EX_TRAVELER, roles/vigencia, vínculo institucional con nroSocio distinto de PK local, T01/snapshots, expediente/M2M, descargo/auditoría y libro mayor con saldo no cero. Un ALTER exacto; segunda ejecución sin DDL/DML y mismas filas/esquemas. |
| RNF77-03: estadísticas desactualizadas | Caché calentada antes de INSERT sintético: lectura debe devolver contador vigente 770034 y coincidir con SHOW CREATE TABLE. Se restaura stats_expiry de sesión tanto al terminar como ante error de lectura; sin modificación global ni ANALYZE. |
| RNF77-02/03: destino, sesión o concurrencia ajenos | Guardias de configuración/MySQL/HTTP antes del cuerpo; no admite base alternativa. Rechaza atomic, autocommit desactivado, FKs desactivadas y bloqueo de otra conexión. Errores del driver redactados, sin secretos. |
| RNF77-03: simular rollback de DDL | Fallo después de ejecutar ALTER real conserva el contrato nuevo y las filas. Otra conexión adquiere el bloqueo, demostrando liberación; reintento acredita el nuevo contrato sin DDL/DML. Un contador discrepante posterior impide informar éxito y conserva la base para diagnóstico. |

| Control | Evidencia |
|---|---|
| TDD inicial | Antes de implementar: **1 failed**, 8,84 s, por ausencia de transition_social_year_schema. |
| TDD de hallazgo del auditor | Al reanudar, **1 failed / 1 passed**, 14,16 s: caché devuelve 1 frente al contador real 770034. Se corrige la lectura de sesión y su restauración en finally. El oráculo de bloqueo usa una conexión distinta. |
| Pruebas enfocadas | **26 passed, 0 errores**, 88,01 s, 59 deselected del archivo. Dos pruebas adicionales cubren caché caliente y error de lectura; no se omiten ensayos MySQL. |
| Suite backend / cobertura | **670 passed, 0 errores**, 305,31 s, sin omisiones. MySQL 8.0.46 real, base de pytest separada y scratch UUID propios, checkout completo y snapshots Compose recién generados/saneados. core.demo_schema: **93%** (239 sentencias/17 sin cubrir); comando: **100%** (18/0); socios.models: **97%** (68/2). Combinada **94,15%**; umbral 80% cumplido. |
| Ruff / Django | ruff check . y format --check de los tres archivos correctos; manage.py check: 0 problemas; makemigrations --check --dry-run: sin cambios. No se agrega ni modifica una migración Django. |
| Demo preparada / conservación | Primera ejecución: altered_columns=[socio_lista.anoSocial], row_count=0, 27 legadas/39 FKs activas. Sólo SHOW CREATE de socio_lista cambia, exactamente NOT NULL→DEFAULT NULL; otros 46 hashes iguales. Todas las huellas de filas/conteos e IDs se conservan, contador 1→1; 47 tablas/32 registros de migración, 0 usuarios/socios locales y legadas vacías. La conservación no vacía se prueba en scratch. |
| Repetición / bootstrap estricto | Segunda transición: altered_columns vacío. prepare_demo_schema posterior: created_tables vacío/migrations_applied=0. Ambos inventarios conservan los 47 hashes de esquema y todas las huellas de filas/conteos/contador de la primera transición. El bootstrap sigue rechazando el contrato anterior en las pruebas. |
| Alcance / archivos protegidos | TS77.39 agrega un comando y la transición interna con sus oráculos; no cambia modelos, migraciones aplicadas, DDL TS77.38, adaptadores, frontend ni Compose. Al reanudar se capturaron 411 hashes: sólo cambió core.demo_schema.py para corregir el contador. Normas/exportaciones, notasPO, constitución, AGENTS, seguimiento macro, fuente SQL, DDL demo y ambos Compose conservan los hashes de esa lectura inicial. |
| Control documental | 286 referencias locales/fragmentos válidos en 27 documentos, 43 IDs/estados sincronizados, git diff --check correcto y hashes protegidos conservados. Corregido un fragmento preexistente del enlace al cierre TS77.29 en el documento de impacto. Sólo TS77.39 pasa a completada; TS77.40 y las tareas siguientes continúan pendientes. |
| Auditoría independiente | audit_ts7739_resume aprobó el cierre integral sin hallazgos pendientes: código, oráculos, regresión/cobertura, demo y documentación coherentes. P2 de estadísticas cacheadas y P3 de liberación del bloqueo resueltos; corregidos dos resúmenes documentales desactualizados y la precisión sobre la única columna alterada. Cotejo independiente de 13 hashes protegidos, 43 IDs/estados y 234 referencias de los nueve documentos del cierre antes del registro final. Auditor en lectura, sin pruebas ni mutaciones propias. |
| Consistencia PO | RN77-01–04, constitución ppio. 8 y notasPO §7 contrastados al inicio/durante/cierre. NULL físico no concede condición exviajero, rol, vigencia, facultades o puntos. G57 permanece fuera de escala, sin año ficticio; fuente/base institucional y reglas no se modifican. |

El bloqueo coordina preparación/transición; las escrituras o cambios de esquema externos requieren coordinación propia. Un error posterior al ALTER puede dejar el DDL aplicado: conservar la base y corregir la causa antes del reintento, sin prometer rollback de esquema. CA77-01/08 y DEP77-02 continúan abiertos por guardias de carga e integración institucional. La próxima unidad es TS77.40, condición institucional explícita, previa confirmación según AGENTS.md; no se inicia aquí.

## Verificación de TS77.40/34/41/42

Completadas el 12/10/2026 por autorización expresa del usuario: root implementa TS77.40 y tres subagentes implementan TS77.34, TS77.41 y TS77.42 en paralelo. Las dependencias metadato → lectores → T01 se respetan; pytest/MySQL se ejecuta por turnos. Revisiones cruzadas de código y auditoría integral final aprobadas sin hallazgos pendientes.

| Unidad / artefactos | Oráculos de comportamiento e integridad |
|---|---|
| TS77.40: [modelo/escritor](../../backend/socios/institutional_conditions.py), [migración 0005](../../backend/socios/migrations/0005_institutional_membership_condition.py), [37 casos](../../backend/tests/test_institutional_membership_condition.py) y [bootstrap](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) | nroSocio real y conexión seleccionada; referencia existente/año nulo, fuente/corte obligatorios, PK/CHECK nativos, código exacto, duplicados y mutaciones rechazados. Repetición idéntica sin DML y rollback de atomic exterior. Modelos local/institucional, cuentas, roles y vigencia conservados. Migra antes del cierre legado, sin FK ni consultas a tablas aún ausentes. |
| TS77.34: [consulta compartida](../../backend/padron/querysets.py), [40 casos puros/mock/HTTP](../../backend/tests/padron/test_social_classification.py), [13 MySQL](../../backend/tests/padron/test_social_classification_db.py) | Junior 1–2 / Senior 3–6; marcador explícito EX_TRAVELER/null y UNKNOWN para anomalías sin marcador. Subcomisión, vigencia o NULL por sí solos no conceden condición. Proyección/filtros/count/páginas coinciden en SQL, cuatro consultas del adaptador y una de ranking para listas de tamaños distintos. Aliases históricos sólo de entrada; desconocidos 400. Omitir is_active no filtra; True/False explícitos funcionan. |
| TS77.41: [servicio](../../backend/expedientes/services/solicitud_t01_service.py), [emisión](../../backend/expedientes/serializers.py), [36 casos](../../backend/tests/test_scrum77_t01_classification.py) | EX_TRAVELER/null; escalas/anomalías e ID seleccionado contra DTO. user_id institucional real único o legajo real corroborado, sin identidad por coincidencia de PK. Legajo compartido entre distintas fichas rechazado para reuso y creación; múltiples carreras del mismo nroSocio admitidas. Sincroniza sólo categoría/año, conserva credenciales/rol/vigencia/campos/vínculos; snapshots nuevos canónicos e históricos intactos. Fallo tardío o de apertura revierte toda la emisión/materialización. |
| TS77.42: [token/serializer](../../backend/accounts/serializers.py), [ruta refresh](../../backend/accounts/urls.py), [30 casos JWT](../../backend/tests/test_scrum77_token_refresh.py) | Login/me vigentes y refresh con categoría leída de DB por petición, incluidos PASSIVE/ACTIVE históricos, EX_TRAVELER y claim ausente. Firma/expiración/tipo, identidad inválida, perfil ausente y reglas de usuario mantienen rechazo; USER_ID_FIELD/CLAIM, lifetimes y rotación conservados. Otros claims se preservan y RBAC sigue leyendo rol/vigencia de DB. Ensayo adicional de tres rotaciones con blacklist real. |

| Control | Evidencia |
|---|---|
| TDD TS77.40 | Antes del modelo/escritor: **30 failed**, 4,42 s. Primera fase **30 passed** en ejecución conjunta de 43 casos; los siete oráculos físicos adicionales y bootstrap se incluyen en la regresión final. |
| TDD TS77.34 | Fase inicial: **22 failed / 10 passed**, 0,82 s. Ampliación a 40 casos: **28 failed / 12 passed** en ejecución conjunta con JWT (9,07 s). Fase MySQL antes de integrar metadato/SQL: **11 failed / 2 passed**, ejecución conjunta 5,25 s. Los **53 casos** finales pasan. |
| TDD TS77.41 / hallazgo | Primeros 29 casos: **24 failed / 5 passed**, ejecución conjunta 14,38 s. Auditoría independiente reproduce P2: **1 failed / 1 passed / 33 deselected**, 4,61 s; legajo compartido emitía 200 en lugar de rechazar. Guardia DISTINCT corregida; control de varias carreras y variante de creación incluidos en los **36 casos** finales verdes. |
| TDD TS77.42 | Primeros 28 casos: **17 failed / 11 passed**, ejecución conjunta con padrón 9,07 s. Después **28 passed**; dos variantes adicionales de USER_AUTHENTICATION_RULE/is_active completan los **30 casos** verdes finales. El caso de USER_ID_FIELD/CLAIM ya estaba entre los 28 iniciales. |
| Pruebas enfocadas | Integración **191 passed / 48 deselected**, 67,55 s; omisiones sólo por selección de esa corrida. Tras P2, T01/JWT/autenticación/RBAC: **106 passed**, 19,23 s. Los casos restantes y la variante final T01 se incluyen en la suite completa. |
| Blacklist real | Proceso separado que habilita la app existente antes de django.setup, sin modificar configuración/dependencias del proyecto: **3 passed / 27 deselected**, 4,82 s. Se comprueba blacklist del refresh anterior y rotación nativa. |
| Suite backend final | **827 passed, 0 errores, sin omisiones**, 327,59 s. MySQL 8.0.46 real, base de pytest separada y scratch UUID propios; checkout completo y snapshot Compose recién generado/saneado. **157 casos nuevos**: 37 metadato + 53 padrón + 36 T01 + 30 JWT + 1 bootstrap, sobre baseline 670. |
| Cobertura | **94,64%** combinada, umbral 80% cumplido: 1325 sentencias/71 sin cubrir en los 12 módulos seleccionados. Dominio/servicios/adaptador de padrón 100%; metadato 93%, consulta compartida 94%, servicio T01 94%, serializer de emisión 96%, JWT 92%, ranking.services 95%, modelo local 97% y bootstrap 93%. ranking.serializers 78% incluye ramas genéricas preexistentes; no se declara 80% por archivo. |
| Ruff / Django | ruff check . correcto; format --check de los 33 archivos cambiados/nuevos correcto. Dos ajustes finales exclusivamente de formato tienen AST idéntico antes/después, sin cambio funcional posterior a la suite. manage.py check: 0 problemas; makemigrations --check --dry-run: sin cambios. |
| Demo / primera preparación | prepare_demo_schema aplica **1 migración**, crea **0 tablas legadas**: total **48 tablas / 33 registros de migración**. Nueva tabla socios_institutionalmembershipcondition vacía. post_migrate agrega **1 content type / 4 permisos de catálogo** sin asignaciones; django_migrations agrega su registro. Filas previas intactas, y los únicos cambios de SHOW CREATE preexistentes son sus tres contadores AUTO_INCREMENT. Resto de tablas/esquemas/filas y contador institucional idénticos. |
| Repetición / límites de datos | Segunda preparación: **0 migraciones / 0 creaciones**, mismos 48 hashes de esquema y huellas de filas/conteos/contador. 27 legadas vacías/39 FKs activas, anoSocial nullable; 0 usuarios/socios locales y 0 metadatos, sin seed. Integridad y preservación no vacías probadas en MySQL propio, sin atribuir esos fixtures a la demo real. |
| Alcance / archivos protegidos | De 411 huellas iniciales, 24 archivos backend preexistentes cambian y se agregan 9; las otras 387 se conservan. Frontend, normas/exportaciones, notasPO, constitución, AGENTS, seguimiento macro, DDL demo/fuente, ambos Compose y migraciones 0001–0004 intactos. Sin dependencias nuevas ni cambios de configuración JWT. La única diferencia de código después de la suite es el formato con AST idéntico de dos archivos. |
| Control documental | 326 referencias/fragmentos válidos: enlaces entre archivos de 27 documentos y autoenlaces de los nueve actualizados en estas unidades. 43 IDs/estados sincronizados y git diff --check correcto. TS77.40/34/41/42 marcadas completadas en TASK.md y este seguimiento; TS77.43/35/36/37 y seed siguen pendientes. No se editan notasPO ni seguimiento macro. |
| Auditoría independiente | implement_ts7734 aprueba TS77.40; root revisa integración TS77.34; implement_ts7742 aprueba TS77.41 con P2 corregido; implement_ts7741 aprueba TS77.42. implement_ts7734 aprueba el cierre integral final en lectura sin hallazgos pendientes: código/oráculos, PO, nueve documentos, estados y evidencia coherentes. Se corrigieron referencias D77 de T01/JWT y la descripción de los dos casos JWT adicionales antes del dictamen. Los auditores no ejecutan Docker/SQL ni modifican documentación; ejecución y conservación acreditadas por root. |
| Consistencia PO | RN77-01–04, constitución ppio. 8 y notasPO §7 contrastados al inicio/durante/cierre. G57 fuera de escala, Junior 1–2/Senior 3–6 y asamblea variable. Categoría independiente de rol/vigencia/facultades/saldo; seis estados, reglas de puntos e historial conservados. Sin automatización de pase anual. |

La protección ORM del metadato no garantiza integridad ante escrituras externas: la conciliación posterior y la propiedad/manifiesto del seed siguen en TS77.09/11. La concurrencia del escritor se revisó mediante atomic y orden de bloqueos, sin ensayo de estrés multiconexión. El refresh conserva claims antiguos de rol/legajo; el servidor decide acceso desde DB. TS77.43 conserva la resolución del namespace/propiedad del legajo; TS77.35/36/37, la SPA y aceptación transversal. CA77-01/08, DEP77-02 y catálogo/seed siguen abiertos. La próxima unidad es TS77.43, previa confirmación según AGENTS.md; no se inicia dentro de estas cuatro unidades.

## Verificación de TS77.43/35/36/37/07

Autorizadas expresamente por el usuario el 12/10/2026: root implementa TS77.43 y un subagente distinto trabaja cada unidad TS77.35, TS77.36, TS77.37 y TS77.07. Con tres plazas de subagentes, TS77.37 comienza cuando termina la preparación del catálogo; se respeta integración TS77.43/35/36 → verificación TS77.37 → aceptación TS77.07. Root centraliza las ejecuciones, con un runner MySQL y uno Karma por vez. Las menciones a pendientes en cierres anteriores describen su estado histórico, no el avance actual.

| Unidad / decisión | Artefactos y comportamiento verificado |
|---|---|
| TS77.43 / D77-08 | [Resolución de identidad](../../backend/socios/identity.py), [vista](../../backend/socios/views.py), [contrato](../../backend/socios/serializers.py) y [33 casos de legajo](../../backend/tests/test_scrum77_legajo_identity.py). identity_source explícito usa sólo la PK de su fuente, con 400 para fuente inválida/repetida y 404 genérico para ausencia/ambigüedad. Llamadas antiguas inequívocas conservadas. Propiedad por user_id institucional único o legajo real corroborado; email/PK coincidente/legajo inventado no acreditan dueño ni rol. legajo ausente es null, errores de consultas no filtran detalles. Lectura sin sincronizar ni crear perfiles. |
| TS77.35 / D77-05/06/08 | [AuthService](../../frontend/src/app/services/auth.service.ts) mantiene identidad/rol/sesión válidos y deja categoría pendiente hasta confirmar auth/me; no traduce aliases ni decodifica JWT para decidirla. Interceptor/401 conservados, errores HTTP/red no inventan categoría y respuestas tardías no restauran una sesión cerrada. [SocioApiService](../../frontend/src/app/services/socio-api.service.ts) transporta la fuente y no reintenta otro namespace. Padrón conserva vigencia independiente y los DTOs históricos de T01; filtros ranking admiten las cuatro categorías. |
| TS77.36 / D77-01/04/05 | [Ranking](../../frontend/src/app/ranking-socios/ranking-socios.component.html) y [modal](../../frontend/src/app/ranking-socios/socio-legajo-dialog/socio-legajo-dialog.component.html) muestran Junior/Senior/Exviajero/Sin clasificación. Modal usa fuente institucional desde ranking, conserva fuente al reintentar, limpia ficha anterior ante error y muestra Sin legajo/null sin año ficticio. Año visible sólo en escala 1–6. [Mock](../../frontend/src/app/ranking-socios/ranking.mock.ts) conserva sus 33 IDs/nombres/saldos/subcomisiones, con corte sintético explícito y Senior de 3.º. Badge consume tokens canónicos. [seed_demo](../../backend/socios/management/commands/seed_demo.py) conserva flujo/credenciales/roles; se ajustan ayuda/docstrings/tipos, con [8 casos de compatibilidad](../../backend/tests/test_seed_demo_classification.py). |
| TS77.37 / RNF77-06, CA77-08 | verify_ts7737 aprueba código, oráculos, denominaciones, contratos, diez documentos y consistencia PO, sin hallazgos pendientes. implement_ts7735 aprueba TS77.36 e implement_ts7736 aprueba TS77.35 en revisiones cruzadas. Todos auditan en lectura; runners/conservación centralizados por root. Barrido distingue aliases de entrada y snapshots históricos de etiquetas vigentes; no reemplaza activo de vigencia/navegación. |
| TS77.07 / RF77-05, DP77-02 | [Catálogo puro](../../backend/socios/demo_catalog.py), [62 oráculos](../../backend/tests/test_scrum77_catalog.py) y [mapa/rangos](../../docs/gestion-proyecto/CATALOGO_DATOS_DEMO_SCRUM-77.md). Versión scrum77-g57-g60-v1, corte PO-SCRUM77-CORTE-01, 16 identidades/cuatro por grupo; seis cuentas nuevas propuestas y cinco referencias seed_demo conservadas. Claves managed se resolverán al cargar. Tres causas/cuatro T01 y ocho asientos con siete respaldos son fixtures futuros; saldo neto esperado +1, sin acreditarlo en demo. Catálogo aceptado y DP77-02 cerrado tras auditoría TS77.37. |

| Control | Evidencia centralizada |
|---|---|
| TDD de legajo | Antes de implementar: 17 fallos/13 verdes, 14,38 s. Casos adicionales de fuente estricta/legajo alternativo y ambigüedad local: 3 fallos/30 deseleccionados, 5,29 s. Tras resolver identidad: **52 passed**, 29,12 s, incluidos los 19 controles preexistentes de legajo. |
| P2 de auditoría y BIGINT | El auditor identifica que una PK local BigAutoField puede superar el INT institucional. [Dos oráculos MySQL nativos](../../backend/tests/infrastructure/test_scrum77_legajo_bigint.py) con PK 2147483648 fallan antes de corregirlo (9,65 s) y pasan después (**2 passed**, 9,28 s). Cada ensayo migra su propio esquema UUID y restaura managers; no eleva contadores compartidos. Sólo el namespace local admite BIGINT positivo hasta 9223372036854775807; nroSocio/legajo institucional siguen limitados a INT firmado. Sin migración ni ALTER. |
| TDD del catálogo | **62 errores** por módulo ausente, 1,51 s; después **62 passed**, 0,32 s. Validación pura determinista de reglas/referencias/rangos/tipos/roles/escenas/resoluciones/saldos, sin Django ni SQL. No demuestra colisiones contra una base cargada. |
| Compatibilidad seed_demo | **8 passed**, 7,72 s, antes de ajustar documentación/tipos del comando. Se verifican 1/2/3/6, EX_TRAVELER/null, cuentas/credenciales/roles, conservación de ediciones, repetición, DEBUG y rollback ante cuenta ajena. No se ejecuta el comando contra la demo. |
| TDD frontend | Primera ejecución bloqueada por cinco diagnósticos TS2352 y siguiente por 33 TS2322 del mock antiguo: 0 pruebas ejecutadas, no resultados verdes. Tras adecuar tipos/fixtures y una aserción temporal retirada al terminar, el comportamiento anterior produce **35 fallos/51 verdes de 86** (0,271 s de runner). Implementación final: **86 passed** (0,259 s); sin casts temporales en producción. |
| Regresión backend | **932 passed, 0 errores, sin omisiones**, 347,16 s, Python 3.12.15/MySQL real. 105 casos nuevos respecto de 827: 33 legajo + 2 BIGINT + 62 catálogo + 8 seed_demo. Esquemas temporales propios, configuración Compose vigente saneada y checkout montado en la misma ejecución. |
| Cobertura backend | 17 módulos, 1761 sentencias/93 faltantes, **94,72%**, umbral 80% cumplido. identity 90%, demo_catalog 95%, views 97%, serializers/seed_demo 100%; no se atribuye cobertura a módulos omitidos. |
| Regresión frontend y build | **202 passed, 0 errores**, sin omisiones, ChromeHeadless 154.0.0.0 real (0,631 s de runner). Tras el único ajuste final de CSS, **16 casos del modal verdes** (0,06 s). Build de producción posterior al freeze correcto, 7646 ms, hash **03903dec0d96c561**, 12/10/2026 17:46:34 UTC. No acredita recorridos UI manuales ni responsive; siguen en TS77.20–24. |
| Límite de lint frontend | npm run lint devuelve exit 1: Cannot find builder @angular-devkit/build-angular:tslint. Limitación heredada del pipeline; se registra, sin agregar dependencias ni cambiar configuración para ocultarla. El build mantiene el aviso de ranking.mock.ts incluido sin uso; no impide compilar. |
| Checks backend | ruff check . correcto; ruff format --check correcto en los nueve Python modificados/agregados. Django check: 0 incidencias; makemigrations --check --dry-run: No changes detected. |
| Demo preservada | Lectura antes/después: **48 hashes de SHOW CREATE, huellas de filas y conteos idénticos**; 33 registros de migración, 27 legadas vacías/39 FKs activas, anoSocial nullable y contador socio_lista=1. Cero usuarios/socios locales/metadatos. No se ejecutan bootstrap, migraciones ni seed en este grupo. Casos no vacíos/BIGINT verificados sólo en bases de pruebas propias. |
| Freeze y archivos protegidos | Los **428 archivos de código/protegidos** son idénticos al freeze anterior a la suite final. Respecto del inicio: 18 preexistentes cambiados y 8 nuevos; otras 402 huellas intactas. **15 protegidos conservados**, incluidos notasPO, constitución, AGENTS, macro Scrum, exportaciones formales, Compose, DDL demo/fuente y migraciones socios 0001–0005. Manifiestos de dependencias/settings intactos; instalación local de paquetes ya declarados sin lock nuevo ni dependencias nuevas. |
| Control documental | **379 referencias/fragmentos válidos**: enlaces entre 28 documentos y autoenlaces de los diez actualizados. 43 IDs/estados TASK.md/tasks.md sincronizados, **23 completados/20 pendientes**, y git diff --check correcto. Las cinco tareas marcadas completadas después del dictamen integral independiente; TS77.08–27 conservan estado pendiente. |
| Dictamen integral | verify_ts7737 aprueba TS77.37 y aceptación TS77.07/DP77-02, sin hallazgos pendientes. P2 BIGINT corregido/probado; dos precisiones documentales corregidas: label Sin clasificación y PK BIGINT distinta del campo legajo VARCHAR(20). Autoriza registrar cierre CA77-08/DEP77-02 y cinco marcas, con lint heredado y CA77-01–07/seed/manifiesto/persistencia/recorridos pendientes. |
| Consistencia PO | RN77-01–04, notasPO §7 y constitución principio 8 contrastados al inicio/durante/cierre. G57 fuera de escala; G58/G59/G60 6/5/4; Junior 1–2/Senior 3–6 y avance en asamblea variable. No cambian vigencia/roles/facultades/saldos ni snapshots históricos, ni se automatiza el pase anual. DP77-FAC-01 mantiene sus propias US. |

CA77-08/DEP77-02 y CF77-01/02 cerrados por verificación transversal; DP77-02/catálogo v1 aceptado tras auditoría TS77.37. Aceptar el catálogo no cierra CA77-02: propiedad/manifiesto, colisiones/carga, conciliación, persistencia y recorridos HTTP/UI quedan en TS77.08–27. CA77-01 sigue abierto por las guardias TS77.08. La US completa sigue en curso; próxima unidad TS77.08 sólo con nueva confirmación según AGENTS.md.

## Verificación de TS77.08–27

Autorización del usuario: terminar las 19 unidades TS77.09–27 con los subagentes necesarios, sin confirmaciones individuales. TS77.08 se incluye como prerrequisito de guardias. Root coordina integración, pruebas MySQL/Karma y operación demo; seed_registry_members implementa propiedad/cuentas/padrón, seed_cases_history escenas/antecedentes y planes/runbook, demo_ui_verification HTTP/SPA y audit_final_seed la revisión independiente. No se crea un commit ni un PR en esta instancia.

Artefactos: [orquestador](../../backend/core/demo_seed.py), [propiedad](../../backend/core/demo_fixtures.py), [miembros](../../backend/core/demo_members.py), [escenas](../../backend/core/demo_scenes.py), [comando](../../backend/core/management/commands/seed_expedientes.py), [migración core](../../backend/core/migrations/0001_initial.py), [runbook](../../docs/gestion-proyecto/GUIA_CARGA_DEMO_SCRUM-77.md), [recorridos UI](../../docs/gestion-proyecto/VERIFICACION_UI_SCRUM-77.md) y [registro de resultados](../../docs/gestion-proyecto/VERIFICACION_CARGA_SCRUM-77.json).

| Unidad / control | Resultado y alcance |
|---|---|
| TS77.08 — guardias | 17 oráculos; perfil, conexión efectiva/configuración, esquema legado, historia managed y unicidades físicas. En demo real: perfil inválido y migración pendiente rechazados con exit 1; los 48 esquemas, huellas de filas/conteos y contador=1 permanecieron idénticos. |
| TS77.09 — propiedad | Registro genérico managed; UNIQUE(profile, fixture_key) y UNIQUE(namespace, object_key) físicos, PK canónica, destino existente y referencias explícitas. Lock compartido con preparación/transición; validación cacheada sólo dentro de la misma adquisición. 16 oráculos de registro, incluido reacquirir el lock después de cambiar el esquema. |
| TS77.10/11 — miembros | 15 oráculos. Seis cuentas nuevas y cinco referencias de seed_demo: 11 usuarios/perfiles locales. 16 fichas institucionales, cuatro por grupo; G57 NULL/EX explícito (cuatro marcadores), G58=6, G59=5 y G60=4. Credenciales, roles, habilitación y ediciones válidas preservados; centinela institucional 99 sin PK local inventada. |
| TS77.12–15 — escenas | 10 oráculos MySQL. Tres causas Creado, dos Justificaciones mediante workflow/T01, siete relaciones de involucrados y siete auditorías. Cuatro solicitudes (dos por actor, borrador/emitida); urgencias y snapshots vigentes. Siete expedientes/resoluciones legados, ocho asientos individuales y total +1,00; PuntajeGeneral y outbox vacíos. |
| TDD backend | Antes de los loaders: 25 errores por módulos de propiedad/miembros ausentes (101,88 s) y diez fallos por escenas ausentes (5,39 s). Guardias/HTTP: trece errores y un fallo antes de existir el seed (4,42 s). Reproducciones posteriores de lock/PK canónica/huérfanos, clasificación y lease antes de corregir. Las incidencias de configuración DEBUG o de un UserManager incorrecto se distinguen de los rojos de comportamiento. |
| TS77.16/17 — repetición/rollback | Cinco oráculos de integración: carga/manifiesto, repetición tras editar nombre/credencial/habilitación/motivo, excepción después de ambos loaders, destino propio desaparecido y excepción CLI saneada. Conservación de filas y contador formal; rollback de DML/propiedad completo. No se promete revertir secuencias AUTO_INCREMENT de MySQL tras una inserción fallida. |
| Preparación real | core.0001_initial aplicada: una migración, nueva core_demofixtureownership; 49 tablas y 34 registros de migración. Cambios esperados de metadatos Django/content types/permisos y sus AUTO_INCREMENT; sin DML del legado ni cambios a sus 27 contratos/39 FKs. Preparación repetida después del ensayo de persistencia: cero migraciones/tablas legadas nuevas. |
| Carga y TS77.16 real | Perfil scrum77-g57-g60-v1/corte PO-SCRUM77-CORTE-01. 162 referencias y 16 identidades; primera y segunda salida con SHA256 b5d6fce4594c743926ae76f2c1703cc234edd8b305d4d250dba89b7b68a28eb8. Los 49 SHOW CREATE, huellas de filas y conteos son idénticos. Contador institucional=770017; formal año 2026/last_value=5. |
| TS77.18 — conciliación | Grupos/años/condición y referencias físicas del manifiesto contra MySQL y API; ocho asientos suman 1,00. Comprobadas 59 restricciones FK de toda la base, cero huérfanos (39 pertenecen al cierre legado). Causas 4/5 con inicio 12/10/2026 19:58 UTC y límite 19/10/2026 19:58 UTC, abiertas al momento del ensayo. |
| TS77.19 — persistencia | ID MySQL 5b793d5d7f35238b749b58c98e3ad58b3fba3862d6008f0ba5b0242dee460617 → e5e7116e56791675a2602acd5e2332640bcabc9decf7342947748fcc1592b30c. Mismo volumen sgd_aveit_scrum77_demo_mysql_data. Los 49 esquemas/huellas/conteos y ambos contadores se conservaron exactamente; ningún seed ni preparación entre mediciones. Servicios saludables. |
| TS77.20–23 — HTTP | [Oráculo](../../backend/tests/infrastructure/test_scrum77_demo_http.py): una prueba UUID verde (10,20 s), incluida en la regresión final. Contra servidor real: 78 controles antes y 78 después de recrear MySQL, iguales. Login/me de 11 cuentas (deshabilitada=401), matriz 401/403/200, ranking/filtros/16 legajos, aislamiento de T01 y board/colección con IDs reales. Login por identifier acredita el contrato existente, sin acreditar contraseña. |
| TS77.23/24 — ajustes FE | TDD modal: tres fallos DOM (0,115 s); semántica de diálogo, foco capturado/restaurado, Cerrar inicial y Escape con CDK existente. Filtro secundario: un fallo/un verde (0,077 s) cuando el servidor devuelve dos casos; ajuste conserva respuesta confirmada y vacío, sin ampliar DTO. Compatibilidad final de GComponent: 23 verdes (0,265 s). |
| TS77.20–24 — navegador | Recorridos reales aprobados a 1440×900, 360×800 y 414×850, claro/oscuro y teclado. Ranking 10+6/filtros/empates/legajos, roles/RBAC, T01 reactivo/múltiple/aislamiento, board/tabla/ secundario 99077013→causas3/5. Modales contenidos, scroll/footer accesibles, nombres largos visibles; sin cambios a fixtures. Evidencia detallada en VERIFICACION_UI_SCRUM-77.md. |
| TS77.25 — backend final | **1008 passed, 0 errores/sin omisiones**, 618,46 s. MySQL 8.0.46 real, base pytest separada/scratch UUID; cobertura combinada **93,91%** en 22 módulos explícitos (2331 sentencias, 142 sin cubrir), umbral 80% superado. Incluye 76 pruebas nuevas frente al cierre TS77.37 de 932. |
| TS77.25 — estáticos | Ruff global correcto; 15 Python nuevos y serializer modificado formateados (16 archivos). Django check sin incidencias y makemigrations --check --dry-run sin cambios. |
| TS77.26 — antecedente frontend previo a revisión visual | **207 pruebas verdes, 0 errores**, ChromeHeadless 154, 0,928 s (0,694 s en pruebas). Producción correcta: hash 8c9cae1bbfeea2f1, 7825 ms. Lint exit 1 por builder TSLint ausente; limitación heredada clasificada, sin añadir dependencias ni declarar lint aprobado. |
| Conservación de fuentes | 450 archivos de código/protegidos congelados; 184 backend idénticos a la regresión 1008 y frontend idéntico a 222/build final. Quince protegidos conservados en esta ejecución: PO, constitución, AGENTS, Seguimiento macro, dos Compose, SQL fuente/demo, cinco migraciones socios y dos PDF formales. |
| Auditoría | Código/loaders/propiedad/registro/manifiestos y correcciones API/UI aprobados sin hallazgos. audit_final_seed verificó directamente los dos JSON y 15 hashes protegidos. Auditoría documental/integral final aprobada sin hallazgos abiertos; la aprobación de código por sí sola no cierra CA77-07. |

Cierre CA→evidencia: CA77-01 guardias/preflight/esquema; CA77-02 catálogo/manifest/SQL; CA77-03 registro/repetición/collision/rollback; CA77-04 workflow/T01/plazos/ledger; CA77-05 recreación sin reseed. CA77-06 quedó verificado mediante el recorrido UI; CA77-07 quedó cerrado por la auditoría documental/integral final aprobada. CA77-00/08 y DP77-01/02/DEP77-02 conservan su cierre anterior.

Chequeo PO al inicio/durante/final: sección 7 de Notas del PO y RN77-01–04 corregidas; roles/vigencia/facultades/saldos independientes, sin año ficticio para G57 ni avance en fecha fija. DEP77-01 y DP77-FAC-01 conservan funciones/reglas fuera del alcance; no impiden cerrar la carga y recorridos incluidos ni se presentan como implementados.


### Correcciones de recorridos incluidos y regresión definitiva

- **Identidad de borradores (TS77.22):** el proveedor resuelve IDs institucionales; se conservan snapshots históricos, orden y legajo real nulo. Sin PK local como fallback ni escrituras en GET; DatabaseError devuelve 503 genérico. [Doce oráculos nuevos](../../backend/tests/expedientes/test_mis_solicitudes_identity.py) y HTTP reforzado: rojo 8 fallos/5 verdes (14,97 s); con baseline, 19 verdes (17,31 s). El servidor real pasa 78 controles incluyendo involucrados de cuatro T01; navegador muestra Malena/99077013 en authority.draft.
- **Contraste y geometría (TS77.24):** seis oráculos iniciales, cinco fallos/uno verde (0,153 s) → seis verdes (0,132 s). Cuatro fallos adicionales de badges antes del fix (0,095 s) → ocho verdes (0,062 s). Se conservan fondos semánticos/textos/signos; colores del ranking intactos. Ficha y toolbar se comprobaron con viewport real/Tab/scroll, sin simular mediaqueries en Karma.
- **Detalle T01 (TS77.22/24):** [cinco oráculos con MatDialog real](../../frontend/src/app/solicitar-puntos/solicitud-detalle-dialog/solicitud-detalle-dialog.accessibility.spec.ts), rojo ampliado 5/5 (0,129 s) con temas reales y composición RGBA → 5/5 verdes (0,109 s). HTML/SCSS mantienen campos/snapshots; título/nombre/foco de Cerrar, contención/scroll y tokens reparados. Navegador real desktop/360/414 confirma footer visible, Tab/Shift+Tab/Escape, contenido completo y contraste medido de badges ≥5,93:1.
- **Frontend final (TS77.26):** **222 pruebas verdes, 0 errores**, Chrome154, 0,907 s (0,725 s de pruebas); build **6fae4265931dc3f8**, 7854 ms, UTC 2026-10-12T20:52:32.414Z. Los resultados 205/207/213/217 y sus builds son etapas anteriores. Lint heredado ausente sigue clasificado, sin declararlo aprobado.
- **Aceptación:** CA77-01–06 verificados con las pruebas/mediciones descritas; CA77-07 cerrado por auditoría final aprobada sin hallazgos abiertos. CA77-00/08 y DP77-01/02/DEP77-02 cerrados. DEP77-01 y DP77-FAC-01 son funciones/reglas de otras US y mantienen su delimitación.


### Dictamen final y cierre de SCRUM-77

audit_final_seed aprobó la revisión integral sin hallazgos abiertos: código, contratos, oráculos, dos manifiestos idénticos, protección de quince archivos, consistencia de diez documentos activos y recorridos reales. La revisión fue independiente y en lectura; no ejecutó runners ni modificó datos. Root coordinó las suites MySQL/Karma y pruebas de infraestructura/HTTP.

TS77.27 y CA77-07 quedan cerrados; **TS77.01–43 completas y sincronizadas**, **CA77-00–08 verificados**. Se completaron las 19 unidades TS77.09–27 autorizadas en conjunto y el prerrequisito TS77.08, sin confirmaciones individuales. No quedan tareas de implementación de SCRUM-77. Lint heredado ausente y funciones/reglas externas DEP77-01/DP77-FAC-01 mantienen su clasificación; no se presentan como nuevos pendientes de esta US.

Después del navegador y suites: los 49 esquemas/huellas de filas/conteos y contadores siguen idénticos; 450 fuentes/protegidos iguales al freeze de las suites, quince protegidos intactos. Demo host 4202 HTTP200 y API8002 health ok/db connected. La pestaña de prueba, tema y sesión se restauraron; el servidor local permanece disponible según el runbook.


## Verificación de TS77.44–46

El usuario aprobó la UAT original y autorizó sincronizar con main/agregar Juniors el 12/10/2026. HEAD avanzó de 0596c64 a 73a2d8a (PR #49), con stash de seguridad conservado y cinco conflictos combinados. El centro de notificaciones y las validaciones de calendario de main conviven con identidad institucional, filtros y accesibilidad de SCRUM-77. Notas del PO, constitución y seguimiento macro se conservaron en esta ampliación.

prepare_demo_schema aplicó cinco migraciones: 49→52 tablas y 34→39 registros de migración. Todas las filas previas se preservaron; los seis expedientes conservaron sus diecisiete columnas originales al añadir calendario_version_id. La demo ya incluía una causa y una T01 de UAT: quedaron seis y cinco totales, frente a cinco/cuatro fixtures. No se eliminaron ni se adoptaron como propiedad del seed.

El catálogo extendió el mismo perfil v1: cuatro Juniors G62/G63, años 2/1, cuentas SOCIO habilitadas y saldo cero. Veinte fichas, quince usuarios/perfiles y 188 referencias. Las 52 tablas conservaron cada fila anterior y los ocho asientos/+1. Primera/repetición produjeron el mismo SHA-256 de manifiesto 8d6ebe7e12143c620181a88e7cd46843ecdc6603f86cbbd9f0fa91ce31b26efe; esquemas, huellas de filas y conteos idénticos. El ensayo no pretende acreditar una nueva recreación de contenedor; la persistencia original se conserva como antecedente.

TDD catálogo: ocho fallos esperados/sesenta verdes antes de implementar; set focal final de setenta verdes, cero errores, 19,84 s. Upgrade en MySQL scratch preservó filas/credenciales editadas, numeración y puntos; se acreditaron colisión y rollback después del tercer Junior. HTTP local: 111 controles esperados (87×200, 3×401, 20×403, 1×404), colecciones completas cotejadas con BD y subconjunto de fixtures verificado sin ocultar las altas UAT. La auditoría reforzó el cotejo exacto de búsqueda de Mis Solicitudes antes de la ejecución final. Todos los hashes de las 52 tablas permanecieron iguales durante los GET/login.

El hallazgo de teclado del detalle custom se reprodujo (un fallo/dos verdes) y se corrigió con tres oráculos CDK/portal reales, sin reiniciar los avisos ni sus temporizadores. Navegador real confirmó cuatro Juniors, fichas de años 1/2, login SOCIO/permisos, avisos de login/T01/ficha ajena, cierre X por Tab/Enter en MatDialog y detalle custom, navegación sin pérdida del aviso y Escape con restauración. Móvil 360×800: aviso contenido (x16/ancho328), sin overflow horizontal; viewport restaurado. Esta ampliación GUI se verificó en tema claro.

Regresión backend completa: 1056 verdes, ocho controles Compose omitidos por mount sólo backend, 729,05 s. Los ocho se ejecutaron aparte con Compose real saneado y hashes fuente comprobados: ocho verdes, 0,26 s. Total: 1064 casos verificados, cero errores y cero controles omitidos sin verificar. Cobertura 93,91% en los veintidós módulos de negocio explícitos, 2363 sentencias/144 sin cubrir. Frontend: 278 verdes, cero errores, Chrome154, 1,051 s. Build b03663973a049f50 correcto, 12186 ms. Ruff global/formato de siete Python cambiados, Django check y makemigrations sin cambios, correctos. Lint continúa con el builder TSLint heredado ausente.

[Registro de ampliación](../../docs/gestion-proyecto/VERIFICACION_AMPLIACION_SCRUM-77.json), [HTTP y conservación](../../docs/gestion-proyecto/evidencias/scrum77-ampliacion/http-local.json), [verificador reproducible](../../docs/gestion-proyecto/evidencias/scrum77-ampliacion/verificar_http.py) y [navegador/capturas](../../docs/gestion-proyecto/VERIFICACION_UI_SCRUM-77.md#verificación-posterior-a-uat--ts774446). Auditoría final independiente aprobada para TS77.44–46 y CA77-09, sin hallazgos abiertos. Los 408 hashes fuente y 220 referencias locales de siete documentos fueron cotejados por el auditor; la QA central valida todo el conjunto documental.


UAT de la ampliación aprobada por el usuario el 12/10/2026. El usuario autorizó publicar esta rama y abrir la PR hacia main, sin mergearla.

## Corrección de CI — PR #54

El usuario autorizó revisar y corregir cualquier fallo de CI el 12/10/2026, manteniendo la PR abierta sin merge. El run 38314352466 pasó Ruff/formato y frontend (278 tests/build), pero pytest terminó con 934 verdes/130 errores MySQL 1044: el usuario CI no tenía permisos para las bases UUID test_scrum77_bootstrap_* y test_scrum77_ddl_*.

- [x] **TS77.47 Corregir permisos de los schemas CI (25 min):** Grants acotados y guiones bajos literales para las dos familias de scratch; usuario de prueba/checks conservados. Reproducción/auditoría aprobadas y fe468b8 publicado. Los runs PR 38316123126 y push 38316117765 aprobaron cada uno 1064 backend/278 frontend, Ruff/formato y build, sin errores ni merge. [Evidencia](../../docs/gestion-proyecto/VERIFICACION_CI_PR54.md).

## Corrección de saldo en Mis Expedientes — PR #54

El usuario autorizó el 12/10/2026 resolver la diferencia de saldo con ranking. RF77-15/CA77-10 formalizan la lectura propia desde el libro mayor; el listado y los descargos conservan su alcance.

- [x] **TS77.48 Leer saldo propio desde el libro mayor (25 min):** GET autenticado de saldo, identidad institucional inequívoca, permisos y errores; TDD de fuentes, individualización y consulta sin escrituras.
- [x] **TS77.49 Conectar widget de Mis Expedientes (25 min):** Contrato tipado y lectura cancelable por sesión; estados de carga/error y saldo real; TDD DOM y carreras, sin sumar puntos pendientes.
- [x] **TS77.50 Verificar corrección integrada (25 min):** HTTP/SQL y navegador sobre demo, regresiones/build, auditoría independiente, documentación y publicación en PR #54; verificar los checks del último commit sin merge.
- [x] **TS77.51 Unificar saldos de las fichas (25 min):** Lector compartido para identidad local/institucional; saldo desconocido explícito y errores de base; modal con dato actual sin snapshot anterior y contratos válidos. TDD y auditoría, sin escrituras de puntos.

## Escenas de todos los estados — PR #54

El usuario autorizó agregar diez causas adicionales el 12/10/2026; RF77-16/CA77-11 incorporan escenas históricas sintéticas y sus respaldos, conservando las causas previas.

- [x] **TS77.52 Definir catálogo de estados avanzados (25 min):** Diez escenas 3/1/2/4, referencias, fechas pasadas, destinatarios y puntos individualizados; TDD de validación.
- [x] **TS77.53 Importar escenas históricas coherentes (25 min):** Inserciones nuevas con numeración, plazo, secuencia de estados, actor/motivo y propiedad, sin alterar escenas previas ni relojes globales; TDD MySQL.
- [x] **TS77.54 Respaldar emitidos y upgrade aditivo (25 min):** Cuatro resoluciones/expedientes/asientos, relaciones verificables y saldo esperado; TDD de conservación/repetición/colisión/rollback.
- [x] **TS77.55 Verificar demo ampliada (25 min):** Carga/repetición sobre demo con UAT, HTTP/SQL de seis estados y saldos, navegador, suites, auditoría y CI de PR #54, sin merge.
- [x] **TS77.56 Preservar los seis estados en la SPA (25 min):** Corregir la conversión que agrupa firma en revisión y envío en firma; TDD de contrato y distribución de las seis columnas, tabla/detalle coherentes, sin modificar estados persistidos.

## Resoluciones que respaldan el saldo — PR #54

El usuario solicitó hacer visible el respaldo emitido de todos los puntos, incluidos los históricos de 99077001. RF77-17/CA77-12 incorporan la lectura de asientos y actos existentes en Mis Expedientes y fichas locales/institucionales bajo sus permisos vigentes.

- [x] **TS77.57 Exponer historial respaldado (25 min):** Identidad/permisos, lectura consistente de asientos/expedientes/resoluciones y enlaces managed acreditados; TDD de atribución, errores y consulta sin escrituras.
- [x] **TS77.58 Mostrar resoluciones aplicadas (25 min):** Widget/historial del mismo DTO y tabla/modal accesibles; contratos, sesiones y estados de cero/desconocido/error, TDD frontend.
- [x] **TS77.59 Verificar trazabilidad visible (25 min):** Todos los asientos por cuenta comparados con SQL/ranking/fichas, navegador, regresiones/cobertura, auditoría y CI final; conservar cantidades/datos previos y PR sin merge.

### Verificación local de TS77.48–59

Código y pruebas finalizados: 1155 backend MySQL verdes sin errores ni omisiones (591,78 s), cobertura 94,17% en 25 módulos; 362 frontend verdes y build c8e0ecb245aa8807 correcto (11830 ms). Ruff global/formato de 169 archivos, Django check y ausencia de migraciones nuevas aprobados. La suite MySQL usó el usuario CI restringido; los ocho controles Compose se incluyeron mediante configuraciones reales saneadas y hashes fuente.

Carga aditiva/repetición conservó las 52 tablas y las altas de UAT. Dieciséis causas efectivas: 4/2/3/1/2/4 en los seis estados, quince fixtures; once respaldos y doce asientos, agregado +1. HTTP final: 197 controles sobre veinte historiales, nueve cuentas propias y cinco referencias locales sin identidad, con SQL/ranking/fichas y huellas sin escrituras. Navegador confirmó saldos/resoluciones propios, ficha autorizada sin cuenta operativa, seis etapas y modal/Escape/foco a 360 px. Auditoría de código aprobada sin hallazgos abiertos y PO contrastado, sin modificar las notas ni el seguimiento macro.

[Evidencia integrada](../../docs/gestion-proyecto/VERIFICACION_CORRECCIONES_PR54.md). El código publicado 4b2f077f331f0bafb1b6e2dccef3e300c3dc615e aprobó los cuatro checks de los runs PR 38323245266 y push 38323240371: 1155 backend y 362 frontend por evento, cero errores/omisiones, Ruff/formato y build f650aba676820783 correctos. Auditoría integral sin hallazgos; TS77.50/55/59 y CA77-10–12 cerradas. El control posterior al navegador mantuvo las 52 huellas completas y la numeración. PR #54 abierta hacia main, sin merge; las Notas del PO y el seguimiento macro siguen intactos.
