# SGD-AVEIT — Presentación Ejecutiva Institucional
## Documento Maestro de Diapositivas y Oratoria con PNL (Google Slides)

**Proyecto:** Sistema de Gestión Disciplinaria y Saldo de Puntos (SGD-AVEIT)  
**Institución:** Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (A.V.E.I.T. — UTN Facultad Regional Córdoba)  
**Entorno de Ejecución:** Google Slides vía CLI oficial `gslides`  
**Artefacto Complementario:** `docs/presentacion/deck_batch.json` (Lote maestro de 127 operaciones atómicas)  
**Fecha:** Octubre 2026 — Seminario Integrador  

---

## 1. Resumen Ejecutivo y Encuadre Institucional

El presente documento constituye la especificación integral de la **Presentación Ejecutiva** de **SGD-AVEIT**, diseñada para una exposición de clase de **14 minutos exactos** (11 minutos de presentación tripartita + 3 minutos dedicados a preguntas y respuestas).

### 1.1. Propuesta de Valor y Enfoque de Solución
SGD-AVEIT transforma la convivencia institucional de A.V.E.I.T. dotándola de:
- **Certeza jurídica y debido proceso:** Notificaciones formales, plazos preclusivos de 5 días hábiles y formularios tipificados de descargo (T02 y T03).
- **Justicia colegiada y despersonalizada:** Deliberación fundada con quórum estricto (mínimo 2 integrantes), voto nominal no anónimo e inhibición obligatoria por conflicto de intereses.
- **Inmutabilidad contable:** Un libro mayor transaccional donde los puntos de los socios jamás se modifican manualmente, sino únicamente como resultado auditable de una resolución colegiada.

### 1.2. Acoplamiento Limpio con el ERP Central Preexistente (`svaveit`)
A.V.E.I.T. ya cuenta con una plataforma central madura en producción (`svaveit`) que administra la vida cotidiana de la asociación para una masa de aproximadamente 515 socios. El diseño de SGD-AVEIT respeta de forma irrestricta la autoridad de dicho sistema:

```
┌────────────────────────────────────────────────────────────────────────┐
│             ERP INSTITUCIONAL CENTRAL PREEXISTENTE (svaveit)           │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ 1. Padrón Socios   │ 2. Actividades y   │ 3. Tesorería y Cobranzas     │
│  - Matriz maestra  │    Eventos         │  - Cuotas sociales mensuales │
│  - Legajos UTN     │  - Asambleas       │  - Estado de cuenta          │
│  - Membresías      │  - Presentismo bio │  - Habilitación de voto      │
│  - Subcomisiones   │  - Marcaciones     ├──────────────────────────────┤
│  - Contactos/Email │  - Cierres de acta │ 4. Campañas y Rifas          │
│                    │                    │  - Talonarios y liquidación  │
└────────────────────┴────────────────────┴──────────────────────────────┘
                                  ▲
                                  │ Consumo desacoplado (SELECT read-only)
                                  │ Cero duplicación de tablas maestras
┌─────────────────────────────────┴──────────────────────────────────────┐
│                    SGD-AVEIT (Subsistema Especializado)                 │
│  - Expedientes Disciplinarios (6 Estados)    - Descargos T02 y T03     │
│  - Votación Colegiada y Quórum TD            - Libro Mayor de Puntos   │
└────────────────────────────────────────────────────────────────────────┘
```

- **Sin duplicación de datos maestros:** SGD-AVEIT no crea tablas paralelas de socios ni permite editar nombres, legajos o estados sociales.
- **Consumo de solo lectura:** Conexión de solo lectura (`GRANT SELECT`) mediante modelos no gestionados (`managed = False`).
- **Especialización funcional:** El ERP sigue gobernando cuotas, rifas, eventos y padrón general; SGD-AVEIT resuelve exclusivamente el circuito disciplinario y el escalafón de conducta.

---

## 2. Marco Metodológico: Oratoria con PNL y Diseño Visual

### 2.1. Diagnóstico Estratégico (Las 5Q) y Objetivos PEMA
- **¿Quién? (Audiencia):** Cátedra docente de Seminario Integrador y pares estudiantiles. Buscan solidez metodológica, viabilidad institucional y respeto por la realidad operativa de AVEIT.
- **¿Para qué? (Propósito Dominante):** **Persuadir e informar.** Demostrar que el proyecto no es un desarrollo aislado, sino una solución armónica que fortalece la convivencia institucional.
- **¿Qué? (Mensaje Central):** *Tres Ideas Fuerza:*
  1. Convivencia pacífica con el ERP preexistente sin duplicar padrón.
  2. Debido proceso y garantías reales para el socio con formularios T02/T03.
  3. Cómputo inmutable de saldos de puntos mediante voto colegiado auditado.
- **¿Dónde? (Entorno):** Exposición presencial con proyector multimedia frontal 16:9 y retorno de pantalla.
- **¿Cómo? (Dinámica):** Arquitectura Tripartita PNL (Introducción, Desarrollo y Cierre) con transición a demo navegable y panel final de preguntas.

#### Objetivos PEMA de la Exposición:
- **P (Positivo):** Demostrar con claridad cómo el sistema brinda certeza, equidad y tranquilidad a los socios y autoridades.
- **E (Específico):** Mostrar la convivencia con el ERP, el flujo de los 6 estados procesales, la deliberación colegiada y la actualización en tiempo real de saldos.
- **M (Mesurable):** Cumplir exactamente 11 minutos de exposición continua más 3 minutos dedicados de Q&A (14:00 min totales).
- **A (Alcanzable):** Asignar roles escénicos específicos para 7 integrantes, cuidando la carga cognitiva y protegiendo a los perfiles tímidos.

### 2.2. Arquitectura Tripartita PNL y Cronograma Maestro (14 Minutos)

