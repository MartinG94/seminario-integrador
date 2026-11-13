# Notas del PO — Revisión de pantallas existentes
> **Fecha:** 27/09/2026 · **Autor:** Diego (Product Owner)

Voy a dejar acá todo lo que necesito que el equipo tenga en cuenta antes de arrancar el sprint. Algunas cosas son cambios de texto, otras son reglas de negocio que estaban mal o que no estaban modeladas. Léanlo con tiempo y consulten antes de tocar código.

---

## Decisiones generales (aplican a todo el sistema)

**Lenguaje de la UI.** Los textos tienen que hablarle a un socio de AVEIT, no a un usuario de software empresarial. Frases largas afuera, términos técnicos afuera. Si algo se puede decir en dos palabras, se dice en dos. "Estado procesal" → "Estado". "Registro formal de causas disciplinarias" → directamente, no va.

**Expedientes con múltiples socios.** Un expediente puede tener más de un acusado. La resolución después se individualiza: uno puede quedar sin sanción y el otro sí. Hay que modelarlo así desde el principio, no es un parche que se puede meter después.

**Llamados de atención y Felicitaciones.** No son ±0,33 ni ±0,5. Son una categoría aparte. Cuando se acumulan tres, ahí sí impactan como un punto completo. El frontend y el backend tienen que respetar esa distinción — no mezclarlo con los movimientos de puntos directos.

---

## Pantalla: Mis Expedientes

**Título del panel:** "Mis Expedientes y Descargos" (sacar "Reglamentarios").

**Subtítulo descriptivo:** eliminarlo. No aporta nada.

**Tabla.** Las columnas tienen que quedar así, en este orden:
`Exp.` · `Título` · `Puntos` · `Creado` (solo DD/MM/YYYY) · `Estado` · `Acciones`

El tiempo restante del plazo **no va como columna separada**. Va integrado dentro del chip/badge del estado "En período de justificaciones" — algo así como "En plazo · 74h". Así el socio entiende el contexto de un vistazo sin tener que cruzar columnas.

**Botón de detalle.** Cada fila necesita un botón en "Acciones" que abra un modal con el detalle completo del expediente. Datos de la causa, socios involucrados, historial de estados, etc.

**Descargo.** El botón dice "Descargo", no "Presentar Descargo". Mientras el plazo esté abierto y el socio ya haya presentado uno, tiene que poder editarlo. No cerrar la ventana de edición hasta que venza el plazo.

**Puntos totales.** El widget arriba tiene que sumar los puntos de todos los expedientes del socio. Hoy muestra un número hardcodeado.

---

## Pantalla: Reglamentos

Es un ABM de artículos del Reglamento Interno. Hay que volcar los artículos ahí. **Todos los socios pueden ver**; solo TD, CD y Admin pueden agregar o editar. El control de acceso tiene que estar en servidor, no solo ocultando botones en el front.

> **Actualizado (13/11/2026):** Implementado el ABM de Reglamentos con auditoría, carga inicial de artículos reglamentarios y control de acceso en servidor.

---

## Pantalla: Crear Expediente (T01)

**Acceso.** Solo TD, CD y Autoridades. Si un socio común entra al sistema, esta opción no tiene que existir para él — ni en el menú, ni como ruta directa.

**Campos y orden del formulario:**
1. Título (antes llamado "Motivo") — va primero
2. Relato / Razón de la apertura
3. Documentos adjuntos (opcional)
4. Testigos (opcional)

**Subcomisión.** Sacar el selector. No es necesario al crear el expediente.

**Socios involucrados.** Tiene que poder cargarse más de uno. Select2 para la búsqueda reactiva (nombre o número de socio). Recordar: las resoluciones después se individualizan por socio.

**Nuevas opciones de tipo de acción:**
- Llamado de atención
- Felicitación
- Pedido de expulsión (tiene que poder cargarse, con su propio flujo)

**Escala de puntos.** Antes de definir los límites fijos, hay que relevar el histórico de pedidos que ya existen para tener datos reales sobre los rangos usados. No queremos inventar topes que después no se aplican.

**"Pautas del Régimen Disciplinario".** Eliminar esa sección completa del formulario.

---

## Pantalla: Ranking / Padrón

**Cabecera de tabla:** `Posición` · `Socio` · `N° de Socio` · `Grupo` · `Subcomisión` · `Puntos` · `Acciones`

