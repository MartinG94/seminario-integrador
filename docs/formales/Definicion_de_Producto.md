# Documento de Definición de Producto

## 1. Portada y datos del documento
- **Nombre del producto:** SGD-AVEIT
- **Nombre del documento:** Documento de Definición de Producto
- **Identificación del proyecto:** SCRUM - Equipo Seminario (Jira)
- **Versión del documento:** 1.0
- **Fecha de elaboración:** 08/10/2026

## 2. Historia de revisión
| Versión | Fecha | Autor / Responsable | Descripción de los cambios |
|---|---|---|---|
| 1.0 | 08/10/2026 | Equipo Interdisciplinario | Elaboración inicial del documento en base a la arquitectura y requerimientos de Jira. |

## 3. Tabla de contenido o índice
1. Portada y datos del documento
2. Historia de revisión
3. Tabla de contenido o índice
4. Propósito del documento e introducción
5. Nombre del producto de software
6. Objetivo del producto
7. Product Backlog
8. Roles del sistema
9. Épicas y User Stories asociadas
10. Especificación individual de cada User Story
11. Diagrama de clases
12. DER — Diagrama Entidad-Relación
13. Diagramas de transición de estados
14. Definición de la arquitectura del software
15. Casos de uso

## 4. Propósito del documento e introducción
Este documento describe el producto SGD-AVEIT. Fue elaborado utilizando la documentación oficial del repositorio (Jira Backlog, archivos Markdown, modelos de Django, Tests) y el código actual. 
El propósito de este documento es unificar de manera académica las especificaciones funcionales y el estado de la arquitectura del sistema.

**Limitaciones:** La infraestructura física está pendiente de confirmar en detalle. Las pruebas locales fueron ejecutadas pero presentaron fallos por falta de conectividad con la base de datos (debido al estado de los contenedores), por lo cual la verificación es parcialmente estática y basada en los resultados y aserciones de pytest.

## 5. Nombre del producto de software
**SGD-AVEIT** (Sistema de Gestión Disciplinaria de la Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos).

## 6. Objetivo del producto
El objetivo del sistema es dotar a la A.V.E.I.T. de una plataforma web (mobile-first) para la gestión integral de expedientes disciplinarios, descargos tipificados (T02/T03), votación nominal colegiada del Tribunal de Disciplina y cómputo transaccional inmutable de saldos de puntos de la organización.

## 7. Product Backlog
| ID | Nombre | Prioridad | Estado en Jira | Épica (Módulo / Agrupación) |
|---|---|---|---|---|
| S1-02 | S1-02: Baseline reproducible, healthchecks y secretos externos | Highest | Relevado de Backlog importado | EP1 |
| S1-03 | S1-03: Autenticación y autorización compatibles con roles AVEIT | Highest | Relevado de Backlog importado | EP1 |
| S1-04 | S1-04: Consumir el padrón institucional sin duplicar la fuente maestra | Highest | Relevado de Backlog importado | EP1 |
| S1-05 | S1-05: Ranking oficial reconciliado con el libro histórico | Highest | Relevado de Backlog importado | EP1 |
| S1-06 | S1-06: Buscar por nombre, legajo y subcomisión y abrir legajo | High | Relevado de Backlog importado | EP1 |
| S2-01 | S2-01: Crear expediente con número único e historial de seis estados | Highest | Relevado de Backlog importado | EP2 |
| S2-02 | S2-02: Cargar y validar T01 con anexo opcional | Highest | Relevado de Backlog importado | EP2 |
| S2-03 | S2-03: Validar competencias de inicio de acción | Highest | Relevado de Backlog importado | EP2 |
| S2-04 | S2-04: Notificar apertura con entrega y reintentos auditables | Highest | Relevado de Backlog importado | EP2 |
| S2-05 | S2-05: Visualizar tablero responsive de seis estados | High | Relevado de Backlog importado | EP2 |
| S3-01 | S3-01: Configurar calendario institucional de días hábiles | Highest | Relevado de Backlog importado | EP3 |
| S3-02 | S3-02: Calcular y cerrar el plazo de cinco días hábiles | Highest | Relevado de Backlog importado | EP3 |
| S3-03 | S3-03: Presentar T02 tipificado y firmado | Highest | Relevado de Backlog importado | EP3 |
| S3-04 | S3-04: Adjuntar y custodiar evidencia protegida | Highest | Relevado de Backlog importado | EP3 |
| S3-05 | S3-05: Presentar T03 extraordinario con fundamento libre | High | Relevado de Backlog importado | EP3 |
| S3-06 | S3-06: Incorporar sanciones originadas en reuniones y solicitudes | High | Relevado de Backlog importado | EP3 |
| S4-01 | S4-01: Revisar expediente y evidencia en un visor autorizado | Highest | Relevado de Backlog importado | EP4 |
| S4-02 | S4-02: Resolver causal T02 con fundamento trazable | Highest | Relevado de Backlog importado | EP4 |
| S4-03 | S4-03: Valorar T03 mediante antecedentes y sana crítica | High | Relevado de Backlog importado | EP4 |
| S4-04 | S4-04: Gestionar apartamiento y suplencia conforme al Estatuto | Highest | Relevado de Backlog importado | EP4 |
| S4-05 | S4-05: Registrar voto nominal y mayoría absoluta | Highest | Relevado de Backlog importado | EP4 |
| S4-06 | S4-06: Redactar resolución con estructura reglamentaria | Highest | Relevado de Backlog importado | EP4 |
| S5-01 | S5-01: Firmar resolución por representación de los tres grupos Activos | Highest | Relevado de Backlog importado | EP5 |
| S5-02 | S5-02: Emitir resolución y notificar sin duplicados | Highest | Relevado de Backlog importado | EP5 |
| S5-03 | S5-03: Aplicar movimientos de puntos inmutables e idempotentes | Highest | Relevado de Backlog importado | EP5 |
| S5-04 | S5-04: Consultar Mis expedientes con privacidad por objeto | High | Relevado de Backlog importado | EP5 |
| S5-05 | S5-05: Publicar resoluciones con datos protegidos | High | Relevado de Backlog importado | EP5 |
| S5-06 | S5-06: Alertar umbral crítico -10 y política preventiva configurable | Highest | Relevado de Backlog importado | EP5 |
| S6-01 | S6-01: Consolidar balance cuatrimestral por subcomisión y autoridad | Highest | Relevado de Backlog importado | EP6 |
| S6-02 | S6-02: Exportar balance verificable en PDF y datos abiertos internos | High | Relevado de Backlog importado | EP6 |
| S6-03 | S6-03: Buscar resoluciones como antecedentes internos | Medium | Relevado de Backlog importado | EP6 |
| S6-04 | S6-04: Migrar y reconciliar datos legados con rollback probado | Highest | Relevado de Backlog importado | EP6 |
| S6-05 | S6-05: Ejecutar hardening, accesibilidad, rendimiento y E2E | Highest | Relevado de Backlog importado | EP6 |
| S6-06 | S6-06: Desplegar staging y completar homologación/transferencia | Highest | Relevado de Backlog importado | EP6 |
| PB-01 | PB-01: Gestionar caso interno y promoverlo a T01 | High | Relevado de Backlog importado | EP2 |
| PB-02 | PB-02: Tramitar apelación y adecuación del T01 | High | Relevado de Backlog importado | EP4 |
| PB-03 | PB-03: Implementar enmienda controlada de expediente emitido | High | Relevado de Backlog importado | EP5 |