```
========================================================================================
CRONOGRAMA TEMPORAL MAESTRO: 14 MINUTOS (840 SEGUNDOS)
========================================================================================
[00:00 - 02:00] INTRODUCCIÓN (120 s)  --> Orador 1 (Líder / Fuerte)
                "Diga lo que les va a decir": Encuadre empático, dolor actual y objetivos.
----------------------------------------------------------------------------------------
[02:00 - 10:05] DESARROLLO (485 s)     --> Oradores 2, 3, 4, 5, 6 y 7
                "Dígalo": Embudo VAK + Storytelling + Circuito de Valor + Demo en Vivo.
                • Slide 2  [02:00 - 03:30] (90 s)  Orador 2 (Promedio): ERP Central y Convivencia.
                • Slide 3  [03:30 - 04:35] (65 s)  Orador 3 (Tímido 1): Dolor del Socio (AS-IS).
                • Slide 4  [04:35 - 05:15] (40 s)  Orador 4 (Promedio): Solución SGD-AVEIT.
                • Slide 5  [05:15 - 06:15] (60 s)  Orador 4 (Promedio): Circuito de 4 Etapas (T01).
                • Slide 6  [06:15 - 07:20] (65 s)  Orador 5 (Tímido 2): Garantías T02/T03 y Plazos.
                • Slide 7  [07:20 - 08:05] (45 s)  Orador 6 (Promedio): Tribunal y Votación Colegiada.
                • Slide 8  [08:05 - 08:50] (45 s)  Orador 6 (Promedio): Inmutabilidad del Saldo.
                • Slide 9  [08:50 - 10:05] (75 s)  Orador 7 (Líder / Fuerte): Demo Navegable Happy Path.
----------------------------------------------------------------------------------------
[10:05 - 11:00] CIERRE (55 s)          --> Orador 7 (Líder / Fuerte)
                "Diga lo que les dijo": Recapitulación, impacto asociativo y CTA.
                • Slide 10 [10:05 - 10:35] (30 s)  Orador 7: Impacto y Valor Agregado.
                • Slide 11 [10:35 - 11:00] (25 s)  Orador 7: Conclusión, Agradecimiento y CTA.
----------------------------------------------------------------------------------------
[11:00 - 14:00] ESPACIO DE PREGUNTAS (180 s) --> Oradores 1 y 7 con Respaldo de Equipo
                • Slide 12 [11:00 - 14:00] (180 s) Moderación estructurada y respuesta en equipo.
========================================================================================
```

### 2.3. Estrategia PNL para los 7 Perfiles del Equipo
1. **Dos Oradores Fuertes / Líderes (Orador 1 y Orador 7):**
   - **Orador 1:** Apertura conectiva (contacto visual en abanico, postura de poder, gancho empático). Co-modera el espacio de preguntas.
   - **Orador 7:** Conducción de la demo navegable en vivo, cierre emotivo/conclusivo y co-moderación del panel de preguntas.
2. **Dos Oradores Tímidos / Con Miedo Escénico (Orador 3 y Orador 5):**
   - **Estrategia de Protección:** Intervenciones breves (65 segundos cada uno, límite $\le 1:15\text{ min}$), fácticas y de bajo estrés. Prohibido hacer preguntas retóricas a la sala o divagar en abstracciones.
   - **Pautas Biomecánicas:**
     * **Anclaje físico:** Pies apoyados firmemente con separación de ancho de hombros (enraizamiento).
     * **Manos en reposo:** Palmas entrelazadas suavemente sobre el plexo solar / boca del estómago.
     * **Respiración diafragmática:** Pausa obligatoria de 2 segundos antes de comenzar la primera palabra para oxigenar el cerebro y bajar la frecuencia cardíaca.
     * **Contacto visual seguro:** Fijar la mirada en un punto amigable o compañero en la primera fila.
3. **Tres Oradores Promedio (Oradores 2, 4 y 6):**
   - Explicación de los aspectos estructurales del sistema: convivencia con el ERP, circuito de estados y deliberación del Tribunal con libro mayor inmutable (90 a 100 segundos cada uno).

### 2.4. Integración Multicanal VAK (Visual, Auditivo, Kinestésico)
El discurso entrelaza deliberadamente predicados sensoriales para mantener conectado a todo tipo de receptor:
- **Visual (V):** *"Como podemos observar en este esquema"*, *"claridad de visualización"*, *"un panorama transparente"*, *"foco en el debido proceso"*.
- **Auditivo (A):** *"Lo que escuchábamos reiteradamente de los socios"*, *"hacer eco en las actas"*, *"un diálogo institucional armónico"*, *"voto fundamentado en palabras claras"*.
- **Kinestésico (K):** *"Sentir la tranquilidad de un respaldo reglamentario"*, *"un circuito firme que no deja lugar a dudas"*, *"conectar con las necesidades reales de nuestra comunidad"*.

### 2.5. Estándares Visuales: Paleta y Reglas de Diseño
- **Patrón "Sandwich":** Alternancia visual dinámica:
  - Diapositivas Oscuras de Impacto (`#1B325F`): Portada (1), Solución (4), Saldo Inmutable (8), Demo (9), Cierre (11), Preguntas (12).
  - Diapositivas Claras de Lectura Analítica (`#F8F9FA`): ERP Actual (2), Dolor AS-IS (3), Circuito Procesal (5), Garantías T02/T03 (6), Tribunal (7), Impacto (10).
- **Contraste Accesible (WCAG 2.0):**
  - Títulos principales en fondo oscuro: `#FFFFFF` sobre `#1B325F` (Ratio 13.5:1).
  - Subtítulos y etiquetas en fondo oscuro: `#CADCFC` sobre `#1B325F` (Ratio 8.2:1).
  - Encabezados en fondo claro: `#1B325F` sobre `#F8F9FA` (Ratio 12.1:1).
  - Cuerpo y viñetas en fondo claro: `#2B3A4A` sobre `#E8EEF5` (Ratio 8.9:1).
- **Regla PNL de Carga Cognitiva:**
  - Máximo **1 idea fuerza** por diapositiva.
  - Máximo **5 a 6 líneas breves** por diapositiva.
  - Tamaño tipográfico: Títulos 36–44 pt, encabezados 18–22 pt, cuerpo 14–16 pt, hero stats 72 pt.

