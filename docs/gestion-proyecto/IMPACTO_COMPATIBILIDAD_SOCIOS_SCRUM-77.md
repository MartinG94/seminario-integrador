# Impacto y compatibilidad de la clasificación social — SCRUM-77

**Fecha:** 11/10/2026. **Unidad:** TS77.29. **Baseline:** rama feature/US-S3-PO2-mysql-seed-g57-g60, commit 0596c64a1002fd06f135733c7090ae4480f7351f, con los artefactos de TS77.03–06 presentes en el checkout.

Esta unidad decide la representación y la transición técnica antes de implementar DEP77-02. No incorpora comportamiento nuevo, migraciones, cambios de esquema ni datos. Las decisiones siguientes son de implementación; las reglas de negocio siguen siendo las de la [spec 005](../../specs/005-mysql-seed-g57-g60/spec.md) y la [aclaración corregida del PO](../../specs/005-mysql-seed-g57-g60/aclaraciones-po.md). Las [Notas del PO](notasPO.md), sección 7, requieren MySQL operativo y fixtures representativos.

**Avance al 12/10/2026:** clasificación/contratos/SPA y seed integrados; repetición/persistencia/HTTP/recorridos reales aprobados. 1008 backend/222 frontend verdes, cobertura 93,91% en 22 módulos y build correcto. Borradores resuelven el proveedor institucional, sin PK local; modales/filtros/temas/móvil/teclado corregidos y verificados. Auditoría integral final aprobada sin hallazgos abiertos. Categoría, rol, vigencia y facultades independientes; antecedentes históricos preservados. [Evidencia](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827).

## Reglas confirmadas y límites

