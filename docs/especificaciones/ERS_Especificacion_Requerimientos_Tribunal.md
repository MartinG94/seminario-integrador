# ESPECIFICACIÓN DE REQUERIMIENTOS DE SOFTWARE (ERS)
## Módulo Unificado de Tribunal de Disciplina y Premiaciones (SGD-AVEIT)

---

### DATOS DEL DOCUMENTO Y CONTROL DE VERSIONES

| Atributo | Especificación |
| :--- | :--- |
| **Organización** | Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (A.V.E.I.T.) - UTN FRC |
| **Sistema** | SGD-AVEIT (Sistema de Gestión del Tribunal de Disciplina y Premiaciones) |
| **Módulo** | Módulo Unificado de Tribunal (6 Submódulos Integrados) |
| **Versión** | 1.1.0 (Iteración 1 - Consolidación de Estados Procesales) |
| **Fecha** | 03/09/2026 |
| **Metodología** | Scrumban / IEEE 830 / ISO/IEC/IEEE 29148 / Tom Gilb Planguage |

---

## 1. INTRODUCCIÓN Y ALCANCE

El presente documento formaliza los Requerimientos de Software para la primera iteración del **Módulo de Tribunal de Disciplina y Premiaciones (SGD-AVEIT)**. El módulo articula en una sola interfaz integral seis (6) submódulos operativos:

1. **Mis Expedientes:** Portal de consulta personal para el socio con contador de días hábiles y acceso condicional al formulario de descargo.
2. **Formulario Unificado de Justificaciones (T02/T03):** Formulario inteligente que consolida justificaciones tipificadas (con carga obligatoria de certificados médicos/académicos) y descargos extraordinarios (exposición libre).
3. **Gestionar Expedientes:** Panel operativo para el Tribunal de Disciplina con selector de vista dual (**Tablero Kanban de 5 estados procesales consolidados** y **Vista Detalle estilo Explorador de Windows** con foco en el expediente).
4. **Reportes:** Motor de analítica y auditoría interna que incluye el Balance Cuatrimestral de Disciplina, desgloses por subcomisión y exportación en PDF/Excel.
5. **Ranking de Socios:** Padrón ordenable de forma ascendente y descendente por puntaje acumulado (+/-), con filtros por categoría (Junior/Senior) y semáforos de advertencia preventiva (7 puntos negativos) y límite de cese (10 puntos negativos).
6. **Solicitar Puntos:** Trámite formal de premios o sanciones mediante Formulario T01 + Hoja Anexo, validando las competencias de cada autoridad.
7. **Eventos y Asistencia Digital:** Programación de actividades institucionales obligatorias con registro de asistencia ("pasar el dedo" / check-in digital) y cierre automático de causas por inasistencias.

> [!NOTE]
> **Consolidación de Estados Procesales:** A efectos de optimizar el flujo operativo y evitar redundancias de transición, se consolidan las fases de análisis probatorio y redacción del dictamen en un único estado procesal: **"En revisión y resolución"**. De esta manera, el ciclo de vida del expediente se estructura en cinco (5) estados:
> 1. *Expediente Creado*
> 2. *En período de justificaciones* (5 días hábiles)
> 3. *En revisión y resolución*
> 4. *Pendiente de firma y envío*
> 5. *Expedientes ya emitidos*

> [!NOTE]
> **Directiva de Diseño de Interfaz (Clean UI):** Las pantallas y componentes de usuario prescinden deliberadamente de citas textuales de artículos y números de leyes ("Art. XX"), comunicando cada regla en términos institucionales claros, directos y amigables.

---

## 2. STAKEHOLDERS Y MATRIZ DE ACTORES