Todas las columnas deben poder ordenarse.

**Saldo.** Solo el número de puntos, con color (verde positivo, rojo negativo). Sacar el badge de "HABILITADO REGULAR" de esa celda.

**Columna Acciones.** Botón para ver el detalle del historial del socio en un modal.

**"Pautas del Régimen Disciplinario" arriba de la tabla.** Eliminar ese bloque con los chips de HABILITADO / ADVERTENCIA / CESE ESTATUTARIO. El criterio de -10 y la política de -7 van a ser configurables, y por ahora no pertenecen a la pantalla de ranking.

> **Actualizado (13/11/2026):** Implementado el ordenamiento por Saldo y compuesto (Grupo + Alfabético), el modal de detalle por socio y la lógica de alertas por umbrales reglamentarios (-10 crítico y -7 preventivo configurable/desactivable) con estricta privacidad.

---

## Pantalla: Reportes

Están en pausa. Tengo que hablar con los usuarios del TD para definir qué necesitan ver. No arrancar nada acá todavía.

> **Actualizado (13/11/2026):** Reportes salió de pausa e ingresó al sistema con vistas de T01, Reuniones, Subcomisiones, Histórico/Récords, Resumen y Exportación CSV (ver sección del 13/11/2026).

---

## Pantalla: Eventos y Asistencia

**Acceso.** Solo CD y Autoridades pueden ver esta sección.

**Flujo básico:**
1. Se crea un evento desde acá.
2. Si alguien no asiste, se genera automáticamente un expediente por inasistencia.
3. Se puede citar a un socio solo o a un grupo de socios.

**Toma de asistencia.** Por ahora se carga a mano. Más adelante se va a conectar con un lector de huellas. Usen el **patrón Strategy** para abstraer el mecanismo de toma de asistencia — así cuando llegue el lector, se conecta sin tocar el resto del código.

---

## Distribución de trabajo sugerida (5 devs)

Acuerden primero el modelo de datos compartido (Expediente, Socio, Estado, Movimiento de puntos). Una vez mergeado eso, cada uno puede trabajar en paralelo sin pisarse:

| Dev | Módulo |
|---|---|
| Dev 1 | Apertura T01 + validación de competencias (Arts. 21–26) |
| Dev 2 | Tablero de estados + filtros + Kanban |
| Dev 3 | Descargos T02/T03 + cálculo de plazos hábiles |
| Dev 4 | Sala de Tribunal: votación, suplencias y resolución |
| Dev 5 | Notificaciones, libro mayor de puntos y "Mis Expedientes" |

Las US en Jira quedan atómicas (2–5 puntos). Cada dev mueve sus propias tarjetas a *Done* cuando cumple la DoD completa: tests, cobertura, responsive y revisión de par.

---

# Notas del PO — Acuerdos con Cómputos y Tribunal de Disciplina (TD)
> **Fecha:** 07/10/2026 · **Autor:** Diego (Product Owner)

Dejo asentadas las definiciones y acuerdos alcanzados en las reuniones mantenidas el **07/10/2026** con la autoridad de la Subcomisión de Cómputos y con representantes del Tribunal de Disciplina (TD). Estos puntos constituyen lineamientos de negocio e infraestructura rectores para la planificación y desarrollo del Sprint 3 y subsiguientes:

---

## 1. Definiciones Institucionales y Gobernanza de Roles

* **Renombrar Rol Fiscalizadora por Revisores (Revisores de Cuentas):**
  - Se debe cambiar en todo el sistema (backend RBAC, frontend, nombres de rutas, selectores, tooltips) y en toda la documentación formal de ingeniería y cátedra el rol "Comisión Fiscalizadora" / "Fiscalizadora" por **"Revisores"** (o **"Revisores de Cuentas"** en contextos formales).
  - La justificación es de estricta adecuación estatutaria e institucional de AVEIT.

* **Delimitación de Soporte Técnico (Cómputos):**
  - Cómputos mantiene el rol técnico administrativo (`ACT-05 Admin`) para gestión de infraestructura, monitoreo de logs, ejecución de copias de seguridad y parametrización de variables de entorno, sin facultades para juzgar expedientes ni alterar saldos de puntos.

---

## 2. Gestión y Tablero de Expedientes

* **Clasificador de Urgencia en Expedientes:**
  - Agregar un clasificador / indicador de urgencia a nivel expediente (`Baja`, `Normal`, `Urgente`).
  - Esto le permite al Tribunal de Disciplina priorizar en el tablero y listados la atención de causas de gravedad institucional o con plazos procesales críticos.