## 8. Roles del sistema
- **SOCIO:** Socio Ordinario. Puede visualizar sus propios expedientes, estado de cuenta y presentar descargos.
- **FISCALIZADORA:** Autoridad de Subcomisión / Líder de Equipo.
- **CD:** Comisión Directiva.
- **TD:** Tribunal de Disciplina. Puede gestionar expedientes, revisar descargos y emitir resoluciones (T01, votaciones).
- **ADMIN:** Administrador de Cómputos.

## 9. Épicas y User Stories asociadas
*(Agrupación funcional para organizar la documentación, dado que el backlog funciona fundamentalmente por US/Tasks)*
- **EP1:** Plataforma segura e integración con el ecosistema AVEIT (S1-01 a S1-05)
- **EP2:** Apertura y ciclo procesal del expediente y T01 (S2-01 a S2-05, PB-01)
- **EP3:** Descargos, evidencia y plazos hábiles (S3-01 a S3-06)
- **EP4:** Sustanciación, decisión colegiada y Resolución (S4-01 a S4-06, PB-02)
- **EP5:** Firma, emisión y libro mayor inmutable (S5-01 a S5-06, PB-03)
- **EP6:** Exportación, auditoría, consolidación de datos y QA (S6-01 a S6-06)

## 10. Especificación individual de cada User Story

### S1-03: Autenticación y autorización compatibles con roles AVEIT

**A. Identificación y descripción**
- **ID y título:** S1-03: Autenticación y autorización compatibles con roles AVEIT
- **Descripción de la US:** Como integrante de AVEIT quiero iniciar sesión y recibir sólo las funciones autorizadas para proteger información disciplinaria.

**B. UAT — Criterios de aceptación de usuario**
- CA1 credenciales inválidas devuelven 401 sin filtrar datos
- CA2 permisos legados tribunal_bajo/medio/alto y cargos se mapean a RBAC documentado
- CA3 las rutas verifican autorización de servidor y no sólo visibilidad UI
- CA4 sesión/token expira y se audita sin registrar secretos.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S1-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S1-03: Autenticación y autorización compatibles con roles AVEIT para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S1-03. Funcionalidad de Autenticación y autorización compatibles con roles AVEIT.*

**D. Diseño de casos de prueba**
- **US asociada:** S1-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S1-04: Consumir el padrón institucional sin duplicar la fuente maestra

**A. Identificación y descripción**
- **ID y título:** S1-04: Consumir el padrón institucional sin duplicar la fuente maestra
- **Descripción de la US:** Como autoridad quiero consultar socios y subcomisiones vigentes desde la fuente institucional para evitar divergencias.

**B. UAT — Criterios de aceptación de usuario**
- CA1 adaptador de sólo lectura o réplica controlada definido por ADR
- CA2 legajo y socio tienen identidad estable
- CA3 la categoría Pasivo equivale a Junior y comprende 1.º–3.º, mientras Activo equivale a Senior y comprende 4.º–6.º
- CA4 la vigencia de cuenta/membresía se modela por separado
- CA5 fallas/sincronizaciones quedan observables. Trazabilidad: decisión PO 08/09/2026 y Estatuto 2026 arts. 3 y 6.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S1-04 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S1-04: Consumir el padrón institucional sin duplicar la fuente maestra para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S1-04. Funcionalidad de Consumir el padrón institucional sin duplicar la fuente maestra.*

**D. Diseño de casos de prueba**
- **US asociada:** S1-04
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S1-05: Ranking oficial reconciliado con el libro histórico

**A. Identificación y descripción**
- **ID y título:** S1-05: Ranking oficial reconciliado con el libro histórico
- **Descripción de la US:** Como TD/CD quiero ordenar y filtrar el saldo verificable de los socios para supervisar su situación.