| Actor | Rol en el Sistema | Atribuciones Principales en el Módulo |
| :--- | :--- | :--- |
| **Socio Ordinario** | Usuario Base (Juniors 1º-2º año y Seniors 3º-6º año) | Consulta sus causas en "Mis Expedientes", presenta descargos y consulta el ranking. |
| **Miembro del TD** | Juez / Operador del Tribunal de Disciplina | Gestiona causas en Kanban/Detalle, revisa descargos, vota, firma resoluciones y emite balances. |
| **Comisión Directiva** | Órgano Ejecutivo de Gobierno | Inicia solicitudes de puntos T01 generales, supervisa el ranking y recibe alertas de 7 y 10 pts. |
| **Autoridad de Subcomisión / Líder** | Solicitante Operativo Descentralizado | Solicita premios o sanciones (T01) sobre los miembros adscriptos a su área o equipo. |
| **Temporizadores del Sistema** | Proceso Automatizado (Daemon/Cron) | Controla el plazo de 5 días hábiles, transiciona estados y evalúa los umbrales de 7 y 10 pts. |
| **Servicio de Correo SMTP** | Mensajería Externa | Notifica aperturas de causas, resoluciones dictadas y alertas urgentes. |

---

## 3. REQUERIMIENTOS FUNCIONALES (RF)

| ID | Denominación | Actor(es) | Descripción Funcional | Entradas / Salidas | Reglas | Prioridad |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **RF-01** | Consulta de Mis Expedientes | Socio Ordinario | El sistema debe mostrar el listado de causas donde el socio autenticado sea imputado o postulado, indicando número de expediente, fecha de apertura, motivo, puntaje provisorio, estado procesal y cuenta regresiva de días hábiles restantes. | **E:** Sesión de socio.<br>**S:** Grilla de causas personales con estado y días de plazo. | RN-01, RN-05 | **Must** |
| **RF-02** | Formulario Unificado de Justificaciones (T02/T03) | Socio Ordinario | El sistema debe proveer una interfaz unificada para ingresar descargos, permitiendo alternar entre *Justificación con Certificado* (exige causal médica, académica o laboral y carga de comprobante en PDF/JPG/PNG) y *Descargo Extraordinario* (exposición libre y adjuntos opcionales). | **E:** Tipo de descargo, causal/texto, archivos adjuntos.<br>**S:** Constancia digital de recepción con sello de tiempo. | RN-02, RN-05, RN-06 | **Must** |
| **RF-03** | Tablero Kanban de Expedientes | Miembro del TD | El sistema debe ofrecer una vista visual en tablero Kanban estructurada en cinco (5) columnas procesales consolidadas: 1) Creado, 2) En período de justificaciones, 3) En revisión y resolución, 4) Pendiente de firma y envío, 5) Ya emitidos. | **E:** Filtros de búsqueda.<br>**S:** Tablero con tarjetas informativas y badges de estado. | RN-03, RN-04 | **Must** |
| **RF-04** | Vista Detalle (Estilo Explorador) | Miembro del TD | El sistema debe ofrecer una vista tabular densa con foco en el expediente, permitiendo ordenar por cualquier columna (N° Exp, Socio, Fecha, Plazo, Estado), buscar en tiempo real y acceder a acciones contextuales rápidas. | **E:** Clic en columna para ordenar, texto de búsqueda.<br>**S:** Grilla tabular interactiva ordenada. | RN-03, RN-04 | **Must** |
| **RF-05** | Sustanciación, Votación y Firma Colegiada | Miembro del TD | En el estado *En revisión y resolución*, el sistema debe permitir a los jueces registrar su voto nominal fundado (aprobación/rechazo/graduación), verificar la mayoría absoluta (>= 2/3 votos), estructurar la resolución (Vistos, Considerandos, Fallo) y pasar a *Pendiente de firma y envío* para recolectar las firmas colegiadas digitales. | **E:** Voto, fundamentación, firma digital.<br>**S:** Resolución formal dictada y firmada. | RN-08, RN-09, RN-10, RN-11 | **Must** |
| **RF-06** | Ranking de Socios con Ordenamiento Bidireccional | Todos los Actores | El sistema debe listar el padrón completo de socios con su saldo neto acumulado de puntos (+/-), permitiendo ordenamiento ascendente (del más sancionado al más premiado) y descendente, con filtros por categoría (Junior/Senior) y Subcomisión. | **E:** Parámetros de orden (asc/desc) y filtros.<br>**S:** Tabla de ranking con semáforos de advertencia. | RN-13, RN-14 | **Must** |
| **RF-07** | Consulta de Legajo y Ficha de Socio | Miembro TD, CD | El sistema debe permitir visualizar la ficha histórica consolidada de un socio, detallando sus expedientes vinculados, resoluciones, descargos y el historial transaccional de movimientos de puntos. | **E:** Selección de socio o legajo.<br>**S:** Ficha integral con historial y estado actual. | RN-12 | **Should** |
| **RF-08** | Solicitud de Puntos (Formulario T01 + Anexo) | Autoridades Habilitadas | El sistema debe permitir tramitar pedidos de puntos positivos (+) en concepto de méritos o negativos (-) por sanciones, exigiendo la carga de la Hoja de Anexo circunstanciada con hechos, fechas y testigos. | **E:** Datos del T01, Anexo fáctico, pruebas.<br>**S:** Expediente disciplinario generado en estado Creado. | RN-01, RN-07 | **Must** |
| **RF-09** | Validación de Competencias de Autoridades | Sistema (Backend) | El sistema debe validar automáticamente que la autoridad solicitante posea facultades estatutarias sobre el socio destinatario antes de admitir la solicitud de puntos. | **E:** ID solicitante, ID destinatario.<br>**S:** Admisión o rechazo por incompetencia. | RN-07 | **Must** |
| **RF-10** | Programación de Eventos y Check-in Digital | Autoridades Habilitadas, Socios | El sistema debe permitir dar de alta reuniones y actividades obligatorias, y proveer una interfaz de "pasar el dedo" (check-in digital) que confirme la asistencia en tiempo real y actualice el conteo de presentes/ausentes. | **E:** Datos de evento, confirmación de asistencia.<br>**S:** Registro de presentes y porcentaje de asistencia. | RN-15 | **Must** |
| **RF-11** | Cierre de Evento y Generación Automática de Causas | Autoridades, Sistema | Al confirmar el cierre definitivo de un evento obligatorio, el sistema debe identificar automáticamente a los socios con inasistencia injustificada y generar los expedientes correspondientes en estado Creado. | **E:** Confirmación de cierre de evento.<br>**S:** Lote de expedientes creados y acuses enviados. | RN-01, RN-05 | **Must** |
| **RF-12** | Generación de Balances Cuatrimestrales y Reportes | Miembro TD, CD | El sistema debe compilar a demanda los datos del período y generar el Balance Cuatrimestral de Disciplina estructurado por subcomisión y grupo social (Juniors/Seniors), permitiendo exportar en PDF y Excel (XLSX). | **E:** Selección de cuatrimestre y filtros.<br>**S:** Reporte analítico interactivo y archivos descargables. | RN-16 | **Must** |