* **Expedientes con Múltiples Socios Involucrados (Botón de Socios):**
  - En la vista de gestión de expedientes (tabla y tablero), cuando un expediente cuente con más de un socio involucrado, se debe incorporar un **botón o acción visible** para desplegar el modal/listado de los socios vinculados a la causa sin necesidad de navegar a pantallas externas.

* **Tarea de I+D para Diego (PO):**
  - Investigar **Laya** (alternativa local y open source a TypeSafe Jev): modelo "System 1" no generativo (~150–400M parámetros) que devuelve decisiones tipadas con probabilidades (`choice`, `score`, `noul`), corre en CPU para inferencia y se ajusta (fine-tuning) en una GPU de escritorio.
  - Alcance: asistir con **sugerencias no vinculantes** de grado de urgencia (`score`) y de artículo del Reglamento a invocar (`choice`) a partir del Motivo y la Hoja de Anexo. La decisión final sigue siendo del Tribunal.
  - Prerrequisito: relevar expedientes y resoluciones históricas del TD con su urgencia y artículo reales para armar el dataset de fine-tuning.

---

## 3. Pantalla: Crear Expediente (Formulario T01) y Hoja de Anexo

* **Grupo Social en Tabla de Involucrados:**
  - En la tabla de selección de socios involucrados del Formulario T01, se debe agregar la columna visible **"Grupo"** (ej. G57, G58, G59, G60) para identificar la cohorte/año social de cada involucrado de un vistazo.

* **Hoja de Anexo Circunstanciada (Ref. Imagen 1):**
  - Precisar los campos forenses:
    - **Lugar o Evento del hecho:** Registrar con exactitud el espacio físico (ej. "Sede AVEIT, Laboratorio de Cómputos") o el evento institucional donde acontecieron los hechos.
    - **Testigos presenciales y cómo se involucraron:** En el detalle de testigos presenciales y relato circunstanciado, registrar no solo los nombres/contacto sino detallar explícitamente *cómo se involucraron los testigos* (ej. qué presenciaron, su grado de participación directa o indirecta).

---

## 4. Sala del Tribunal y Detalle del Expediente (Ref. Imágenes 2 y 3)

* **Detalle del Expediente según Formato Oficial del TD (Imagen 2):**
  - En la vista de detalle de la causa para el Tribunal de Disciplina se deben respetar rigurosamente los campos y formato que utiliza el TD actualmente:
    - **Cabecera:** N° de Expediente/Año (ej. `Expediente 419/2025`), Estado de expediente, Fecha de Solicitud, Título y Motivo (relato pormenorizado).
    - **Graduación requerida:** Sanción/Mérito solicitado, Reglamento invocado y datos del Solicitante (`N° de Socio - Nombre y Apellido`).
    - **Responsables del Tribunal:** Bloque con los tres integrantes intervinientes:
      - `Responsable 1`: N° de Socio - Nombre y Apellido - Grupo (ej. `11239 - Giuliano Toselli - G57`)
      - `Responsable 2`: N° de Socio - Nombre y Apellido - Grupo (ej. `11737 - Catalina Cerda Gallego - G58`)
      - `Responsable 3`: N° de Socio - Nombre y Apellido - Grupo (ej. `11735 - Candela Moreno Migliore - G59`)
    - **Reglamentos respaldantes de resolución:** Listado de artículos y secciones normativas de respaldo.
    - **Tabla de Involucrados:** Columnas `N° de Socio` · `N° de Grupo` · `Nombre` · `Apellido` · `Estado de Justificación`.

* **Simplificación de la Votación y Redacción de Resolución:**
  - **La votación nominal compleja queda por fuera del sistema:** No se implementará un flujo intrincado de votación voto a voto en la sala virtual.
  - En su lugar, la interfaz de emisión de dictamen debe proveer un **recuadro unificado para redactar el texto formal de la Resolución** y fijar el **Puntaje Final Aplicado** (sanción o reconocimiento consolidado por cada socio involucrado).

* **Distinción de Año Social en Miembros del TD al Firmar (Imagen 3):**
  - Al suscribir la resolución y en su pie de firma, se debe distinguir obligatoriamente el **año social / grupo** de cada miembro del Tribunal, así como su condición de Titular o Suplente.
  - Formato canónico: `[N° de Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]`  
    *(Ejemplo real: `11735 - Candela Moreno Migliore - G59  12123 - Abril Sofia Moya - G60  11928 - Abril Gusella - G58 (Sup.)`)*.

