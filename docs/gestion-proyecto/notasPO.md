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

---

## Pantalla: Reportes

Están en pausa. Tengo que hablar con los usuarios del TD para definir qué necesitan ver. No arrancar nada acá todavía.

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