---

## 4. REGLAS DE NEGOCIO (RN)

| Código | Nombre de la Regla | Enunciado Lógico Formal |
| :---: | :--- | :--- |
| **RN-01** | **Disparo del Plazo de Justificación** | Al pasar un expediente al estado *En período de justificaciones*, se inicia un temporizador improrrogable de exactamente **cinco (5) días hábiles** (120 horas hábiles). |
| **RN-02** | **Preclusión Automática de Descargos** | Vencidos los 5 días hábiles sin que el socio haya enviado su descargo, el sistema bloquea irreversiblemente el botón de justificación y transiciona automáticamente la causa a *En revisión y resolución*. |
| **RN-03** | **Coherencia de Estados Procesales Consolidados** | Todo expediente debe transitar estrictamente por los 5 estados oficiales consolidados: Creado ➔ En período de justificaciones ➔ En revisión y resolución ➔ Pendiente de firma y envío ➔ Expedientes ya emitidos. |
| **RN-04** | **Sincronización de Vistas de Gestión** | Cualquier cambio de estado o acción ejecutada en la Vista Tablero Kanban debe reflejarse inmediatamente en la Vista Detalle y viceversa. |
| **RN-05** | **Obligatoriedad de Comprobante en Causal Tipificada** | En el Formulario Unificado, si el usuario selecciona una causal tipificada (salud, examen, viaje laboral), es condición obligatoria adjuntar al menos un archivo digitalizado válido para habilitar el botón de envío. |
| **RN-06** | **Declaración Jurada en Descargos** | Toda justificación o descargo enviado reviste carácter de declaración jurada digital, registrándose con sello de tiempo UTC e identificador de usuario. |
| **RN-07** | **Límites de Competencia para Solicitudes** | Las autoridades de subcomisión y líderes de equipo solo pueden solicitar sanciones o premios sobre miembros adscriptos a su propia área; la Comisión Directiva puede accionar sobre cualquier socio salvo miembros de su propia mesa ejecutiva. |
| **RN-08** | **Incompatibilidad por Conflicto de Interés** | Si un juez del Tribunal fue quien inició la solicitud de puntos o es parte involucrada en la causa, queda automáticamente inhibido de votar, convocándose al juez suplente correspondiente. |
| **RN-09** | **Mayoría Calificada en Dictámenes** | Las resoluciones del Tribunal se aprueban por mayoría absoluta (al menos dos votos concordantes de tres jueces intervinientes). |
| **RN-10** | **Estructura Mandatoria del Fallo** | Toda resolución requiere obligatoriamente completar los tres bloques institucionales: Vistos, Considerandos y Resolución/Fallo. |
| **RN-11** | **Eficacia Jurídica por Firma Colegiada** | Ninguna resolución surte efecto ni impacta puntos hasta contar con la firma digital de los tres jueces habilitados. |
| **RN-12** | **Inmutabilidad Transaccional del Saldo** | Queda estrictamente prohibida la modificación manual del saldo de puntos mediante sentencias SQL directas (`UPDATE`); todo movimiento requiere una resolución firmada que genere un registro de auditoría inmutable. |
| **RN-13** | **Alerta Preventiva a los 7 Puntos** | Al acumular un socio un saldo igual o superior a siete (-7.0) puntos negativos netos, el sistema emite automáticamente una Alerta Preventiva Amarilla al socio y a su autoridad de área. |
| **RN-14** | **Límite Crítico de Pérdida de Condición de Socio (10 Puntos)** | Todo socio que alcance o supere diez (-10.0) puntos negativos netos pierde de forma automática su condición de socio de AVEIT; el sistema emite de inmediato una Alerta Roja Crítica a la Comisión Directiva para formalizar el cese. |
| **RN-15** | **Cómputo Automático de Inasistencias** | Los socios convocados a un evento obligatorio que no registren check-in ("pasar el dedo") al momento del cierre formal son clasificados automáticamente como ausentes injustificados. |
| **RN-16** | **Segmentación Obligatoria en Balances** | Los balances cuatrimestrales deben discriminar obligatoriamente el desempeño y saldos de los Socios Juniors (1º y 2º año social) respecto de los Socios Seniors (3º a 6º año social). |

