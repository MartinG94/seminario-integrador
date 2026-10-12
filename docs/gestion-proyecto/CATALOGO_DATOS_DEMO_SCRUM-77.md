# Catálogo sintético de demostración — SCRUM-77

**Unidad:** TS77.07, [spec 005](../../specs/005-mysql-seed-g57-g60/spec.md), RF77-05 y DP77-02.

**Versión:** scrum77-g57-g60-v1. **Registro técnico:** 12/10/2026.

**Antecedente TS77.01–43:** perfil v1/corte confirmado cargado y conciliado: 16 identidades/cuatro por grupo y 162 referencias. Repetición y persistencia sin reseed verificadas; 1008 backend/222 frontend verdes, cobertura 93,91% en 22 módulos y build correcto. Recorridos reales aprobados; auditoría integral final aprobada sin hallazgos abiertos. [Evidencia](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827). La aceptación inicial TS77.07 se conserva como antecedente.

El [módulo puro](../../backend/socios/demo_catalog.py) conserva las claves y valores del conjunto; sus [oráculos](../../backend/tests/test_scrum77_catalog.py) verifican corte social, referencias, compatibilidad de campos y saldos esperados de una carga futura. El catálogo no abre conexiones, crea filas, asigna números de expediente ni modifica servicios de negocio.

## Corte y procedencia

| Campo | Valor |
|---|---|
| Perfil/version | scrum77-g57-g60-v1 |
| Corte social | PO-SCRUM77-CORTE-01 |
| Fuente | SRC77-PO-02; RN77-01–04, versión escrita corregida del PO |
| Registro técnico | 12/10/2026; identifica esta versión del catálogo, no la fecha de una asamblea |
| Volumen ampliado | 20 socios ficticios: cuatro por G57–G60 y dos por G62/G63 |

| Clave de grupo | nroGrupo / nombre | Año social | Clasificación |
|---|---|---:|---|
| group.g57 | 57 / G57 | NULL, fuera de escala | EX_TRAVELER / Exviajero |
| group.g58 | 58 / G58 | 6 | SENIOR / Senior |
| group.g59 | 59 / G59 | 5 | SENIOR / Senior |
| group.g60 | 60 / G60 | 4 | SENIOR / Senior |
| group.g62 | 62 / G62 | 2 | JUNIOR / Junior |
| group.g63 | 63 / G63 | 1 | JUNIOR / Junior |

El corte corresponde a la [respuesta corregida](../../specs/005-mysql-seed-g57-g60/aclaraciones-po.md), no a una fórmula permanente número de grupo → año. El conjunto original G57–G60 no contenía Juniors; la ampliación autorizada agrega dos integrantes G62 de 2.º año y dos G63 de 1.º año, manteniendo el corte explícito y la referencia G63 confirmada por el PO. El avance institucional ocurre en la asamblea de recambio, de fecha variable. No se calcula un pase anual desde la fecha del equipo ni desde los ingresos ficticios.

Los cuatro G57 requieren, además de anoSocial NULL, un marcador EX_TRAVELER por nroSocio en socios_institutionalmembershipcondition, con esta fuente y este corte. NULL, subcomisión o estado de membresía por sí solos no acreditan esa condición. La carga y la propiedad de estos marcadores corresponden a TS77.09/11.

## Identidades y rangos

| Namespace / campo | Valores del conjunto v1 | Restricción comprobada en el contrato |
|---|---|---|
| legacy / socio_lista.nroSocio | 770001–770020 | INT firmado positivo, PK, distinto del legajo académico |
| legacy / socio_estudio.nroLegajo | 99077001–99077020 | INT firmado positivo; cadena de ocho caracteres en socio local |
| legacy / socio_lista.nroDoc | 100077001–100077020 | INT firmado positivo; documentos ficticios de nueve cifras |
| legacy / socio_estudio.compositeKey | 1770001–1770020 | INT firmado positivo, PK satélite |
| legacy / socio_email.compositeKey | 2770001–2770020 | INT firmado positivo, PK satélite |
| legacy / socio_email.idEmail | 1 por cada socio | Identificador de correo por ficha; compositeKey es la PK real |
| legacy / grupo_lista.nroGrupo | 57–60, 62 y 63 | INT firmado; se verifica cada identidad de grupo |
| managed / auth_user.id y socios_socio.id | Sin asignar | Se obtienen al crear o resolver referencias propias; no se reserva una PK |
| managed / expedientes y T01 | Sin asignar | Numeración, fechas, IDs y auditoría mediante los servicios vigentes |
| legacy / antecedentes y resoluciones | Sin asignar | Referencias estables; sus IDs reales quedan en el manifiesto de TS77.09/15 |