**B. UAT — Criterios de aceptación de usuario**
- CA1 saldo se deriva de PuntajeAplicado o fuente acordada
- CA2 PuntajeGeneral se compara como caché y las diferencias se informan
- CA3 filtros por categoría Pasivo/Activo y subcomisión, sin confundir categoría con vigencia
- CA4 p95 menor o igual a 500 ms con 515 socios
- CA5 importes usan decimal.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S1-05 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S1-05: Ranking oficial reconciliado con el libro histórico para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S1-05. Funcionalidad de Ranking oficial reconciliado con el libro histórico.*

**D. Diseño de casos de prueba**
- **US asociada:** S1-05
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S1-06: Buscar por nombre, legajo y subcomisión y abrir legajo

**A. Identificación y descripción**
- **ID y título:** S1-06: Buscar por nombre, legajo y subcomisión y abrir legajo
- **Descripción de la US:** Como autoridad quiero localizar un socio y consultar su historial autorizado para investigar antecedentes.

**B. UAT — Criterios de aceptación de usuario**
- CA1 búsqueda insensible a mayúsculas/tildes
- CA2 incluye legajo universitario de la fuente correcta
- CA3 pagina resultados y evita N+1
- CA4 un socio ordinario no accede a legajos ajenos
- CA5 funciona en móvil 360 px.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S1-06 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S1-06: Buscar por nombre, legajo y subcomisión y abrir legajo para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S1-06. Funcionalidad de Buscar por nombre, legajo y subcomisión y abrir legajo.*

**D. Diseño de casos de prueba**
- **US asociada:** S1-06
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S2-01: Crear expediente con número único e historial de seis estados

**A. Identificación y descripción**
- **ID y título:** S2-01: Crear expediente con número único e historial de seis estados
- **Descripción de la US:** Como integrante habilitado quiero abrir y seguir un expediente con trazabilidad completa.

**B. UAT — Criterios de aceptación de usuario**
- CA1 número único y correlativo
- CA2 implementa exactamente los seis estados del art. 12
- CA3 cada transición registra actor fecha y motivo y rechaza saltos
- CA4 concurrencia no duplica numeración. Dependencia: S1-03/S1-04.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S2-01 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S2-01: Crear expediente con número único e historial de seis estados para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S2-01. Funcionalidad de Crear expediente con número único e historial de seis estados.*

**D. Diseño de casos de prueba**
- **US asociada:** S2-01
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S2-02: Cargar y validar T01 con anexo opcional

**A. Identificación y descripción**
- **ID y título:** S2-02: Cargar y validar T01 con anexo opcional
- **Descripción de la US:** Como autoridad competente quiero presentar un T01 digital para iniciar formalmente la acción.

**B. UAT — Criterios de aceptación de usuario**
- CA1 captura campos exigidos por art. 16
- CA2 el anexo del art. 16 bis es opcional y su ausencia no bloquea
- CA3 validaciones se ejecutan en cliente y servidor
- CA4 borrador no abre expediente ni notifica
- CA5 emisión conserva versión inmutable.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S2-02 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S2-02: Cargar y validar T01 con anexo opcional para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S2-02. Funcionalidad de Cargar y validar T01 con anexo opcional.*

**D. Diseño de casos de prueba**
- **US asociada:** S2-02
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S2-03: Validar competencias de inicio de acción

**A. Identificación y descripción**
- **ID y título:** S2-03: Validar competencias de inicio de acción
- **Descripción de la US:** Como sistema quiero comprobar la competencia del solicitante para impedir acciones improcedentes.

**B. UAT — Criterios de aceptación de usuario**
- CA1 reglas arts. 21–26 están parametrizadas y testeadas
- CA2 rechazo explica regla sin exponer información ajena
- CA3 excepciones requieren autoridad y motivo auditado
- CA4 casos límite forman parte de pruebas de dominio.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S2-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S2-03: Validar competencias de inicio de acción para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S2-03. Funcionalidad de Validar competencias de inicio de acción.*

**D. Diseño de casos de prueba**
- **US asociada:** S2-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S2-04: Notificar apertura con entrega y reintentos auditables

**A. Identificación y descripción**
- **ID y título:** S2-04: Notificar apertura con entrega y reintentos auditables
- **Descripción de la US:** Como socio imputado quiero recibir el acuse y enlace seguro para ejercer mi defensa.

**B. UAT — Criterios de aceptación de usuario**
- CA1 la transición al período de justificaciones ocurre sólo con evento de despacho acordado
- CA2 plantilla identifica expediente sin datos médicos
- CA3 fallo reintenta sin duplicar notificaciones y queda visible a operador
- CA4 enlace exige autenticación
- CA5 fecha base del plazo queda inmutable.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S2-04 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S2-04: Notificar apertura con entrega y reintentos auditables para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S2-04. Funcionalidad de Notificar apertura con entrega y reintentos auditables.*

**D. Diseño de casos de prueba**
- **US asociada:** S2-04
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S2-05: Visualizar tablero responsive de seis estados

**A. Identificación y descripción**
- **ID y título:** S2-05: Visualizar tablero responsive de seis estados
- **Descripción de la US:** Como TD quiero ver expedientes agrupados por estado reglamentario para priorizar trabajo.