* **Formato Institucional de la Resolución (Imagen 3):**
  - Emisión con membrete y escudo oficial del Tribunal de Disciplina.
  - Identificación formal: `RESOLUCIÓN NNN/AAAA`, `Ref: ...`, `Córdoba, DD de Mes de AAAA, HH:MM hs`.
  - Estructura canónica:
    - **VISTO:** Artículos reglamentarios citados con numeración correlativa.
    - **CONSIDERANDO:** Argumentación y valoración probatoria de la sanción o mérito.
    - **SE RESUELVE:** Artículos dispositivos individualizando expresamente el impacto en puntos de cada socio por nombre y legajo, notificación a CD y archivo.

> **Actualizado (13/11/2026):** Se consolidó el modal de Resolución Oficial sin votación nominal, con permisos exclusivos del TD, persistencia de reglamentación y considerando limpio, incorporando el estado intermedio **"Pendiente de firma"** previo a la emisión definitiva (ver sección del 13/11/2026 y acuerdos de Sprint 5 sobre el reemplazo de "legajo" por "Número de Socio").

---

## 5. Pantalla: Ranking de Socios

* **Detalle de Expedientes por Socio:**
  - Permitir consultar el historial de causas/expedientes que conformaron el puntaje de cada socio (mediante modal o vista de detalle interactiva).

* **Limpieza de Controles y Ordenamiento Directo por Saldo:**
  - Eliminar los botones de filtro *"Más reconocidos"* y *"Mayor sanción"*.
  - Permitir ordenar la tabla directamente haciendo clic sobre la cabecera de la columna **Saldo** (asegurar que las columnas clave sean ordenables).

* **Ordenamiento Múltiple y Anidado:**
  - Incorporar la capacidad de ordenamiento compuesto: permitir ordenar en primer nivel por **Grupo Social** y luego por **Orden Alfabético** (Apellido y Nombre).

---

## 6. Regla de Puntos: Felicitaciones y Llamados de Atención

* **Inmutabilidad de la Regla de Acumulación 3:1:**
  - Se reitera y ratifica taxativamente: las felicitaciones y los llamados de atención **no aplican movimientos directos fraccionarios de ±0,33 ni ±0,5 puntos**.
  - Son categorías independientes. Cada **tres (3) acumulados** consolidan **un (1) punto neto** (+1 o -1 respectivamente).

---

## 7. Acuerdos Técnicos con Cómputos y Base de Datos

* **Estabilidad de Base de Datos MySQL:**
  - Corroborar el funcionamiento y conectividad del servicio MySQL en Docker.
* **Ampliación de Datos de Prueba (Seed Data):**
  - Incorporar fixtures y seed data más exhaustivos y representativos (socios con distribución real en grupos G57 a G60, subcomisiones y causas disciplinarias testigo) para asegurar pruebas de integración y demostraciones fieles al uso institucional.

---

# Notas del PO — Consolidación de sprints 3–4 y acuerdos del sprint 5
> **Fecha:** 13/11/2026 · **Autor:** Diego (Product Owner)

Dejo asentado lo que ya quedó implementado y funcionando en el sistema durante los Sprints 3 y 4, más los acuerdos que cerramos para terminar el Sprint 5. Todo lo que se desarrolle o revise de acá en adelante tiene que respetar estas definiciones.

---

## 1. Decisiones transversales y experiencia de usuario (implementado)

* **Notificaciones (toast):** En toda la app (incluidos login y modales), los avisos de éxito, error, advertencia e información salen abajo a la derecha por el servicio central. Duran 10 segundos, se desvanecen solos y se pueden cerrar con una X accesible. Cambiar de pantalla no los borra. No ponemos alertas transitorias dentro de formularios ni usamos `$.notify`. Todo en texto plano, sin trazas ni detalles técnicos.
* **Formato de expedientes y visor:** Unificamos el código a `EXP-NNNN/YYYY` en todo el sistema y sumamos el visor de detalle según rol. La evidencia adjunta tiene acceso restringido para proteger datos sensibles de las causas.

---

## 2. Ciclo procesal, descargos, antecedentes y resoluciones (implementado)