Los rangos están fijados para este conjunto sintético y caben en el contrato físico [DDL demo](../../backend/core/sql/scrum77_legacy_schema.sql). No constituyen una reserva global ni prueban ausencia de filas ajenas. TS77.08/09/11 deben cotejar PKs, legajos, documentos, correos, usernames, códigos y registros de propiedad en la base destino antes de insertar; una coincidencia ajena aborta, aun si sus datos visibles son iguales. La representación local exige legajo único y correo único, y el vínculo institucional user_id debe identificar una sola ficha.

Los nombres y documentos son ficticios. Todos los correos usan @scrum77.test y no superan los 45 caracteres del satélite institucional. Los nombres/apellidos caben en VARCHAR(45), aunque un apellido largo y varios nombres con tildes permiten probar tablas, búsquedas y modales. No se reutilizan las personas mencionadas en las Notas del PO.

## Socios institucionales

El número de orden determina exclusivamente los cinco valores sintéticos declarados: nroSocio=770000+orden, nroLegajo=99077000+orden, nroDoc=100077000+orden, compositeKey de estudio=1770000+orden y de correo=2770000+orden. La clasificación se consulta en la tabla explícita del corte.

| Orden / clave estable | Nombre ficticio | nroSocio | nroLegajo | Subcomisión | Vigencia inicial |
|---|---|---:|---:|---|---|
| 01 / member.g57.01 | Ámbar Faro Demo | 770001 | 99077001 | Cómputos | Habilitado |
| 02 / member.g57.02 | Bastián Bruma Demo | 770002 | 99077002 | Recursos Humanos | En receso |
| 03 / member.g57.03 | Cira Cumbre Demo | 770003 | 99077003 | Relaciones Institucionales | Habilitado |
| 04 / member.g57.04 | Darío Duna Demo | 770004 | 99077004 | Cómputos | Habilitado |
| 05 / member.g58.01 | Elena Ensayo Demo | 770005 | 99077005 | Recursos Humanos | Habilitado |
| 06 / member.g58.02 | Félix Fábula Demo | 770006 | 99077006 | Relaciones Institucionales | Habilitado |
| 07 / member.g58.03 | Galatea García de las Nubes de Ensayo | 770007 | 99077007 | Cómputos | Habilitado |
| 08 / member.g58.04 | Héctor Horizonte Demo | 770008 | 99077008 | Recursos Humanos | Habilitado |
| 09 / member.g59.01 | Irina Isla Demo | 770009 | 99077009 | Relaciones Institucionales | Habilitado |
| 10 / member.g59.02 | Julián Jardín Demo | 770010 | 99077010 | Cómputos | Habilitado |
| 11 / member.g59.03 | Kira Kilómetro Demo | 770011 | 99077011 | Recursos Humanos | Habilitado |
| 12 / member.g59.04 | León Lago Demo | 770012 | 99077012 | Relaciones Institucionales | Habilitado |
| 13 / member.g60.01 | Malena Marea Demo | 770013 | 99077013 | Cómputos | Habilitado |
| 14 / member.g60.02 | Nereo Niebla Demo | 770014 | 99077014 | Recursos Humanos | Habilitado |
| 15 / member.g60.03 | Ópalo Orilla Demo | 770015 | 99077015 | Relaciones Institucionales | Habilitado |
| 16 / member.g60.04 | Paz Puente Demo | 770016 | 99077016 | Sin asignación, centinela 99 | En receso |
| 17 / member.g62.01 | Quimey Quimera Demo | 770017 | 99077017 | Cómputos | Habilitado |
| 18 / member.g62.02 | Rocío Rumbo Demo | 770018 | 99077018 | Recursos Humanos | Habilitado |
| 19 / member.g63.01 | Sol Sendero Demo | 770019 | 99077019 | Relaciones Institucionales | Habilitado |
| 20 / member.g63.02 | Tomás Trama Demo | 770020 | 99077020 | Cómputos | Habilitado |

Cada correo es gNN.XX@scrum77.test, coincidente con el sufijo de la clave de socio. El módulo incluye las fechas ficticias de nacimiento e ingreso para cumplir las columnas DATE obligatorias. No simulan hechos jurídicos, una asamblea ni la apertura de una causa; su única función es completar una ficha sintética válida.

## Referencias de catálogo y pertenencia