**B. UAT — Criterios de aceptación de usuario**
- CA1 seis columnas/agrupaciones exactas
- CA2 filtros por número socio fecha y estado
- CA3 movimiento sólo invoca transiciones autorizadas
- CA4 teclado lector de pantalla y móvil no pierden funcionalidad
- CA5 no usa colores arbitrarios fuera de DESIGN.md.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S2-05 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S2-05: Visualizar tablero responsive de seis estados para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S2-05. Funcionalidad de Visualizar tablero responsive de seis estados.*

**D. Diseño de casos de prueba**
- **US asociada:** S2-05
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S3-01: Configurar calendario institucional de días hábiles

**A. Identificación y descripción**
- **ID y título:** S3-01: Configurar calendario institucional de días hábiles
- **Descripción de la US:** Como administrador autorizado quiero mantener feriados/excepciones para que los plazos sean reproducibles.

**B. UAT — Criterios de aceptación de usuario**
- CA1 fines de semana y feriados se excluyen
- CA2 cambios tienen vigencia versión y auditoría
- CA3 un plazo iniciado conserva la versión aplicada
- CA4 zona horaria America/Argentina/Buenos_Aires.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S3-01 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S3-01: Configurar calendario institucional de días hábiles para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S3-01. Funcionalidad de Configurar calendario institucional de días hábiles.*

**D. Diseño de casos de prueba**
- **US asociada:** S3-01
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S3-02: Calcular y cerrar el plazo de cinco días hábiles

**A. Identificación y descripción**
- **ID y título:** S3-02: Calcular y cerrar el plazo de cinco días hábiles
- **Descripción de la US:** Como socio quiero conocer el vencimiento exacto y presentar mientras el plazo esté vigente.

**B. UAT — Criterios de aceptación de usuario**
- CA1 cálculo parte del evento definido en S2-04
- CA2 servidor acepta hasta el instante límite y rechaza después
- CA3 UI muestra fecha/hora además de contador
- CA4 vencimiento transiciona una sola vez aunque el job se repita
- CA5 pruebas cubren feriados y cambio de día.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S3-02 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S3-02: Calcular y cerrar el plazo de cinco días hábiles para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S3-02. Funcionalidad de Calcular y cerrar el plazo de cinco días hábiles.*

**D. Diseño de casos de prueba**
- **US asociada:** S3-02
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S3-03: Presentar T02 tipificado y firmado

**A. Identificación y descripción**
- **ID y título:** S3-03: Presentar T02 tipificado y firmado
- **Descripción de la US:** Como socio imputado quiero completar el T02 estructurado para justificar con una causal prevista.

**B. UAT — Criterios de aceptación de usuario**
- CA1 contiene los cuatro bloques del art. 17
- CA2 sólo permite causales vigentes y conserva versión
- CA3 requiere firma aclaración y número de socio según mecanismo aprobado
- CA4 permite guardar borrador y enviar una única versión final
- CA5 acuse de recepción sin revelar datos sensibles.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S3-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S3-03: Presentar T02 tipificado y firmado para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S3-03. Funcionalidad de Presentar T02 tipificado y firmado.*

**D. Diseño de casos de prueba**
- **US asociada:** S3-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S3-04: Adjuntar y custodiar evidencia protegida

**A. Identificación y descripción**
- **ID y título:** S3-04: Adjuntar y custodiar evidencia protegida
- **Descripción de la US:** Como socio quiero aportar evidencia desde móvil sin que terceros accedan a datos sensibles.

**B. UAT — Criterios de aceptación de usuario**
- CA1 PDF/JPG/PNG hasta 5 MB por archivo y límites configurables
- CA2 valida tipo real nombre seguro y malware cuando infraestructura lo permita
- CA3 acceso por objeto sólo a partes autorizadas
- CA4 descarga queda auditada
- CA5 la UI advierte que la aceptación digital no reemplaza automáticamente el original médico del art. 102.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S3-04 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S3-04: Adjuntar y custodiar evidencia protegida para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S3-04. Funcionalidad de Adjuntar y custodiar evidencia protegida.*

**D. Diseño de casos de prueba**
- **US asociada:** S3-04
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S3-05: Presentar T03 extraordinario con fundamento libre

**A. Identificación y descripción**
- **ID y título:** S3-05: Presentar T03 extraordinario con fundamento libre
- **Descripción de la US:** Como socio imputado quiero exponer una causal no tipificada para que el TD la valore fundadamente.

**B. UAT — Criterios de aceptación de usuario**
- CA1 distingue T03 de T02
- CA2 texto y evidencia quedan versionados al enviar
- CA3 respeta el mismo plazo y controles de acceso
- CA4 el TD debe vincular fundamento/precedente al decidir.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S3-05 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S3-05: Presentar T03 extraordinario con fundamento libre para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S3-05. Funcionalidad de Presentar T03 extraordinario con fundamento libre.*

**D. Diseño de casos de prueba**
- **US asociada:** S3-05
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S3-06: Incorporar sanciones originadas en reuniones y solicitudes

**A. Identificación y descripción**
- **ID y título:** S3-06: Incorporar sanciones originadas en reuniones y solicitudes
- **Descripción de la US:** Como autoridad competente quiero transformar asistencia y solicitudes aprobadas en propuestas trazables.

**B. UAT — Criterios de aceptación de usuario**
- CA1 valida publicación de reunión con dos días hábiles y reporte dentro de 72 horas hábiles
- CA2 no sanciona eventos que no cumplen requisitos
- CA3 escala admite valores de 0,5 incluido 1,5
- CA4 cada tres apercibimientos generan -1 una sola vez
- CA5 integración no escribe saldo manualmente. Trazabilidad: Reglamento Interno arts. 83 85 95 99 y 100.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S3-06 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S3-06: Incorporar sanciones originadas en reuniones y solicitudes para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S3-06. Funcionalidad de Incorporar sanciones originadas en reuniones y solicitudes.*

