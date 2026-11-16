# Spec 011 — Libro Mayor Inmutable, Portal "Mis Expedientes" y Publicación Oficial Protegida (MACRO-02 / SCRUM-59)

> **Origen:** Notas del PO del 27/09/2026 (Mis Expedientes; Felicitaciones y Llamados de atención), 07/10/2026 (sección 6, regla 3:1) y 13/11/2026 (secciones 1 y 4), `PLAN_SPRINT_5_CONSOLIDADO.md` (MACRO-02, Paquete 3) y Constitución (principios 2 y 6).
> **Subtareas Jira:** `SCRUM-104` (S5-02.1), `SCRUM-105` (S5-02.2), `SCRUM-106` (S5-02.3).

## 1. Historia de usuario

**Como** socio de AVEIT, **quiero** que los puntos de cada resolución emitida se registren solos y de forma inalterable, ver solamente mis expedientes con mi saldo real y poder leer la resolución oficial de mis causas, **para** confiar en que mi saldo refleja lo resuelto por el Tribunal sin exponer datos de otros socios ni datos de salud.

## 2. Alcance

| Subtarea | Entregable |
| --- | --- |
| S5-02.1 | Al emitirse una resolución, el sistema genera los asientos del libro mayor por socio, aplica la regla 3:1 y no modifica ni borra asientos existentes. |
| S5-02.2 | "Mis Expedientes" muestra solo las causas del socio autenticado, su saldo del libro mayor, sus llamados y felicitaciones pendientes y los puntos aplicados en cada causa. |
| S5-02.3 | Publicación de la resolución emitida para el imputado y las autoridades, sin adjuntos, sin descargos y con los datos de salud censurados, descargable en PDF. |

## 3. Requisitos (EARS)

### S5-02.1 — Libro mayor transaccional inmutable

- **RF-01 — Asiento automático.** CUANDO una resolución pasa a `Emitida`, EL SISTEMA registra en la misma transacción un asiento por cada socio involucrado con el impacto individualizado que le corresponde.
- **RF-02 — Impacto individual.** EL SISTEMA determina el impacto de cada socio con este orden: (1) última valoración del Tribunal sobre su descargo T02 o T03 (puntaje final ratificado; si no lo hay, causal aceptada = 0 y rechazada = puntaje solicitado); (2) si no presentó descargo, el puntaje solicitado o la medida especial solicitada (llamado de atención o felicitación).
- **RF-03 — Movimiento directo.** CUANDO el impacto es un puntaje numérico distinto de cero, EL SISTEMA inserta un movimiento en el libro mayor legado (`tribunal_puntajeaplicado`) vinculado al expediente y al socio.
- **RF-04 — Regla 3:1.** CUANDO el impacto es un llamado de atención o una felicitación, EL SISTEMA no inserta puntos fraccionarios: suma uno al contador del socio y, al llegar a tres, inserta un único movimiento de -1,00 (llamados) o +1,00 (felicitaciones) y descuenta tres del contador.
- **RF-05 — Sin impacto.** CUANDO el impacto es cero, EL SISTEMA deja constancia de la absolución en la auditoría sin insertar puntos.
- **RF-06 — Auditoría inmutable.** Cada asiento registra resolución, expediente, socio, tipo, puntos, contador resultante, autor de la emisión, fecha y un hash SHA-256 encadenado con el asiento anterior del mismo socio. Los asientos no se modifican ni se eliminan, tampoco con operaciones masivas.
- **RF-07 — Idempotencia.** SI la resolución ya tiene asientos, EL SISTEMA no los duplica.
- **RF-08 — Saldo único.** EL SISTEMA calcula el saldo de un socio como la suma de sus movimientos en el libro mayor, el mismo criterio que usa el Ranking.

### S5-02.2 — Portal "Mis Expedientes" con aislamiento por socio

- **RF-09 — Solo mis causas.** EL SISTEMA devuelve en "Mis Expedientes" únicamente las causas donde el socio autenticado es imputado (titular o coimputado), cualquiera sea su rol. La interfaz nunca reemplaza esa respuesta por otra lista local.
- **RF-10 — Solo mis datos.** En "Mis Expedientes", EL SISTEMA expone únicamente el descargo, los comprobantes y el impacto del propio socio, aunque el socio integre TD, CD o Admin.
- **RF-11 — Resolución no emitida.** MIENTRAS la resolución no esté emitida, EL SISTEMA no expone su texto, firmas ni hash al imputado.
- **RF-12 — Saldo del socio.** CUANDO el socio abre "Mis Expedientes", EL SISTEMA devuelve su saldo del libro mayor, sus llamados de atención y felicitaciones pendientes (0 a 2) y sus movimientos registrados por resoluciones.
- **RF-13 — Puntos de la causa.** CUANDO la causa está emitida, la columna `Puntos` muestra los puntos aplicados al socio por esa resolución o la medida aplicada (llamado de atención o felicitación).
- **RF-14 — Acceso por enlace.** SI un socio intenta abrir la causa de otro socio, EL SISTEMA responde `403` y deja constancia en la pista de seguridad.

### S5-02.3 — Publicación oficial protegida

- **RF-15 — Publicación.** CUANDO la resolución está emitida, EL SISTEMA publica para el imputado y para TD, CD y Admin: identificación, expediente, título, fecha de emisión, Vistos, Considerandos, artículos resolutivos, reglamentos de respaldo, firmantes (número de socio, nombre y grupo) y hash de integridad con su verificación.
- **RF-16 — Impactos visibles.** El imputado ve solo su impacto; TD, CD y Admin ven el de todos los involucrados.
- **RF-17 — Censura de salud.** EL SISTEMA reemplaza por "[Dato de salud reservado]" toda oración de la publicación que contenga datos de salud, para cualquier lector.
- **RF-18 — Sin adjuntos privados.** La publicación nunca incluye descargos, causales, comprobantes, rutas de archivos ni identificadores internos de usuarios.
- **RF-19 — Sin publicación previa.** SI la resolución no está emitida o el lector no está autorizado, EL SISTEMA responde `404` o `403` respectivamente.
- **RF-20 — PDF.** CUANDO el lector autorizado lo pide, EL SISTEMA entrega el PDF de la publicación con el mismo contenido censurado.
- **RF-21 — Auditoría de consulta.** CADA consulta o descarga de la publicación queda registrada en la auditoría de consultas del expediente.

## 4. Fuera de alcance

- Alertas automáticas por cruce de umbrales (SCRUM-62).
- Enmiendas y contra-asientos de resoluciones emitidas (MACRO-01, `SCRUM-103`).
- Repositorio público de jurisprudencia (MACRO-08, `SCRUM-125`).
- Recalcular la caché legada `tribunal_puntajegeneral`: el saldo vigente es la suma del libro mayor.

## 5. Decisiones a confirmar con el PO

1. Al llegar a tres llamados o felicitaciones por resolución, el punto completo se acredita en la misma resolución que completa el tercero, sin abrir un expediente adicional (el circuito de apercibimientos por inasistencia no cambia).
2. La publicación se censura siempre, aun para el propio imputado: el texto completo sigue disponible para el Tribunal en su pantalla de resolución.
3. Los asientos anteriores a esta versión (migración legada) se siguen sumando al saldo, pero no figuran como movimientos con resolución.