| Clave | Código institucional / nombre fuente | Correspondencia local |
|---|---|---|
| subcommission.computing | 1 / Cómputos | Subcomision.name=Cómputos, PK por resolver |
| subcommission.people | 2 / Recursos Humanos | Subcomision.name=Recursos Humanos, PK por resolver |
| subcommission.relations | 3 / Relaciones Institucionales | Subcomision.name=Relaciones Institucionales, PK por resolver |
| subcommission.unassigned | 99 / Sin Subcomisión | subcomision=NULL; el DTO institucional también proyecta None |

Las fichas asignadas se reparten siete en Cómputos, seis en Recursos Humanos y seis en Relaciones Institucionales. member.g60.04 conserva el centinela documentado: socio_lista.codSubcomision es NOT NULL y no admite omitir su destino FK.

Las demás referencias obligatorias son los códigos fuente documentados: codTipoDoc=1 (DNI), codSexo=3 (Otro), idTipoSocio=12 (Socio Ordinario), codEspecialidad=1 (Ingeniería en Sistemas de Información) y socio_motivoCambioEstado=1 (Regular). codEstadoSocio=1 para las dieciocho fichas habilitadas y 2 para las dos en receso. codEstadoCivil, codTurno, curso, aula y fechaBaja pueden permanecer NULL. ingresante y forzarCambioClave parten en False; cada correo parte comprobado/habilitado. La carga debe crear o verificar los destinos del [catálogo fuente](../analisis-proceso-actual/sistema-actual/sistema_actual_legado_schema.sql), no asumir que los códigos ya existen por haber preparado las tablas.

El estado de membresía mantiene su namespace legado y es independiente de JUNIOR/SENIOR/EX_TRAVELER. Los nombres históricos del catálogo de vigencia no se traducen como categorías sociales. Cada ficha requiere un historial inicial que vincule su grupo, estado y motivo; su fechaHora se obtendrá al cargar, sin incluir un timestamp fijo en este catálogo.

## Cuentas y socio operativo

| Cuenta / socio institucional | Referencia de usuario | Referencia de socio local | Username y legajo | Rol actual | is_enabled inicial |
|---|---|---|---|---|---|
| account.g57.01 / member.g57.01 | user.g57.01 | local_socio.g57.01 | 99077001 | SOCIO | True |
| account.g57.02 / member.g57.02 | user.g57.02 | local_socio.g57.02 | 99077002 | SOCIO | False |
| account.g58.01 / member.g58.01 | user.g58.01 | local_socio.g58.01 | 99077005 | CD | True |
| account.g58.02 / member.g58.02 | user.g58.02 | local_socio.g58.02 | 99077006 | SOCIO | True |
| account.g59.01 / member.g59.01 | user.g59.01 | local_socio.g59.01 | 99077009 | FISCALIZADORA | True |
| account.g60.01 / member.g60.01 | user.g60.01 | local_socio.g60.01 | 99077013 | SOCIO | True |
| account.g62.01 / member.g62.01 | user.g62.01 | local_socio.g62.01 | 99077017 | SOCIO | True |
| account.g62.02 / member.g62.02 | user.g62.02 | local_socio.g62.02 | 99077018 | SOCIO | True |
| account.g63.01 / member.g63.01 | user.g63.01 | local_socio.g63.01 | 99077019 | SOCIO | True |
| account.g63.02 / member.g63.02 | user.g63.02 | local_socio.g63.02 | 99077020 | SOCIO | True |

Se fijan diez cuentas del catálogo y sus diez perfiles iniciales; el resto de las fichas no se vincula a una cuenta por coincidencia numérica. FISCALIZADORA es el código RBAC existente que representa autoridad de subcomisión en este producto; no se inventa AUTORIDAD ni se redefine Revisores dentro de SCRUM-77. CD y FISCALIZADORA permiten las dos identidades solicitantes según las reglas actuales de T01. La categoría no otorga rol, firma, habilitación ni saldo. G57 incluye cuentas habilitada y deshabilitada explícitas para verificar esa independencia.

El contrato del manifiesto exige resolver, por cada referencia, auth_user.id, socios_socio.id, legajo local, nroSocio institucional, nroLegajo académico, grupo y ambas referencias de subcomisión. user_id institucional contiene auth_user.id realmente resuelto; no recibe el nroSocio ni la PK de socio local. No se incluyen contraseñas ni hashes en el catálogo; su política de alta corresponde a TS77.10 y conserva las credenciales existentes en las repeticiones.