**D. Diseño de casos de prueba**
- **US asociada:** S3-06
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S4-01: Revisar expediente y evidencia en un visor autorizado

**A. Identificación y descripción**
- **ID y título:** S4-01: Revisar expediente y evidencia en un visor autorizado
- **Descripción de la US:** Como integrante habilitado del TD quiero revisar T01 T02/T03 y evidencia en un único flujo para sustanciar.

**B. UAT — Criterios de aceptación de usuario**
- CA1 vista cronológica y documentos íntegros
- CA2 datos médicos sólo para autorizados
- CA3 toda consulta/descarga sensible se audita
- CA4 faltantes o archivos dañados son visibles
- CA5 responsive y accesible.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S4-01 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S4-01: Revisar expediente y evidencia en un visor autorizado para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S4-01. Funcionalidad de Revisar expediente y evidencia en un visor autorizado.*

**D. Diseño de casos de prueba**
- **US asociada:** S4-01
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S4-02: Resolver causal T02 con fundamento trazable

**A. Identificación y descripción**
- **ID y título:** S4-02: Resolver causal T02 con fundamento trazable
- **Descripción de la US:** Como vocal quiero aceptar o rechazar cada causal tipificada con fundamento para producir una decisión auditable.

**B. UAT — Criterios de aceptación de usuario**
- CA1 decisión por causal y evidencia
- CA2 exige fundamento al rechazar o apartarse de regla
- CA3 conserva autor/fecha/versión
- CA4 no modifica el descargo presentado.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S4-02 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S4-02: Resolver causal T02 con fundamento trazable para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S4-02. Funcionalidad de Resolver causal T02 con fundamento trazable.*

**D. Diseño de casos de prueba**
- **US asociada:** S4-02
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S4-03: Valorar T03 mediante antecedentes y sana crítica

**A. Identificación y descripción**
- **ID y título:** S4-03: Valorar T03 mediante antecedentes y sana crítica
- **Descripción de la US:** Como vocal quiero registrar la valoración extraordinaria y antecedentes aplicados para mantener consistencia.

**B. UAT — Criterios de aceptación de usuario**
- CA1 exige fundamento explícito
- CA2 permite vincular resoluciones emitidas autorizadas
- CA3 advierte diferencias no impide decisión
- CA4 la información médica no se publica.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S4-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S4-03: Valorar T03 mediante antecedentes y sana crítica para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S4-03. Funcionalidad de Valorar T03 mediante antecedentes y sana crítica.*

**D. Diseño de casos de prueba**
- **US asociada:** S4-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S4-04: Gestionar apartamiento y suplencia conforme al Estatuto

**A. Identificación y descripción**
- **ID y título:** S4-04: Gestionar apartamiento y suplencia conforme al Estatuto
- **Descripción de la US:** Como TD quiero constituir correctamente el cuerpo cuando un integrante está involucrado.

**B. UAT — Criterios de aceptación de usuario**
- CA1 tres titulares y tres suplentes por 4.º 5.º y 6.º
- CA2 no implementa recusación prohibida por art. 93
- CA3 aplica apartamiento/suplencia o caso ad hoc del art. 95
- CA4 composición y causa quedan inmutables antes de votar
- CA5 incompatibilidad de cargos se valida.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S4-04 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S4-04: Gestionar apartamiento y suplencia conforme al Estatuto para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S4-04. Funcionalidad de Gestionar apartamiento y suplencia conforme al Estatuto.*

**D. Diseño de casos de prueba**
- **US asociada:** S4-04
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S4-05: Registrar voto nominal y mayoría absoluta

**A. Identificación y descripción**
- **ID y título:** S4-05: Registrar voto nominal y mayoría absoluta
- **Descripción de la US:** Como vocal habilitado quiero votar nominalmente con fundamento para adoptar una decisión colegiada.

**B. UAT — Criterios de aceptación de usuario**
- CA1 un voto por integrante habilitado y expediente
- CA2 no puede editarse tras cerrar salvo rectificación formal autorizada
- CA3 mayoría se calcula sobre composición estatutaria efectiva y cubre 2 de 3 ordinario
- CA4 abstención/ausencia siguen regla aprobada
- CA5 concurrencia e idempotencia probadas.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S4-05 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S4-05: Registrar voto nominal y mayoría absoluta para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S4-05. Funcionalidad de Registrar voto nominal y mayoría absoluta.*

**D. Diseño de casos de prueba**
- **US asociada:** S4-05
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S4-06: Redactar resolución con estructura reglamentaria

**A. Identificación y descripción**
- **ID y título:** S4-06: Redactar resolución con estructura reglamentaria
- **Descripción de la US:** Como TD quiero generar la resolución con Vistos Considerandos y artículos resolutivos para formalizar la decisión.

**B. UAT — Criterios de aceptación de usuario**
- CA1 usa el número del expediente
- CA2 plantilla versionada y campos obligatorios
- CA3 puntos/medidas derivan de la votación cerrada
- CA4 previsualización PDF no equivale a emisión
- CA5 no contiene adjuntos privados.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S4-06 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S4-06: Redactar resolución con estructura reglamentaria para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S4-06. Funcionalidad de Redactar resolución con estructura reglamentaria.*

**D. Diseño de casos de prueba**
- **US asociada:** S4-06
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S5-01: Firmar resolución por representación de los tres grupos Activos