* **Descargos unificados (T02 y T03) y vencimiento:** Juntamos los descargos tipificados (T02) y extraordinarios (T03) en un mismo selector con persistencia. Cuando vence el plazo de justificación y no quedan instancias abiertas, el expediente pasa solo a revisión para que lo tome el Tribunal.
* **Expedientes referenciados y antecedentes:** Al cargar una solicitud (T01), presentar un descargo o redactar una resolución, se pueden vincular expedientes anteriores desde una tabla y un modal selector. El Tribunal valora los descargos viendo esos antecedentes al lado del expediente.
* **Resolución oficial y "Pendiente de firma":** El modal de resolución es exclusivo del rol TD, no tiene votación nominal y el *Considerando* arranca completamente en blanco. Guarda la reglamentación de respaldo y el texto dispositivo, y deja el expediente en estado "Pendiente de firma" hasta completar las firmas.
* **Apartamiento y suplencia en el TD:** Si un integrante del Tribunal se aparta de una causa con motivo fundado, entra su suplente sin frenar el trámite.
* **Apelación y adecuación de T01:** Ya funciona el circuito de apelación sobre resoluciones y el ajuste del formulario T01 para las causales y revisiones vinculadas.

---

## 3. Reglamentos, reportes, eventos y ranking (implementado)

* **Reglamentos (ABM):** Quedó andando la carga inicial de artículos, el historial de cambios y el control de permisos en el servidor. Todos los socios pueden leer; solo TD, CD y Admin cargan o editan.
* **Reportes e informes (sale de pausa):** Ya está operativa la pantalla con vistas para solicitudes T01, reuniones, subcomisiones, histórico/récords, resumen general y exportación a CSV. También sumamos la clasificación por concepto en los expedientes para alimentar estos informes.
* **Eventos, reuniones y sanciones por inasistencia:** Se implementó la apertura y cierre de reuniones, la toma de asistencia y la generación automática de solicitudes cuando alguien falta sin justificación.
* **Ranking de socios y umbrales:** Se puede ordenar por Saldo o de forma compuesta (Grupo y después alfabético), y abrir el modal con los expedientes de cada socio. Las alertas por puntos quedaron en -10 para el umbral crítico (cruce descendente único) y -7 para el preventivo (configurable y desactivable hasta la Circular 001/2026), sin incluir ningún dato médico ni sensible.

---

## 4. Acuerdos aprobados para el cierre (Sprint 5 consolidado)

Esto es lo que validamos para cerrar el sistema en el Sprint 5:

* **"Número de Socio" en vez de "legajo":** En AVEIT nos manejamos por número de socio. Cambiamos el término en toda la UI, las notificaciones y las resoluciones oficiales. En la base de datos dejamos la columna original para no romper el esquema legacy.
* **Código canónico en Solicitar Puntos:** Apenas se crea una solicitud T01 se tiene que ver su número real (`EXP-NNNN/YYYY`), afuera los hashes temporales tipo `T01-<yyyy>-<hash>`.
* **Exclusión fundada de involucrados (solo TD):** El TD puede excluir a un socio en cualquier estado previo a `Emitido` cargando un motivo obligatorio. Queda tachado en la causa, no suma puntos ni presenta descargo, y se avisa por mail tanto al excluido como a quien abrió el expediente. Si se excluye al último involucrado, la causa pasa a `Emitido` como "Sin efecto / Causa archivada".
* **Enmienda de resoluciones emitidas:** Si hace falta corregir puntajes o fundamentos de una resolución ya emitida, se genera una nueva enlazada (`EXP-NNNN/YYYY-ENM-1`), se hace un contra-asiento en el libro mayor (cero `UPDATE` manuales) y vuelven a firmar los 3 representantes de los grupos activos (4.º, 5.º y 6.º año).
* **Panel de Administración (solo Admin):** Pantalla para configurar parámetros del sistema (umbrales, plazos, mails institucionales y límites de adjuntos) con auditoría, y gestionar altas y bajas del rol TD usando Select2.
* **Tablas, eventos, permisos y manual:** Revisamos todas las tablas para que cada columna muestre un solo dato sin concatenar textos. Vamos a rediseñar la pantalla de creación de eventos junto con el equipo, formalizar la matriz de permisos (RBAC) en backend y frontend, verificar todos los envíos de mail (`EmailOutbox`), optimizar paginación y consultas, y armar el manual de usuario separado por rol.