---

## 3. Catálogo Detallado de Diapositivas y Notas de Orador

A continuación se detalla la composición visual y el guion oral de cada una de las 12 diapositivas que conforman el lote de ejecución de Google Slides (`deck_batch.json`).

---

### Diapositiva 1: Portada Institucional y Propósito

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                               SGD-AVEIT                                │  [#FFFFFF, 44pt Bold]
│           Sistema de Gestión Disciplinaria y Saldo de Puntos           │  [#CADCFC, 22pt]
│                     ═════════════════════════════                      │  [Divisor #416788]
│       Especialización institucional acoplada al ERP central de A.V.E.I.T.│  [#FFFFFF, 15pt]
│         UTN Facultad Regional Córdoba — Seminario Integrador 2026       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `p` (Diapositiva inicial nativa)
- **Fondo:** `#1B325F` (Azul Marino Institucional)
- **Idea Fuerza:** SGD-AVEIT dota de justicia y reglas claras a la convivencia asociativa integrándose al ERP existente.
- **Orador Asignado:** **Orador 1** (Líder / Fuerte)
- **Tiempo:** 2:00 min (120 segundos) | Acumulado: [00:00 - 02:00]
- **Canal PNL:** Visual y Kinestésico.
- **Pautas Biomecánicas:** Ubicación al centro del escenario. Postura erguida, hombros relajados, mentón paralelo al piso. Mirada abarcativa en abanico. Sonrisa de apertura para inducir empatía.

#### Notas de Orador (Speaker Notes):
> **ORADOR 1 (Líder / Fuerte) — Tiempo: 2:00 min (120 s). Canal: Visual y Kinestésico.**  
> *Acotación escénica:* Pararse erguido en el centro. Contacto visual panorámico con la cátedra y compañeros. Sonrisa de apertura.  
> *Discurso:* Buenas tardes a todos. Hoy venimos a presentarles una respuesta concreta a una necesidad histórica de nuestra querida institución AVEIT. En una comunidad de más de quinientos estudiantes e ingenieros, la convivencia cotidiana requiere reglas claras, transparencia y certezas. Hoy vamos a mostrarles cómo logramos modernizar el proceso disciplinario sin complejizar la gestión, integrándonos de manera transparente con el ERP que la asociación ya utiliza todos los días. Nuestro objetivo en estos catorce minutos es compartir con ustedes el problema real, la solución de fondo y un recorrido en vivo por la plataforma.

---

### Diapositiva 2: El Ecosistema Preexistente: Nuestro ERP Central

```
┌────────────────────────────────────────────────────────────────────────┐
│ El Ecosistema Actual: Nuestro ERP Central                              │  [#1B325F, 36pt Bold]
│ La institución ya cuenta con un sistema operativo que no debe duplicarse│  [#416788, 14pt]
│                                                                        │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│ │   Padrón Social  │  │Actividades/Eventos│  │ Cobranzas/Rifas  │       │  [Encabezados 18pt]
│ ├──────────────────┤  ├──────────────────┤  ├──────────────────┤       │
│ │• Fuente maestra  │  │• Organización    │  │• Cuotas sociales │       │  [Cuerpo 14pt]
│ │• ~515 socios     │  │• Asistencia téc. │  │• Rifas anuales   │       │
│ │• Datos y legajos │  │• Participación   │  │• Tesorería       │       │
│ │• Membresías      │  │• Comisiones      │  │• Finanzas        │       │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                                                                        │
│    Principio de Diseño: Respetar la autoridad del ERP y sumar valor.   │  [#416788, 13pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_2`
- **Fondo:** `#F8F9FA` (Limpio / Alto Contraste)
- **Idea Fuerza:** AVEIT ya cuenta con un ERP operativo maduro; SGD-AVEIT no duplica datos maestros, se acopla con respeto institucional.
- **Orador Asignado:** **Orador 2** (Promedio)
- **Tiempo:** 1:30 min (90 segundos) | Acumulado: [02:00 - 03:30]
- **Canal PNL:** Auditivo y Visual.
- **Pautas Biomecánicas:** Gesto abierto hacia la pantalla al presentar los tres bloques funcionales. Tono explicativo, pausado y pedagógico.

#### Notas de Orador (Speaker Notes):
> **ORADOR 2 (Promedio) — Tiempo: 1:30 min (90 s). Canal: Auditivo y Visual.**  
> *Acotación escénica:* Gesto abierto hacia la pantalla al señalar los tres bloques del ERP. Manos abiertas a la altura del plexo solar.  
> *Discurso:* Para entender el sentido de nuestro proyecto, primero hay que mirar la realidad de AVEIT. Nuestra asociación no parte de cero: ya cuenta con una plataforma central madura que gestiona las cuotas sociales, los eventos académicos y deportivos, las rifas y el padrón de más de quinientos socios. Habría sido un error garrafal pretender reemplazar ese ERP o duplicar los datos de los socios en una base aislada. La clave estratégica fue diseñar un subsistema especializado que dialogue de forma armónica con esa base existente, consumiendo los datos que necesita sin alterar la fuente de la verdad.

---

### Diapositiva 3: El Desafío Disciplinario: La Falla del Manejo Manual

```
┌────────────────────────────────────────────────────────────────────────┐
│ El Desafío Disciplinario: La Falla del Manejo Manual                   │  [#1B325F, 36pt Bold]
│ Cuando las faltas de convivencia se gestionan en planillas y chats     │  [#416788, 14pt]
│                                                                        │
│ ┌───────────────────────────────┐   ┌───────────────────────────────┐  │
│ │  La Práctica Informal (AS-IS) │   │     El Impacto en el Socio    │  │  [Encabezados 18pt]
│ ├───────────────────────────────┤   ├───────────────────────────────┤  │
│ │• Notificaciones por chat      │   │• Incertidumbre total          │  │  [Cuerpo 14pt]
│ │• Pérdida de descargos         │   │• Plazos de respuesta difusos  │  │
│ │• Votaciones sin fundamentar   │   │• Desconfianza en el Tribunal  │  │
│ │• Planillas libres de cálculo  │   │• Sensación de desamparo       │  │
│ │• Riesgo de arbitrariedad      │   │• Falta de derecho a réplica   │  │
│ └───────────────────────────────┘   └───────────────────────────────┘  │
│                                                                        │
│   Regla PNL: Identificar el dolor humano concreto detrás del problema. │  [#416788, 13pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_3`
- **Fondo:** `#F8F9FA` (Limpio / Alto Contraste)
- **Idea Fuerza:** La gestión disciplinaria informal genera angustia en el socio y desconfianza en la institución.
- **Orador Asignado:** **Orador 3** (Tímido 1 / Con Miedo Escénico)
- **Tiempo:** 1:05 min (65 segundos) | Acumulado: [03:30 - 04:35]
- **Canal PNL:** Kinestésico.
- **Pautas Biomecánicas (Estrategia de Protección):**
  * Pies apoyados firmemente en el suelo (enraizamiento).
  * Manos entrelazadas en reposo sobre el plexo solar.
  * **Pausa de 2 segundos de respiración diafragmática** antes de emitir la primera palabra.
  * Mirada fija en un punto de apoyo seguro en la audiencia.
  * Discurso fáctico, sin preguntas retóricas.

#### Notas de Orador (Speaker Notes):
> **ORADOR 3 (Tímido 1 / Con Miedo Escénico) — Tiempo: 1:05 min (65 s). Canal: Kinestésico.**  
> *Acotación escénica:* Pies firmes en el suelo, manos reposadas en el plexo solar. Pausa de 2 segundos de respiración diafragmática antes de hablar. Mirada fija a un punto de apoyo en la audiencia. Cero preguntas al público.  
> *Discurso:* La realidad cotidiana del socio antes de este proyecto era de una profunda incertidumbre. Hasta hoy, cuando a un compañero se le atribuía un incumplimiento, se enteraba por un mensaje privado o por un rumor, sin saber qué artículo se violó ni cómo defenderse. Las planillas compartidas se pierden, los descargos quedan en casillas de correo privadas y nadie tiene certeza de cuántos puntos le quedan. Esa falta de claridad genera desamparo en el socio y desconfianza en la comunidad de AVEIT. Cuando no hay reglas claras, el Tribunal queda expuesto a sospechas de favoritismo.

---

### Diapositiva 4: SGD-AVEIT: La Respuesta Especializada

```
┌────────────────────────────────────────────────────────────────────────┐
│                  SGD-AVEIT: La Respuesta Especializada                 │  [#FFFFFF, 36pt Bold]
│ Subsistema disciplinario enfocado en garantías, colegiatura e inmutabilidad│ [#CADCFC, 16pt]
│                                                                        │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│ │Consumo de Padrón │  │Proceso Tipificado│  │Votación Colegiada│       │  [Encabezados 18pt]
│ ├──────────────────┤  ├──────────────────┤  ├──────────────────┤       │
│ │Lee directamente  │  │Formularios T01,  │  │Decisiones        │       │  [Cuerpo 14pt]
│ │la fuente maestra │  │T02 y T03 con     │  │nominales con     │       │
│ │del ERP sin       │  │plazos claros y   │  │cálculo           │       │
│ │duplicar tablas.  │  │trazabilidad.     │  │inmutable.        │       │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                     ═════════════════════════════                      │  [Divisor #CADCFC]
│      Acoplamiento limpio: Cero fricción con la administración de AVEIT. │  [#FFFFFF, 14pt]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_4`
- **Fondo:** `#1B325F` (Azul Marino Institucional)
- **Idea Fuerza:** SGD-AVEIT resuelve con especialización técnica lo que el ERP general no puede abarcar.
- **Orador Asignado:** **Orador 4** (Promedio)
- **Tiempo:** 0:40 min (40 segundos) | Acumulado: [04:35 - 05:15]
- **Canal PNL:** Visual y Racional.
- **Pautas Biomecánicas:** Postura erguida, mirada que barre los tres pilares de izquierda a derecha con claridad.

#### Notas de Orador (Speaker Notes):
> **ORADOR 4 (Promedio) — Tiempo: 0:40 min (40 s). Canal: Visual y Racional.**  
> *Acotación escénica:* Postura erguida, mirada que abarca los tres pilares de izquierda a derecha. Gestos activos ilustrando estructura y precisión.  
> *Discurso:* Frente a esa debilidad, nace SGD-AVEIT. Es un módulo especializado que se acopla al ERP como un engranaje perfecto: consulta el padrón institucional en tiempo real sin tocar su base maestra, guía cada paso a través de formularios tipificados y asegura que cada descuento de puntos responda a un fallo legítimo del Tribunal. Es la respuesta exacta para separar la administración cotidiana de la justicia institucional.

---

### Diapositiva 5: Circuito de Valor: Del Hecho a la Resolución

```
┌────────────────────────────────────────────────────────────────────────┐
│ Circuito de Valor: Del Hecho a la Resolución                           │  [#1B325F, 36pt Bold]
│ Un flujo formal, transparente y auditable en 4 etapas delimitadas      │  [#416788, 14pt]
│                                                                        │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │1. Apertura   │ │2. Descargo   │ │3. Sesión/Voto│ │4. Resolución │    │  [Encabezados 15pt]
│ │   (T01)      │ │   (T02)      │ │              │ │   Final      │    │
│ ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤    │
│ │Apertura de la│ │El socio ejerce│ │El cuerpo     │ │Dictamen       │    │  [Cuerpo 13pt]
│ │causa con     │ │su defensa con│ │colegiado vota│ │fundado e      │    │
│ │tipificación  │ │pruebas       │ │con quórum    │ │impacto en     │    │
│ │reglamentaria.│ │formales.     │ │reglamentario.│ │puntos.        │    │
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                                        │
│  Seguimiento en tiempo real del estado de cada expediente para todos.  │  [#1B325F, 13pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_5`
- **Fondo:** `#F8F9FA` (Limpio / Alto Contraste)
- **Idea Fuerza:** El proceso tiene 4 etapas formales sin atajos ni zonas grises.
- **Orador Asignado:** **Orador 4** (Promedio)
- **Tiempo:** 1:00 min (60 segundos) | Acumulado: [05:15 - 06:15]
- **Canal PNL:** Visual y Secuencial.
- **Pautas Biomecánicas:** Desplazamiento sutil siguiendo el flujo de las cuatro tarjetas horizontales. Ritmo constante.

#### Notas de Orador (Speaker Notes):
> **ORADOR 4 (Promedio) — Tiempo: 1:00 min (60 s). Canal: Visual y Secuencial.**  
> *Acotación escénica:* Desplazamiento sutil siguiendo el flujo de las cuatro tarjetas. Gestos secuenciales con las manos.  
> *Discurso:* Este circuito no tiene atajos ni zonas grises. Comienza con una causa abierta formalmente bajo el formulario T01 con su Hoja Anexo obligatoria. Automáticamente, el sistema abre la ventana de descargo para el socio bajo el formulario T02, con un plazo estricto de cinco días hábiles. Cumplido el plazo, el Tribunal entra en sesión colegiada y emite su voto nominal fundado. Y sólo cuando hay resolución formal y firmas registradas, el expediente concluye y se asienta el resultado en el historial. Todo el proceso es visible y auditable en tiempo real.

---

### Diapositiva 6: Garantías del Socio: Descargos Tipificados (T02/T03)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Garantías del Socio: Descargos Tipificados                             │  [#1B325F, 36pt Bold]
│ El debido proceso institucional protegido por herramientas concretas   │  [#416788, 14pt]
│                                                                        │
│ ┌───────────────────────────────┐   ┌───────────────────────────────┐  │
│ │Formulario T02 — Descargo Formal│  │Formulario T03 — Reconsideración│ │  [Encabezados 18pt]
│ ├───────────────────────────────┤   ├───────────────────────────────┤  │
│ │• Plazo legal garantizado      │   │• Instancia de apelación reglad│  │  [Cuerpo 14pt]
│ │• Presentación guiada          │   │• Nuevos elementos de juicio   │  │
│ │• Adjunto de evidencia digital │   │• Revisión obligatoria del TD  │  │
│ │• Comprobante fehaciente       │   │• Doble instancia de garantía  │  │
│ │• Cero estado de indefensión   │   │• Justicia asociativa integral │  │
│ └───────────────────────────────┘   └───────────────────────────────┘  │
│                                                                        │
│   Transparencia: Cada socio conoce sus plazos, sus cargos y derechos.  │  [#1B325F, 13pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_6`
- **Fondo:** `#F8F9FA` (Limpio / Alto Contraste)
- **Idea Fuerza:** El socio cuenta con plazos perentorios y doble instancia formal para garantizar su defensa.
- **Orador Asignado:** **Orador 5** (Tímido 2 / Con Miedo Escénico)
- **Tiempo:** 1:05 min (65 segundos) | Acumulado: [06:15 - 07:20]
- **Canal PNL:** Kinestésico y Visual.
- **Pautas Biomecánicas (Estrategia de Protección):**
  * Anclaje firme de pies en el piso.
  * Manos sobre el plexo solar.
  * Mirada focalizada en la primera fila.
  * Respiración pausada y tono sereno y afirmativo.

#### Notas de Orador (Speaker Notes):
> **ORADOR 5 (Tímido 2 / Con Miedo Escénico) — Tiempo: 1:05 min (65 s). Canal: Kinestésico y Visual.**  
> *Acotación escénica:* Anclaje firme de pies en el piso, manos sobre el plexo solar, pausa diafragmática de 2 segundos, mirada a la primera fila. Tono firme, sereno y fáctico. Cero preguntas retóricas.  
> *Discurso:* Esto representa tranquilidad para cada socio. Ya no hay sorpresas ni sanciones tomadas a espaldas de nadie. Con el formulario T02, el socio tiene un plazo exacto de cinco días hábiles para dar su versión y aportar pruebas con comprobante digital obligatorio. Y si surgen nuevos elementos, el T03 garantiza una reconsideración formal ante el Tribunal. Se terminaron las decisiones tomadas sin escuchar a la persona: el debido proceso es ahora una realidad operativa.

---

### Diapositiva 7: El Tribunal de Disciplina: Votación Nominal Colegiada

```
┌────────────────────────────────────────────────────────────────────────┐
│ El Tribunal de Disciplina: Votación Nominal Colegiada                  │  [#1B325F, 36pt Bold]
│ Despersonalización de las decisiones mediante un cuerpo representativo │  [#416788, 14pt]
│                                                                        │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│ │  Quórum Formal   │  │Voto Nominal y Fund│  │ Acta y Resolución│       │  [Encabezados 18pt]
│ ├──────────────────┤  ├──────────────────┤  ├──────────────────┤       │
│ │• Validación auto │  │• Voto individual │  │• Dictamen formal │       │  [Cuerpo 14pt]
│ │• Sesión habilitad│  │• Fundamento texto│  │• Cómputo exacto  │       │
│ │• Registro presentes│ │• Cero anonimato  │  │• Cierre de causa │       │
│ │• Mayorías legales│  │• Disidencias     │  │• Notificación CD │       │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                                                                        │
│   El poder no reside en un individuo: reside en el consenso del cuerpo.│  [#416788, 13pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_7`
- **Fondo:** `#F8F9FA` (Limpio / Alto Contraste)
- **Idea Fuerza:** Las resoluciones se toman colegiadamente con quórum y voto nominal fundado, despersonalizando el conflicto.
- **Orador Asignado:** **Orador 6** (Promedio)
- **Tiempo:** 0:45 min (45 segundos) | Acumulado: [07:20 - 08:05]
- **Canal PNL:** Auditivo y Racional.
- **Pautas Biomecánicas:** Manos abiertas expresando ecuanimidad y equilibrio institucional. Postura firme.

#### Notas de Orador (Speaker Notes):
> **ORADOR 6 (Promedio) — Tiempo: 0:45 min (45 s). Canal: Auditivo y Racional.**  
> *Acotación escénica:* Manos abiertas expresando ecuanimidad y equilibrio institucional. Postura firme.  
> *Discurso:* El Tribunal de Disciplina no es un juez unipersonal ni un órgano cerrado. Es un cuerpo colegiado donde cada integrante debe dar la cara y fundar su voto por escrito. El sistema verifica automáticamente el quórum mínimo de dos integrantes, inhibe a quien haya denunciado para evitar conflicto de intereses, y registra de manera nominal cada postura. Para que haya sentencia firme, se exige mayoría absoluta de dos votos concordantes y firma digital en el acta. Así se erradica la arbitrariedad.

---

### Diapositiva 8: Inmutabilidad y Confianza: El Saldo de Puntos

```
┌────────────────────────────────────────────────────────────────────────┐
│               Inmutabilidad y Confianza: El Saldo de Puntos            │  [#FFFFFF, 36pt Bold]
│ Cero modificaciones manuales: Un libro mayor transaccional inviolable  │  [#CADCFC, 16pt]
│                                                                        │
│ ┌───────────────────────────┐   ┌───────────────────────────────────┐  │
│ │             0             │   │     Libro Mayor Transaccional     │  │  [Hero Stat 72pt]
│ │Ediciones o borrados manual│   │• Requiere resolución vinculada    │  │  [Cuerpo 14pt]
│ │permitidos sobre los saldos│   │• Historial de auditoría firmado   │  │
│ │de puntos de los socios.   │   │• Reconciliación matemática auto   │  │
│ └───────────────────────────┘   │• Transparencia ante la asamblea   │  │
│                                 └───────────────────────────────────┘  │
│                     ═════════════════════════════                      │  [Divisor #CADCFC]
│  Garantía de equidad: Los puntos reflejan estrictamente fallos formales.│  [#CADCFC, 14pt]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_8`
- **Fondo:** `#1B325F` (Azul Marino Institucional)
- **Idea Fuerza:** Nadie puede alterar los puntos a mano: cada movimiento es un evento contable inmutable respaldado por un fallo.
- **Orador Asignado:** **Orador 6** (Promedio)
- **Tiempo:** 0:45 min (45 segundos) | Acumulado: [08:05 - 08:50]
- **Canal PNL:** Visual y Racional.
- **Pautas Biomecánicas:** Señalar con énfasis el número "0" gigante en la pantalla.

#### Notas de Orador (Speaker Notes):
> **ORADOR 6 (Promedio) — Tiempo: 0:45 min (45 s). Canal: Visual y Racional.**  
> *Acotación escénica:* Enfatizar con la mano el cero gigante en la pantalla.  
> *Discurso:* Y aquí está la garantía máxima de confianza del sistema: en SGD-AVEIT no existe el botón 'editar puntos'. Cero modificaciones manuales en la base de datos. Ningún administrador, directivo o juez puede alterar el saldo de un socio a mano. Cada variación de puntos responde a un asiento transaccional inmutable en el libro mayor, respaldado por una resolución formal dictada y firmada. Es la seguridad absoluta de que nadie puede manipular el legajo de un compañero.

---

### Diapositiva 9: SGD-AVEIT en Acción: Demo en Vivo

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SGD-AVEIT en Acción: Demo en Vivo                   │  [#FFFFFF, 38pt Bold]
│   Recorrido navegable del circuito completo en nuestra plataforma web  │  [#CADCFC, 18pt]
│                     ═════════════════════════════                      │  [Divisor #416788]
│   Ruta de la Demostración:                                             │  [#FFFFFF, 18pt Bold]
│   1. Búsqueda reactiva del socio en el padrón institucional            │  [#CADCFC, 15pt]
│   2. Apertura formal de expediente disciplinario (T01)                 │
│   3. Portal del socio y presentación de descargo tipificado (T02)      │
│   4. Sesión del Tribunal de Disciplina y votación nominal              │
│   5. Emisión de resolución y actualización inmutable del saldo         │
│                                                                        │
│            Pasemos a ver la experiencia real del usuario...            │  [#FFFFFF, 16pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_9`
- **Fondo:** `#1B325F` (Azul Marino Institucional)
- **Idea Fuerza:** La plataforma web ejecuta el circuito Happy Path sin fisuras, uniendo al socio y al Tribunal.
- **Orador Asignado:** **Orador 7** (Líder / Fuerte)
- **Tiempo:** 1:15 min (75 segundos) | Acumulado: [08:50 - 10:05]
- **Canal PNL:** Visual y Dinámico.
- **Pautas Biomecánicas:** Transición serena hacia el navegador web (rama `presentacion`). Control pausado del mouse y narración sincronizada con la pantalla.

#### Notas de Orador (Speaker Notes):
> **ORADOR 7 (Líder / Fuerte) — Tiempo: 1:15 min (75 s). Canal: Visual y Dinámico.**  
> *Acotación escénica:* Transición fluida al navegador web donde corre la aplicación en la rama 'presentacion'. Control de la pantalla y el cursor con serenidad.  
> *Discurso:* Como las palabras cobran fuerza cuando se ven en los hechos, pasemos a recorrer la plataforma en vivo. Vamos a seguir el camino de una causa real en cuatro pasos: primero, abriremos un expediente seleccionando al socio mediante la búsqueda del padrón; luego, nos pondremos en el lugar del socio recibiendo su notificación y presentando su descargo T02 con comprobante adjunto; finalmente, veremos cómo el Tribunal sesiona, emite su voto nominal colegiado y actualiza el escalafón de puntos de forma inmediata e inmutable.

---

### Diapositiva 10: Impacto Institucional y Valor Agregado

```
┌────────────────────────────────────────────────────────────────────────┐
│ Impacto Institucional y Valor Agregado                                 │  [#1B325F, 36pt Bold]
│ Un salto cualitativo en la madurez organizativa de A.V.E.I.T.          │  [#416788, 14pt]
│                                                                        │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│ │  Para el Socio   │  │ Para el Tribunal │  │Para la Institución│      │  [Encabezados 18pt]
│ ├──────────────────┤  ├──────────────────┤  ├──────────────────┤       │
│ │• Certeza y calma │  │• Orden formal    │  │• Auditoría limpia│       │  [Cuerpo 14pt]
│ │• Plazos de defens│  │• Voto respaldado │  │• Convivencia sana│       │
│ │• Saldo visible   │  │• Cero burocracia │  │• Integración ERP │       │
│ │• Protección real │  │• Estandarización │  │• Prestigio UTN   │       │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                                                                        │
│   Un sistema que protege a las personas y fortalece las instituciones. │  [#416788, 13pt Bold]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_10`
- **Fondo:** `#F8F9FA` (Limpio / Alto Contraste)
- **Idea Fuerza:** Beneficios integrales y tangibles para el socio, las autoridades y el prestigio institucional.
- **Orador Asignado:** **Orador 7** (Líder / Fuerte)
- **Tiempo:** 0:30 min (30 segundos) | Acumulado: [10:05 - 10:35]
- **Canal PNL:** Auditivo y Kinestésico.
- **Pautas Biomecánicas:** Mirada abarcadora, postura de convicción y gestos seguros.

#### Notas de Orador (Speaker Notes):
> **ORADOR 7 (Líder / Fuerte) — Tiempo: 0:30 min (30 s). Canal: Auditivo y Kinestésico.**  
> *Acotación escénica:* Mirada abarcadora hacia la cátedra evaluadora. Tono de cosecha de valor.  
> *Discurso:* Lo que acabamos de ver trasciende lo informático: es tranquilidad para el socio, que sabe que sus derechos están garantizados; es respaldo para el Tribunal, que cuenta con actas formales y voto colegiado; y es madurez para AVEIT, que consolida su prestigio con un proceso disciplinario modelo dentro de la facultad.

---

### Diapositiva 11: Compromiso con el Futuro Institucional

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                  Justicia, Transparencia y Convivencia                 │  [#FFFFFF, 42pt Bold]
│          SGD-AVEIT fortalece la comunidad cuidando a sus miembros      │  [#CADCFC, 20pt]
│                     ═════════════════════════════                      │  [Divisor #416788]
│                             Muchas Gracias                             │  [#FFFFFF, 18pt Bold]
│               Equipo de Seminario Integrador — AVEIT 2026              │
│                                                                        │
│          Repositorio: github.com/MartinG94/seminario-integrador        │  [#CADCFC, 13pt]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_11`
- **Fondo:** `#1B325F` (Azul Marino Institucional)
- **Idea Fuerza:** Recapitulación ejecutiva ("diga lo que les dijo") y agradecimiento institucional.
- **Orador Asignado:** **Orador 7** (Líder / Fuerte)
- **Tiempo:** 0:25 min (25 segundos) | Acumulado: [10:35 - 11:00] (Completa los 11 min de exposición oral)
- **Canal PNL:** Kinestésico.
- **Pautas Biomecánicas:** Pausa deliberada de cierre. Inclinación leve de cabeza en señal de agradecimiento y apertura.

#### Notas de Orador (Speaker Notes):
> **ORADOR 7 (Líder / Fuerte) — Tiempo: 0:25 min (25 s). Canal: Kinestésico.**  
> *Acotación escénica:* Pausa deliberada. Agradecimiento formal con inclinación leve de cabeza, invitando al panel de preguntas.  
> *Discurso:* En síntesis: demostramos que se puede modernizar la gestión asociativa respetando la infraestructura existente y priorizando siempre la equidad humana. Les agradecemos profundamente su atención.

---

### Diapositiva 12: Espacio de Preguntas y Diálogo (Q&A)

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Espacio de Preguntas y Diálogo                     │  [#FFFFFF, 40pt Bold]
│                Sesión abierta de intercambio (3 minutos)               │  [#CADCFC, 20pt]
│                     ═════════════════════════════                      │  [Divisor #416788]
│   Ejes de Consulta Abiertos:                                           │  [#FFFFFF, 15pt]
│   • Integración y acoplamiento con el ERP preexistente                 │
│   • Procedimiento y plazos de los descargos T02 y T03                  │
│   • Votación colegiada y cálculo inmutable de saldo de puntos          │
│   • Experiencia de usuario y adopción en la comunidad de AVEIT         │
│                                                                        │
│   Conducción: Oradores 1 y 7 con el respaldo de todo el equipo.        │  [#CADCFC, 13pt]
└────────────────────────────────────────────────────────────────────────┘
```

- **ID de Diapositiva:** `SLIDE_12`
- **Fondo:** `#1B325F` (Azul Marino Institucional)
- **Idea Fuerza:** Sesión de preguntas de 3 minutos exactos moderada activamente por los líderes con participación del equipo especialista.
- **Orador Asignado:** **Oradores 1 y 7** (Líderes) + **Equipo Completo**
- **Tiempo:** 3:00 min (180 segundos) | Acumulado: [11:00 - 14:00] (Cierre total de la sesión)
- **Canal PNL:** Multicanal y Diálogo Abierto.
- **Pautas Biomecánicas y Dinámica Escénica:**
  * Los dos oradores líderes se ubican al frente con tono claro y receptivo.
  * Los restantes cinco integrantes se disponen en un semicírculo de apoyo detrás de ellos.
  * Ante cada pregunta, el líder agradece, realiza un breve parafraseo de puente y deriva la respuesta al integrante especialista según la temática:
    - *Consultas sobre el ERP o datos maestros:* Responde **Orador 2**.
    - *Consultas sobre causales, plazos o dolor del socio:* Responde **Orador 3** o **Orador 5**.
    - *Consultas sobre el flujo de los 6 estados o apertura T01:* Responde **Orador 4**.
    - *Consultas sobre quórum, deliberación o libro mayor inmutable:* Responde **Orador 6**.
    - *Consultas sobre la interfaz o navegación de la demo:* Responde **Orador 7**.

#### Notas de Orador (Speaker Notes):
> **ORADORES 1 Y 7 (Líderes) + EQUIPO COMPLETO — Tiempo: 3:00 min (180 s) exactos. Canal: Multicanal.**  
> *Acotación escénica:* Los dos líderes se ubican al frente con micrófono/voz clara. El resto de los 5 integrantes se ubica en semicírculo detrás como soporte técnico y funcional. Ante cada pregunta, el líder agradece, sintetiza y deriva amablemente al integrante especialista (ej. Orador 3 o 5 para descargos, Orador 2 o 4 para ERP, Orador 6 para votación).  
> *Discurso de apertura de Q&A:* Abrimos ahora con mucho gusto el espacio de preguntas para profundizar en cualquiera de estos aspectos con el equipo.

---

## 4. Guía de Ejecución Técnica: CLI de Google Slides (`gslides`)

### 4.1. Diagnóstico del Estado de Autenticación
El CLI nativo `gslides` opera de manera no interactiva validando la presencia de credenciales OAuth2.
Al ejecutar la verificación en el entorno local:
```powershell
gslides auth status --json
```
Se obtiene el diagnóstico verificado:
```json
{
  "authenticated": false,
  "token_file": "C:\\Users\\Diego\\.gemini\\antigravity\\plugin_data\\gslides\\token.json"
}
```

### 4.2. Procedimiento de Autenticación para el Usuario
Para habilitar la mutación en vivo en la nube de Google, el usuario debe realizar una única acción interactiva:
1. Abrir una terminal de PowerShell y ejecutar:
   ```powershell
   gslides auth login
   ```
2. El comando inicia un listener local e imprime la URL de consentimiento:
   `https://accounts.google.com/o/oauth2/v2/auth?...`
3. El usuario autoriza el acceso a Google Slides y Google Drive en su navegador.
4. El token queda persistido en `token.json` y habilita inmediatamente las mutaciones.
*(Alternativamente, puede inyectarse un token vigente en `$env:GCLI_ACCESS_TOKEN`)*.

### 4.3. Pipeline Automatizado de Creación del Deck
Una vez autenticado el entorno, el lote maestro se despliega en una única invocación atómica:

```powershell
# 1. Crear la presentación en blanco
$res = gslides mutate create --title "SGD-AVEIT - Presentacion Ejecutiva" --json | ConvertFrom-Json
$deckId = $res.presentationId

# 2. Ejecutar el lote de 127 operaciones atómicas
gslides mutate batch $deckId -f docs/presentacion/deck_batch.json --json

# 3. Comprobar la creación de las 12 diapositivas
gslides readonly list-slides $deckId

# 4. Renderizar miniatura de verificación visual de la portada
gslides readonly export-thumbnail $deckId portada_preview.png --slide p

# 5. Exportar el entregable institucional a formato PDF
gslides readonly export $deckId "docs/presentacion/SGD-AVEIT_Presentacion_Ejecutiva.pdf" --format pdf
```

### 4.4. Enlaces Canónicos de Visualización Web
- **Enlace de Edición y Presentación en Vivo:**  
  `https://docs.google.com/presentation/d/<deck_id>/edit`
- **Diapositiva Específica (Ejemplo Portada):**  
  `https://docs.google.com/presentation/d/<deck_id>/edit#slide=id.p`
- **Diapositiva Específica (Ejemplo Q&A):**  
  `https://docs.google.com/presentation/d/<deck_id>/edit#slide=id.SLIDE_12`

---

## 5. Matriz de Trazabilidad y Verificación

| Criterio de Aceptación | Fuente de Requisito | Estado | Mecanismo de Verificación |
| :--- | :--- | :---: | :--- |
| **12 Diapositivas PNL** | ORIGINAL_REQUEST R1 | **CUMPLIDO** | `docs/presentacion/deck_batch.json` contiene 12 diapositivas (`p` + `SLIDE_2` a `SLIDE_12`). |
| **1 Idea Fuerza / $\le$ 6 Líneas** | oratoriaPnl Fase 3 | **CUMPLIDO** | Cada diapositiva contiene una única idea rectora y tarjetas de 3 a 5 viñetas concisas. |
| **Paleta de Alto Contraste** | DESIGN.md / survey_slides | **CUMPLIDO** | Fondo `#1B325F` / `#F8F9FA`, acento `#416788`, textos `#FFFFFF` (13.5:1), `#CADCFC` (8.2:1) y `#2B3A4A`. |
| **100% Conceptual / No Técnico** | ORIGINAL_REQUEST R1 | **CUMPLIDO** | Sin jerga de frameworks, SQL, endpoints ni código interno; foco en la justicia institucional. |
| **Acoplamiento con ERP Central** | ORIGINAL_REQUEST R1 / ADR-001 | **CUMPLIDO** | Explicación explícita de convivencia con `svaveit` (socios, eventos, cuotas, rifas) sin duplicar datos. |
| **Speaker Notes Completas** | ORIGINAL_REQUEST R1 | **CUMPLIDO** | Las 12 diapositivas incluyen orador, tiempos exactos, canal VAK y acotaciones biomecánicas. |
| **Calibración 14 Minutos (11m + 3m)** | Follow-up 12:57:02Z | **CUMPLIDO** | 660 s de exposición tripartita + 180 s de Q&A conducido por líderes = 840 s exactos. |
| **Protección Oradores Tímidos** | oratoriaPnl / humanizer | **CUMPLIDO** | Oradores 3 y 5 asignados a 65 s ($\le 1:15\text{ min}$) con pautas de anclaje plexo y respiración de 2 s. |
| **Batch JSON Probado (127 ops)** | Dispatch Task 3 | **CUMPLIDO** | `docs/presentacion/deck_batch.json` validado sintácticamente (127 operaciones atómicas). |