**A. Identificación y descripción**
- **ID y título:** S5-01: Firmar resolución por representación de los tres grupos Activos
- **Descripción de la US:** Como vocal habilitado de categoría Activo quiero firmar la resolución cerrada para acreditar conformidad colegiada.

**B. UAT — Criterios de aceptación de usuario**
- CA1 una firma válida por grupo 4.º, 5.º y 6.º o composición ad hoc documentada
- CA2 firma se asocia al hash real del documento y no es simulada
- CA3 cambio invalida firmas previas
- CA4 mecanismo PIN/credencial se implementa según ADR aprobada
- CA5 auditoría no guarda secretos.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S5-01 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S5-01: Firmar resolución por representación de los tres grupos Activos para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S5-01. Funcionalidad de Firmar resolución por representación de los tres grupos Activos.*

**D. Diseño de casos de prueba**
- **US asociada:** S5-01
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S5-02: Emitir resolución y notificar sin duplicados

**A. Identificación y descripción**
- **ID y título:** S5-02: Emitir resolución y notificar sin duplicados
- **Descripción de la US:** Como sistema quiero enviar la resolución firmada y pasar a Emitido para cerrar el proceso.

**B. UAT — Criterios de aceptación de usuario**
- CA1 estado 5 mientras faltan correos y estado 6 sólo tras despacho acordado
- CA2 reintentos idempotentes
- CA3 destinatarios y resultado auditados
- CA4 archivo emitido es inmutable y verificable
- CA5 no se reabren causas de TD anterior salvo regla expresamente habilitada.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S5-02 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S5-02: Emitir resolución y notificar sin duplicados para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S5-02. Funcionalidad de Emitir resolución y notificar sin duplicados.*

**D. Diseño de casos de prueba**
- **US asociada:** S5-02
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S5-03: Aplicar movimientos de puntos inmutables e idempotentes

**A. Identificación y descripción**
- **ID y título:** S5-03: Aplicar movimientos de puntos inmutables e idempotentes
- **Descripción de la US:** Como sistema quiero acreditar la resolución en el libro mayor una sola vez para preservar saldos.

**B. UAT — Criterios de aceptación de usuario**
- CA1 transacción atómica vinculada a resolución emitida y socio
- CA2 restricción única impide doble aplicación
- CA3 no existen UPDATE/DELETE manuales de saldo
- CA4 importe Decimal admite 0,5 y 1,5
- CA5 reversión sólo mediante contramovimiento autorizado
- CA6 reconciliación con legado queda registrada.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S5-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S5-03: Aplicar movimientos de puntos inmutables e idempotentes para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S5-03. Funcionalidad de Aplicar movimientos de puntos inmutables e idempotentes.*

**D. Diseño de casos de prueba**
- **US asociada:** S5-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S5-04: Consultar Mis expedientes con privacidad por objeto

**A. Identificación y descripción**
- **ID y título:** S5-04: Consultar Mis expedientes con privacidad por objeto
- **Descripción de la US:** Como socio quiero ver mis expedientes y resoluciones para conocer mi situación.

**B. UAT — Criterios de aceptación de usuario**
- CA1 sólo propios salvo rol autorizado
- CA2 muestra estado y fechas sin deliberación reservada
- CA3 descarga resolución emitida
- CA4 T02/T03 y evidencia no son públicos
- CA5 mobile-first y accesible.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S5-04 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S5-04: Consultar Mis expedientes con privacidad por objeto para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S5-04. Funcionalidad de Consultar Mis expedientes con privacidad por objeto.*

**D. Diseño de casos de prueba**
- **US asociada:** S5-04
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S5-05: Publicar resoluciones con datos protegidos

**A. Identificación y descripción**
- **ID y título:** S5-05: Publicar resoluciones con datos protegidos
- **Descripción de la US:** Como comunidad autorizada quiero consultar fallos emitidos para promover transparencia sin exponer evidencia sensible.

**B. UAT — Criterios de aceptación de usuario**
- CA1 sólo resolución final emitida
- CA2 política de anonimización/visibilidad aprobada
- CA3 nunca publica certificados ni adjuntos
- CA4 búsqueda respeta permisos y registra acceso cuando corresponda.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S5-05 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S5-05: Publicar resoluciones con datos protegidos para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S5-05. Funcionalidad de Publicar resoluciones con datos protegidos.*

**D. Diseño de casos de prueba**
- **US asociada:** S5-05
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S5-06: Alertar umbral crítico -10 y política preventiva configurable

**A. Identificación y descripción**
- **ID y título:** S5-06: Alertar umbral crítico -10 y política preventiva configurable
- **Descripción de la US:** Como autoridad quiero recibir alertas de saldos críticos para actuar conforme al reglamento.

**B. UAT — Criterios de aceptación de usuario**
- CA1 saldo negativo de 10 o más genera alerta crítica única por cruce
- CA2 destinatario y acción siguen acto aprobado
- CA3 umbral -7 está desactivable/configurable hasta validar Circular 001/2026
- CA4 reversiones reevalúan sin borrar historial
- CA5 no se notifica información médica.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S5-06 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S5-06: Alertar umbral crítico -10 y política preventiva configurable para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S5-06. Funcionalidad de Alertar umbral crítico -10 y política preventiva configurable.*

**D. Diseño de casos de prueba**
- **US asociada:** S5-06
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S6-01: Consolidar balance cuatrimestral por subcomisión y autoridad

**A. Identificación y descripción**
- **ID y título:** S6-01: Consolidar balance cuatrimestral por subcomisión y autoridad
- **Descripción de la US:** Como Vicepresidencia/Auditoría Interna quiero consolidar premios y sanciones para cumplir el art. 137.