---

## 5. REQUERIMIENTOS NO FUNCIONALES (RNF) BAJO ISO/IEC 25010 Y PLANGUAGE

### RNF-01: Rendimiento y Comportamiento Temporal (Eficiencia de Desempeño)
* **Categoría FURPS+:** Performance / Eficiencia de Desempeño (ISO 25010).
* **Métrica Planguage (Tom Gilb):**
  - **SCALE:** Tiempo de respuesta de la interfaz al alternar entre Vista Kanban y Vista Detalle, y al ordenar el Ranking de socios.
  - **METER:** Medición en milisegundos mediante Navigation Timing API bajo 100 usuarios concurrentes simulados con un padrón de 600 socios.
  - **BASELINE:** 3.800 ms (hojas de cálculo Google Sheets actuales).
  - **WORST_ACCEPTABLE:** 1.000 ms.
  - **TARGET_PLAN:** `<= 250 ms`.
  - **STRETCH_WISH:** `<= 100 ms` con renderizado en cliente y virtualización de listas.

### RNF-02: Seguridad e Integridad Transaccional (Seguridad)
* **Categoría FURPS+:** Security / Seguridad de la Información (ISO 25010).
* **Métrica Planguage:**
  - **SCALE:** Porcentaje de modificaciones de puntos ejecutadas sin un expediente formal y firma colegiada asociada.
  - **METER:** Auditoría automatizada de logs y triggers de base de datos comparando registros de ledger con resoluciones válidas.
  - **BASELINE:** ~15% de puntos modificados manualmente por base de datos o planillas sin pista de auditoría.
  - **TARGET_PLAN:** `0.0%` (Cero tolerancia a mutaciones directas; integridad 100% garantizada).