Las cinco cuentas seed_demo se conservan como referencias externas al conjunto institucional: preserved.seed-demo.74907, .85194, .87414, .408917 y .403655. Se identifican por su legajo local, no por nombres ni PKs supuestos. TS77.10 comprueba su coexistencia y conserva credenciales, permisos y ediciones. No se asigna a esas cinco cuentas una cohorte institucional inventada.

## Escenas futuras y oráculos de saldo

Estos datos sirven como referencias para TS77.12–15. No son resultados persistidos de TS77.07, ni amplían las etapas disponibles o autorizan movimientos manuales.

| Clave | Solicitante | Destinatarios | Etapa prevista / urgencia | Puntos solicitados |
|---|---|---|---|---:|
| cause.created.low | account.g58.01 | member.g57.01 | Creado / baja | -1 |
| cause.created.normal | account.g59.01 | member.g58.02 | Creado / normal | -2 |
| cause.created.urgent.multi | account.g58.01 | member.g57.01, member.g60.01 | Creado / urgente | -3 |
| t01.cd.draft | account.g58.01 | Vacío; borrador incompleto | DRAFT / normal; sin expediente | 0 |
| t01.authority.draft | account.g59.01 | member.g60.01 | DRAFT / normal; sin expediente | -1 |
| t01.cd.issued.multi | account.g58.01 | member.g57.01, member.g58.02 | ISSUED → Justificaciones / urgente | -2 |
| t01.authority.issued | account.g59.01 | member.g60.01 | ISSUED → Justificaciones / baja | -1 |

Oráculo posterior a TS77.12–14: cinco expedientes managed, tres en Creado y dos en Justificaciones; cuatro T01, dos por cada creador. Los seis estados canónicos se mantienen, con cuatro columnas vacías. Las aperturas, plazos hábiles, actos y auditorías usarán el momento de carga y los servicios vigentes; no se incluyen números formales, fechas futuras ni progresiones forzadas. El borrador vacío no puede emitirse mientras permanezca incompleto.

| Movimiento futuro | Socio | Resolución / expediente legacy | Puntos aplicados |
|---|---|---|---:|
| history.movement.g57-merit | member.g57.01 | history.resolution.shared-merit / history.expediente.shared-merit | +2 |
| history.movement.g58-shared-merit | member.g58.02 | history.resolution.shared-merit / history.expediente.shared-merit | +1 |
| history.movement.g59-merit | member.g59.01 | history.resolution.g59-merit / history.expediente.g59-merit | +2 |
| history.movement.g57-sanction | member.g57.02 | history.resolution.g57-sanction / history.expediente.g57-sanction | -1 |
| history.movement.g58-positive | member.g58.01 | history.resolution.g58-positive / history.expediente.g58-positive | +3 |
| history.movement.g58-negative | member.g58.01 | history.resolution.g58-negative / history.expediente.g58-negative | -3 |
| history.movement.g59-sanction | member.g59.02 | history.resolution.g59-sanction / history.expediente.g59-sanction | -4 |
| history.movement.g60-merit | member.g60.01 | history.resolution.g60-merit / history.expediente.g60-merit | +1 |

Oráculo posterior a TS77.15: ocho asientos individuales con siete respaldos resolutivos y siete expedientes legacy, cada uno con su FK correcta. La resolución compartida atribuye +2 y +1 a destinatarios distintos, sin imputar el total a cada involucrado. El fixture formal y sus textos/números/fechas se implementan en esa tarea; estas claves no acreditan actos emitidos ni permisos de firma. Ninguna PK de expediente managed se utiliza como expediente_id del movimiento legado.

| Socio | Saldo esperado después de los antecedentes |
|---|---:|
| member.g57.01 | +2 |
| member.g57.02 | -1 |
| member.g58.01 | 0, compensado por +3 y -3 |
| member.g58.02 | +1 |
| member.g59.01 | +2, empate con G57.01 |
| member.g59.02 | -4 |
| member.g60.01 | +1, empate con G58.02 |
| Otras trece fichas, incluidos los cuatro Juniors antes de RF77-16 | 0, sin movimientos iniciales |

La suma del conjunto es +1. Los pedidos de las cinco causas actuales quedan separados y no integran ese saldo. No se fabrica PuntajeGeneral para ocultar historial vacío. No se usan movimientos fraccionarios para felicitaciones/llamados ni se implementa el motor 3:1; sus pruebas continúan en sus US propias.

## Verificación y límites de aceptación