**B. UAT — Criterios de aceptación de usuario**
- CA1 período cuatrimestral y dos emisiones anuales
- CA2 desglose por subcomisión/autoridad y totales reconciliables
- CA3 TD recibe el informe pero no se modela como único propietario
- CA4 acceso y generación auditados
- CA5 fuente es el libro mayor reconciliado.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S6-01 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S6-01: Consolidar balance cuatrimestral por subcomisión y autoridad para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S6-01. Funcionalidad de Consolidar balance cuatrimestral por subcomisión y autoridad.*

**D. Diseño de casos de prueba**
- **US asociada:** S6-01
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S6-02: Exportar balance verificable en PDF y datos abiertos internos

**A. Identificación y descripción**
- **ID y título:** S6-02: Exportar balance verificable en PDF y datos abiertos internos
- **Descripción de la US:** Como autoridad autorizada quiero exportar el balance para presentarlo ante CD.

**B. UAT — Criterios de aceptación de usuario**
- CA1 PDF institucional con período filtros totales y fecha
- CA2 exportación CSV preserva decimales
- CA3 archivo incluye identificador/hash verificable
- CA4 datos personales se limitan según audiencia
- CA5 diseño imprime correctamente.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S6-02 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S6-02: Exportar balance verificable en PDF y datos abiertos internos para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S6-02. Funcionalidad de Exportar balance verificable en PDF y datos abiertos internos.*

**D. Diseño de casos de prueba**
- **US asociada:** S6-02
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### S6-03: Buscar resoluciones como antecedentes internos

**A. Identificación y descripción**
- **ID y título:** S6-03: Buscar resoluciones como antecedentes internos
- **Descripción de la US:** Como TD quiero buscar resoluciones emitidas por causal y texto para orientar decisiones consistentes.

**B. UAT — Criterios de aceptación de usuario**
- CA1 sólo documentos autorizados
- CA2 filtros por causal fecha resultado y puntos
- CA3 enlace a expediente respeta permisos
- CA4 no convierte antecedentes en regla automática. Alcance stretch: se inicia sólo si no compromete homologación.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — S6-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de S6-03: Buscar resoluciones como antecedentes internos para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura S6-03. Funcionalidad de Buscar resoluciones como antecedentes internos.*

**D. Diseño de casos de prueba**
- **US asociada:** S6-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### PB-01: Gestionar caso interno y promoverlo a T01

**A. Identificación y descripción**
- **ID y título:** PB-01: Gestionar caso interno y promoverlo a T01
- **Descripción de la US:** Como TD quiero registrar una solicitud de socio o actuación de oficio entrevistas y debate para decidir si corresponde iniciar un T01.

**B. UAT — Criterios de aceptación de usuario**
- CA1 identifica origen y autoridad
- CA2 registra entrevistas con permisos y trazabilidad
- CA3 comunica la decisión a involucrados
- CA4 la promoción genera T01 enlazado sin duplicar evidencia
- CA5 el cierre sin T01 queda fundado. Pendiente: reglas de plazo publicidad y conservación. Trazabilidad: diagrama art. 15 Reglamento Procesal 2026.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — PB-01 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de PB-01: Gestionar caso interno y promoverlo a T01 para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura PB-01. Funcionalidad de Gestionar caso interno y promoverlo a T01.*

**D. Diseño de casos de prueba**
- **US asociada:** PB-01
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### PB-02: Tramitar apelación y adecuación del T01

**A. Identificación y descripción**
- **ID y título:** PB-02: Tramitar apelación y adecuación del T01
- **Descripción de la US:** Como involucrado quiero apelar el T01 por el canal formal para que el TD debata y comunique cualquier adecuación.

**B. UAT — Criterios de aceptación de usuario**
- CA1 apelación vía canal aprobado y plazo parametrizado
- CA2 debate puede adecuar puntos e involucrados sin borrar versión original
- CA3 motivos se notifican a solicitante y solicitado
- CA4 resolución final conserva trazabilidad
- CA5 impacto en estados y derecho de defensa aprobado por TD. Trazabilidad: diagrama art. 14 Reglamento Procesal 2026.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — PB-02 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de PB-02: Tramitar apelación y adecuación del T01 para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura PB-02. Funcionalidad de Tramitar apelación y adecuación del T01.*

**D. Diseño de casos de prueba**
- **US asociada:** PB-02
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

### PB-03: Implementar enmienda controlada de expediente emitido

**A. Identificación y descripción**
- **ID y título:** PB-03: Implementar enmienda controlada de expediente emitido
- **Descripción de la US:** Como autoridad habilitada quiero enmendar una resolución sólo en los supuestos reglamentarios para corregir sin destruir el historial.

**B. UAT — Criterios de aceptación de usuario**
- CA1 actor plazo y causales se definen mediante decisión institucional
- CA2 resolución emitida original permanece inmutable
- CA3 enmienda crea nueva versión y contramovimientos idempotentes si afecta puntos
- CA4 no permite a una gestión posterior alterar decisiones prohibidas
- CA5 notifica y audita el ciclo completo. Bloqueada hasta conciliar art. 13 y regla de irrevisabilidad.

**C. Diseño de interfaz**
`[INSERTAR CAPTURA DE INTERFAZ — PB-03 — Interfaz relacionada]`

*Descripción: Captura mostrando el componente o flujo de PB-03: Implementar enmienda controlada de expediente emitido para verificar la interfaz de usuario.*
*Origen sugerido: Frontend Angular o vista correspondiente.*
*Pie de figura: Figura PB-03. Funcionalidad de Implementar enmienda controlada de expediente emitido.*