- Junior: años 1 y 2; Senior: desde el año 3 dentro de la escala operativa vigente. No se amplía el rango 1–6 para representar G57.
- G57 es exviajero fuera de esa escala. G58/G59/G60 corresponden a años 6/5/4; G63 es la referencia de año 1. Es el corte confirmado por el PO, no una fórmula perpetua sobre el número de grupo.
- Un grupo comparte año social sin excepciones individuales. El avance ocurre en la asamblea de recambio, de fecha variable; su automatización queda fuera de esta US.
- Categoría, vigencia, cargo, rol y saldo conservan significados distintos. La clasificación no otorga ni retira permisos por sí misma.
- En el baseline anterior a TS77.30, la constitución y documentos previos conservaban el corte 1–3/4–6. La aclaración posterior autorizada define el objetivo nuevo; TS77.30 alinea los documentos activos. El [antecedente de la constitución](../constitution.md#antecedentes) conserva commit y localizador del corte anterior, sin modificar las Notas del PO ni el seguimiento macro.

## Inventario verificable del baseline

Se usaron search_graph, get_code_snippet, trace_path y search_code sobre el índice seminario-integrador. Las rutas y fuentes se contrastaron con el checkout; los resultados del grafo no se consideran una enumeración completa de llamadas dinámicas, plantillas o migraciones excluidas del índice.

| Área / evidencia | Comportamiento relevado e impacto | Unidad de adecuación |
|---|---|---|
| [SocialCategory y Socio](../../backend/socios/models.py#L26) | Baseline relevado en TS77.29: PASSIVE/ACTIVE, social_year obligatorio, validadores 1–6, corte en 4 y category de longitud máxima 10. TS77.31 incorpora EX_TRAVELER/null y longitud 12; TS77.32 implementa JUNIOR 1/2 y SENIOR 3–6. TS77.33 implementa el recálculo histórico local por año/situación. | TS77.31/32/33 |
| [Migración inicial local](../../backend/socios/migrations/0001_initial.py#L39) | Persiste el contrato previo. No debe reescribirse una migración aplicada: se necesitan migraciones nuevas y modelos históricos para los datos. | TS77.31/33 |
| [Login y perfil](../../backend/accounts/serializers.py#L80), [me](../../backend/accounts/views.py#L28), [refresh](../../backend/accounts/urls.py#L10) | Perfil y JWT exponen category; el perfil no incluye año. Login usa el dato persistido y refresh es TokenRefreshView estándar: un claim emitido previamente puede conservar el valor antiguo. | TS77.33/42 |
| [Permisos](../../backend/accounts/permissions.py#L20) y [RBAC](../especificaciones/RBAC-SGD-AVEIT.md) | HasAnyRole relee role/is_enabled de la base, sin decidir por category. T01 y legajo conservan controles de rol, vigencia y propiedad. socio_tipoSocio representa cargos; no es un marcador de exviajero. | Invariante TS77.31–43 |
| [DTO y enums institucionales](../../backend/padron/domain.py#L17), [clasificador](../../backend/padron/services.py#L29) | PASSIVE/ACTIVE/UNKNOWN; rangos 1–3/4–6 y social_year tipado int. No hay condición de exviajero. Año inválido es UNKNOWN. | TS77.34 |
| [Socio unmanaged](../../backend/padron/models.py#L90), [DDL aprobado](../../backend/core/sql/scrum77_legacy_schema.sql#L79) | TS77.38 declara anoSocial INT nullable sólo en el DDL demo; TS77.39 ya aplica/repite la transición en la demo preparada, con auditoría integral aprobada sin hallazgos pendientes. Un modelo managed=False no altera el contrato físico; el fuente institucional permanece intacto. | TS77.38/39 |
| [Adaptador de padrón](../../backend/padron/adapters.py#L270) | Mapea categoría desde anoSocial y vigencia desde historial/baja. list_socios usa rangos SQL antes de paginar; el nuevo marcador debe participar tanto en la proyección como en el filtro y count. Mock y adaptador real deben coincidir. | TS77.40/34 |
| [Serializer de padrón](../../backend/padron/serializers.py#L19) | Filtro ChoiceField con PASSIVE/ACTIVE/UNKNOWN; social_year no admite null. Hay que validar aliases y tipos sin mezclar is_active/membership_status con categoría. | TS77.34 |
| [Ranking: respuesta](../../backend/ranking/serializers.py#L74), [consulta](../../backend/ranking/services.py#L127), [vista](../../backend/ranking/views.py#L67) | Respuesta y filtros usan ACTIVO/PASIVO. Año null/0 termina presentado como PASIVO; año >=4 se toma como ACTIVO sin límite superior. Debe compartir clasificación con padrón, distinguir UNKNOWN y filtrar en SQL. | TS77.34 |
| [Adaptador de legajo](../../backend/socios/views.py#L28), [serializer](../../backend/socios/serializers.py#L6) | get_category_display devuelve Pasivo para cualquier código diferente de ACTIVE, incluido UNKNOWN. La proyección institucional debe conservar EX_TRAVELER/null y una etiqueta explícita para UNKNOWN. | TS77.34 |
| [Resolución de legajo](../../backend/socios/views.py#L104), [propiedad](../../backend/socios/views.py#L57), [apertura desde ranking](../../frontend/src/app/ranking-socios/ranking-socios.component.ts#L28) | El ranking envía el ID institucional, pero get_object busca antes por PK/legajo local: una colisión numérica puede devolver otra persona. CanViewSocioLegajo compara PK sólo para objetos con user; el adaptador institucional no tiene user y se compara su legajo. Su fallback str(nroSocio) cuando falta legajo no acredita propiedad institucional. | TS77.43/35 |
| [Puente de emisión T01](../../backend/expedientes/serializers.py#L367), [snapshot](../../backend/expedientes/serializers.py#L318), [involucrados](../../backend/expedientes/serializers.py#L624) | Al materializar un socio institucional usa social_year or 1: un exviajero terminaría con año ficticio. Busca primero por PK local y después por legajo/email; no puede asumirse que la PK local coincida con nroSocio. El snapshot guarda clasificación/año; el listado actual de involucrados no expone esos campos, pero debe conservar la identidad correcta. | TS77.41 |
| [Perfil Angular](../../frontend/src/app/services/auth.service.ts#L10) | Unión PASSIVE/ACTIVE y perfil restaurado de localStorage sin consultar me. El caché no contiene año: no permite distinguir el antiguo PASSIVE de 3.º. | TS77.35/42 |
| [DTO de legajo/lista](../../frontend/src/app/services/socio-api.service.ts#L7), [modal](../../frontend/src/app/ranking-socios/socio-legajo-dialog/socio-legajo-dialog.component.ts#L64), [plantilla](../../frontend/src/app/ranking-socios/socio-legajo-dialog/socio-legajo-dialog.component.html#L71) | social_year:number y dos categorías; badge ACTIVE/else. La plantilla siempre añade º Año. Requiere tipos/estados explícitos y mostrar Exviajero cuando no corresponde año social. | TS77.35/36 |
| [Ranking Angular](../../frontend/src/app/ranking-socios/ranking-socio.model.ts#L9), [filtros](../../frontend/src/app/ranking-socios/ranking-socios.component.ts#L12), [opciones](../../frontend/src/app/ranking-socios/ranking-socios.component.html#L57) | ACTIVO/PASIVO en DTO y filtro local. Debe adoptar los códigos canónicos y etiquetas nuevas, conservando IDs, saldo, paginación y orden existentes. | TS77.35/36 |
| [Selector de socios](../../frontend/src/app/services/padron-api.service.ts#L25) | Consume is_active=true y todas las páginas. No filtra por categoría: ser exviajero no debe deshabilitar al socio ni retirarlo del selector por defecto. No se añade Grupo al DTO en esta tarea. | Regresión TS77.37/41 |
| [seed_demo](../../backend/socios/management/commands/seed_demo.py#L19), [mock ranking](../../frontend/src/app/ranking-socios/ranking.mock.ts), [fixtures](../../backend/tests/conftest.py#L29) | El seed omite legajos existentes; repetirlo no migra categorías. Los fixtures/asserts usan vocabularios y corte antiguos; el mock no tiene año para recalcular PASSIVE. Deben actualizarse en sus unidades, sin alterar credenciales ni datos ajenos. | TS77.33/36/37 |
| [Bootstrap](../../backend/core/demo_schema.py), [comando](../../backend/core/management/commands/prepare_demo_schema.py), [oráculos DDL](../../backend/tests/infrastructure/test_scrum77_legacy_ddl.py) | Contrato físico exacto y migraciones antes de CREATE de tablas legadas. La demo existente rechazaría una nulabilidad nueva sin transición. Una FK managed a socio_lista fallaría al migrar una base vacía antes del DDL. | TS77.38/39/40 |

Los usos de activo que describen cuenta habilitada, estado procesal, CSS o archivo pasivo no son categorías sociales. No se aplica un reemplazo global de palabras.

## Decisiones de representación

### D77-01 — Vocabulario y año social

Se adopta el siguiente contrato canónico. Se conservan las claves category y categoria según su endpoint, las rutas y las identidades actuales.

| Código | Etiqueta | Año social | Fuente de clasificación |
|---|---|---|---|
| JUNIOR | Junior | 1 o 2 | Año válido dentro de la escala. |
| SENIOR | Senior | 3, 4, 5 o 6 | Año válido dentro de la escala. |
| EX_TRAVELER | Exviajero | null | Condición explícita confirmada; fuera de Junior/Senior. |
| UNKNOWN | Sin clasificación | null cuando el año no es válido | Lectura institucional incompleta o anómala, sin condición confirmada. No se persiste como socio operativo válido. |

EX_TRAVELER es la representación de la condición en el campo de clasificación existente; no implica que el exviajero pertenezca a la escala Junior/Senior. Su nombre técnico tiene 11 caracteres; TS77.31 amplía category a max_length=12 mediante una migración nueva.

En el modelo operativo se requiere la combinación explícita category=EX_TRAVELER y social_year=null. Un año nulo sin esa condición, un EX_TRAVELER con año de la escala y los años 0/7 deben rechazarse. Para socios de la escala la categoría se deriva del año, no de una etiqueta proporcionada por el cliente. El clasificador puro de años no interpreta None como exviajero.

### D77-02 — Fuente institucional explícita

La condición se registrará en un metadato managed propio del proyecto, separado de la ficha institucional. Contendrá el identificador institucional real nroSocio, la condición EX_TRAVELER y la referencia al corte/fuente que la confirma. No utilizará idTipoSocio, cargo, baja, membership_status, is_active ni un año inválido como señales de esa condición.

Para el seed, el manifiesto versionado resolverá G57 por la identidad de grupo y las referencias institucionales persistidas, y asociará cada socio ficticio de ese grupo con su metadato. No equiparará IDs institucionales, PK local, legajo o número de grupo. La escritura deberá acreditar existencia del socio, propiedad del fixture, asociación al grupo del corte confirmado y ausencia de un marcador contradictorio; un marcador huérfano o ajeno abortará la carga transaccional.

La referencia institucional será un identificador único validado en aplicación. No se incorporará una FK física desde la migración managed hacia socio_lista, porque en el bootstrap vacío esa tabla todavía no existe al ejecutar migrate. Esta decisión exige validación de asociación en el servicio escritor, conciliación posterior y pruebas de integridad; la unicidad por sí sola no basta.

La lectura dará prioridad a la condición confirmada y proyectará EX_TRAVELER/null. En ausencia de marcador, clasificará únicamente años válidos y tratará los restantes como UNKNOWN. Ningún dato desconocido se convierte automáticamente en exviajero. Este diseño cubre el catálogo sintético autorizado; clasificar datos ajenos al catálogo exige una fuente confirmada y sus referencias reales, sin extrapolar el caso de G57 a todos los registros anómalos.

### D77-03 — Nulabilidad de la demo y evolución explícita

La ficha ficticia de G57 necesita anoSocial=null. Se ajustará la nulabilidad de esa columna en el DDL específico de la demo, conservando nombre, tipo firmado, FKs y demás contratos. Se documentará como una tercera adaptación deliberada frente al SQL fuente, además de las dos precisiones Decimal ya aprobadas. El dump fuente y la base institucional permanecen fuera de esa modificación.

Se separan dos unidades: definir/probar el contrato nuevo para una base vacía y transicionar una demo ya preparada. La transición deberá acreditar perfil demo, identidad, sesión y grants, adquirir el mismo bloqueo por base y comparar el contrato anterior íntegro antes del único ALTER autorizado de anoSocial. Después comprobará el contrato nuevo y conservación de filas/IDs/FKs. Si ya está actualizado será una operación vacía; cualquier divergencia adicional se rechazará. No se reinicia el volumen, no se recrean tablas, no se modifican saldos/expedientes y no se promete rollback de DDL MySQL.

prepare_demo_schema mantendrá su contrato estricto: no relajará globalmente la nulabilidad ni esconderá divergencias mediante IF NOT EXISTS. El caso viejo compatible se reconocerá sólo en la transición prevista, con ambas versiones identificadas. Las migraciones managed nuevas deben seguir funcionando antes del cierre legado en una demo vacía. Los oráculos de TS77.05/06 y el mapeo deberán incorporar esta evolución en sus unidades.

## Compatibilidad de datos y contratos

### D77-04 — Recalcular datos locales

Se utilizará una migración de datos nueva con modelos históricos. Para filas dentro de la escala se calculará Junior/Senior por año: un PASSIVE de año 3 pasa a SENIOR; un PASSIVE de año 1/2 pasa a JUNIOR. Un ACTIVE no prueba por sí solo ni año ni condición de exviajero.

Antes de escribir se verificará que todas las filas alcanzadas tienen año/situación resolubles. Las anomalías sin fuente confirmada impedirán completar la migración; no se les asignará año ni condición ficticios. Se conservarán PKs, usuarios, contraseñas, role, is_enabled, relaciones, saldos y auditorías. No se corregirán categorías con SQL manual sobre saldos/expedientes ni con una nueva ejecución de seed_demo.

No se promete una reversión sin pérdida mediante JUNIOR→PASSIVE/SENIOR→ACTIVE: el corte del año 3 cambió. TS77.33 conserva año/situación y revierte semánticamente por año al corte anterior: PASSIVE en 1–3 y ACTIVE en 4–6. Mantiene EX_TRAVELER/null porque la predecesora 0003 ya puede representarlo; no recupera etiquetas arbitrarias originales ni deshace ediciones posteriores. Un retroceso adicional hasta 0001 conserva la guardia de 0002, que rechaza exviajeros antes de alterar columnas; no degrada sus datos para aparentar compatibilidad.

### D77-05 — Respuestas canónicas y aliases de consulta

Las respuestas de clasificación vigente y los snapshots nuevos utilizarán JUNIOR/SENIOR/EX_TRAVELER; padrón, ranking y legajo institucional también contemplarán UNKNOWN. Esas representaciones no devolverán códigos obsoletos ni renombrarán category/categoria para este cambio. social_year aceptará null en los DTOs que lo exponen. Los snapshots históricos quedan exceptuados: conservan los códigos originales y pueden exponerlos al consultar su evidencia, sin presentarlos como clasificación vigente ni reescribirlos.

Sólo los filtros de entrada mantendrán equivalencias explícitas:

| Entrada histórica | Filtro canónico |
|---|---|
| PASSIVE o PASIVO | JUNIOR |
| ACTIVE o ACTIVO | SENIOR |

Los aliases aplican la **regla nueva**: PASIVO no conserva una consulta 1–3 y ACTIVO no conserva una consulta 4–6. Esta diferencia se documentará en los contratos; son una ayuda de transición de nombres, no una promesa de conservar el significado anterior. Un alias no se usará para recalcular una fila, normalizar un perfil viejo ni reetiquetar un JWT. Valores desconocidos conservarán el rechazo HTTP 400 según las convenciones actuales.

La SPA y el backend deberán liberarse de forma coordinada después de TS77.37; los tipos estrictos anteriores no aceptan EX_TRAVELER ni años nulos. No se declara compatibilidad de salida con consumidores externos no relevados. En el checkout se identificó la SPA como consumidor; la revisión no prueba ausencia de integraciones externas en otros entornos. No se cambia el prefijo /v1 en esta unidad.

### D77-06 — Perfil, caché y JWT

Un perfil persistido antiguo no contiene año y no puede normalizarse por reemplazo de PASSIVE/ACTIVE. Al recuperar una sesión, la SPA debe obtener el perfil canónico de GET /api/v1/auth/me/ y actualizar su caché; mientras no lo tenga no debe mostrar una clasificación inventada. Los errores deben seguir el tratamiento vigente de autenticación/HTTP, sin convertir un error de red en un cambio de categoría o de rol.

Login emitirá la clasificación persistida nueva. La actualización de refresh deberá leer la clasificación del socio vigente al emitir el nuevo access token, en lugar de traducir el claim antiguo; se respetarán las opciones y validaciones JWT existentes. Los tokens ya emitidos conservan sus claims históricos hasta renovarse o expirar. La autorización continuará consultando rol/vigencia en servidor: category no será una nueva condición de acceso. La UI mostrará categoría del perfil confirmado, no del claim de un token viejo.

### D77-07 — Puente T01 y legajo

La materialización del DTO institucional debe transmitir EX_TRAVELER/null explícitos y eliminar social_year or 1. Para DTOs anómalos sin clasificación suficiente, debe producir un error verificable antes de crear el socio operativo; no completar el año por defecto. Un socio local existente no pierde credenciales, rol ni vigencia por ser resuelto desde el padrón.

Las referencias se verificarán mediante el mapa de identidades y datos inequívocos; la igualdad de PKs de namespaces distintos no demuestra identidad. Una colisión no permite reutilizar un socio ajeno. Esta protección se verifica en la integración afectada; no autoriza una reestructuración general de identidad fuera de los recorridos de SCRUM-77.

Los snapshots ya emitidos conservarán su contenido histórico. Las nuevas representaciones tendrán el vocabulario nuevo; no se reescribirán solicitudes emitidas, auditorías ni movimientos para eliminar términos antiguos de registros históricos.

### D77-08 — Identidad explícita en el legajo

La ruta actual de legajo y sus claves de respuesta se conservan. Se añadirá el parámetro opcional identity_source=local|institutional para resolver exclusivamente la identidad solicitada. La apertura desde ranking indicará institutional; una coincidencia con una PK local no habilitará un fallback a esa persona. Una fuente inválida devolverá HTTP 400.

Las llamadas anteriores sin parámetro seguirán funcionando cuando la identidad sea inequívoca. Si el identificador alcanza personas diferentes en los dos namespaces, se rechazará con HTTP 404 genérico, sin revelar candidatos; es un cambio deliberado frente a la prioridad local actual y debe documentarse como tal. No se declara ambigüedad por dos referencias que un vínculo confirmado demuestra que pertenecen a la misma persona.

Se conservarán los controles actuales de rol, habilitación y propiedad. Para acreditar propietario institucional se exige un vínculo confirmado o un legajo institucional real inequívoco: ni la igualdad de PKs ni el legajo artificial str(nroSocio) son evidencia suficiente. El adaptador actual carece de user y ya evita la rama de comparación directa de PK en CanViewSocioLegajo; el problema observado está en la resolución previa y en el fallback de legajo, no en un bypass demostrado por comparar PK del DTO.

TS77.43 deberá cubrir IDs distintos e iguales entre namespaces, fuente explícita con ausencia de registro, ambigüedad sin parámetro, propietario real, legajo ausente, acceso a otra persona denegado y permisos de autoridades conservados. TS77.35 integrará el parámetro en el consumidor Angular; no se cambia la autorización por categoría.

## Documentación y reglas que requieren fuente propia

TS77.30 debe revisar [constitución](../constitution.md), [spec del Walking Skeleton](../../specs/001-walking-skeleton/spec.md), [ADR-001](../adr/ADR-001-consumo-padron-institucional.md), [ERS](../especificaciones/ERS-SGD-AVEIT.md), [ERS del Tribunal](../especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md), [modelo de dominio](../especificaciones/MODELO_DOMINIO_SGD_AVEIT.md), [actores](../analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md) y [RBAC](../especificaciones/RBAC-SGD-AVEIT.md). El plan de proyecto y las referencias de proceso deben distinguir descripción vigente de antecedentes históricos; no se reescriben normas fuente ni evidencias de decisiones anteriores mediante reemplazo textual.

Las referencias anteriores a Socios Activos en firma, presidencia y elegibilidad del TD no determinan automáticamente si todo Senior desde 3.º o un exviajero puede ejercer esas facultades. [DP77-FAC-01](../constitution.md#facultades-pendientes) conserva la pregunta para las US que implementen esas reglas: **¿Qué condiciones de año, categoría, cargo y habilitación rigen la elegibilidad y firma de titulares/suplentes del TD y la presidencia de subcomisiones, incluyendo 3.º año y exviajeros?** Es una regla independiente y fuera del alcance de firma/emisión de SCRUM-77; no bloquea clasificación, ni autoriza modificar los permisos existentes.

No queda una pregunta necesaria al PO para elegir la representación técnica del seed sintético ya autorizado. Cantidades/rangos del catálogo siguen en DP77-02/TS77.07; la condición de otros socios exige evidencia antes de aplicar el marcador.

## Desglose y oráculos de las unidades futuras

El descubrimiento de nulabilidad, fuente institucional, puente T01, refresh e identidad del legajo exige separar trabajo que no cabe en el alcance original de TS77.31/34/35. Se conservan los IDs existentes y se agregan TS77.38–43; TS77.38/39 completan contrato/transición, TS77.40/34/41/42 implementan metadato/lectores/T01/JWT con cierre integral aprobado sin hallazgos pendientes. TS77.43 y TS77.35–37 conservan sus pendientes en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

| Unidad | Entrega y oráculo obligatorio |
|---|---|
| TS77.30 | Documentación activa conforme al PO, con vigencia/cargo/roles separados y pendientes de firma sin resolver por inferencia. |
| TS77.31 | Modelo local con EX_TRAVELER/null explícito, longitud 12 y migración managed nueva. Rechazar null sin condición, condición con año, 0 y 7; conservar rol/vigencia. |
| TS77.32 | Clasificador local: años 1/2 Junior; 3/4/6 Senior. Escritura mediante save mantiene el invariante, incluidos caminos con update_fields. |
| TS77.33 | Migración histórica de datos; año 3 recalculado, segunda ejecución estable y anomalía previa sin escrituras parciales. Credenciales, IDs y datos vinculados conservados. |
| TS77.38 | DDL demo y contratos con anoSocial nullable; cierre vacío con FKs activas. Comparación con fuente acepta sólo las tres adaptaciones documentadas. |
| TS77.39 | Transición demo anterior→nueva con una alteración acotada, preservación íntegra de datos y repetición vacía; divergencias y destinos ajenos rechazados. Bootstrap nuevo y demo existente comprobados. |
| TS77.40 | Metadato propio de condición institucional, referencia/procedencia e integridad verificadas sin FK hacia una tabla ausente durante migrate. Casos huérfano, ajeno, contradictorio y duplicado rechazados. |
| TS77.34 | DTOs, mock/DB, ranking, legajo y filtros comparten clasificación. EX_TRAVELER confirmado no aparece en Junior/Senior; UNKNOWN no se presenta como Junior. Count/paginación y aliases equivalentes en SQL. |
| TS77.41 | T01 materializa exviajero sin año ficticio, valida identidad y conserva socios/usuarios existentes. Involucrados y snapshots nuevos coherentes, históricos intactos. |
| TS77.42 | Login/refresh producen claims canónicos desde el socio actual; me devuelve el perfil vigente. Token histórico no modifica RBAC ni sustituye el dato actual; opciones JWT existentes conservadas. |
| TS77.43 | Legajo con fuente explícita, colisiones rechazadas sin fallback a otra persona y llamadas anteriores inequívocas conservadas. Fuente inválida 400 / ambigüedad sin parámetro 404; propiedad institucional acreditada sin PK ni legajo artificial. |
| TS77.35/36 | Tipos, caché hidratado por me, filtros, etiquetas, badge y año nulo coherentes; ranking abre legajo con identidad institucional. Fallos HTTP/red no inventan clasificación; mock y seed_demo compatibles. El selector por vigencia no excluye exviajeros por categoría. |
| TS77.37 | Regresión backend/frontend, auditoría de contratos/denominaciones y conservación de roles, vigencia, IDs, saldos y seis estados. Sólo entonces se libera la adecuación y se habilita TS77.07. |

Secuencia técnica fijada en TS77.29: TS77.30 → 31 → 32 → 33 → 38 → 39 → 40 → 34 → 41 → 42 → 43 → 35 → 36 → 37 → 07. Cada unidad requiere autorización y TDD cuando modifica código; el inventario por sí solo no acredita implementación. El 12/10/2026 el usuario autorizó expresamente TS77.40 y tres subagentes en paralelo para TS77.34/41/42; la integración conserva dependencias y serializa pytest/MySQL. Estas cuatro unidades están implementadas/verificadas, con cierre integral aprobado sin hallazgos pendientes. Los avances se registran aquí y en tasks.md. Próxima TS77.43 pendiente de confirmación; TS77.35–37 y seed pendientes.

## Verificación de esta revisión

Las decisiones y el inventario se auditan en lectura y se contrastan con las fuentes del PO. La suite ejecutada para esta unidad verifica el baseline conservado; no acredita todavía CA77-08. El resultado de pruebas, la comprobación física de sólo lectura, la auditoría y el seguimiento se registran en el [cierre de TS77.29](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7729).

## Adecuación documental de TS77.30

El usuario confirmó esta unidad el 11/10/2026. La actualización aplica RN77-01–04 a las reglas/documentación activa y mantiene el alcance técnico de D77-01–08. El código todavía conserva el baseline del inventario; este cierre documental no acredita CA77-08 ni habilita el catálogo/seed.

| Documentos | Tratamiento en esta unidad |
|---|---|
| [Constitución](../constitution.md), [README](../../README.md), [spec 001](../../specs/001-walking-skeleton/spec.md) | Regla vigente Junior 1.º–2.º / Senior desde 3.º, exviajero fuera de escala, corte confirmado y ciclo de asamblea variable. Separación de clasificación, vigencia, roles y facultades. |
| [ADR-001](../adr/ADR-001-consumo-padron-institucional.md), [RBAC](../especificaciones/RBAC-SGD-AVEIT.md) | Mapper como objetivo pendiente; condición exviajero desde fuente confirmada, UNKNOWN separado y padrón institucional de sólo lectura. Roles/grants actuales conservados; consecuencias de Sprint 1 delimitadas como históricas. |
| [ERS general](../especificaciones/ERS-SGD-AVEIT.md), [ERS del Tribunal](../especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md) | Clasificación, filtros, balances previstos y muestras de usabilidad con nomenclatura vigente. IDs, cantidades/umbrales y citas originales del relevamiento conservados; el cambio no implementa reportes ni firma. |
| [Modelo conceptual](../especificaciones/MODELO_DOMINIO_SGD_AVEIT.md), [actores](../analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md) | Mermaid/PlantUML, diccionario y trazabilidad distinguen clasificación de habilitación para firmar; facultades pendientes en DP77-FAC-01. Los descriptores de faltas y causales conservan su significado propio. |
| [Plan de proyecto](PLAN_DE_PROYECTO_SGD_AVEIT.md), [Estudio Inicial](../analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md), [BPMN relevado](../analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md), [escenarios de calidad](../especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md), [plantilla de CU](../especificaciones/PLANTILLA_CASO_DE_USO.md) | Referencias actuales alineadas; cronograma, estados/flujo del proceso y umbrales no se cambian. Historial de versiones, marco normativo y relato AS-IS mantienen su contexto original. |
| [Plan](../../specs/001-walking-skeleton/plan.md) y [tareas Sprint 1](../../specs/001-walking-skeleton/tasks.md), [backlog de septiembre](ANALISIS_INTEGRAL_BACKLOG_JIRA.md), [sistema legado](../analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md) | Encabezados explican su alcance histórico y enlazan las reglas vigentes; no se reescriben implementaciones, tareas cerradas ni conclusiones del relevamiento anterior. |

Las exportaciones PDF/DOCX/ODT de docs/formales y las normas fuente conservan su contenido; el README identifica las exportaciones como versiones históricas y remite al Markdown vigente. [SRC77-BASE-01](../../specs/005-mysql-seed-g57-g60/aclaraciones-po.md) ahora referencia el commit/antecedente, no una constitución activa con el corte anterior. Las Notas del PO y el seguimiento macro permanecen inalterados.

DP77-FAC-01 conserva la pregunta sobre elegibilidad, presidencia y firma en sus propias US, sin traducir Socios Activos a una facultad de todo Senior/exviajero. La evidencia de tests, controles documentales y auditoría se registra en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md). Al cierre de TS77.30, la siguiente unidad era TS77.31, posteriormente autorizada por el usuario.

## Representación local de TS77.31

TS77.31 implementa EX_TRAVELER/año nulo explícito, longitud 12 y validación coherente en el modelo y MySQL. La migración managed nueva conserva filas e identidades, detecta años históricos inválidos antes de alterar y protege la reversión si el esquema anterior no puede representar las filas. El modelo no cambia roles ni habilitación, ni clasifica al exviajero como Senior.

La demo conserva las 27 tablas legadas y sus 39 FKs. Sólo se evolucionó socios_socio y se registró la migración; no hay seed ni cambios a socio_lista. Las 594 pruebas backend pasan en MySQL y la auditoría integral aprobó el cierre sin hallazgos pendientes; evidencia detallada en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

Al cierre de TS77.31, CA77-08 y DEP77-02 seguían abiertos y el enum/corte de la escala aún conservaba el baseline. TS77.32 lo adecua en el ámbito local, como se registra a continuación. DP77-FAC-01 mantiene su alcance independiente.

## Cálculo local de TS77.32

El modelo local usa JUNIOR/SENIOR/EX_TRAVELER y deriva Junior en 1/2, Senior en 3–6. El helper rechaza año nulo, booleanos, valores no enteros y años fuera de escala; EX_TRAVELER requiere su marcador y año nulo explícitos. save conserva el par categoría/año en las escrituras de clasificación y mantiene independientes rol, vigencia, credenciales e identidad.

La [migración 0003](../../backend/socios/migrations/0003_local_social_categories.py) sólo cambia choices del estado Django; sqlmigrate informa no-op físico. No recategoriza filas: el ensayo preserva PASSIVE de año 3, ACTIVE de año 6 y EX_TRAVELER/null, credenciales, expediente, M2M y SHOW CREATE. Revertir 0003 restaura opciones del estado y conserva los valores persistidos; no restaura automáticamente el corte/nomenclatura previos.

La suite final pasa **621 pruebas**, con 109 casos enfocados verdes y 97% de cobertura de socios.models. Las expectativas de autenticación y legajo locales se adecuaron a los socios creados por el modelo; el código de cuentas y el adaptador institucional permanecen en sus unidades propias. La demo registra una migración sin alterar tablas de negocio; repetición vacía con hashes y conteos estables. Auditoría integral aprobada sin hallazgos pendientes; evidencia en [tasks.md](../../specs/005-mysql-seed-g57-g60/tasks.md).

Al cerrar TS77.32, las filas antiguas podían mantener PASSIVE/ACTIVE hasta TS77.33 o una escritura seleccionada de su clasificación. Padrón, ranking/filtros institucionales, T01 institucional, refresh/tokens previos y SPA mantienen sus tareas pendientes. CA77-08 y DEP77-02 continúan abiertos y la liberación transversal sigue dependiendo de TS77.37.

## Recálculo histórico local de TS77.33

La [migración de datos 0004](../../backend/socios/migrations/0004_recalculate_social_categories.py) implementa D77-04 con modelos históricos y alias explícito. Bloquea y valida el conjunto completo dentro de transaction.atomic antes de modificar únicamente category. Recalcula por año, incluido PASSIVE de 3.º→SENIOR, conserva EX_TRAVELER/null exacto y rechaza códigos/años incompatibles sin escrituras. No modifica saldos/expedientes mediante SQL manual ni ejecuta seed_demo.

Los [21 ensayos MySQL](../../backend/tests/infrastructure/test_scrum77_schema_bootstrap.py) verifican avance/reversión semántica, repetición directa sin UPDATE, anomalías tardías y rollback después de una escritura real. Conservan todas las tablas de negocio/columnas ajenas a category, incluidos usuarios/credenciales/grupos, roles/vigencia, relaciones, T01/snapshots originales, descargo, auditoría y libro mayor institucional con saldo no cero y sus FKs válidas. La identidad institucional no se equipara con la PK local.

La regresión completa pasó **642 pruebas, 0 errores**, con cobertura de sentencias de 0004 del **100%**. La demo aplicó una migración sin crear tablas ni cambiar esquemas/conteos de negocio; la repetición aplicó cero cambios y conservó los 47 hashes/conteos. Auditoría integral aprobada sin hallazgos pendientes. CA77-08 y DEP77-02 siguen abiertos por la integración institucional/consumidores. La siguiente unidad es TS77.38, previa confirmación.

## Contrato vacío de TS77.38

El DDL demo implementa la tercera adaptación D77-03: anoSocial INT firmado DEFAULT NULL, conservando las 27 tablas/39 FKs y todas las restantes definiciones frente al fuente, salvo las dos precisiones Decimal previas. El SQL fuente, modelo institucional y bootstrap conservan su contenido. El oráculo ORM documenta únicamente la diferencia física temporal de nulabilidad de anoSocial, hasta TS77.34.

**644 pruebas backend verdes, 0 errores**, incluidas 66 de DDL/bootstrap, acreditan cierre vacío/repetición y rechazo previo del contrato anterior con datos, migración pendiente y tabla faltante. Código/oráculos aprobados por auditoría independiente; auditoría integral aprobada sin hallazgos pendientes. La demo preparada conserva NOT NULL: prepare_demo_schema la rechaza por socio_lista y los 47 esquemas/conteos permanecen idénticos. Transición TS77.39 y metadato TS77.40 siguen pendientes. CA77-08 y DEP77-02 permanecen abiertos; no se siembra ni se altera información institucional.

## Transición protegida de la demo — TS77.39

El usuario autorizó la transición del contrato anterior de la demo preparada. El [comando separado](../../backend/core/management/commands/transition_demo_schema.py) exige el preflight y el contrato íntegro anterior o actual, comparte GET_LOCK con la preparación y ejecuta únicamente el ALTER de anoSocial. Conserva filas/IDs y contador vigente, con lectura sin caché y restauración de sesión aun ante error. Repetir sobre la versión actual no ejecuta DDL ni DML; el bootstrap mantiene su rechazo del contrato anterior.

**670 pruebas backend verdes, 0 errores**, incluidas 26 nuevas de transición, y código/oráculos aprobados sin hallazgos pendientes. Se corrigieron la lectura cacheada de AUTO_INCREMENT y la prueba de liberación de bloqueo, verificada desde una conexión distinta. La demo admite ahora anoSocial NULL: sólo cambió socio_lista y se conservaron las huellas de datos, conteos y contador; 47 tablas/32 registros de migración/27 legadas vacías/39 FKs. Transición y bootstrap estricto repetidos conservaron los 47 hashes y las huellas de datos, con cero alteraciones adicionales, creaciones o migraciones. Auditoría integral aprobada sin hallazgos pendientes. [Evidencia TS77.39](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7739).

El bloqueo no serializa otros escritores; se coordinan fuera de la ejecución. Un fallo posterior al ALTER puede dejar DDL aplicado, sin rollback prometido ni limpieza. NULL físico no acredita condición exviajero: TS77.40 y los consumidores siguientes conservan su alcance propio. CA77-08 y DEP77-02 permanecen abiertos; no se carga el catálogo ni se cambian roles, vigencia, facultades, puntos o normas fuente.

## Integración backend de TS77.40/34/41/42

La autorización expresa del usuario del 12/10/2026 habilita estas cuatro unidades y tres subagentes en paralelo, conservando las decisiones D77-01–08 y RN77-01–04. Root implementa el metadato; implement_ts7734, los lectores/filtros; implement_ts7741, T01; implement_ts7742, JWT. Revisiones cruzadas de código aprobadas; auditoría integral aprobada sin hallazgos pendientes.

| Decisión / unidad | Implementación y compatibilidad verificadas |
|---|---|
| D77-02/03 / TS77.40 | [Metadato managed](../../backend/socios/institutional_conditions.py) por nroSocio real, EX_TRAVELER y fuente/corte obligatorios. [0005](../../backend/socios/migrations/0005_institutional_membership_condition.py) crea PK/CHECK sin FK al legado y migra antes de las tablas institucionales. Escritor valida referencia/año nulo/conexión, bloquea en orden, rechaza contradicciones y repite sin DML. Guardias ORM no sustituyen conciliación externa ni propiedad/manifiesto futuros del seed. |
| D77-01/05/06 / TS77.34 | [Consulta común](../../backend/padron/querysets.py) para padrón/ranking, Exists del marcador, proyección canónica y filtros/count/paginación SQL sin N+1. UNKNOWN separado, EX_TRAVELER explícito/null; aliases históricos sólo de entrada. Omitir is_active no aplica False implícito. Año unmanaged nullable alineado con demo, sin ALTER; excepción ORM retirada. La resolución del namespace/propiedad del legajo sigue en TS77.43. |
| D77-01/05/07 / TS77.41 | [Servicio T01](../../backend/expedientes/services/solicitud_t01_service.py) y emisión atómica con EX_TRAVELER/null, ID contra DTO y persona acreditada por user_id institucional único o legajo real corroborado. Rechaza legajo compartido entre fichas mediante DISTINCT, admitiendo varias carreras de una misma persona. Sin PK como identidad, año por defecto ni cuenta ajena. Sincroniza sólo categoría/año; conserva credenciales/rol/vigencia/campos/vínculos, snapshots históricos y revierte fallos de apertura. |
| D77-06 / TS77.42 | [Refresh](../../backend/accounts/serializers.py) relee category actual en cada access y delega validaciones, identidad configurada, rotación, blacklist y duración a SimpleJWT 5.5.1 instalado. Otros claims se preservan, login/me mantienen claves y RBAC sigue leyendo rol/vigencia de DB. Tres rotaciones adicionales probadas con blacklist real habilitada sólo en proceso aislado; settings/dependencias intactos. Caché SPA sigue en TS77.35. |

**827 pruebas backend verdes, 0 errores y sin omisiones**, 157 casos nuevos sobre baseline 670; cobertura combinada 94,64%, umbral 80% cumplido. La auditoría de T01 reprodujo un P2 de legajo ambiguo antes de su corrección; los 36 casos finales incluyen reuso/creación rechazados y múltiples carreras válidas. Código y dictamen documental integral aprobados sin hallazgos pendientes; referencias D77 y descripción de pruebas JWT verificadas antes del cierre. [Evidencia detallada](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142).

La demo agrega la tabla de metadatos vacía: 48 tablas/33 registros de migración. post_migrate incorpora un content type y cuatro permisos de catálogo sin asignaciones; filas anteriores intactas y cambios de definición preexistentes sólo en sus tres contadores. Repetición sin migraciones/creaciones y mismos 48 hashes/huellas de datos/contador; 27 legadas vacías/39 FKs activas, cero usuarios/socios locales/metadatos y sin seed. Datos no vacíos verificados en esquemas de pruebas propios. No cambian notasPO, normas, constitución, seguimiento macro, migraciones aplicadas, Compose, DDL/fuente ni frontend.

CA77-08 y DEP77-02 permanecen abiertos hasta TS77.43/35/36/37. DP77-FAC-01 conserva las facultades en sus propias US; no se deducen desde la clasificación. La siguiente unidad es TS77.43, previa confirmación; no se inicia con este cierre ni se habilita aún catálogo/seed.

## Integración y catálogo de TS77.43/35/36/37/07

La autorización expresa del usuario habilita root en TS77.43 y agentes distintos para las otras cuatro unidades. Se respeta identidad/SPA → verificación transversal → aceptación del catálogo; la preparación de un módulo puro en paralelo no implica cargarlo. Los cuatro subagentes implement_ts7735, implement_ts7736, verify_ts7737 e implement_ts7707 participan sin ejecutar runners concurrentes.

| Decisión / unidad | Implementación y compatibilidad verificadas |
|---|---|
| D77-08 / TS77.43 | [Identidad](../../backend/socios/identity.py) separada por fuente opcional local/institutional; explícita resuelve sólo ID de su namespace, sin fallback por legajo ni por otra fuente. Llamada antigua conserva candidatos inequívocos, 404 genérico para ambigüedad entre/dentro de namespaces y 400 para fuente inválida/repetida. Propiedad institucional por user_id único real o legajo real corroborado mediante DISTINCT; email/PK coincidentes y legajo fabricado no asignan dueño/rol. Ausencia legajo=null y fallos de consultas sin detalles sensibles. Autoridades/propietario habilitado conservan acceso. Sólo lectura. |
| D77-05/06/08 / TS77.35 | [AuthService](../../frontend/src/app/services/auth.service.ts) conserva sesión/rol/identidad válidos y confirma categoría desde auth/me, sin aliases/JWT. Respuestas viejas no restauran sesiones ni pisan otro login; error HTTP/red deja categoría pendiente. Servicios/DTOs admiten cuatro categorías y nulos coherentes; vigencia separada, DTOs de snapshots T01 antiguos preservados. Ranking filtra sin cambiar puntos/paginación y abre legajo con fuente institutional. |
| D77-01/04/05 / TS77.36 | Etiquetas Junior/Senior/Exviajero/Sin clasificación y Sin legajo; año visible sólo en escala 1–6. Modal conserva fuente al reintentar y no deja ficha ajena anterior ante error. Badge usa tokens DESIGN. Mock de 33 identidades conserva IDs/nombres/saldos/subcomisiones y explicita corte sintético. seed_demo mantiene flujo/cuentas/roles/credenciales con pruebas de conservación y rollback; sólo ayuda/docstrings/tipos cambian en producción. |
| RNF77-06, CA77-08 / TS77.37 | Auditoría integral independiente de código/oráculos/denominaciones/diez documentos/PO aprobada sin hallazgos, incluida corrección P2 BIGINT local sin ampliar INT institucional y precisiones de label/campo legajo. CA77-08/DEP77-02 y CF77-01/02 cerrados. Runtime sólo conserva activo para vigencia/navegación y aliases históricos de entrada; snapshots antiguos no se reescriben. La clasificación no decide roles/firma/actividad ni altera puntos. |
| RF77-05, DP77-02 / TS77.07 | [Catálogo v1](CATALOGO_DATOS_DEMO_SCRUM-77.md) puro aceptado tras auditoría TS77.37; DP77-02 cerrado. 16 identidades/cuatro por grupo, fuente/corte explícitos, seis cuentas nuevas y cinco referencias seed_demo. Rangos candidatos y oráculos de escenas/asientos futuros fijados; no reserva IDs managed ni acredita ausencia de colisiones o carga en la demo. CA77-02 permanece abierto por manifiesto/carga/conciliación. |

**932 pruebas backend y 202 frontend verdes, 0 errores**, cobertura backend **94,72%**, build de producción final correcto. Dos oráculos con BIGINT físico 2147483648 fallan antes y pasan después de corregir el parser local en bases propias. Ruff/formato, Django check y ausencia de nuevas migraciones correctos. Lint frontend falla por el builder TSLint ausente; no se oculta ni se amplía esta US para reemplazar su pipeline. [Evidencia detallada](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).

Las 48 definiciones/huellas de filas/conteos y contador de la demo se conservan exactamente; 33 migraciones, 27 legadas vacías/39 FKs y metadato/usuarios/socios locales vacíos. Los 428 archivos del freeze de código/protegidos son idénticos después de la suite; 15 protegidos, dependencias/settings y migraciones aplicadas intactos. Sin carga ni avance anual automático. Próxima TS77.08 pendiente de confirmación; guardias/propiedad/carga/conciliación/persistencia/smoke conservan sus unidades y DP77-FAC-01 sus propias US.

## Integración de carga y lectura — TS77.08–27

La autorización global del usuario permite terminar TS77.09–27 con subagentes, sin confirmación por unidad; TS77.08 se incorpora como guardia previa. Propiedad, cuentas/padrón, causas/T01, antecedentes y manifiesto ya se implementaron y cargaron con corte confirmado. Las colisiones abortan, las referencias propias no se recrean y la repetición/persistencia conservan todos los datos/contadores.

La revisión de navegador identificó una lectura de borradores que confundía destinatarios institucionales con PK locales. MisSolicitudesT01Serializer conserva snapshots literales primero; sin snapshot consulta el proveedor de padrón, mantiene ID/orden/legajo real nulo y no materializa datos. DatabaseError devuelve 503 genérico. Doce casos nuevos y el HTTP fortalecido acreditan ausencia de fallback/escrituras; 19 focales verdes, 78 HTTP live y destinataria Malena verificada en GUI.

Regresión backend final: 1008 pruebas verdes, 0 errores, 618,46 s; cobertura 93,91% en los 22 módulos explícitos. Los ajustes visuales usan tokens/contención/foco existentes y no cambian roles, vigencia, actos, saldos o las funciones excluidas. El detalle T01 móvil y la regresión frontend final quedaron verificados, con 222 pruebas verdes/build correcto y auditoría independiente aprobada. [Evidencia](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827), [runbook](GUIA_CARGA_DEMO_SCRUM-77.md) y [registro](VERIFICACION_CARGA_SCRUM-77.json).