### RNF-03: Usabilidad y Diseño Responsive Mobile-First (Usabilidad)
* **Categoría FURPS+:** Usability / Usabilidad y Calidad en Uso (ISO 25010).
* **Métrica Planguage:**
  - **SCALE:** Tiempo en segundos que le toma a un socio completar su justificación con comprobante desde un teléfono móvil.
  - **METER:** Prueba de usabilidad con 10 socios Juniors en dispositivos Android/iOS sin capacitación previa.
  - **BASELINE:** 12 minutos (descargar plantilla Word, editar, escanear, enviar mail).
  - **WORST_ACCEPTABLE:** 3 minutos.
  - **TARGET_PLAN:** `<= 60 segundos`.
  - **STRETCH_WISH:** `<= 30 segundos`.

### RNF-04: Fiabilidad y Control de Plazos (Confiabilidad)
* **Categoría FURPS+:** Reliability / Fiabilidad y Madurez (ISO 25010).
* **Métrica Planguage:**
  - **SCALE:** Precisión del temporizador preclusivo de 5 días hábiles en transicionar automáticamente el estado de la causa hacia *En revisión y resolución*.
  - **METER:** Verificación de ejecución del daemon de tareas programadas frente a calendario oficial de días hábiles.
  - **TARGET_PLAN:** `100%` de precisión en el corte a las 120 horas hábiles exactas con registro de auditoría UTC.

### RNF-05: Mantenibilidad y Modularidad (Mantenibilidad)
* **Categoría FURPS+:** Supportability / Mantenibilidad (ISO 25010).
* **Métrica Planguage:**
  - **SCALE:** Esfuerzo en horas-persona para incorporar un nuevo tipo de evento o causal tipificada sin alterar el motor de expedientes.
  - **TARGET_PLAN:** `<= 2 horas-persona` mediante configuración tabular sin recompilación del núcleo.

### RNF-06: Portabilidad y Compatibilidad Web (Portabilidad)
* **Categoría FURPS+:** Portability / Compatibilidad (ISO 25010).
* **TARGET_PLAN:** Funcionamiento 100% garantizado en navegadores modernos (Chrome, Firefox, Safari, Edge) en entornos Desktop y Mobile, cumpliendo con la guía de diseño [DESIGN.md](file:///g:/My%20Drive/Estudios/Seminario/Repositorio/seminario-integrador/DESIGN.md).

---

## 6. SUPUESTOS, RESTRICCIONES Y DEPENDENCIAS

* **SUP-01 (Supuesto):** Todos los socios activos disponen de acceso a un navegador web móvil o de escritorio para consultar su legajo y registrar descargos.
* **SUP-02 (Supuesto):** El calendario institucional define al inicio del año social los feriados y días inhábiles para el cómputo de plazos.
* **RES-01 (Restricción de Negocio):** El límite de 10 puntos negativos provoca la pérdida automática e irreversible de la condición de socio, la cual no puede ser suspendida por el software.
* **RES-02 (Restricción Tecnológica):** El backend debe integrarse con el servidor existente de AVEIT (Python + MySQL).
* **RES-03 (Restricción de Diseño):** Las interfaces de usuario no deben contener menciones directas a números de artículos legales, priorizando la comprensión funcional.
* **DEP-01 (Dependencia):** Disponibilidad del servicio de correo institucional (SMTP) para el despacho fehaciente de notificaciones.