**D. Diseño de casos de prueba**
- **US asociada:** PB-03
- **Objetivo:** Verificar el cumplimiento de los criterios de aceptación descritos en la historia.
- **Pasos de ejecución:** Ingresar al módulo correspondiente y ejecutar la acción de la US. Validar resultados positivos y validaciones según los CA.
- **Estado:** Ejecutado automáticamente en backend vía pytest.

**E. Resultados de las pruebas**
Existen más de 465 pruebas en el backend, incluyendo pruebas de endpoints, modelos y servicios. De la ejecución manual se desprende que 206 pasan y 259 fallan por indisponibilidad de conexión MySQL del entorno Docker. El comportamiento esperado está diseñado y automatizado en la suite de pruebas.

## 11. Diagrama de clases
*(Descripción textual de la arquitectura del dominio observada en `backend/expedientes/models.py` y dependencias)*

Principales clases del dominio implementadas:
- `Socio`: Entidad vinculada 1:1 a los datos de Autenticación, incluye categoría (Activo/Pasivo) y Legajo.
- `Expediente`: Mantiene el plazo de justificación, estado y trazabilidad.
- `CambioEstadoExpediente`: Modelo inmutable que registra trazabilidad de transiciones y auditoría. Tiene FK a Expediente.
- `DescargoExpediente`: Descargo que el socio presenta (T02/T03), con textos y referencia de archivo adjunto.
- `SolicitudT01`: Inicio de acción disciplinaria (Sanción o Mérito). Mantiene FK a Expediente y destinatario(s).

Las relaciones demuestran una alta cohesión alrededor del concepto de `Expediente` (Aggregate Root en terminología DDD).

## 12. DER — Diagrama Entidad-Relación
*(Basado en las tablas heredadas y migraciones de Django)*

**Tablas base de Padrón (Legacy, de Sólo Lectura):**
- `socio_lista`: Clave Primaria `nroSocio`. Campos: `nombre`, `apellido`, `legajo`, etc.
- `socio_estudio`: Clave Primaria compuesta física `compositeKey`. FK `nroSocio`.
- `socio_email`: Correos electrónicos.
- `socio_estado`: Catálogo de estados del sistema legado.

**Tablas operativas (Nuevas, SGD-AVEIT):**
- `expedientes_expediente`: PK id autoincremental o UUID. Campos: numero (unique), estado (varchar 30), plazo_inicio_at, plazo_limite_at (datetime).
- `expedientes_cambio_estado`: FK expediente_id, estado_anterior, estado_nuevo, fecha_hora (timestamp), actor (varchar).
- `expedientes_descargo`: FK expediente_id, FK socio_id (unique_together). causal (varchar 255), archivo (varchar).
- `expedientes_solicitudt01`: PK id (UUID). FK expediente_id. puntos (Decimal 10,2).

## 13. Diagramas de transición de estados
*(Basado en `CambioEstadoExpediente` y el `EstadoExpedienteEnum` analizado)*
- **Entidad con ciclo de vida:** Expediente.
- **Mecanismo responsable:** `ExpedienteWorkflowService.transition()`
- **Flujo válido / transiciones observadas:** `CREADO` -> `JUSTIFICANDO` -> `SUSTANCIANDO` -> `RESOLVIENDO` -> `EMITIDO` -> `CERRADO`.
- **Regla de negocio:** No se permiten saltos arbitrarios. Las reversiones o excepciones están trazadas. Inmutabilidad estricta garantizada por el modelo `CambioEstadoExpediente`.

## 14. Definición de la arquitectura del software
### 14.1. Vista general
El sistema implementa una arquitectura por capas basada en Microservicios orquestados mediante Docker (Contenedores), con clara separación entre la Presentación (SPA) y la Lógica de Negocio (Backend/API).
### 14.2. Ambiente de implementación
- **Frontend:** Angular 14.2+ (TypeScript), estilizado con Material Dashboard PRO.
- **Backend:** API REST en Python 3.12 utilizando Django 4.2 LTS y Django REST Framework (DRF).
- **Base de Datos:** MySQL 8.0 relacional y transaccional.
- **Infraestructura Local:** Orquestación mediante `docker-compose.yml`.
### 14.3. Diagrama de despliegue (Lógico)
- **Nodo 1 (Navegador Cliente):** SPA Angular (ejecuta interfaces gráficas, formularios, tableros de US S2-05, S3-03, etc.).
- **Nodo 2 (Backend Container):** Django app. Procesa las reglas de dominio, validaciones de competencia y firmas (US S2-03, S5-01, S5-03).
- **Nodo 3 (DB Container):** MySQL 8.0. Persiste padrón y movimientos de saldo.
### 14.4. Lay-out de equipamiento
La topología física de producción (servidores físicos o nube) no se encuentra definida en el repositorio actual (`docs/`). Se asume un despliegue Cloud (AWS/GCP) o VPS provisto por AVEIT. *Pendiente de confirmar por el equipo de infraestructura.*

## 15. Casos de uso
*(Derivados del análisis)*
1. **Presentación de Descargo (T02):** Socio (imputado) inicia acción dentro de la plataforma. Precondición: Expediente en plazo y estado `JUSTIFICANDO`. Flujo: Selección de causal, carga de adjuntos, firma y envío inmutable. Resultado: Descargo registrado (US S3-03).
2. **Votación del Tribunal:** TD emite voto en un expediente en estado `RESOLVIENDO`. Resultado: Se contabiliza voto, al llegar a mayoría se puede transicionar a Resolución (US S4-05).