La validación pura exige las cantidades, corte del PO, referencias existentes dentro del catálogo, claves estables y unicidad de cada namespace. Rechaza campos fuera de rango, booleanos como IDs, cadenas largas/vacías, correos externos, cuentas ambiguas, marcadores incompletos o contradictorios, escenas con etapas nuevas y asientos sin referencia resolutiva o con puntos fraccionarios. Los oráculos de futuros saldos son independientes de puntos solicitados y no consultan MySQL.

Root registra cantidades/rangos en DP77-02 y acepta este catálogo después de la auditoría integral TS77.37; la preparación paralela por sí sola no acreditó DEP77-02. Esa dependencia y CA77-08 se cierran por sus pruebas de adecuación, sin cargar fixtures. TS77.08–18 deben demostrar guardias, propiedad, carga transaccional, repeticiones, conservación, rollback y conciliación SQL/API/manifiesto. La persistencia sin reseed y los recorridos UI siguen en sus tareas. Notas del PO, constitución, fuentes SQL, esquema físico, cuentas y saldos se conservan en TS77.07.

## Carga verificada — TS77.08–19

El 12/10/2026 se cargó el perfil v1/corte confirmado en MySQL demo: 16 fichas, cuatro por grupo, y 162 referencias físicas de propiedad. G57 conserva NULL y cuatro marcadores EX_TRAVELER; G58/G59/G60 mantienen 6/5/4. Seis cuentas nuevas y cinco referencias seed_demo coexisten; diez fichas institucionales no tienen cuenta y mantienen los vínculos locales nulos.

Los ocho asientos y siete respaldos históricos concilian con los saldos de esta tabla, total +1,00. La segunda carga produjo un manifiesto idéntico y conservó los 49 esquemas/huellas de filas/conteos y contadores. Recrear MySQL sobre el mismo volumen mantuvo esas huellas, sin reseed. Se comprobaron 59 FKs sin huérfanos y 78 controles HTTP antes y después. [Resultados](VERIFICACION_CARGA_SCRUM-77.json), [procedimiento](GUIA_CARGA_DEMO_SCRUM-77.md) y [seguimiento](../../specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827).


## Ampliación Junior autorizada — TS77.45

El usuario pidió incorporar Juniors después de aprobar la UAT original. Se conserva el perfil scrum77-g57-g60-v1 y el corte explícito, agregando G62 de 2.º año y G63 de 1.º año según la escala del corte de referencia. No se modifica el conjunto original ni se recalculan años desde el calendario. La carga ampliada quedó verificada y auditada en TS77.44–46: veinte fichas, quince cuentas/perfiles y 188 referencias; cuatro Junior con saldo cero, sin alterar las filas previas ni las altas de UAT. Primera/repetición mantienen el mismo manifiesto y las 52 tablas. [Evidencia ampliada](VERIFICACION_AMPLIACION_SCRUM-77.json).

## Estados avanzados y saldos actuales — RF77-15/16

El usuario autorizó añadir diez escenas históricas: tres En revisión, una Pendiente de firma, dos Pendientes de envío y cuatro Emitidos. El catálogo original de cinco causas/cuatro T01 se conserva; las diez causas nuevas tienen fechas pasadas, plazo vencido e historial canónico. Los cuatro emitidos añaden cuatro resoluciones/expedientes históricos y cuatro asientos individuales. El conjunto previsto tiene quince causas fixtures, doce asientos y once respaldos históricos, con saldo agregado +1. Las altas de UAT se mantienen además de los fixtures.

| Cuenta Junior | Escena emitida | Saldo después del acto sintético |
| --- | --- | ---: |
| 99077017 — Quimey Quimera Demo | advanced.emitted.01 | +2 |
| 99077018 — Rocío Rumbo Demo | advanced.emitted.02 | -1 |
| 99077019 — Sol Sendero Demo | advanced.emitted.03 | -2 |
| 99077020 — Tomás Trama Demo | advanced.emitted.04 | +1 |

Estos cuatro movimientos son posteriores al alta inicial con cero; conservan los ocho asientos y saldos anteriores. Mis Expedientes y las fichas consultan el saldo aplicado del libro mayor, igual que ranking. PuntajeGeneral se conserva como caché de conciliación y los pedidos pendientes no se suman. Las cinco cuentas seed_demo carecen de vínculo institucional en este catálogo: muestran saldo desconocido, sin inventar un número ni otra identidad. La [verificación de PR #54](VERIFICACION_CORRECCIONES_PR54.md) registra carga, conservación y recorridos finales.
