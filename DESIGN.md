---
name: "AVEIT Design System 2026"
version: "1.0.0"
description: "Sistema de diseño canónico e institucional de AVEIT (Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos - UTN Facultad Regional Córdoba). Unifica el Manual de Marca Oficial AVEIT 2026 y los componentes de la plataforma web en producción bajo la especificación DESIGN.md de Google Labs y WCAG 2.2 AA/AAA."
colors:
  primary: "#151846"
  accent: "#6E9DDC"
  tint: "#B3D3E4"
  surface: "#F2EEE9"
  surface-card: "#FFFFFF"
  surface-elevated: "#FFFFFF"
  brand-black: "#000000"
  text-primary: "#151846"
  text-secondary: "#334155"
  text-inverse: "#FFFFFF"
  border-main: "#D1D5DB"
  border-focus: "#6E9DDC"
  success: "#15803D"
  warning: "#92400E"
  danger: "#B91C1C"
  info: "#0369A1"
typography:
  display:
    fontFamily: "Archivo Black, sans-serif"
    fontSize: "40px"
    fontWeight: "900"
    lineHeight: "1.1"
  h1:
    fontFamily: "Garet, Montserrat, sans-serif"
    fontSize: "32px"
    fontWeight: "700"
    lineHeight: "1.2"
  h2:
    fontFamily: "Montserrat, sans-serif"
    fontSize: "24px"
    fontWeight: "600"
    lineHeight: "1.3"
  h3:
    fontFamily: "Montserrat, sans-serif"
    fontSize: "20px"
    fontWeight: "600"
    lineHeight: "1.4"
  subtitle:
    fontFamily: "Arimo, Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: "500"
    lineHeight: "1.5"
  body:
    fontFamily: "Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: "400"
    lineHeight: "1.6"
  caption:
    fontFamily: "Arimo, Roboto, sans-serif"
    fontSize: "12px"
    fontWeight: "400"
    lineHeight: "1.4"
  button:
    fontFamily: "Montserrat, sans-serif"
    fontSize: "14px"
    fontWeight: "600"
    lineHeight: "1.2"
rounded:
  none: "0px"
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  "2xl": "48px"
  "3xl": "64px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
  button-secondary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
  button-round:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "12px 28px"
  button-outline:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
  card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "24px"
  card-institutional:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "24px"
  page-container:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
  navbar:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.primary}"
    padding: "16px 24px"
  badge-accent:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-info:
    backgroundColor: "{colors.info}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  input-field:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
  footer:
    backgroundColor: "{colors.brand-black}"
    textColor: "{colors.surface}"
    padding: "32px 24px"
  metadata-label:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    padding: "2px 0px"
  dropdown-menu:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "8px 0px"
  focus-indicator:
    backgroundColor: "{colors.border-focus}"
    textColor: "{colors.text-primary}"
    padding: "2px"
  border-container:
    backgroundColor: "{colors.border-main}"
    textColor: "{colors.text-primary}"
    padding: "1px"
---

# AVEIT Design System 2026 (`DESIGN.md`)

## Overview

Este documento establece la **fuente de verdad canónica de diseño y tokens** para todos los productos digitales de la **Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (AVEIT)** de la Universidad Tecnológica Nacional - Facultad Regional Córdoba (UTN FRC).

El sistema formaliza la evolución de identidad definida en el **Manual de Marca Oficial AVEIT 2026** y su integración operativa con las plataformas de software de la institución (incluyendo el portal web institucional en producción en [`https://aveit.frc.utn.edu.ar/`](https://aveit.frc.utn.edu.ar/) y los sistemas de gestión académica y disciplinaria como el **SGD-AVEIT**).

### Principios Fundamentales
1. **Identidad Ingenieril y Confiable:** Reflejar el rigor académico, tecnológico y estatutario de AVEIT mediante contrastes cromáticos sólidos, tipografía estructurada y layout con ritmo predecible.
2. **Accesibilidad Universal (WCAG 2.2 AA / AAA):** Garantizar legibilidad inmediata en cualquier condición de iluminación, evitando combinaciones de bajo contraste y erradicando el cansancio ocular.
3. **Ergonomía Operativa:** Diseñado tanto para lectura prolongada de reglamentos y resoluciones disciplinarias como para operaciones rápidas en dispositivos móviles y de escritorio.
4. **Diseño Anti-Slop (Taste Design):** Cero uso de componentes genéricos de IA, cero negro absoluto en tipografía continua, cero emojis en elementos de control y un único acento cromático interactivo principal.

---

## Colors

La paleta se estructura a partir de los 5 colores fundacionales normados en el **Manual de Marca 2026**, complementados con colores semánticos de estado para aplicaciones de gestión:

### 1. Colores de Identidad Institucional
- **`primary` (`#151846` - Color 1 del Manual):**
  - Azul noche profundo / Navy institucional UTN AVEIT.
  - **Uso:** Encabezados de página, barra de navegación institucional, botones de acción primaria y texto predominante.
  - **Accesibilidad:** Brinda un contraste sobresaliente de **14.2:1** sobre la superficie Beige (`#F2EEE9`) y **16.6:1** sobre fondo blanco (`#FFFFFF`), superando holgadamente el estándar WCAG AAA.
- **`accent` (`#6E9DDC` - Color 2 del Manual):**
  - Azul celeste tecnológico / Cyan suave.
  - **Uso:** Acento interactivo principal, estados activos de menú, botones secundarios, anillos de foco y enlaces contextuales.
  - **Accesibilidad:** Con texto `{colors.primary}`, alcanza un ratio de contraste de **6.0:1** (cumple WCAG AA).
- **`tint` (`#B3D3E4` - Color 3 del Manual):**
  - Ice blue pastel institucional.
  - **Uso:** Fondos atenuados de badges, indicadores de categoría institucional, resaltado suave de filas y micro-accesorios visuales.
  - **Accesibilidad:** Diseñado para utilizarse exclusivamente con texto `{colors.primary}` (ratio **10.6:1** WCAG AAA).
- **`surface` (`#F2EEE9` - Beige del Manual):**
  - Arena cálido / Off-white institucional.
  - **Uso:** Fondo general de pantalla (`page-container`) y superficies institucionales, reduciendo el deslumbramiento en jornadas extensas de uso.
- **`brand-black` (`#000000` - Negro del Manual):**
  - Negro absoluto oficial de la marca.
  - **Uso:** Pie de página (`footer`), fondos de alto contraste gráfico en material publicitario y elementos que requieran solemnidad estricta.

### 2. Superficies y Neutros de Interfaz
- **`surface-card` (`#FFFFFF`):** Blanco puro para tarjetas modulares, formularios, modales y tablas de datos.
- **`surface-elevated` (`#FFFFFF`):** Menús desplegables, popovers y paneles flotantes con sombra de elevación.
- **`text-primary` (`#151846`):** Color semántico del texto principal. Sustituye al negro puro en textos continuos.
- **`text-secondary` (`#334155`):** Gris pizarra azulado para metadatos, descripciones secundarias y etiquetas de apoyo (ratio > 5.8:1 sobre blanco y beige).
- **`text-inverse` (`#FFFFFF`):** Texto blanco para superficies oscuras (`primary`, `brand-black`, botones principales).
- **`border-main` (`#D1D5DB`):** Borde sutil de 1px para tarjetas, contenedores e inputs.
- **`border-focus` (`#6E9DDC`):** Borde resaltado para accesibilidad al navegar por teclado (`:focus-visible`).

### 3. Semántica de Estados y Alertas Estatutarias
- **`success` (`#15803D`):** Estado de cumplimiento estatutario, trámite aprobado o socio regular habilitado (ratio 4.52:1 sobre blanco).
- **`warning` (`#92400E`):** Estado de advertencia disciplinaria, apercibimiento o acumulación de faltas (ratio 5.95:1 sobre blanco).
- **`danger` (`#B91C1C`):** Alerta crítica, sanción grave, suspensión o revocación de beneficios (ratio 5.88:1 sobre blanco).
- **`info` (`#0369A1`):** Avisos de convocatoria institucional, asambleas o notificaciones de secretaría (ratio 4.90:1 sobre blanco).

---

## Typography

El sistema tipográfico combina la tradición geométrica de la web institucional (`Montserrat`) con las fuentes normadas en el Manual 2026 (`Archivo Black`, `Garet`, `Arimo`, `Roboto`):

| Escala | Familia Tipográfica | Tamaño | Peso | Line-Height | Rol Semántico en la Aplicación |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`display`** | `Archivo Black, sans-serif` | 40px | 900 | 1.1 | Portadas hero, grandes títulos institucionales y alertas de máximo impacto. |
| **`h1`** | `Garet, Montserrat, sans-serif` | 32px | 700 | 1.2 | Encabezados principales de pantalla y nombres de módulos o secciones clave. |
| **`h2`** | `Montserrat, sans-serif` | 24px | 600 | 1.3 | Títulos de tarjetas principales, bloques de contenido y modales. |
| **`h3`** | `Montserrat, sans-serif` | 20px | 600 | 1.4 | Subsecciones internas, títulos de tablas y grupos de campos de formulario. |
| **`subtitle`** | `Arimo, Roboto, sans-serif` | 16px | 500 | 1.5 | Subtítulos explicativos, encabezados de columnas y resúmenes ejecutivos. |
| **`body`** | `Roboto, sans-serif` | 16px | 400 | 1.6 | Cuerpo de texto continuo, resoluciones, reglamentos, inputs y celdas de datos. |
| **`caption`** | `Arimo, Roboto, sans-serif` | 12px | 400 | 1.4 | Metadatos, marcas temporales, notas al pie e indicadores de versión. |
| **`button`** | `Montserrat, sans-serif` | 14px | 600 | 1.2 | Botones, acciones primarias/secundarias y elementos de menú de navegación. |

---

## Layout

1. **Ritmo de Espaciado Modular (Base 8px):**
   - Micro-espaciado (`xs: 4px`): Ajuste milimétrico interno entre iconos y texto.
   - Espaciado compacto (`sm: 8px`): Gaps entre botones en grupo y padding vertical de botones/chips.
   - Espaciado estándar (`md: 16px`): Márgenes entre campos de formulario y padding de celdas.
   - Espaciado generoso (`lg: 24px`): Padding interno de tarjetas (`card`) y diálogos.
   - Separación estructural (`xl: 32px`, `2xl: 48px`, `3xl: 64px`): Espaciado entre secciones de página y contenedores de navegación.
2. **Estructura de Contenedores:**
   - Contenedor desktop estándar con ancho máximo de `1200px` centrado con márgenes simétricos.
   - Layout de dos columnas asimétrico (ej. panel de control 70% / panel de contexto estatutario 30%).
   - En pantallas móviles (<768px), todas las grillas colapsan ordenadamente a 1 columna vertical sin desbordamiento horizontal.

---

## Elevation & Depth

La tridimensionalidad se resuelve mediante **profundidad tonal nítida** combinada con sombras sutiles heredadas de la estética Paper Kit:

- **Plano Base (Nivel 0):** Superficie beige `{colors.surface}` (`#F2EEE9`).
- **Plano Contenedor (Nivel 1):** Tarjetas blancas `{colors.surface-card}` (`#FFFFFF`) con borde de 1px `{colors.border-main}` y sombra `0 2px 4px rgba(21, 24, 70, 0.05)`.
- **Plano Elevado (Nivel 2):** Modales, popovers y selectores flotantes con sombra de elevación `0 10px 25px -5px rgba(21, 24, 70, 0.12), 0 8px 10px -6px rgba(21, 24, 70, 0.08)`.
- **Barra de Navegación (`navbar`):** Fondo blanco o translúcido con desenfoque de fondo (`backdrop-filter: blur(8px)`) y borde inferior de 1px.

---

## Shapes

La geometría de los componentes equilibra precisión técnica con ergonomía táctil:

- **`none` (`0px`):** Separadores horizontales y bordes de unión estricta.
- **`sm` (`4px`):** Botones rectangulares estándar, cajas de texto de formularios (`inputs`) y controles de selección (herencia funcional de Bootstrap y Paper Kit).
- **`md` (`8px`):** Menús contextuales, cuadros de diálogo secundarios y tooltips.
- **`lg` (`12px`):** Tarjetas contenedoras principales (`card`), paneles de módulo y contenedores institucionales.
- **`full` (`9999px`):** Badges de estado, píldoras informativas y botones circulares de acción (`button-round`).

---

## Components

### 1. Botones de Acción
- **`button-primary`:** Fondo `{colors.primary}`, texto `{colors.text-inverse}`, radio `{rounded.sm}` (4px), padding `12px 24px`. Para la acción principal e inequívoca de cada vista.
- **`button-secondary`:** Fondo `{colors.accent}`, texto `{colors.primary}`, radio `{rounded.sm}` (4px), padding `12px 24px`. Para acciones de soporte y navegación alternativa.
- **`button-round`:** Fondo `{colors.primary}`, texto `{colors.text-inverse}`, radio `{rounded.full}` (9999px), padding `12px 28px`. Variante de alta presencia visual para landing pages y llamados a la acción destacados.
- **`button-outline`:** Fondo `{colors.surface-card}`, borde 1px `{colors.primary}`, texto `{colors.primary}`, radio `{rounded.sm}`, padding `12px 24px`.

### 2. Tarjetas y Contenedores
- **`card`:** Fondo blanco `{colors.surface-card}`, borde 1px `{colors.border-main}`, radio `{rounded.lg}` (12px), padding `24px`. Contenedor principal de listas de casos, fichas de socio y estadísticas.
- **`card-institutional`:** Fondo `{colors.surface}` (beige), borde 1px `{colors.border-main}`, radio `{rounded.lg}`, padding `24px`. Para bloques destacados de misión, visión y artículos estatutarios.
- **`page-container`:** Superficie global `{colors.surface}` con texto `{colors.text-primary}`.

### 3. Insignias y Badges Semánticos
- **`badge-accent`:** Fondo `{colors.tint}` (`#B3D3E4`), texto `{colors.primary}`, radio `{rounded.full}`, padding `4px 12px`.
- **`badge-status-success`:** Fondo `{colors.success}` (`#15803D`), texto `{colors.text-inverse}`, radio `{rounded.full}`, padding `4px 12px`.
- **`badge-status-warning`:** Fondo `{colors.warning}` (`#92400E`), texto `{colors.text-inverse}`, radio `{rounded.full}`, padding `4px 12px`.
- **`badge-status-danger`:** Fondo `{colors.danger}` (`#B91C1C`), texto `{colors.text-inverse}`, radio `{rounded.full}`, padding `4px 12px`.
- **`badge-status-info`:** Fondo `{colors.info}` (`#0369A1`), texto `{colors.text-inverse}`, radio `{rounded.full}`, padding `4px 12px`.

### 4. Campos de Entrada e Interacción
- **`input-field`:** Fondo blanco `{colors.surface-card}`, texto `{colors.text-primary}`, borde 1px `{colors.border-main}`, radio `{rounded.sm}` (4px), padding `10px 16px`. En estado foco aplica borde `{colors.border-focus}` con sombra perimetral de 2px.
- **`navbar`:** Fondo blanco `{colors.surface-card}`, texto `{colors.primary}`, padding `16px 24px`.
- **`footer`:** Fondo `{colors.brand-black}`, texto `{colors.surface}`, padding `32px 24px`.
- **`dropdown-menu`:** Fondo `{colors.surface-elevated}`, texto `{colors.text-primary}`, radio `{rounded.md}` (8px), padding `8px 0px`.

---

## Do's and Don'ts

### Qué HACER (Do's)
- **HACER:** Utilizar `{colors.primary}` (`#151846`) sobre `{colors.surface}` (`#F2EEE9`) y `{colors.surface-card}` (`#FFFFFF`) para asegurar ratios de contraste superiores a 14:1 (WCAG AAA).
- **HACER:** Combinar botones secundarios `{colors.accent}` (`#6E9DDC`) obligatoriamente con texto `{colors.primary}` (`#151846`) para asegurar un ratio accesible de 6.0:1.
- **HACER:** Emplear `Roboto` para textos de más de dos líneas, descripciones y tablas de expedientes, reservando `Montserrat`, `Garet` y `Archivo Black` para encabezados y destacados.
- **HACER:** Respetar los radios Paper Kit de 4px para controles de formulario e inputs, y 12px para paneles y tarjetas completas.
- **HACER:** Proporcionar foco visible con `{colors.border-focus}` en todos los controles navegables por teclado.

### Qué NO HACER (Don'ts)
- **NO HACER:** Colocar texto blanco `{colors.text-inverse}` sobre fondos de acento `{colors.accent}` o tinte `{colors.tint}`, ya que incumple el ratio mínimo de 4.5:1.
- **NO HACER:** Utilizar negro absoluto (`#000000`) como color de texto para párrafos o interfaces de datos densos; utilizar siempre `{colors.text-primary}` (`#151846`).
- **NO HACER:** Incluir emojis en títulos, botones o tablas de datos administrativos (anti-patrón de IA). Utilizar iconografía vectorial sobria (Material Icons o FontAwesome).
- **NO HACER:** Utilizar fuentes por defecto de asistentes de IA como `Inter`; apegarse estrictamente a la matriz tipográfica oficial de AVEIT.
- **NO HACER:** Emplear más de un color de acento interactivo en la misma pantalla; `{colors.accent}` es el único acento normado para interacción.
- **NO HACER:** Diseñar secciones con filas simétricas forzadas de 3 tarjetas idénticas cuando la información requiera jerarquía o tratamiento asimétrico bento-box.
